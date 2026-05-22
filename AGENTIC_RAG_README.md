# Advanced Agentic RAG Pipeline

A production-ready, modular Advanced Agentic RAG (Retrieval-Augmented Generation) system for agricultural question answering, built with LangChain and the Groq API (ChatGroq).

## Architecture Overview

The pipeline consists of 4 modular components working together:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC RAG PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Query Analyzer & Router (Domain Guardrail)                 │
│     ├─ Validates: Is query agriculture-related?                │
│     └─ Routes to: "vector_db" or "web_search"                  │
│                                                                 │
│  2. Query Rewriter (Multi-Query Generation)                    │
│     ├─ Breaks complex queries into 2-3 sub-queries            │
│     └─ Optimizes for vector DB retrieval                       │
│                                                                 │
│  3. Dual Retrieval System                                      │
│     ├─ Web Search Agent: Real-time data via DuckDuckGo         │
│     └─ Vector DB: ChromaDB with multi-query retrieval          │
│                                                                 │
│  4. Final Synthesizer                                          │
│     └─ Generates comprehensive, farmer-friendly answer        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Query Analyzer & Router (`query_analyzer_router.py`)

**Purpose**: Domain guardrail that validates agricultural relevance and routes queries.

**Features**:

- Structured Pydantic output parsing
- Returns JSON with:
  - `is_agriculture`: Boolean (true/false)
  - `route`: "vector_db" or "web_search"
  - `reasoning`: Explanation of the decision

**Usage**:

```python
from rag.query_analyzer_router import create_query_analyzer_router

analyzer = create_query_analyzer_router()
analysis = analyzer("How to prevent tomato leaf spots?")
# Returns: QueryAnalysis(is_agriculture=True, route="vector_db", reasoning="...")
```

### 2. Query Rewriter (`query_rewriter.py`)

**Purpose**: Generates optimized sub-queries for multi-query retrieval from ChromaDB.

**Features**:

- Breaks complex questions into 2-3 focused sub-queries
- Each sub-query is standalone and search-optimized
- Uses agricultural terminology

**Usage**:

```python
from rag.query_rewriter import create_query_rewriter

rewriter = create_query_rewriter()
sub_queries = rewriter("How do I improve soil health for better crop yield?")
# Returns: ["soil health improvement techniques", "crop yield optimization", "soil fertility management"]
```

### 3. Web Search Agent (`web_search_agent.py`)

**Purpose**: Autonomous agent for real-time agricultural data retrieval.

**Features**:

- LangChain agent with tool-calling
- DuckDuckGo search integration
- Autonomous decision-making
- Handles follow-up searches

**Usage**:

```python
from rag.web_search_agent import create_web_search_agent, search_agriculture_web

agent = create_web_search_agent()
results = search_agriculture_web("Current rice prices in Asia", agent)
# Returns: Synthesized answer with current market data
```

### 4. Final Synthesizer (`final_synthesizer.py`)

**Purpose**: Generates comprehensive, well-structured final answers.

**Features**:

- Integrates context from either vector DB or web search
- Practical, farmer-focused guidance
- Source attribution
- Structured formatting

**Usage**:

```python
from rag.final_synthesizer import create_final_synthesizer, format_vector_db_context

synthesizer = create_final_synthesizer()
answer = synthesizer(context="[retrieved context]", question="How to prevent powdery mildew?")
```

## Main Pipeline (`agentic_rag_pipeline.py`)

The `AgenticRAGPipeline` class orchestrates all components:

```python
from rag.agentic_rag_pipeline import AgenticRAGPipeline, run_agentic_rag

# Simple usage
result = run_agentic_rag("What are best practices for tomato irrigation?")
print(result['answer'])

# Or with full control
pipeline = AgenticRAGPipeline()
response = pipeline.process("Tell me about nitrogen deficiency in corn")
print(f"Route: {response.route}")
print(f"Answer: {response.answer}")
```

## Installation

### Prerequisites

- Python 3.9+
- GROQ_API_KEY set in environment or `.env` file

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.3
GROQ_MAX_TOKENS=2000

# ChromaDB
CHROMA_COLLECTION=agroscan_rag
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
```

## Usage Examples

### Example 1: Simple Query

```python
from rag.agentic_rag_pipeline import run_agentic_rag

question = "What are the best practices for preventing powdery mildew?"
result = run_agentic_rag(question)

print(f"Route: {result['route']}")
print(f"Answer: {result['answer']}")
print(f"Reasoning: {result['reasoning']}")
print(f"Metadata: {result['metadata']}")
```

### Example 2: Real-time Data Query

```python
question = "What are current wheat prices in international markets?"
result = run_agentic_rag(question)
# Automatically routes to web_search
```

### Example 3: Batch Processing

```python
from rag.agentic_rag_pipeline import AgenticRAGPipeline
from rag.vector_store import ChromaRAGStore

questions = [
    "How to fix nitrogen deficiency?",
    "Best irrigation practices?",
    "What insects are harmful to tomatoes?",
]

vector_store = ChromaRAGStore()
pipeline = AgenticRAGPipeline(vector_store=vector_store)

for question in questions:
    response = pipeline.process(question)
    print(f"Q: {question}")
    print(f"A: {response.answer}\n")
```

### Example 4: Integration with FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel
from rag.agentic_rag_pipeline import AgenticRAGPipeline
from rag.vector_store import ChromaRAGStore

app = FastAPI()
pipeline = None

@app.on_event("startup")
async def startup():
    global pipeline
    vector_store = ChromaRAGStore()
    pipeline = AgenticRAGPipeline(vector_store=vector_store)

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query(request: QueryRequest):
    response = pipeline.process(request.question)
    return {
        "answer": response.answer,
        "route": response.route,
        "reasoning": response.reasoning,
    }
```

### Example 5: Integration with Streamlit

```python
import streamlit as st
from rag.agentic_rag_pipeline import run_agentic_rag

st.title("🌾 Agricultural Assistant")

question = st.text_input("Ask an agricultural question:")

if st.button("Search"):
    if question:
        result = run_agentic_rag(question)
        st.write(result['answer'])

        with st.expander("Details"):
            st.json(result['metadata'])
```

## Query Routing Logic

The pipeline automatically routes queries:

### **Vector DB Route** (for general knowledge)

- Technical questions about crops, diseases, soil
- Procedural guidance (how to plant, harvest, etc.)
- Information about agricultural techniques
- Disease identification and management

**Example questions**:

- "How do I prevent powdery mildew in tomatoes?"
- "What is nitrogen deficiency and how to fix it?"
- "Best practices for crop rotation?"

### **Web Search Route** (for real-time data)

- Current market prices
- Live weather forecasts
- Recent agricultural news
- Real-time disease/pest alerts
- Recent research developments

**Example questions**:

- "What are current wheat prices?"
- "Weather forecast for tomorrow?"
- "Recent tomato disease outbreaks?"
- "Latest farming technology news?"

### **Rejected** (non-agriculture)

Off-topic queries are immediately rejected with a friendly message.

## Response Structure

All pipeline responses follow this structure:

```python
{
    "answer": "str",           # Main answer text
    "route": "str",            # "vector_db", "web_search", or "rejected"
    "is_agriculture": bool,    # Whether query passed domain check
    "reasoning": "str",        # Why the route was chosen
    "sources": [               # Retrieved documents (vector_db only)
        {
            "text": "str",
            "metadata": {...},
            "score": float
        }
    ],
    "metadata": {              # Additional context
        "sub_queries_used": [...],    # Sub-queries generated
        "documents_retrieved": int,
        "web_search_used": bool,
        ...
    }
}
```

## Performance Considerations

1. **Caching**: The pipeline caches embedding models to avoid reloading
2. **Deduplication**: Multi-query retrieval deduplicates results
3. **Token limits**: Configured to stay within LLM token limits
4. **Vector DB**: ChromaDB is optimized for fast semantic search

## Error Handling

The pipeline includes robust error handling:

```python
try:
    result = run_agentic_rag(question)
except ValueError as e:
    # Empty or invalid question
except RuntimeError as e:
    # Missing API keys or dependencies
```

## Troubleshooting

### Issue: "GROQ_API_KEY is not set"

**Solution**: Set your Groq API key:

```bash
export GROQ_API_KEY=your_key_here
# or add to .env file
```

### Issue: ChromaDB errors

**Solution**: Ensure data directory exists and is accessible:

```python
from pathlib import Path
Path("data-RAG").mkdir(exist_ok=True)
```

### Issue: Slow web search queries

**Solution**: Web searches are intentionally slower. Consider caching results or setting appropriate timeouts.

## File Structure

```
rag/
├── __init__.py
├── vector_store.py              # ChromaDB wrapper
├── chat.py                       # Legacy chat interface
├── groq_client.py               # Groq API client
├── query_analyzer_router.py     # NEW: Domain guardrail & routing
├── query_rewriter.py            # NEW: Sub-query generation
├── web_search_agent.py          # NEW: Web search agent
├── final_synthesizer.py         # NEW: Answer synthesis
└── agentic_rag_pipeline.py      # NEW: Main orchestration

agentic_rag_examples.py          # NEW: Comprehensive examples
```

## Next Steps

1. **Data Indexing**: Populate ChromaDB with agricultural documents
2. **Testing**: Run `agentic_rag_examples.py` to test all components
3. **Customization**: Modify system prompts and routing logic as needed
4. **Deployment**: Deploy via FastAPI or Streamlit
5. **Monitoring**: Track query performance and model accuracy

## Architecture Diagram

```
User Question
      ↓
┌─────────────────────────────────────────┐
│ Query Analyzer & Router                 │
│ (Domain Guardrail + Routing)            │
└──────────────┬──────────────────────────┘
               ↓
        Is Agriculture?
        /              \
      NO              YES
      ↓                ↓
  REJECT          Route Selection
                  /            \
            web_search      vector_db
              ↓                ↓
        ┌─────────────┐  ┌──────────────────┐
        │ Web Search  │  │ Query Rewriter   │
        │ Agent       │  │ (Sub-queries)    │
        │ (Real-time) │  └────────┬─────────┘
        └──────┬──────┘           ↓
               │        ┌─────────────────────┐
               │        │ Multi-Query         │
               │        │ Retrieval from      │
               │        │ ChromaDB            │
               │        └────────┬────────────┘
               │                 ↓
               │        Aggregated Context
               │                 ↓
               └────────┬────────┘
                        ↓
            ┌────────────────────────────┐
            │ Final Synthesizer          │
            │ (Answer Generation)        │
            └────────────┬───────────────┘
                         ↓
                   Final Answer
                         ↓
                    To User
```

## Contributing

When adding new components:

1. Follow the existing modular structure
2. Use Pydantic for structured output
3. Include comprehensive docstrings
4. Add error handling
5. Include usage examples

## License

[Your License Here]

## Support

For issues or questions:

1. Check `agentic_rag_examples.py` for usage patterns
2. Review error messages and traceback
3. Ensure all environment variables are set
4. Verify ChromaDB data exists

---

**Built with**: LangChain, Groq ChatGroq, ChromaDB, DuckDuckGo Search
