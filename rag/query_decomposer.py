"""Query Decomposer - Break down multi-question prompts into structured sub-questions with routing."""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()


class SubQuery(BaseModel):
    """Structured representation of a single decomposed question."""
    sub_query: str = Field(
        description="The distinct, standalone question extracted from the user's prompt"
    )
    route: str = Field(
        description="Routing decision: 'web_search' for real-time data (weather, prices, news) or 'vector_db' for agricultural knowledge (diseases, guides, techniques)"
    )


class QueryDecomposition(BaseModel):
    """Structured output from query decomposition."""
    is_agriculture: bool = Field(
        description="True if the overall query has any relation to agriculture, farming, crops, weather, soil, livestock, etc. False if completely off-topic."
    )
    tasks: list[SubQuery] = Field(
        description="List of distinct sub-questions extracted from the user's prompt, each with its routing decision"
    )


def create_query_decomposer() -> callable:
    """
    Create a query decomposer chain that analyzes user input and breaks it down
    into multiple distinct sub-questions with routing decisions.
    
    Returns a function that takes a user_question and returns QueryDecomposition.
    """
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1")),
        max_tokens=1000,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    parser = PydanticOutputParser(pydantic_object=QueryDecomposition)
    
    prompt = PromptTemplate(
        template="""You are an expert agricultural domain classifier and query analyzer.

Your task:
1. Determine if the user's prompt is agriculture-related (crops, farming, plant diseases, weather, soil, irrigation, livestock, postharvest, fruit production, etc.)
2. If agriculture-related: Break down the user's prompt into distinct, standalone sub-questions
3. For each sub-question, decide the best retrieval route:
   - "web_search": For real-time data, current weather, live market prices, recent news, seasonal information
   - "vector_db": For agricultural knowledge bases, disease guides, growing techniques, postharvest practices

User Prompt:
{question}

{format_instructions}

IMPORTANT:
- If the prompt is NOT agriculture-related at all, set is_agriculture to false and return an empty tasks list
- If agriculture-related, ALWAYS provide at least one task (never return empty tasks if is_agriculture is true)
- Each sub_query should be a complete, self-contained question
- Route based on the type of information needed, not the phrasing""",
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    def decompose_query(question: str) -> QueryDecomposition:
        """Decompose a user question into sub-questions with routing."""
        result = chain.invoke({"question": question})
        return result
    
    return decompose_query
