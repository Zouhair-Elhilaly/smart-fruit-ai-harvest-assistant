"""Groq LLM client used by the RAG chat assistant."""

import os

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - surfaced at runtime with a clear message
    Groq = None


load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = """\
You are AgroScan Assistant, a concise agricultural AI assistant.
Use the provided context from the project knowledge base when it is relevant.
If the context does not contain the answer, say that clearly and give a careful
general answer only when it is safe to do so. Do not invent document citations.
"""


def _get_client() -> Groq:
    """Create a Groq client from GROQ_API_KEY."""
    if Groq is None:
        raise RuntimeError("The 'groq' package is not installed. Run: pip install groq")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment or .env file.")

    return Groq(api_key=api_key)


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
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )

    return (completion.choices[0].message.content or "").strip()

