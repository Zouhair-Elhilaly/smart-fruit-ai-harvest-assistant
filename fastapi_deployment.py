"""
FastAPI Deployment Template for Advanced Agentic RAG Pipeline

This is a ready-to-use FastAPI application that can be deployed immediately.
Just fill in your GROQ_API_KEY and run!
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from rag.agentic_rag_pipeline import AgenticRAGPipeline, AgenticRAGResponse
from rag.vector_store import ChromaRAGStore

# ============================================================================
# CONFIGURATION
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Agricultural RAG API",
    description="Advanced Agentic RAG Pipeline for Agricultural Queries",
    version="1.0.0",
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for agricultural queries."""
    question: str
    top_k: Optional[int] = 4

    class Config:
        example = {
            "question": "How do I prevent powdery mildew in tomatoes?",
            "top_k": 4
        }


class SourceInfo(BaseModel):
    """Information about a retrieved source document."""
    text: str
    filename: Optional[str] = None
    score: float
    page: Optional[int] = None


class QueryResponse(BaseModel):
    """Response model for agricultural queries."""
    success: bool
    route: str
    is_agriculture: bool
    reasoning: str
    answer: str
    sources: list[SourceInfo] = []
    metadata: dict = {}

    class Config:
        example = {
            "success": True,
            "route": "vector_db",
            "is_agriculture": True,
            "reasoning": "Query is about crop disease prevention",
            "answer": "To prevent powdery mildew...",
            "sources": [],
            "metadata": {"documents_retrieved": 3}
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    pipeline_initialized: bool
    vector_store_documents: int


# ============================================================================
# GLOBAL STATE
# ============================================================================

pipeline: Optional[AgenticRAGPipeline] = None
vector_store: Optional[ChromaRAGStore] = None


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup."""
    global pipeline, vector_store
    
    try:
        logger.info("Initializing Advanced Agentic RAG Pipeline...")
        
        vector_store = ChromaRAGStore()
        doc_count = vector_store.count()
        logger.info(f"Vector store initialized with {doc_count} documents")
        
        pipeline = AgenticRAGPipeline(vector_store=vector_store)
        logger.info("✓ Pipeline initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Advanced Agentic RAG Pipeline...")
    # Add any cleanup code here


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and pipeline status."""
    if pipeline is None or vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized"
        )
    
    return HealthResponse(
        status="healthy",
        pipeline_initialized=True,
        vector_store_documents=vector_store.count()
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_agriculture(request: QueryRequest):
    """
    Process an agricultural query through the agentic RAG pipeline.
    
    **Query Routing:**
    - Validates agricultural relevance (domain guardrail)
    - Routes to "vector_db" for general knowledge
    - Routes to "web_search" for real-time data
    - Rejects non-agricultural queries
    
    **Response includes:**
    - Comprehensive answer
    - Route taken (vector_db/web_search/rejected)
    - Reasoning for the route decision
    - Retrieved sources (if vector_db)
    - Metadata about the process
    """
    
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized"
        )
    
    try:
        # Validate input
        if not request.question or not request.question.strip():
            raise ValueError("Question cannot be empty")
        
        logger.info(f"Processing query: {request.question[:100]}...")
        
        # Process query
        response: AgenticRAGResponse = pipeline.process(request.question)
        
        # Handle rejected queries
        if response.route == "rejected":
            raise HTTPException(
                status_code=400,
                detail=response.answer
            )
        
        # Format sources
        sources = []
        if response.context_sources:
            for source in response.context_sources:
                sources.append(SourceInfo(
                    text=source.get('text', ''),
                    filename=source.get('metadata', {}).get('filename'),
                    score=source.get('score', 0),
                    page=source.get('metadata', {}).get('page'),
                ))
        
        # Return response
        return QueryResponse(
            success=True,
            route=response.route,
            is_agriculture=response.is_agriculture,
            reasoning=response.reasoning,
            answer=response.answer,
            sources=sources,
            metadata=response.metadata or {},
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing query"
        )


@app.post("/api/v1/batch-query")
async def batch_query(requests: list[QueryRequest]):
    """
    Process multiple queries in batch.
    
    Useful for:
    - Processing multiple farmer questions
    - Batch analysis of agricultural scenarios
    - Performance testing
    """
    
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized"
        )
    
    results = []
    
    for i, request in enumerate(requests):
        try:
            logger.info(f"Batch processing query {i+1}/{len(requests)}")
            
            response: AgenticRAGResponse = pipeline.process(request.question)
            
            if response.route == "rejected":
                results.append({
                    "success": False,
                    "error": response.answer
                })
            else:
                results.append({
                    "success": True,
                    "route": response.route,
                    "answer": response.answer,
                    "reasoning": response.reasoning,
                })
        
        except Exception as e:
            logger.error(f"Error in batch query {i+1}: {e}")
            results.append({
                "success": False,
                "error": str(e)
            })
    
    return {"queries_processed": len(requests), "results": results}


@app.get("/api/v1/info")
async def pipeline_info():
    """Get information about the pipeline configuration."""
    if pipeline is None or vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized"
        )
    
    return {
        "name": "Advanced Agentic RAG Pipeline",
        "version": "1.0.0",
        "description": "Agricultural question answering with intelligent routing",
        "components": [
            "Query Analyzer & Router (Domain Guardrail)",
            "Query Rewriter (Multi-Query Generation)",
            "Web Search Agent (Real-time Data)",
            "Final Synthesizer (Answer Generation)",
        ],
        "vector_store": {
            "type": "ChromaDB",
            "documents": vector_store.count(),
            "embedding_model": vector_store.embedding_model_name,
            "collection_name": vector_store.collection_name,
        },
        "llm": {
            "provider": "Groq",
            "model": "llama-3.3-70b-versatile",
        }
    }


# ============================================================================
# EXAMPLE QUERIES ENDPOINT (for testing)
# ============================================================================

@app.get("/api/v1/examples")
async def get_example_queries():
    """Get example agricultural queries for testing."""
    return {
        "examples": [
            {
                "category": "Disease Prevention",
                "question": "How do I prevent powdery mildew in tomatoes?",
                "expected_route": "vector_db"
            },
            {
                "category": "Real-time Market Data",
                "question": "What are current wheat prices in international markets?",
                "expected_route": "web_search"
            },
            {
                "category": "Crop Management",
                "question": "Best practices for corn irrigation during drought?",
                "expected_route": "vector_db"
            },
            {
                "category": "Soil Health",
                "question": "How to improve soil fertility naturally?",
                "expected_route": "vector_db"
            },
            {
                "category": "Weather-based",
                "question": "Weather forecast for tomorrow?",
                "expected_route": "web_search"
            },
            {
                "category": "Off-topic",
                "question": "What is the capital of France?",
                "expected_route": "rejected"
            },
        ]
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root with documentation links."""
    return {
        "name": "Advanced Agentic RAG Pipeline",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/api/v1/query",
            "batch_query": "/api/v1/batch-query",
            "info": "/api/v1/info",
            "examples": "/api/v1/examples",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        }
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return {
        "success": False,
        "error": str(exc)
    }


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    """Handle runtime errors."""
    logger.error(f"Runtime error: {exc}", exc_info=True)
    return {
        "success": False,
        "error": "Internal server error"
    }


# ============================================================================
# USAGE
# ============================================================================

"""
DEPLOYMENT INSTRUCTIONS:

1. Install dependencies:
   pip install -r requirements.txt

2. Set environment variables:
   export GROQ_API_KEY=your_api_key_here
   
   Or create .env file with:
   GROQ_API_KEY=your_api_key_here

3. Run the server:
   uvicorn fastapi_deployment:app --reload
   
   Or for production:
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker fastapi_deployment:app

4. Access the API:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - OpenAPI JSON: http://localhost:8000/openapi.json

5. Example queries:
   
   curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"question":"How to prevent powdery mildew?"}'
   
   curl -X GET "http://localhost:8000/health"
   
   curl -X GET "http://localhost:8000/api/v1/examples"

DEPLOYMENT OPTIONS:

1. Local development:
   uvicorn fastapi_deployment:app --reload

2. Production with Gunicorn:
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker fastapi_deployment:app

3. Docker:
   docker build -t agentic-rag .
   docker run -p 8000:8000 -e GROQ_API_KEY=xxx agentic-rag

4. Cloud deployment:
   - Heroku: Add Procfile with "web: gunicorn ..."
   - AWS: Deploy to API Gateway + Lambda
   - Google Cloud: Deploy to Cloud Run
   - Azure: Deploy to App Service

SECURITY CONSIDERATIONS:

1. Set CORS origins appropriately for production
2. Implement authentication/authorization as needed
3. Use HTTPS in production
4. Set rate limiting
5. Monitor API usage and logs
6. Keep API keys secure (use environment variables, secrets manager)
"""

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Advanced Agentic RAG API...")
    print("📖 Docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "fastapi_deployment:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
