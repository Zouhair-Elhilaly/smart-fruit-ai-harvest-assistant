"""Parallel Executor - Execute vector_db and web_search tasks concurrently with result aggregation."""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from rag.vector_store import ChromaRAGStore, SearchResult
from rag.web_search_agent import search_agriculture_web, create_web_search_agent

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result from executing a single sub-query."""
    sub_query: str
    route: str
    status: str  # 'success' or 'error'
    results: List[Dict[str, Any]] = None  # For vector_db: list of {text, metadata, score}
    web_content: str = None  # For web_search: aggregated web search results
    error: Optional[str] = None


class ParallelExecutor:
    """
    Execute multiple sub-queries in parallel against different retrieval routes.
    Combines results with clear source attribution.
    """
    
    def __init__(self, vector_store: Optional[ChromaRAGStore] = None):
        """
        Initialize the parallel executor.
        
        Args:
            vector_store: Optional ChromaRAGStore instance. If None, creates one.
        """
        self.vector_store = vector_store or ChromaRAGStore()
        self.web_search_agent = create_web_search_agent()
    
    async def execute_vector_search(
        self,
        sub_query: str,
        top_k: int = 3,
    ) -> ExecutionResult:
        """
        Execute a vector database search for a sub-query.
        
        Args:
            sub_query: The question to search for
            top_k: Number of top results to retrieve
        
        Returns:
            ExecutionResult with search results
        """
        try:
            logger.info(f"Vector DB search: {sub_query[:80]}...")
            results = self.vector_store.search(sub_query, top_k=top_k)
            
            formatted_results = [
                {
                    "text": result.text,
                    "metadata": result.metadata,
                    "score": result.score,
                }
                for result in results
            ]
            
            logger.info(f"Retrieved {len(formatted_results)} documents")
            return ExecutionResult(
                sub_query=sub_query,
                route="vector_db",
                status="success",
                results=formatted_results,
            )
        except Exception as error:
            logger.error(f"Vector DB search failed: {error}")
            return ExecutionResult(
                sub_query=sub_query,
                route="vector_db",
                status="error",
                error=str(error),
            )
    
    async def execute_web_search(self, sub_query: str) -> ExecutionResult:
        """
        Execute a web search for a sub-query.
        
        Args:
            sub_query: The question to search for
        
        Returns:
            ExecutionResult with web search content
        """
        try:
            logger.info(f"Web search: {sub_query[:80]}...")
            web_content = search_agriculture_web(sub_query, self.web_search_agent)
            
            logger.info(f"Web search completed, content length: {len(web_content)}")
            return ExecutionResult(
                sub_query=sub_query,
                route="web_search",
                status="success",
                web_content=web_content,
            )
        except Exception as error:
            logger.error(f"Web search failed: {error}")
            return ExecutionResult(
                sub_query=sub_query,
                route="web_search",
                status="error",
                error=str(error),
            )
    
    async def execute_all(
        self,
        tasks: List[Dict[str, str]],
        vector_top_k: int = 3,
    ) -> List[ExecutionResult]:
        """
        Execute multiple tasks in parallel.
        
        Args:
            tasks: List of dicts with 'sub_query' and 'route' keys
            vector_top_k: Number of top results for vector searches
        
        Returns:
            List of ExecutionResults (in the same order as input tasks)
        """
        logger.info(f"Starting parallel execution of {len(tasks)} tasks")
        
        async_tasks = []
        for task in tasks:
            sub_query = task["sub_query"]
            route = task["route"]
            
            if route == "vector_db":
                async_tasks.append(
                    self.execute_vector_search(sub_query, top_k=vector_top_k)
                )
            elif route == "web_search":
                async_tasks.append(self.execute_web_search(sub_query))
            else:
                logger.warning(f"Unknown route: {route}")
                async_tasks.append(
                    asyncio.coroutine(lambda: ExecutionResult(
                        sub_query=sub_query,
                        route=route,
                        status="error",
                        error=f"Unknown route: {route}",
                    ))()
                )
        
        # Run all tasks concurrently
        results = await asyncio.gather(*async_tasks)
        logger.info(f"Parallel execution completed: {len(results)} results")
        
        return results
    
    def execute_sync(
        self,
        tasks: List[Dict[str, str]],
        vector_top_k: int = 3,
    ) -> List[ExecutionResult]:
        """
        Synchronous wrapper around execute_all() for use in non-async contexts.
        Handles Streamlit threading issues by safely creating event loops.
        
        Args:
            tasks: List of dicts with 'sub_query' and 'route' keys
            vector_top_k: Number of top results for vector searches
        
        Returns:
            List of ExecutionResults
        """
        try:
            # Safe event loop handling for Streamlit threading
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Streamlit creates new threads without event loops
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is already running, use a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.execute_all(tasks, vector_top_k)
                    ).result()
            else:
                return asyncio.run(self.execute_all(tasks, vector_top_k))
        except Exception as e:
            logger.error(f"Error in execute_sync: {e}", exc_info=True)
            raise
