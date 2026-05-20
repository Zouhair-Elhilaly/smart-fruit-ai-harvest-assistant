"""
Quick-Start Guide for Advanced Agentic RAG Pipeline

This guide walks you through setting up and using the agentic RAG system.
"""

# ============================================================================
# STEP 1: INSTALLATION
# ============================================================================

"""
Run these commands in your terminal:

1. Install dependencies:
   pip install -r requirements.txt

2. Set up your Groq API key:
   - Get API key from: https://console.groq.com
   - Create a .env file in project root:
     
     GROQ_API_KEY=your_api_key_here
     GROQ_MODEL=llama-3.3-70b-versatile
     GROQ_TEMPERATURE=0.3
     GROQ_MAX_TOKENS=2000

3. Verify installation:
   python -c "from rag.agentic_rag_pipeline import AgenticRAGPipeline; print('✓ Ready!')"
"""

# ============================================================================
# STEP 2: BASIC USAGE (5 minutes)
# ============================================================================

def quick_example_basic():
    """The simplest way to use the pipeline."""
    from rag.agentic_rag_pipeline import run_agentic_rag
    
    # Ask a question
    question = "How do I prevent tomato leaf spots?"
    
    # Get answer
    result = run_agentic_rag(question)
    
    # Print response
    print(f"Answer: {result['answer']}")
    print(f"Route: {result['route']}")
    print(f"Reasoning: {result['reasoning']}")


# ============================================================================
# STEP 3: UNDERSTANDING ROUTING (10 minutes)
# ============================================================================

def understand_routing():
    """Learn how queries are routed."""
    from rag.agentic_rag_pipeline import run_agentic_rag
    
    # Example 1: Vector DB routing (general knowledge)
    q1 = "What causes nitrogen deficiency in crops?"
    r1 = run_agentic_rag(q1)
    print(f"Q1: {q1}")
    print(f"Route: {r1['route']}")  # Expected: 'vector_db'
    print()
    
    # Example 2: Web search routing (real-time data)
    q2 = "What are current corn prices?"
    r2 = run_agentic_rag(q2)
    print(f"Q2: {q2}")
    print(f"Route: {r2['route']}")  # Expected: 'web_search'
    print()
    
    # Example 3: Rejected (off-topic)
    q3 = "What is the capital of France?"
    r3 = run_agentic_rag(q3)
    print(f"Q3: {q3}")
    print(f"Route: {r3['route']}")  # Expected: 'rejected'
    print(f"Answer: {r3['answer']}")


# ============================================================================
# STEP 4: ADVANCED USAGE (15 minutes)
# ============================================================================

def advanced_example():
    """Full control over the pipeline."""
    from rag.agentic_rag_pipeline import AgenticRAGPipeline
    from rag.vector_store import ChromaRAGStore
    
    # Initialize pipeline once
    vector_store = ChromaRAGStore()
    pipeline = AgenticRAGPipeline(vector_store=vector_store)
    
    # Process a question
    question = "How to optimize irrigation for corn?"
    response = pipeline.process(question)
    
    # Access response details
    print(f"Answer:\n{response.answer}\n")
    print(f"Route: {response.route}")
    print(f"Is Agriculture: {response.is_agriculture}")
    print(f"Reasoning: {response.reasoning}")
    
    if response.route == "vector_db":
        print(f"Sub-queries: {response.metadata.get('sub_queries_used', [])}")
        print(f"Documents retrieved: {response.metadata.get('documents_retrieved', 0)}")
        
        # Access sources
        for i, source in enumerate(response.context_sources[:2], 1):
            print(f"\nSource {i}:")
            print(f"  File: {source['metadata'].get('filename', 'N/A')}")
            print(f"  Score: {source['score']:.3f}")
            print(f"  Text: {source['text'][:100]}...")


# ============================================================================
# STEP 5: BATCH PROCESSING (20 minutes)
# ============================================================================

def batch_processing_example():
    """Process multiple questions efficiently."""
    from rag.agentic_rag_pipeline import AgenticRAGPipeline
    from rag.vector_store import ChromaRAGStore
    
    # Initialize once for multiple queries
    vector_store = ChromaRAGStore()
    pipeline = AgenticRAGPipeline(vector_store=vector_store)
    
    questions = [
        "How to prevent powdery mildew?",
        "Best time to plant tomatoes?",
        "How to improve soil fertility?",
        "What are current crop prices?",  # This will use web_search
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {question}")
        
        try:
            response = pipeline.process(question)
            print(f"  Route: {response.route}")
            print(f"  Answer: {response.answer[:150]}...")
        except Exception as e:
            print(f"  ✗ Error: {e}")


# ============================================================================
# STEP 6: UNDERSTANDING COMPONENTS (25 minutes)
# ============================================================================

def understand_components():
    """Learn about each component individually."""
    
    # Component 1: Query Analyzer & Router
    print("\n1. QUERY ANALYZER & ROUTER")
    print("-" * 50)
    from rag.query_analyzer_router import create_query_analyzer_router
    
    analyzer = create_query_analyzer_router()
    analysis = analyzer("What's the best fertilizer for tomatoes?")
    print(f"Is Agriculture: {analysis.is_agriculture}")
    print(f"Route: {analysis.route}")
    print(f"Reasoning: {analysis.reasoning}")
    
    # Component 2: Query Rewriter
    print("\n2. QUERY REWRITER")
    print("-" * 50)
    from rag.query_rewriter import create_query_rewriter
    
    rewriter = create_query_rewriter()
    sub_queries = rewriter("How do I improve soil health and increase crop yield?")
    print(f"Original: How do I improve soil health and increase crop yield?")
    print(f"Sub-queries:")
    for i, sq in enumerate(sub_queries, 1):
        print(f"  {i}. {sq}")
    
    # Component 3: Web Search Agent
    print("\n3. WEB SEARCH AGENT")
    print("-" * 50)
    from rag.web_search_agent import create_web_search_agent, search_agriculture_web
    
    agent = create_web_search_agent()
    web_result = search_agriculture_web(
        "What are current wheat prices in the market?",
        agent
    )
    print(f"Web search result (first 200 chars):")
    print(f"{web_result[:200]}...")
    
    # Component 4: Final Synthesizer
    print("\n4. FINAL SYNTHESIZER")
    print("-" * 50)
    from rag.final_synthesizer import create_final_synthesizer
    
    synthesizer = create_final_synthesizer()
    sample_context = "Nitrogen deficiency symptoms: yellowing leaves, stunted growth, reduced yield"
    answer = synthesizer(
        context=sample_context,
        question="How do I identify nitrogen deficiency?"
    )
    print(f"Synthesized answer:")
    print(answer[:200])


# ============================================================================
# STEP 7: DEPLOYMENT OPTIONS (30 minutes)
# ============================================================================

def deployment_fastapi_example():
    """How to deploy with FastAPI."""
    code = """
# fastapi_app.py
from fastapi import FastAPI
from pydantic import BaseModel
from rag.agentic_rag_pipeline import AgenticRAGPipeline
from rag.vector_store import ChromaRAGStore

app = FastAPI(title="Agricultural RAG API")
pipeline = None

@app.on_event("startup")
async def startup():
    global pipeline
    vector_store = ChromaRAGStore()
    pipeline = AgenticRAGPipeline(vector_store=vector_store)
    print("✓ Pipeline initialized")

class Question(BaseModel):
    text: str

@app.post("/ask")
async def ask(query: Question):
    response = pipeline.process(query.text)
    
    if response.route == "rejected":
        return {"error": response.answer}
    
    return {
        "answer": response.answer,
        "route": response.route,
        "reasoning": response.reasoning,
    }

# Run: uvicorn fastapi_app:app --reload
# Test: curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"text":"How to prevent tomato disease?"}'
    """
    print(code)


def deployment_streamlit_example():
    """How to deploy with Streamlit."""
    code = """
# streamlit_app.py
import streamlit as st
from rag.agentic_rag_pipeline import run_agentic_rag

st.set_page_config(page_title="Agricultural Assistant", page_icon="🌾")
st.title("🌾 Agricultural RAG Assistant")

st.markdown("Ask any agricultural question and get instant answers powered by AI.")

question = st.text_input("Your question:")

if st.button("Get Answer"):
    if question:
        with st.spinner("Thinking..."):
            result = run_agentic_rag(question)
        
        st.subheader("Answer")
        st.write(result['answer'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Route", result['route'])
        with col2:
            st.metric("Agriculture", "✓" if result['is_agriculture'] else "✗")
        
        with st.expander("Details"):
            st.json(result['metadata'])

# Run: streamlit run streamlit_app.py
    """
    print(code)


# ============================================================================
# STEP 8: COMMON PATTERNS
# ============================================================================

def common_patterns():
    """Common usage patterns."""
    
    patterns = """
    PATTERN 1: Simple one-off query
    ─────────────────────────────────
    from rag.agentic_rag_pipeline import run_agentic_rag
    
    result = run_agentic_rag("Your question here")
    print(result['answer'])
    
    
    PATTERN 2: Reuse pipeline for multiple queries
    ───────────────────────────────────────────────
    from rag.agentic_rag_pipeline import AgenticRAGPipeline
    
    pipeline = AgenticRAGPipeline()
    
    for question in questions:
        response = pipeline.process(question)
        # Use response
    
    
    PATTERN 3: Custom vector store
    ──────────────────────────────
    from rag.agentic_rag_pipeline import AgenticRAGPipeline
    from rag.vector_store import ChromaRAGStore
    
    custom_store = ChromaRAGStore(
        data_dir="path/to/data",
        collection_name="my_crops"
    )
    pipeline = AgenticRAGPipeline(vector_store=custom_store)
    
    
    PATTERN 4: Error handling
    ─────────────────────────
    from rag.agentic_rag_pipeline import run_agentic_rag
    
    try:
        result = run_agentic_rag(question)
    except ValueError as e:
        print(f"Invalid input: {e}")
    except RuntimeError as e:
        print(f"System error: {e}")
    """
    
    print(patterns)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  ADVANCED AGENTIC RAG PIPELINE - QUICK START GUIDE")
    print("=" * 70)
    
    import sys
    
    if len(sys.argv) > 1:
        step = sys.argv[1]
    else:
        print("\nAvailable steps:")
        print("  python quick_start.py basic       - Basic usage")
        print("  python quick_start.py routing     - Understanding routing")
        print("  python quick_start.py advanced    - Advanced usage")
        print("  python quick_start.py batch       - Batch processing")
        print("  python quick_start.py components  - Component details")
        print("  python quick_start.py fastapi     - FastAPI deployment")
        print("  python quick_start.py streamlit   - Streamlit deployment")
        print("  python quick_start.py patterns    - Common patterns")
        sys.exit(0)
    
    try:
        if step == "basic":
            quick_example_basic()
        elif step == "routing":
            understand_routing()
        elif step == "advanced":
            advanced_example()
        elif step == "batch":
            batch_processing_example()
        elif step == "components":
            understand_components()
        elif step == "fastapi":
            deployment_fastapi_example()
        elif step == "streamlit":
            deployment_streamlit_example()
        elif step == "patterns":
            common_patterns()
        else:
            print(f"Unknown step: {step}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
