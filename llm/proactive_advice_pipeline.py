from __future__ import annotations

from typing import Any

from llm.proactive_ai import generate_advice_summary, generate_proactive_queries
from rag.vector_store import ChromaRAGStore


def _combine_context(
    store: ChromaRAGStore,
    queries: list[str],
    top_k_per_query: int = 3,
) -> tuple[str, list[dict]]:
    retrieved_chunks: list[str] = []
    sources: list[dict] = []

    for q in queries:
        q = (q or "").strip()
        if not q:
            continue

        results = store.search(q, top_k=top_k_per_query)
        for r in results:
            retrieved_chunks.append(r.text)
            sources.append({
                "text": r.text,
                "score": r.score,
                **(r.metadata or {}),
                "query": q,
            })

    context = "\n\n".join(retrieved_chunks).strip()
    return context, sources


def run_proactive_advice(
    *,
    vision_payload: dict[str, Any],
    vector_store: ChromaRAGStore,
    top_k_per_query: int = 3,
) -> dict[str, Any]:
    """Proactive pipeline: (1) Groq query planning -> (2) Chroma retrieval -> (3) Groq advice."""

    queries = generate_proactive_queries(vision_payload)

    retrieved_context, sources = _combine_context(
        vector_store,
        queries,
        top_k_per_query=top_k_per_query,
    )

    summary_script = generate_advice_summary(vision_payload, retrieved_context)

    return {
        "queries": queries,
        "retrieved_context": retrieved_context,
        "sources": sources,
        "summary": summary_script,
    }

