from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from llm.groq_client import _get_client


load_dotenv()


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _coerce_confidence(payload: dict[str, Any]) -> float | None:
    try:
        v = payload.get("confidence")
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def generate_proactive_queries(vision_payload: dict) -> list[str]:
    """Generate 1–3 targeted RAG sub-queries for proactive advice.

    Uses Groq JSON mode: response_format={"type": "json_object"}.

    Returns:
        list[str]: 1..3 short RAG queries.
    """

    vision_payload = vision_payload or {}

    fruit_class = str(
        vision_payload.get("class")
        or vision_payload.get("raw_class")
        or vision_payload.get("class_label")
        or "unknown"
    )
    caption = str(vision_payload.get("caption") or "")
    confidence = _coerce_confidence(vision_payload)

    client = _get_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "450"))

    system_prompt = (
    "Tu es AgroVision, un expert en planification agricole proactive pour le Maroc. "
    "Analyse les champs du 'vision_payload' (classe du fruit, score de confiance, légende BLIP) "
    "pour déduire l'état physique de la culture (saine, malade, gâtée/pourrie, ou stade de maturité). "
    "En fonction de cet état, génère 1 à 3 requêtes de recherche RAG ciblées en FRANÇAIS, car la base de connaissances est en français. "
    "Les requêtes doivent être concises, techniques et optimisées pour la recherche documentaire (mots-clés, pas de phrases complètes). "
    "Instructions contextuelles : "
    "1. Si la culture est saine : Priorise les conseils de conservation, de logistique et de prolongation de la durée de vie (post-récolte). "
    "2. Si la culture est malade ou pourrie : Priorise les traitements phytosanitaires autorisés au Maroc, les mesures de quarantaine, l'assainissement et les méthodes d'élimination sûres. "
    "Assure-toi que les termes techniques correspondent aux pratiques agricoles locales au Maroc."
)

    user_message = _json_text(
        {
            "vision_payload": {
                "class": fruit_class,
                "confidence": confidence,
                "caption": caption,
                "top_probabilities": vision_payload.get("top_probabilities"),
                "is_ood": vision_payload.get("is_ood"),
            }
        }
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Return JSON only. Inputs JSON:\n" + user_message,
            },
        ],
        temperature=temperature,
        max_completion_tokens=max_tokens,
        response_format={"type": "json_object"},
    )

    text = (completion.choices[0].message.content or "").strip()
    if not text:
        return []
    print("Raw Groq queries response:", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    
    queries = parsed.get("suggested_queries") or parsed.get("queries") or parsed.get("sub_queries")
    print("\n\nthe query for crop viison is : ",queries,"\n\n")
    if not isinstance(queries, list):
        return []

    cleaned: list[str] = []
    for q in queries:
        if q is None:
            continue
        s = str(q).strip()
        if not s:
            continue
        cleaned.append(s)

    if not cleaned:
        return []

    if len(cleaned) <= 3:
        return cleaned

    return cleaned[:3]


def generate_advice_summary(vision_payload: dict, retrieved_context: str) -> str:
    """Generate the final user-friendly advice & summary script.

    Args:
        vision_payload: dict with class, confidence, caption, etc.
        retrieved_context: combined text from RAG retrieval.

    Returns:
        str: concise advice and summary script.
    """

    vision_payload = vision_payload or {}

    fruit_class = str(
        vision_payload.get("class")
        or vision_payload.get("raw_class")
        or vision_payload.get("class_label")
        or "unknown"
    )
    confidence = _coerce_confidence(vision_payload)
    caption = str(vision_payload.get("caption") or "")

    client = _get_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "650"))

    system_prompt = (
        "You are AgroVision Advice Generator."
        "Create a concise, user-friendly Advice & Summary script for farmers."
        "Ground your recommendations ONLY in the retrieved_context."
        "If retrieved_context is empty or contains no strong evidence, say so and give only safe general guidance."
    )

    user_message = (
        "Vision payload (JSON):\n"
        + _json_text(
            {
                "class": fruit_class,
                "confidence": confidence,
                "caption": caption,
                "is_ood": vision_payload.get("is_ood"),
            }
        )
        + "\n\n"
        + "Retrieved context:\n"
        + (retrieved_context or "")
        + "\n\n"
        + "Write the script in this structure:\n"
        + "1) Summary (1-2 sentences)\n"
        + "2) What to do now (bullet list)\n"
        + "3) Storage / treatment recommendations (bullet list)\n"
        + "4) Prevention (short bullet list)\n"
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )

    return (completion.choices[0].message.content or "").strip()

