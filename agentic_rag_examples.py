"""
Example usage and integration guide for the Advanced Agentic RAG Pipeline.

This script demonstrates:
1. How to initialize and use the agentic RAG pipeline
2. Different types of agricultural queries (vector_db vs web_search)
3. How to integrate with existing FastAPI or Streamlit applications
"""

import logging
from typing import Optional

from rag.agentic_rag_pipeline import AgenticRAGPipeline, run_agentic_rag
from rag.vector_store import ChromaRAGStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_simple_query():
    """Example 1: Simple usage with convenience function."""
    print("\n" + "="*80)
    print("Example 1: Simple Query with Convenience Function")
    print("="*80)
    
    question = "What are the best practices for preventing powdery mildew in tomato crops?"
    
    result = run_agentic_rag(question)
    
    print(f"\nQuestion: {question}")
    print(f"Route: {result['route']}")
    print(f"Is Agriculture: {result['is_agriculture']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nMetadata: {result['metadata']}")


def example_2_real_time_query():
    """Example 2: Real-time data query that uses web search."""
    print("\n" + "="*80)
    print("Example 2: Real-time Query (Web Search Route)")
    print("="*80)
    
    question = "What are the current wheat prices in the international market today?"
    
    result = run_agentic_rag(question)
    
    print(f"\nQuestion: {question}")
    print(f"Route: {result['route']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"\nAnswer:\n{result['answer']}")


def example_3_off_topic_query():
    """Example 3: Off-topic query (domain guardrail)."""
    print("\n" + "="*80)
    print("Example 3: Off-Topic Query (Domain Guardrail)")
    print("="*80)
    
    question = "What is the capital of France?"
    
    result = run_agentic_rag(question)
    
    print(f"\nQuestion: {question}")
    print(f"Route: {result['route']}")
    print(f"Is Agriculture: {result['is_agriculture']}")
    print(f"\nAnswer (Guardrail Response):\n{result['answer']}")


def example_4_advanced_usage():
    """Example 4: Advanced usage with full pipeline control."""
    print("\n" + "="*80)
    print("Example 4: Advanced Usage with Full Pipeline Control")
    print("="*80)
    
    # Initialize vector store once (reuse for multiple queries)
    vector_store = ChromaRAGStore()
    logger.info(f"Vector store initialized with {vector_store.count()} documents")
    
    # Initialize pipeline
    pipeline = AgenticRAGPipeline(vector_store=vector_store)
    
    questions = [
        "How do I optimize irrigation for corn during drought conditions?",
        "What are the latest developments in precision agriculture technology?",
        "Tell me about sustainable farming practices for rice cultivation",
    ]
    
    for question in questions:
        print(f"\n--- Processing: {question}")
        response = pipeline.process(question)
        
        print(f"Route: {response.route}")
        print(f"Reasoning: {response.reasoning}")
        if response.route == "vector_db":
            print(f"Sub-queries generated: {response.metadata.get('sub_queries_used', [])}")
            print(f"Documents retrieved: {response.metadata.get('documents_retrieved', 0)}")
        print(f"Answer preview: {response.answer[:200]}...")


def example_5_integration_with_streamlit():
    """Example 5: How to integrate with Streamlit (pseudo-code)."""
    code = """
# streamlit_app.py
import streamlit as st
from rag.agentic_rag_pipeline import run_agentic_rag

st.title("🌾 Advanced Agentic RAG - Agricultural Assistant")

# Initialize session state
if 'pipeline_history' not in st.session_state:
    st.session_state.pipeline_history = []

# User input
question = st.text_input("Ask an agricultural question:")

if st.button("Search"):
    if question:
        with st.spinner("Analyzing query and retrieving information..."):
            result = run_agentic_rag(question)
            
            # Display results
            st.subheader("Response")
            st.write(result['answer'])
            
            # Show metadata
            with st.expander("View Details"):
                st.json({
                    "route": result['route'],
                    "reasoning": result['reasoning'],
                    "metadata": result['metadata'],
                })
            
            # Store in history
            st.session_state.pipeline_history.append({
                "question": question,
                "route": result['route'],
            })

# Show query history
if st.session_state.pipeline_history:
    st.sidebar.subheader("Query History")
    for item in st.session_state.pipeline_history[-5:]:
        st.sidebar.write(f"Q: {item['question'][:50]}... ({item['route']})")
    """
    print(code)


def example_6_integration_with_fastapi():
    """Example 6: How to integrate with FastAPI (pseudo-code)."""
    code = """
# fastapi_app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag.agentic_rag_pipeline import AgenticRAGPipeline
from rag.vector_store import ChromaRAGStore

app = FastAPI(title="Agentic RAG API")

# Initialize pipeline at startup
pipeline = None

@app.on_event("startup")
async def startup():
    global pipeline
    vector_store = ChromaRAGStore()
    pipeline = AgenticRAGPipeline(vector_store=vector_store)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    route: str
    reasoning: str
    metadata: dict

@app.post("/api/query", response_model=QueryResponse)
async def query_agriculture(request: QueryRequest):
    '''Process agricultural query through agentic RAG pipeline'''
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        response = pipeline.process(request.question)
        
        if response.route == "rejected":
            raise HTTPException(status_code=400, detail=response.answer)
        
        return QueryResponse(
            answer=response.answer,
            route=response.route,
            reasoning=response.reasoning,
            metadata=response.metadata or {},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Usage: curl -X POST "http://localhost:8000/api/query" \\
#              -H "Content-Type: application/json" \\
#              -d '{"question": "How to prevent powdery mildew?"}'
    """
    print(code)


def example_7_batch_processing():
    """Example 7: Batch processing multiple queries."""
    print("\n" + "="*80)
    print("Example 7: Batch Processing Multiple Queries")
    print("="*80)
    
    questions = [
        "What is nitrogen deficiency in crops and how to fix it?",
        "What are common tomato diseases?",
        "How do I prepare soil for planting?",
        "What are weather forecasts for tomorrow?",  # Will likely trigger web_search
    ]
    
    vector_store = ChromaRAGStore()
    pipeline = AgenticRAGPipeline(vector_store=vector_store)
    
    results_summary = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Processing: {question}")
        
        try:
            response = pipeline.process(question)
            
            summary = {
                "question": question,
                "route": response.route,
                "successful": True,
            }
            
            if response.route == "vector_db":
                summary["docs_retrieved"] = response.metadata.get("documents_retrieved", 0)
            
            results_summary.append(summary)
            print(f"  ✓ Route: {response.route}")
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            results_summary.append({
                "question": question,
                "successful": False,
                "error": str(e),
            })
            print(f"  ✗ Error: {e}")
    
    print("\n" + "-"*80)
    print("Batch Processing Summary:")
    print("-"*80)
    for item in results_summary:
        if item["successful"]:
            print(f"✓ {item['question'][:50]}... ({item['route']})")
        else:
            print(f"✗ {item['question'][:50]}... (Error: {item.get('error', 'Unknown')})")


if __name__ == "__main__":
    print("\n🚀 Advanced Agentic RAG Pipeline - Examples\n")
    
    # Run examples
    try:
        example_1_simple_query()
    except Exception as e:
        logger.error(f"Example 1 failed: {e}")
    
    try:
        example_2_real_time_query()
    except Exception as e:
        logger.error(f"Example 2 failed: {e}")
    
    try:
        example_3_off_topic_query()
    except Exception as e:
        logger.error(f"Example 3 failed: {e}")
    
    try:
        example_4_advanced_usage()
    except Exception as e:
        logger.error(f"Example 4 failed: {e}")
    
    # Print integration examples (pseudo-code)
    print("\n" + "="*80)
    print("Example 5: Streamlit Integration (Pseudo-Code)")
    print("="*80)
    example_5_integration_with_streamlit()
    
    print("\n" + "="*80)
    print("Example 6: FastAPI Integration (Pseudo-Code)")
    print("="*80)
    example_6_integration_with_fastapi()
    
    try:
        example_7_batch_processing()
    except Exception as e:
        logger.error(f"Example 7 failed: {e}")
    
    print("\n✅ Examples completed!\n")
