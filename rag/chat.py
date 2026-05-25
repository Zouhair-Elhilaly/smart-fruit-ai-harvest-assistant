"""RAG chat orchestration with multi-query decomposition support."""

import logging
from typing import Optional

from llm.groq_client import generate_agrovision_response
from rag.vector_store import ChromaRAGStore, SearchResult
from rag.query_decomposer import create_query_decomposer
from rag.parallel_executor import ParallelExecutor
from rag.context_aggregator import ContextAggregator
from rag.final_synthesizer import create_final_synthesizer

logger = logging.getLogger(__name__)


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


def answer_question_decomposed(
    question: str,
    vector_store: Optional[ChromaRAGStore] = None,
    enable_web_search: bool = True,
) -> dict:
    """
    Advanced RAG with Query Decomposition & Multi-Router.
    
    Breaks down multi-question prompts into distinct sub-questions,
    routes each to the appropriate retrieval method (vector_db or web_search),
    executes in parallel, and synthesizes a comprehensive answer.
    
    Args:
        question: User's question (can contain multiple distinct queries)
        vector_store: Optional ChromaRAGStore instance
        enable_web_search: Whether to allow web_search routing
    
    Returns:
        dict with 'answer', 'sources', 'decomposition_steps', and metadata
    """
    question = (question or "").strip()
    if not question:
        raise ValueError("question cannot be empty")
    
    logger.info(f"Processing decomposed query: {question[:100]}...")
    
    # Step 1: Query Decomposition
    decomposer = create_query_decomposer()
    decomposition = decomposer(question)
    logger.info(f"Decomposition: is_agriculture={decomposition.is_agriculture}, tasks={len(decomposition.tasks)}")
    
    # Check domain guardrail
    if not decomposition.is_agriculture:
        logger.warning(f"Query rejected: not agriculture-related")
        return {
            "answer": "I am an AI assistant specialized strictly in agriculture. How can I help you with your crops today?",
            "sources": [],
            "decomposition_steps": [],
            "is_agriculture": False,
            "metadata": {
                "decomposition_count": 0,
                "rejected_by_guardrail": True,
            },
        }
    
    # If no tasks decomposed (shouldn't happen if is_agriculture=True, but handle it)
    if not decomposition.tasks:
        logger.warning("Query marked agriculture-related but no tasks decomposed")
        return answer_question(question, vector_store, top_k=4)
    
    # Log decomposition details
    decomposition_steps = [
        {
            "sub_query": task.sub_query,
            "route": task.route,
        }
        for task in decomposition.tasks
    ]
    logger.info(f"Decomposition steps: {decomposition_steps}")
    
    # Step 2: Parallel Task Execution
    vector_store = vector_store or ChromaRAGStore()
    executor = ParallelExecutor(vector_store=vector_store)
    
    # Build task list for executor
    tasks = [
        {
            "sub_query": task.sub_query,
            "route": task.route if enable_web_search else "vector_db",
        }
        for task in decomposition.tasks
    ]
    
    execution_results = executor.execute_sync(tasks, vector_top_k=3)
    logger.info(f"Execution complete: {len(execution_results)} results")
    
    # Step 3: Context Aggregation
    aggregator = ContextAggregator()
    aggregated_context = aggregator.aggregate(execution_results)
    logger.info(f"Context aggregated: {aggregated_context.execution_summary}")
    
    # Step 4: Final Synthesis
    synthesizer = create_final_synthesizer()
    final_answer = synthesizer(
        context=aggregated_context.full_context,
        question=question,
    )
    
    logger.info("Answer synthesis complete")
    
    # Format sources for display
    display_sources = []
    for source in aggregated_context.sources:
        if source.get("source_type") == "vector_db":
            display_sources.append({
                "task_idx": source.get("task_idx"),
                "query": source.get("query"),
                "text": source.get("text"),
                "filename": source.get("filename"),
                "page": source.get("page"),
                "score": source.get("score"),
                "type": "vector_db",
            })
        elif source.get("source_type") == "web_search":
            display_sources.append({
                "task_idx": source.get("task_idx"),
                "query": source.get("query"),
                "content": source.get("content"),
                "type": "web_search",
            })
    
    return {
        "answer": final_answer,
        "sources": display_sources,
        "decomposition_steps": decomposition_steps,
        "is_agriculture": True,
        "execution_summary": aggregated_context.execution_summary,
        "metadata": {
            "decomposition_count": len(decomposition_steps),
            "execution_summary": aggregated_context.execution_summary,
        },
    }

