"""Query Rewriter - Generate optimized sub-queries for multi-query retrieval."""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()


class SubQueries(BaseModel):
    """Structured output for sub-query generation."""
    sub_queries: List[str] = Field(
        description="List of 2-3 optimized, standalone sub-queries",
        min_items=2,
        max_items=3,
    )


def create_query_rewriter() -> callable:
    """
    Create a query rewriting chain that generates optimized sub-queries.
    
    Returns a function that takes an original question and returns a list of sub-queries.
    """
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.2")),
        max_tokens=500,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    parser = PydanticOutputParser(pydantic_object=SubQueries)
    
    prompt = PromptTemplate(
        template="""You are an agricultural knowledge expert. Break down the following complex question into 2-3 specific, optimized sub-queries that can be searched independently in a vector database. Each sub-query should be:

1. Standalone (can be understood without the original context)
2. Specific (targets a particular agricultural topic or concept)
3. Search-friendly (uses relevant agricultural terminology)

Original Question: {question}

Generate 2-3 optimized sub-queries that collectively capture all aspects of the original question:

{format_instructions}

Return only the JSON with sub_queries list.""",
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    def rewrite_query(question: str) -> List[str]:
        """Rewrite query into optimized sub-queries."""
        result = chain.invoke({"question": question})
        return result.sub_queries
    
    return rewrite_query
