# Advanced Agentic RAG Pipeline - Complete Reference Guide

## 📚 Table of Contents

1. [Architecture](#architecture)
2. [Components](#components)
3. [Usage Patterns](#usage-patterns)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│          Advanced Agentic RAG Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: User Question                                      │
│    ↓                                                        │
│  ┌────────────────────────────────────────────┐            │
│  │ 1. Query Analyzer & Router                 │            │
│  │    ├─ Check: Is agriculture-related?      │            │
│  │    ├─ Decide: vector_db or web_search?    │            │
│  │    └─ Return: QueryAnalysis (JSON)        │            │
│  └────────────────┬─────────────────────────┘             │
│                   │                                        │
│         ┌─────────┴─────────┐                              │
│         ↓                   ↓                              │
│   NOT AGRICULTURE     IS AGRICULTURE                       │
│         │                   │                              │
│         ↓                   ↓                              │
│    [REJECT]         ┌──────────────────────────┐          │
│                     │ 2. Query Rewriter        │          │
│                     │    └─ Generate sub-      │          │
│                     │      queries (2-3)       │          │
│                     └──────────────────────────┘          │
│                             │                              │
│                      ┌──────┴────────┐                     │
│                      ↓               ↓                     │
│              VECTOR_DB          WEB_SEARCH                │
│                      │               │                     │
│                      ↓               ↓                     │
│        ┌───────────────────┐  ┌─────────────┐            │
│        │ 3a. Multi-Query   │  │ 3b. Web     │            │
│        │ ChromaDB          │  │ Search      │            │
│        │ Retrieval         │  │ Agent       │            │
│        └─────────┬─────────┘  └──────┬──────┘            │
│                  │                   │                     │
│                  └───────────┬───────┘                     │
│                              ↓                             │
│                  ┌──────────────────────┐                 │
│                  │ 4. Final Synthesizer │                 │
│                  │    └─ Generate final │                 │
│                  │      answer          │                 │
│                  └──────────┬───────────┘                 │
│                             ↓                             │
│                     Output: Answer                        │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Question Input
    │
    ├─→ Query Analyzer & Router
    │   ├─→ Pydantic: QueryAnalysis
    │   └─→ Decision: agriculture? route?
    │
    ├─→ Query Rewriter (if vector_db)
    │   ├─→ ChatGroq: Generate sub-queries
    │   ├─→ Pydantic: SubQueries
    │   └─→ Multi-Query Retrieval
    │
    ├─→ ChromaDB Search (if vector_db)
    │   ├─→ Search with Query 1
    │   ├─→ Search with Query 2
    │   ├─→ Search with Query 3
    │   └─→ Deduplicate results
    │
    ├─→ Web Search Agent (if web_search)
    │   ├─→ LangChain Agent
    │   ├─→ DuckDuckGo tool
    │   └─→ Autonomous search
    │
    └─→ Final Synthesizer
        ├─→ Format context
        ├─→ ChatGroq: Generate answer
        └─→ Answer Output
```

---

## Components

### 1. Query Analyzer & Router

**Module**: `rag/query_analyzer_router.py`

**Purpose**: Domain guardrail + intelligent routing

**Key Classes**:

```python
class QueryAnalysis(BaseModel):
    is_agriculture: bool
    route: str  # "vector_db" | "web_search"
    reasoning: str
```

**Main Functions**:

```python
def create_query_analyzer_router() -> callable
    # Creates and returns the analyzer chain
    # Returns: Function that takes question → QueryAnalysis

def validate_agriculture_query(question: str) -> Optional[str]
    # Returns error message if not agriculture, None if valid
```

**Example**:

```python
from rag.query_analyzer_router import create_query_analyzer_router

analyzer = create_query_analyzer_router()

# Valid agriculture query
analysis = analyzer("How to prevent tomato disease?")
assert analysis.is_agriculture == True
assert analysis.route in ["vector_db", "web_search"]

# Non-agriculture query
analysis = analyzer("What's the capital of France?")
assert analysis.is_agriculture == False
```

---

### 2. Query Rewriter

**Module**: `rag/query_rewriter.py`

**Purpose**: Generate optimized sub-queries for multi-query retrieval

**Key Classes**:

```python
class SubQueries(BaseModel):
    sub_queries: List[str]  # 2-3 queries
```

**Main Functions**:

```python
def create_query_rewriter() -> callable
    # Creates and returns the rewriter chain
    # Returns: Function that takes question → List[str]
```

**Example**:

```python
from rag.query_rewriter import create_query_rewriter

rewriter = create_query_rewriter()

question = "How to improve soil health and crop yield?"
sub_queries = rewriter(question)
# Returns: [
#     "soil health improvement techniques",
#     "crop yield optimization methods",
#     "sustainable farming practices"
# ]
```

---

### 3. Web Search Agent

**Module**: `rag/web_search_agent.py`

**Purpose**: Autonomous agent for real-time agricultural data

**Key Functions**:

```python
def create_web_search_agent() -> AgentExecutor
    # Creates and returns the agent
    # Returns: LangChain AgentExecutor

def search_agriculture_web(question: str, agent: Optional[AgentExecutor] = None) -> str
    # Executes web search
    # Returns: Synthesized answer string
```

**Example**:

```python
from rag.web_search_agent import create_web_search_agent, search_agriculture_web

agent = create_web_search_agent()
result = search_agriculture_web("Current wheat prices?", agent)
print(result)  # Current market information
```

---

### 4. Final Synthesizer

**Module**: `rag/final_synthesizer.py`

**Purpose**: Generate comprehensive, well-structured answers

**Main Functions**:

```python
def create_final_synthesizer() -> callable
    # Creates and returns the synthesis chain
    # Returns: Function that takes (context, question) → answer

def format_vector_db_context(search_results: List[dict]) -> str
    # Formats ChromaDB results into context string

def format_web_search_context(web_results: str) -> str
    # Formats web search results into context string
```

**Example**:

```python
from rag.final_synthesizer import create_final_synthesizer, format_vector_db_context

synthesizer = create_final_synthesizer()
context = "Nitrogen deficiency: yellowing leaves, stunted growth"
answer = synthesizer(context, "How to identify nitrogen deficiency?")
```

---

### 5. Main Orchestrator

**Module**: `rag/agentic_rag_pipeline.py`

**Purpose**: Coordinates all components

**Key Classes**:

```python
@dataclass
class AgenticRAGResponse:
    answer: str
    route: str  # "vector_db" | "web_search" | "rejected"
    is_agriculture: bool
    reasoning: str
    context_sources: list = None
    metadata: Dict[str, Any] = None

class AgenticRAGPipeline:
    def __init__(self, vector_store: Optional[ChromaRAGStore] = None)

    def process(self, question: str) -> AgenticRAGResponse
        # Main entry point for processing questions
        # Executes complete workflow
        # Returns: AgenticRAGResponse with answer
```

**Main Functions**:

```python
def run_agentic_rag(question: str, vector_store: Optional[ChromaRAGStore] = None) -> Dict[str, Any]
    # Convenience function for simple usage
    # Returns: Dict with answer, route, reasoning, metadata
```

**Example**:

```python
from rag.agentic_rag_pipeline import AgenticRAGPipeline, run_agentic_rag

# Simple usage
result = run_agentic_rag("How to prevent powdery mildew?")
print(result['answer'])

# Full control
pipeline = AgenticRAGPipeline()
response = pipeline.process("Your question")
print(f"Route: {response.route}")
print(f"Answer: {response.answer}")
print(f"Sources: {len(response.context_sources)} documents")
```

---

## Usage Patterns

### Pattern 1: Simple Query

```python
from rag.agentic_rag_pipeline import run_agentic_rag

question = "How to prevent powdery mildew in tomatoes?"
result = run_agentic_rag(question)

print(f"Answer: {result['answer']}")
print(f"Route: {result['route']}")
```

### Pattern 2: Full Pipeline Control

```python
from rag.agentic_rag_pipeline import AgenticRAGPipeline
from rag.vector_store import ChromaRAGStore

vector_store = ChromaRAGStore()
pipeline = AgenticRAGPipeline(vector_store=vector_store)

response = pipeline.process("Your question")

if response.route == "vector_db":
    print(f"Documents retrieved: {response.metadata['documents_retrieved']}")
    for source in response.context_sources:
        print(f"  - {source['metadata']['filename']}")

print(f"Answer: {response.answer}")
```

### Pattern 3: Batch Processing

```python
from rag.agentic_rag_pipeline import AgenticRAGPipeline

pipeline = AgenticRAGPipeline()
questions = ["Q1?", "Q2?", "Q3?"]

for question in questions:
    response = pipeline.process(question)
    print(f"{question} → {response.route}")
```

### Pattern 4: Error Handling

```python
from rag.agentic_rag_pipeline import run_agentic_rag

try:
    result = run_agentic_rag(question)
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"System error: {e}")
```

---

## API Reference

### Query Analyzer & Router

```python
create_query_analyzer_router() -> Callable[[str], QueryAnalysis]
```

**Parameters**:

- None (uses environment configuration)

**Returns**:

- Function that takes `question: str` and returns `QueryAnalysis`

**QueryAnalysis fields**:

- `is_agriculture: bool` - Is query agriculture-related?
- `route: str` - "vector_db" or "web_search"
- `reasoning: str` - Explanation of decision

---

### Query Rewriter

```python
create_query_rewriter() -> Callable[[str], List[str]]
```

**Parameters**:

- None (uses environment configuration)

**Returns**:

- Function that takes `question: str` and returns `List[str]` (2-3 sub-queries)

---

### Web Search Agent

```python
create_web_search_agent() -> AgentExecutor

search_agriculture_web(question: str, agent: Optional[AgentExecutor] = None) -> str
```

**Parameters**:

- `question: str` - Agricultural question
- `agent: Optional[AgentExecutor]` - Pre-created agent (optional)

**Returns**:

- `str` - Synthesized answer from web search

---

### Final Synthesizer

```python
create_final_synthesizer() -> Callable[[str, str], str]

format_vector_db_context(search_results: List[dict]) -> str

format_web_search_context(web_results: str) -> str
```

**Parameters**:

- `context: str` - Aggregated context
- `question: str` - User question
- `search_results: List[dict]` - ChromaDB search results
- `web_results: str` - Web search output

**Returns**:

- `str` - Formatted answer or context

---

### Agentic RAG Pipeline

```python
class AgenticRAGPipeline:
    def __init__(self, vector_store: Optional[ChromaRAGStore] = None)

    def process(self, question: str) -> AgenticRAGResponse

run_agentic_rag(question: str, vector_store: Optional[ChromaRAGStore] = None) -> Dict[str, Any]
```

**Parameters**:

- `question: str` - Agricultural question
- `vector_store: Optional[ChromaRAGStore]` - Pre-initialized store (optional)

**Returns**:

- `AgenticRAGResponse` or `Dict` with:
  - `answer: str` - Final answer
  - `route: str` - Routing decision
  - `is_agriculture: bool` - Agriculture check
  - `reasoning: str` - Route reasoning
  - `sources: List` - Retrieved documents
  - `metadata: Dict` - Process metadata

---

## Configuration

### Environment Variables

```env
# Required
GROQ_API_KEY=your_api_key_here

# Optional (defaults provided)
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.3
GROQ_MAX_TOKENS=2000

# ChromaDB
CHROMA_COLLECTION=agroscan_rag
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG
RAG_DATA_DIR=data-RAG
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
EMBEDDING_BATCH_SIZE=64
```

### .env File

Create `.env` in project root:

```env
GROQ_API_KEY=gsk_your_key_here_12345
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.3
```

---

## Deployment

### FastAPI Deployment

```bash
# Install
pip install fastapi uvicorn

# Run (development)
uvicorn fastapi_deployment:app --reload

# Run (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker fastapi_deployment:app

# Test
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"How to prevent powdery mildew?"}'
```

### Streamlit Deployment

```bash
# Install
pip install streamlit

# Run
streamlit run streamlit_deployment.py

# Access: http://localhost:8501
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GROQ_API_KEY=your_key_here
CMD ["uvicorn", "fastapi_deployment:app", "--host", "0.0.0.0"]
```

```bash
docker build -t agentic-rag .
docker run -p 8000:8000 -e GROQ_API_KEY=xxx agentic-rag
```

---

## Troubleshooting

### Issue: GROQ_API_KEY not set

**Solution**:

```bash
# Option 1: Environment variable
export GROQ_API_KEY=your_key_here

# Option 2: .env file
echo "GROQ_API_KEY=your_key_here" > .env

# Option 3: Verify
python -c "import os; print(os.getenv('GROQ_API_KEY'))"
```

### Issue: ChromaDB connection error

**Solution**:

```bash
# Ensure data directory exists
mkdir -p .chroma

# Or specify custom path in code
from rag.vector_store import ChromaRAGStore
store = ChromaRAGStore(persist_dir="/path/to/chroma")
```

### Issue: Module not found

**Solution**:

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify installation
python validate_agentic_rag.py
```

### Issue: Slow queries

**Solution**:

- First query loads embedding model (slower)
- Subsequent queries are faster
- Consider preloading: `pipeline = AgenticRAGPipeline()`

### Issue: Web search not returning results

**Solution**:

- DuckDuckGo sometimes blocks rapid requests
- Add delays between queries
- Consider alternative search tools (Tavily, SerpAPI)

### Issue: Memory usage high

**Solution**:

- Reduce chunk size: `RAG_CHUNK_SIZE=500`
- Reduce batch size: `EMBEDDING_BATCH_SIZE=32`
- Use smaller embedding model: `sentence-transformers/all-MiniLM-L6-v2`

---

## Performance Tips

1. **Reuse Pipeline**: Create once, use multiple times

   ```python
   pipeline = AgenticRAGPipeline()
   for question in questions:
       response = pipeline.process(question)
   ```

2. **Batch Processing**: Process multiple queries efficiently

   ```python
   for question in questions:
       response = pipeline.process(question)
   ```

3. **Caching**: Cache embedding model
   - Automatically cached in memory
   - First query loads model
   - Subsequent queries faster

4. **Optimize ChromaDB**: Use persistent storage

   ```python
   store = ChromaRAGStore(persist_dir=".chroma")
   ```

5. **Monitor Resources**: Track memory and CPU
   - Log response times
   - Profile bottlenecks
   - Adjust batch sizes

---

## Support

**For Issues**:

1. Check `validate_agentic_rag.py` output
2. Review error logs
3. Check `AGENTIC_RAG_README.md`
4. Review example code
5. Check environment variables

**For Questions**:

1. Review `quick_start.py`
2. Check `agentic_rag_examples.py`
3. Read inline docstrings
4. Review FastAPI deployment template

---

**Built with**: LangChain, Groq ChatGroq, ChromaDB, DuckDuckGo Search
