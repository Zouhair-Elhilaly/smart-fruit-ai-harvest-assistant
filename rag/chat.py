"""RAG chat orchestration."""

from typing import Optional

from llm.groq_client import generate_agrovision_response
from rag.vector_store import ChromaRAGStore, SearchResult


def _format_context(results: list[SearchResult]) -> str:
    """Build the retrieved document context block sent to the LLM."""
    sections: list[str] = []

    for idx, result in enumerate(results, start=1):
        meta = result.metadata
        page = meta.get("page")
        page_text = "" if page in (None, -1, "-1") else f", page {page}"
        sections.append(
            f"[Source {idx}: {meta.get('filename', 'unknown')}{page_text}, "
            f"score={result.score:.3f}]\n{result.text}"
        )

    return "\n\n".join(sections)


def _build_search_query(
    question: str,
) -> str:
    """Create a retrieval query using only the user's text question."""
    parts = [
        question,
        "fruit ripening storage postharvest humidity disease prevention",
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())



def _as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def answer_question(
    question: str,
    vector_store: Optional[ChromaRAGStore] = None,
    top_k: int = 4,
) -> dict:
    """Text-only RAG: retrieve from ChromaDB and generate an AgroVision response."""
    question = (question or "").strip()
    if not question:
        raise ValueError("question cannot be empty")

    store = vector_store or ChromaRAGStore()
    search_query = _build_search_query(question)
    results = store.search(search_query, top_k=top_k)
    context = _format_context(results)

    answer = generate_agrovision_response(
        fruit_class="unknown",
        confidence=None,
        caption="",
        context_docs=context,
        user_question=question,
    )


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
        "search_query": search_query,
    }
