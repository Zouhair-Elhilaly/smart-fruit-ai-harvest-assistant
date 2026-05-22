# Advanced Agentic RAG Pipeline - Architecture Diagram

## System Architecture

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                    ADVANCED AGENTIC RAG PIPELINE                              ║
║                  Powered by LangChain & Groq ChatGroq                          ║
╚════════════════════════════════════════════════════════════════════════════════╝

                              USER QUESTION
                                    ↓
         ┌──────────────────────────────────────────────────────────┐
         │                                                          │
         │  STEP 1: QUERY ANALYZER & ROUTER                       │
         │  ──────────────────────────────────────────────        │
         │  • Check: Is agriculture-related?                       │
         │  • Decide: vector_db or web_search?                    │
         │  • Output: QueryAnalysis (Pydantic JSON)               │
         │                                                          │
         └──────────────┬─────────────────────────────────────────┘
                        │
                        ↓
                   IS AGRICULTURE?
                        │
            ┌───────────┼───────────┐
            │           │           │
           YES          NO       UNCERTAIN
            │           │           │
            ↓           ↓           ↓
       CONTINUE     REJECT      VALIDATE
            │       (Reply)         │
            │                       ↓
            │                   CONTINUE
            │
            └────────────────────┬─────────────────────────┘
                                 ↓
                        SELECT ROUTING
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
             VECTOR_DB       WEB_SEARCH      DEBUG
                 │               │
                 ↓               ↓
        ┌─────────────────┐  ┌──────────────────┐
        │ STEP 2:         │  │ STEP 3b:         │
        │ QUERY REWRITER  │  │ WEB SEARCH AGENT │
        │ ─────────────── │  │ ──────────────── │
        │ Generate        │  │ • LangChain      │
        │ sub-queries     │  │   Agent          │
        │ (2-3 queries)   │  │ • DuckDuckGo     │
        │                 │  │   tool           │
        │ Output:         │  │ • Autonomous     │
        │ List[str]       │  │   search         │
        └────────┬────────┘  │                  │
                 │            │ Output:         │
                 │            │ str (answer)    │
                 │            └────────┬────────┘
                 │                    │
                 ↓                    ↓
        ┌─────────────────────────────────────────┐
        │ STEP 3a: MULTI-QUERY RETRIEVAL          │
        │ ───────────────────────────────────────│
        │                                         │
        │ ┌─────────────────────────────────┐    │
        │ │ Query 1 → ChromaDB Search       │    │
        │ │ ↓ (Top 3 results)               │    │
        │ │ ┌──────────────────────────┐    │    │
        │ │ │ Doc 1 (score: 0.89)      │    │    │
        │ │ │ Doc 2 (score: 0.85)      │    │    │
        │ │ │ Doc 3 (score: 0.78)      │    │    │
        │ │ └──────────────────────────┘    │    │
        │ └─────────────────────────────────┘    │
        │                                         │
        │ ┌─────────────────────────────────┐    │
        │ │ Query 2 → ChromaDB Search       │    │
        │ │ ↓ (Top 3 results)               │    │
        │ │ ┌──────────────────────────┐    │    │
        │ │ │ Doc 4 (score: 0.82)      │    │    │
        │ │ │ Doc 5 (score: 0.74)      │    │    │
        │ │ │ Doc 6 (score: 0.68)      │    │    │
        │ │ └──────────────────────────┘    │    │
        │ └─────────────────────────────────┘    │
        │                                         │
        │ ┌─────────────────────────────────┐    │
        │ │ Query 3 → ChromaDB Search       │    │
        │ │ ↓ (Top 3 results)               │    │
        │ │ ┌──────────────────────────┐    │    │
        │ │ │ Doc 7 (score: 0.88)      │    │    │
        │ │ │ Doc 8 (score: 0.80)      │    │    │
        │ │ │ Doc 9 (score: 0.72)      │    │    │
        │ │ └──────────────────────────┘    │    │
        │ └─────────────────────────────────┘    │
        │                                         │
        │ ┌─────────────────────────────────┐    │
        │ │ DEDUPLICATION                   │    │
        │ │ Remove duplicate documents      │    │
        │ │ Keep highest scoring versions   │    │
        │ │ Final: 7 unique documents      │    │
        │ └─────────────────────────────────┘    │
        │                                         │
        │ Output: List[SearchResult]              │
        └──────────────────┬──────────────────────┘
                           │
                    ┌──────┴───────┐
                    ↓              ↓
            (vector_db)      (web_search)
              Results          Results
                │              │
                └──────┬───────┘
                       │
                       ↓
        ┌─────────────────────────────────────────┐
        │ STEP 4: CONTEXT FORMATTING              │
        │ ──────────────────────────────────────  │
        │ • Format vector DB results into         │
        │   structured context                    │
        │ • OR format web search results          │
        │ • Include source attribution            │
        │ • Maintain relevance scores             │
        │                                         │
        │ Output: str (formatted context)         │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
        ┌─────────────────────────────────────────┐
        │ STEP 5: FINAL SYNTHESIZER               │
        │ ──────────────────────────────────────  │
        │ • Input: Context + Original Question    │
        │ • Call: ChatGroq LLM                    │
        │ • Process: Generate comprehensive ans  │
        │ • Output: Farmer-focused answer         │
        │                                         │
        │ System Prompt:                          │
        │ "You are an expert agricultural         │
        │  assistant. Generate practical,        │
        │  grounded, farmer-friendly guidance"   │
        │                                         │
        │ Output: str (final answer)              │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
                    ┌─────────────┐
                    │   ANSWER    │
                    │             │
                    │ "To prevent │
                    │  powdery    │
                    │  mildew,    │
                    │  you should │
                    │  ..."       │
                    └─────────────┘
                           │
                           ↓
                    RETURN TO USER

```

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                │
│            (agentic_rag_pipeline.py)                            │
│                                                                  │
│  ┌─ process(question)                                          │
│  │                                                              │
│  ├─→ [1] Query Analyzer & Router                              │
│  │       (query_analyzer_router.py)                           │
│  │       └─→ analysis = analyzer(question)                    │
│  │           ├─ is_agriculture: bool                          │
│  │           ├─ route: str                                    │
│  │           └─ reasoning: str                                │
│  │                                                              │
│  ├─→ [2a] IF route == "vector_db":                            │
│  │         ├─ Query Rewriter                                  │
│  │         │  (query_rewriter.py)                            │
│  │         │  └─→ sub_queries = rewriter(question)           │
│  │         │                                                   │
│  │         ├─ Multi-Query Retrieval                           │
│  │         │  └─→ FOR each sub_query:                        │
│  │         │       results += store.search(sub_query)        │
│  │         │                                                   │
│  │         └─ Deduplication                                   │
│  │            └─→ final_results = dedup(all_results)         │
│  │                                                              │
│  ├─→ [2b] IF route == "web_search":                           │
│  │         └─ Web Search Agent                                │
│  │            (web_search_agent.py)                          │
│  │            └─→ web_results = agent.invoke(question)      │
│  │                                                              │
│  ├─→ [3] Format Context                                       │
│  │       (final_synthesizer.py)                              │
│  │       ├─ Vector DB: format_vector_db_context()           │
│  │       └─ Web: format_web_search_context()                 │
│  │                                                              │
│  └─→ [4] Final Synthesizer                                    │
│          (final_synthesizer.py)                              │
│          └─→ answer = synthesizer(context, question)        │
│                                                              │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
                           User Input
                                │
                                ↓
                        ┌───────────────┐
                        │   Question    │
                        │    String     │
                        └───────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                ↓               ↓               ↓
            ┌────────┐    ┌────────┐      ┌────────┐
            │ Analyze│    │ Extract│      │ Clean  │
            │        │    │        │      │        │
            └───┬────┘    └───┬────┘      └───┬────┘
                │            │              │
                └────────┬───┴──────────────┘
                         │
                         ↓
            ┌──────────────────────────┐
            │ QueryAnalysis            │
            │ {                        │
            │   is_agriculture: bool,  │
            │   route: str,            │
            │   reasoning: str         │
            │ }                        │
            └─────┬──────────┬─────────┘
                  │          │
             YES  │          │  NO
                  ↓          ↓
            ┌─────────────┐ REJECT
            │ SubQueries  │
            │ [           │
            │   "Q1",     │
            │   "Q2",     │
            │   "Q3"      │
            │ ]           │
            └──────┬──────┘
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
    ┌──────┐  ┌──────┐  ┌──────┐
    │Embed │  │Embed │  │Embed │
    │ Q1   │  │ Q2   │  │ Q3   │
    └──┬───┘  └──┬───┘  └──┬───┘
       │         │         │
       ↓         ↓         ↓
    ┌──────────────────────────────────┐
    │ ChromaDB Semantic Search         │
    │                                  │
    │ For each embedding:              │
    │   Find K nearest documents       │
    │   Return with scores (0-1)       │
    └─────────────┬────────────────────┘
                  │
         ┌────────┴────────┐
         ↓                 ↓
    ┌──────────┐      ┌──────────┐
    │ Doc Set  │      │ Doc Set  │
    │ from Q1  │      │ from Q2  │
    │ + Q3     │      │ Scores   │
    │ Scores   │      │          │
    └────┬─────┘      └────┬─────┘
         │                 │
         └────────┬────────┘
                  │
                  ↓
        ┌──────────────────┐
        │ Deduplicate      │
        │ Union results    │
        │ Keep best scores │
        └────────┬─────────┘
                 │
                 ↓
         ┌──────────────────┐
         │ Final Documents  │
         │ (unique, scored) │
         └────────┬─────────┘
                  │
                  ↓
        ┌──────────────────────┐
        │ Format Context       │
        │ Add sources, refs    │
        │ Create readable text │
        └────────┬─────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │ Prompt to ChatGroq   │
        │ • System prompt      │
        │ • Question           │
        │ • Context            │
        └────────┬─────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │ LLM Generation       │
        │ ChatGroq processes   │
        │ Returns answer       │
        └────────┬─────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │ Format Output        │
        │ Validate             │
        │ Create response      │
        └────────┬─────────────┘
                 │
                 ↓
            USER ANSWER
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌──────────────┐        ┌─────────────┐                  │
│  │ LangChain    │        │ Groq API    │                  │
│  │ ────────────│        │ ──────────  │                  │
│  │ • Core       │        │ ChatGroq    │                  │
│  │ • Expression │        │ llama-3.3   │                  │
│  │   Language   │        │ 70b         │                  │
│  │ • Agents     │        │             │                  │
│  │ • Chains     │        └─────────────┘                  │
│  │ • Prompts    │                                         │
│  └──────┬───────┘                                         │
│         │                                                 │
│  ┌──────┴──────────┐        ┌──────────────┐             │
│  │ ChromaDB        │        │ DuckDuckGo   │             │
│  │ ────────────   │        │ ──────────── │             │
│  │ • Vector DB     │        │ Web Search   │             │
│  │ • Similarity    │        │ Results      │             │
│  │   Search        │        │              │             │
│  │ • Persistence   │        └──────────────┘             │
│  └─────────────────┘                                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Pydantic                                            │  │
│  │ Data validation & serialization                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  agentic_rag_pipeline.py (Main Orchestrator)           │
│         │                                              │
│         ├─→ query_analyzer_router.py                  │
│         │   ├─ LangChain                              │
│         │   ├─ ChatGroq                               │
│         │   └─ Pydantic                               │
│         │                                              │
│         ├─→ query_rewriter.py                        │
│         │   ├─ LangChain                              │
│         │   ├─ ChatGroq                               │
│         │   └─ Pydantic                               │
│         │                                              │
│         ├─→ vector_store.py (ChromaDB)               │
│         │   ├─ ChromaDB                               │
│         │   ├─ Sentence Transformers                  │
│         │   └─ File I/O                               │
│         │                                              │
│         ├─→ web_search_agent.py                      │
│         │   ├─ LangChain Agents                       │
│         │   ├─ ChatGroq                               │
│         │   └─ DuckDuckGo                             │
│         │                                              │
│         └─→ final_synthesizer.py                     │
│             ├─ LangChain                              │
│             ├─ ChatGroq                               │
│             └─ String Formatting                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  FastAPI Application (fastapi_deployment.py)           │
│  ──────────────────────────────────────────            │
│                                                          │
│  ┌────────────────────────────────────────┐            │
│  │ /health                                │            │
│  │ /api/v1/query                         │            │
│  │ /api/v1/batch-query                  │            │
│  │ /api/v1/info                         │            │
│  │ /api/v1/examples                     │            │
│  │ /docs (Swagger)                      │            │
│  │ /redoc (ReDoc)                       │            │
│  └────────────────┬─────────────────────┘            │
│                   │                                    │
│                   ↓                                    │
│  ┌────────────────────────────────────────┐            │
│  │ AgenticRAGPipeline Instance           │            │
│  │                                        │            │
│  │ • query_analyzer_router               │            │
│  │ • query_rewriter                      │            │
│  │ • web_search_agent                    │            │
│  │ • final_synthesizer                   │            │
│  │ • vector_store (ChromaDB)             │            │
│  └────────────────┬─────────────────────┘            │
│                   │                                    │
│         ┌─────────┼─────────┐                         │
│         ↓         ↓         ↓                         │
│      LLM API   Web Search ChromaDB                   │
│      (Groq)   (DuckDuckGo)                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

**Legend:**

- ✓ Fully implemented
- → Data flow
- ↓ Process flow
- ├─ Dependency
- └─ Final item in dependency

This diagram shows the complete flow of the Advanced Agentic RAG Pipeline!
