"""Context Aggregator - Combine results from all retrieval routes with source attribution."""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AggregatedContext:
    """Aggregated context from all execution results."""
    full_context: str  # Combined context string for LLM
    sources: List[Dict[str, Any]]  # List of all sources for UI display
    execution_summary: Dict[str, Any]  # Summary stats about execution


class ContextAggregator:
    """
    Combine results from parallel task execution into a unified context
    with clear source attribution for the final synthesizer.
    """
    
    @staticmethod
    def aggregate(execution_results: List[Any]) -> AggregatedContext:
        """
        Aggregate execution results into a unified context.
        
        Args:
            execution_results: List of ExecutionResult objects from ParallelExecutor
        
        Returns:
            AggregatedContext with formatted context and source metadata
        """
        sections: List[str] = []
        all_sources: List[Dict[str, Any]] = []
        
        vector_db_count = 0
        web_search_count = 0
        success_count = 0
        error_count = 0
        
        for idx, result in enumerate(execution_results, start=1):
            logger.debug(f"Processing result {idx}/{len(execution_results)}: {result.route}")
            
            if result.status == "error":
                error_count += 1
                logger.warning(f"Task failed - route: {result.route}, error: {result.error}")
                sections.append(
                    f"[Task {idx}: {result.route.upper()}]\n"
                    f"Query: {result.sub_query}\n"
                    f"Status: ERROR - {result.error}\n"
                )
                continue
            
            success_count += 1
            
            # Process vector_db results
            if result.route == "vector_db":
                vector_db_count += 1
                if result.results:
                    sections.append(f"[Task {idx}: VECTOR_DB SEARCH]")
                    sections.append(f"Query: {result.sub_query}\n")
                    
                    for doc_idx, doc in enumerate(result.results, start=1):
                        text = doc.get("text", "")
                        metadata = doc.get("metadata", {})
                        score = doc.get("score", 0.0)
                        
                        filename = metadata.get("filename", "unknown")
                        page = metadata.get("page", -1)
                        page_text = "" if page in (None, -1, "-1") else f", page {page}"
                        
                        source_label = f"[VectorDB-Task{idx}-Doc{doc_idx}: {filename}{page_text} (relevance: {score:.2f})]"
                        sections.append(f"{source_label}\n{text}\n")
                        
                        # Track source for UI
                        all_sources.append({
                            "task_idx": idx,
                            "source_type": "vector_db",
                            "query": result.sub_query,
                            "filename": filename,
                            "page": page,
                            "text": text,
                            "score": score,
                        })
                else:
                    sections.append(
                        f"[Task {idx}: VECTOR_DB SEARCH]\n"
                        f"Query: {result.sub_query}\n"
                        f"No documents retrieved.\n"
                    )
            
            # Process web_search results
            elif result.route == "web_search":
                web_search_count += 1
                if result.web_content and result.web_content.strip():
                    sections.append(f"[Task {idx}: WEB SEARCH]")
                    sections.append(f"Query: {result.sub_query}\n")
                    sections.append(result.web_content)
                    
                    # Track source for UI
                    all_sources.append({
                        "task_idx": idx,
                        "source_type": "web_search",
                        "query": result.sub_query,
                        "content": result.web_content[:300],  # Truncate for UI display
                    })
                else:
                    sections.append(
                        f"[Task {idx}: WEB SEARCH]\n"
                        f"Query: {result.sub_query}\n"
                        f"No web results found.\n"
                    )
        
        # Build final context string
        full_context = "\n".join(sections)
        
        if not full_context.strip():
            full_context = "[No relevant information was retrieved from any source.]"
        
        # Build execution summary
        execution_summary = {
            "total_tasks": len(execution_results),
            "successful_tasks": success_count,
            "failed_tasks": error_count,
            "vector_db_searches": vector_db_count,
            "web_searches": web_search_count,
            "total_sources": len(all_sources),
        }
        
        logger.info(f"Aggregation complete: {execution_summary}")
        
        return AggregatedContext(
            full_context=full_context,
            sources=all_sources,
            execution_summary=execution_summary,
        )
    
    @staticmethod
    def format_context_for_display(aggregated_context: AggregatedContext) -> str:
        """
        Format the aggregated context for user display (for debugging/transparency).
        
        Args:
            aggregated_context: The AggregatedContext object
        
        Returns:
            Formatted string for display
        """
        summary = aggregated_context.execution_summary
        display = (
            f"**Retrieval Summary:**\n"
            f"- Tasks executed: {summary['total_tasks']}\n"
            f"- Successful: {summary['successful_tasks']}\n"
            f"- Failed: {summary['failed_tasks']}\n"
            f"- Vector DB searches: {summary['vector_db_searches']}\n"
            f"- Web searches: {summary['web_searches']}\n"
            f"- Total sources retrieved: {summary['total_sources']}\n"
        )
        return display
