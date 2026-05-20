"""Advanced Agentic RAG Pipeline - Main orchestration module."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

from rag.query_analyzer_router import create_query_analyzer_router, validate_agriculture_query
from rag.query_rewriter import create_query_rewriter
from rag.web_search_agent import create_web_search_agent, search_agriculture_web
from rag.final_synthesizer import (
    create_final_synthesizer,
    format_vector_db_context,
    format_web_search_context,
)
from rag.vector_store import ChromaRAGStore

logger = logging.getLogger(__name__)


@dataclass
class AgenticRAGResponse:
    """Structured response from the agentic RAG pipeline."""
    answer: str
    route: str  # 'vector_db' or 'web_search'
    is_agriculture: bool
    reasoning: str
    context_sources: list = None
    metadata: Dict[str, Any] = None


class AgenticRAGPipeline:
    """
    Advanced Agentic RAG Pipeline combining:
    1. Query Analysis & Routing (Domain Guardrail)
    2. Query Rewriting (Sub-query Generation)
    3. Web Search Agent (Real-time Data)
    4. Final Synthesizer (Answer Generation)
    """
    
    def __init__(self, vector_store: Optional[ChromaRAGStore] = None):
        """
        Initialize the agentic RAG pipeline.
        
        Args:
            vector_store: Optional ChromaRAGStore instance. If None, creates one.
        """
        self.vector_store = vector_store or ChromaRAGStore()
        
        # Initialize all components
        self.analyzer_router = create_query_analyzer_router()
        self.query_rewriter = create_query_rewriter()
        self.web_search_agent = create_web_search_agent()
        self.synthesizer = create_final_synthesizer()
        
        logger.info("Advanced Agentic RAG Pipeline initialized")
    
    def process(self, question: str) -> AgenticRAGResponse:
        """
        Process a user question through the complete agentic RAG pipeline.
        
        Workflow:
        1. Validate that question is agriculture-related (domain guardrail)
        2. Analyze and route the query (vector_db or web_search)
        3. If web_search: Use agent with web search
           If vector_db: Generate sub-queries and retrieve from ChromaDB
        4. Synthesize final answer
        
        Args:
            question: The user's agricultural question
        
        Returns:
            AgenticRAGResponse with answer, route, and metadata
        """
        question = (question or "").strip()
        if not question:
            raise ValueError("Question cannot be empty")
        
        logger.info(f"Processing question: {question[:100]}...")
        
        # Step 1: Domain Guardrail - Validate agriculture query
        guardrail_error = validate_agriculture_query(question)
        if guardrail_error:
            logger.warning(f"Non-agriculture query rejected: {question[:50]}...")
            return AgenticRAGResponse(
                answer=guardrail_error,
                route="rejected",
                is_agriculture=False,
                reasoning="Query is not related to agriculture",
                context_sources=[],
                metadata={"rejected": True},
            )
        
        # Step 2: Query Analysis & Routing
        analysis = self.analyzer_router(question)
        logger.info(f"Query route: {analysis.route}, reasoning: {analysis.reasoning}")
        
        # Step 3a: Web Search Route
        if analysis.route == "web_search":
            logger.info("Routing to web search agent")
            web_results = search_agriculture_web(question, self.web_search_agent)
            context = format_web_search_context(web_results)
            
            # Step 4: Synthesize answer
            final_answer = self.synthesizer(context, question)
            
            return AgenticRAGResponse(
                answer=final_answer,
                route="web_search",
                is_agriculture=True,
                reasoning=analysis.reasoning,
                context_sources=[],
                metadata={
                    "web_search_used": True,
                    "raw_web_results": web_results[:500],
                },
            )
        
        # Step 3b: Vector DB Route with Multi-Query Retrieval
        else:
            logger.info("Routing to vector database with multi-query retrieval")
            
            # Generate sub-queries
            sub_queries = self.query_rewriter(question)
            logger.info(f"Generated {len(sub_queries)} sub-queries: {sub_queries}")
            
            # Retrieve context using each sub-query
            all_results = []
            seen_texts = set()  # Deduplicate
            
            for sub_query in sub_queries:
                results = self.vector_store.search(sub_query, top_k=3)
                for result in results:
                    text_hash = hash(result.text)
                    if text_hash not in seen_texts:
                        seen_texts.add(text_hash)
                        all_results.append({
                            "text": result.text,
                            "metadata": result.metadata,
                            "score": result.score,
                        })
            
            logger.info(f"Retrieved {len(all_results)} unique documents")
            
            # Format context from retrieved results
            context = format_vector_db_context(all_results)
            
            # Step 4: Synthesize answer
            final_answer = self.synthesizer(context, question)
            
            return AgenticRAGResponse(
                answer=final_answer,
                route="vector_db",
                is_agriculture=True,
                reasoning=analysis.reasoning,
                context_sources=all_results,
                metadata={
                    "sub_queries_used": sub_queries,
                    "documents_retrieved": len(all_results),
                },
            )


def run_agentic_rag(
    question: str,
    vector_store: Optional[ChromaRAGStore] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run the agentic RAG pipeline on a single question.
    
    Args:
        question: The user's agricultural question
        vector_store: Optional pre-initialized ChromaRAGStore
    
    Returns:
        Dictionary with answer and metadata
    """
    pipeline = AgenticRAGPipeline(vector_store=vector_store)
    response = pipeline.process(question)
    
    return {
        "answer": response.answer,
        "route": response.route,
        "is_agriculture": response.is_agriculture,
        "reasoning": response.reasoning,
        "sources": response.context_sources or [],
        "metadata": response.metadata or {},
    }
