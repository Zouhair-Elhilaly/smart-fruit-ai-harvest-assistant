"""RAG chat orchestration."""

from typing import Optional

from llm.groq_client import generate_response
from rag.vector_store import ChromaRAGStore, SearchResult


def _format_context(results: list[SearchResult], extra_context: Optional[str] = None) -> str:
    """Build the context block sent to the LLM."""
    sections: list[str] = []

    if extra_context:
        sections.append(f"[Current image analysis]\n{extra_context.strip()}")

    for idx, result in enumerate(results, start=1):
        meta = result.metadata
        page = meta.get("page")
        page_text = "" if page in (None, -1, "-1") else f", page {page}"
        sections.append(
            f"[Source {idx}: {meta.get('filename', 'unknown')}{page_text}, "
            f"score={result.score:.3f}]\n{result.text}"
        )

    return "\n\n".join(sections)


def answer_question(
    question: str,
    vector_store: Optional[ChromaRAGStore] = None,
    top_k: int = 4,
    extra_context: Optional[str] = None,
) -> dict:
    """
    Retrieve context from ChromaDB and generate an answer with Groq.

    Returns a dict with answer, sources, and the raw context used.
    """
    question = (question or "").strip()
    if not question:
        raise ValueError("question cannot be empty")

    store = vector_store or ChromaRAGStore()
    results = store.search(question, top_k=top_k)
    context = _format_context(results, extra_context=extra_context)
    answer = generate_response(prompt=question, context=context)

    return {
        "answer": answer,
        "sources": [
            {
                "text": result.text,
                "score": result.score,
                **result.metadata,
            }
            for result in results
        ],
        "context": context,
    }

