"""Groq LLM client used by the AgroVision RAG assistant."""

import json
import os
from typing import Any

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - surfaced at runtime with a clear message
    Groq = None


load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"
LEGACY_SYSTEM_PROMPT = """\
You are AgroScan Assistant, a concise agricultural AI assistant.
Use the provided context from the project knowledge base when it is relevant.
If the context does not contain the answer, say that clearly and give a careful
general answer only when it is safe to do so. Do not invent document citations.
"""
AGROVISION_SYSTEM_PROMPT = """\
You are AgroVision AI, an advanced agricultural multimodal assistant.

You analyze agricultural images using:
1. BLIP image captioning
2. Fruit classification model output
3. ChromaDB agricultural knowledge base documents
4. An optional user question

Rules:
- Return only one valid JSON object. Do not use markdown fences.
- Use the BLIP caption and classifier output to describe the image.
- Use only retrieved ChromaDB documents for factual agricultural support.
- If retrieved documents are empty or not relevant, set agriculture_context to
  "No strong evidence found in database".
- Do not hallucinate scientific facts or document citations.
- If confidence is below 0.80, mention uncertainty.
- Keep explanations simple, practical, and farmer-focused.
- The JSON object must contain exactly these keys:
  observation, reasoning, agriculture_context, advice, prevention,
  suggested_queries.
- suggested_queries must be an array of short RAG search queries.
"""

REQUIRED_AGROVISION_KEYS = (
    "observation",
    "reasoning",
    "agriculture_context",
    "advice",
    "prevention",
    "suggested_queries",
)


def _get_client() -> Groq:
    """Create a Groq client from GROQ_API_KEY."""
    if Groq is None:
        raise RuntimeError("The 'groq' package is not installed. Run: pip install groq")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment or .env file.")

    return Groq(api_key=api_key)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _fallback_queries(fruit_class: str, caption: str, user_question: str) -> list[str]:
    base = " ".join(
        part.strip()
        for part in [fruit_class, caption, user_question]
        if part and part.strip()
    )
    base = base[:120].strip() or "fruit condition"
    return [
        f"{base} ripening storage humidity",
        f"{base} postharvest disease prevention",
    ]


def _strict_json_or_fallback(
    response_text: str,
    *,
    fruit_class: str,
    confidence: float | None,
    caption: str,
    context_docs: str,
    user_question: str,
) -> str:
    """Normalize an LLM response so the UI always receives strict JSON."""
    text = (response_text or "").strip()
    payload: dict[str, Any] | None = None

    if text:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(text[start : end + 1])
                    if isinstance(parsed, dict):
                        payload = parsed
                except json.JSONDecodeError:
                    payload = None

    if payload is None:
        confidence_text = "unknown" if confidence is None else f"{confidence:.2f}"
        uncertainty_text = (
            " Classification confidence is below 0.80, so this analysis is uncertain."
            if confidence is not None and confidence < 0.80
            else ""
        )
        return _json_text(
            {
                "observation": (
                    f"Classifier output: {fruit_class or 'unknown'} "
                    f"(confidence {confidence_text}). "
                    f"BLIP caption: {caption or 'unavailable'}."
                    f"{uncertainty_text}"
                ),
                "reasoning": (
                    "The language model did not return a parseable JSON analysis, "
                    "so no additional agricultural reasoning is added."
                ),
                "agriculture_context": (
                    "No strong evidence found in database"
                    if not context_docs.strip()
                    else "Retrieved database context was available, but no parseable grounded analysis was returned."
                ),
                "advice": "Review the image, classifier confidence, and retrieved sources before taking action.",
                "prevention": "Capture clear images and retrieve targeted postharvest or crop-health documents for future analysis.",
                "suggested_queries": _fallback_queries(fruit_class, caption, user_question),
            }
        )

    normalized: dict[str, Any] = {}
    for key in REQUIRED_AGROVISION_KEYS:
        value = payload.get(key)
        if key == "suggested_queries":
            if not isinstance(value, list):
                value = _fallback_queries(fruit_class, caption, user_question)
            normalized[key] = [str(item) for item in value if str(item).strip()][:5]
            fallback_queries = _fallback_queries(fruit_class, caption, user_question)
            for query in fallback_queries:
                if len(normalized[key]) >= 2:
                    break
                if query not in normalized[key]:
                    normalized[key].append(query)
            continue
        normalized[key] = str(value).strip() if value is not None else ""

    if not context_docs.strip():
        normalized["agriculture_context"] = "No strong evidence found in database"
    elif not normalized["agriculture_context"]:
        normalized["agriculture_context"] = (
            "Retrieved database context was used, but the model did not summarize the support."
        )

    if confidence is not None and confidence < 0.80:
        uncertainty_note = (
            f" Classification confidence is below 0.80 ({confidence:.2f}), "
            "so this analysis is uncertain."
        )
        uncertainty_text = (
            normalized["observation"] + " " + normalized["reasoning"]
        ).lower()
        if "uncertain" not in uncertainty_text and "uncertainty" not in uncertainty_text:
            normalized["observation"] = (
                normalized["observation"].rstrip() + uncertainty_note
            ).strip()

    return _json_text(normalized)


def generate_response(prompt: str, context: str) -> str:
    """
    Generate an LLM answer using Groq.

    Args:
        prompt: User question.
        context: Retrieved RAG context, optionally including current image prediction.

    Returns:
        Assistant response text.
    """
    prompt = (prompt or "").strip()
    context = (context or "").strip()
    if not prompt:
        raise ValueError("prompt cannot be empty")

    client = _get_client()
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "800"))

    user_message = (
        "Context:\n"
        f"{context if context else '[No relevant context was retrieved.]'}\n\n"
        "Question:\n"
        f"{prompt}\n\n"
        "Answer with practical, grounded guidance. Mention when the answer is based on retrieved context."
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": LEGACY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )

    return (completion.choices[0].message.content or "").strip()


def generate_agrovision_response(
    *,
    fruit_class: str,
    confidence: float | None,
    caption: str,
    context_docs: str,
    user_question: str = "",
) -> str:
    """
    Generate the strict AgroVision JSON response from multimodal/RAG inputs.

    Args:
        fruit_class: Top class from the fruit classification model.
        confidence: Model confidence as a 0-1 float.
        caption: BLIP caption generated from the image.
        context_docs: Retrieved ChromaDB context only.
        user_question: Optional user question.

    Returns:
        Strict JSON string with the required AgroVision keys.
    """
    fruit_class = (fruit_class or "").strip() or "unknown"
    caption = (caption or "").strip()
    context_docs = (context_docs or "").strip()
    user_question = (user_question or "").strip()

    client = _get_client()
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    temperature = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "900"))

    confidence_text = "unknown" if confidence is None else f"{confidence:.4f}"
    user_message = f"""\
INPUTS

1. Vision Model Output:
- class: {fruit_class}
- confidence: {confidence_text}

2. BLIP Image Caption:
{caption if caption else "[No BLIP caption was available.]"}

3. Retrieved Agricultural Knowledge (RAG):
{context_docs if context_docs else "[No relevant context was retrieved.]"}

4. User Question (optional):
{user_question if user_question else "[No user question provided.]"}

TASK
Follow these steps inside the JSON fields:
1. Understand the image using the BLIP caption and class prediction.
2. Explain why the fruit may be in this condition using simple agricultural logic.
3. Ground factual support only in the retrieved ChromaDB documents.
4. Give practical farming or storage advice.
5. Explain prevention for the future.
6. Suggest better RAG search queries.

Return exactly this JSON shape:
{{
  "observation": "what is seen in image",
  "reasoning": "why fruit is in this state",
  "agriculture_context": "support from RAG docs",
  "advice": "practical steps to take",
  "prevention": "how to avoid in future",
  "suggested_queries": [
    "query 1",
    "query 2"
  ]
}}
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": AGROVISION_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )

    response_text = (completion.choices[0].message.content or "").strip()
    return _strict_json_or_fallback(
        response_text,
        fruit_class=fruit_class,
        confidence=confidence,
        caption=caption,
        context_docs=context_docs,
        user_question=user_question,
    )
