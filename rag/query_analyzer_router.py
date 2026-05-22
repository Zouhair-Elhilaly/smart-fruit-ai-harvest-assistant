"""Query Analyzer & Router - Domain guardrail and query classification."""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()


class QueryAnalysis(BaseModel):
    """Structured output for query analysis."""
    is_agriculture: bool = Field(
        description="True if query is agriculture-related, false otherwise"
    )
    route: str = Field(
        description="Either 'vector_db' for general knowledge or 'web_search' for real-time data"
    )
    reasoning: str = Field(
        description="Brief explanation of the classification decision"
    )


def create_query_analyzer_router() -> callable:
    """
    Create a query analyzer and router chain.
    
    Returns a function that takes a user question and returns QueryAnalysis.
    """
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1")),
        max_tokens=500,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
    
    prompt = PromptTemplate(
        template="""You are an expert agricultural domain classifier. Analyze the following user question and determine:

1. Whether it is agriculture-related (crops, farming, plant diseases, weather, soil, irrigation, livestock, postharvest, etc.)
2. What retrieval route is best:
   - "vector_db" for general knowledge, technical questions, or procedural agricultural guidance
   - "web_search" for questions about real-time data, current crop prices, recent news, live weather, or market information

Question: {question}

{format_instructions}

Make your decision and provide brief reasoning.""",
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    def analyze_and_route(question: str) -> QueryAnalysis:
        """Analyze query and determine routing."""
        result = chain.invoke({"question": question})
        return result
    
    return analyze_and_route


def validate_agriculture_query(question: str) -> Optional[str]:
    """
    Check if query is agriculture-related. Returns error message if not, None if it is.
    """
    analyzer = create_query_analyzer_router()
    analysis = analyzer(question)
    
    if not analysis.is_agriculture:
        return "I am an AI assistant specialized strictly in agriculture. How can I help you with your crops today?"
    
    return None
