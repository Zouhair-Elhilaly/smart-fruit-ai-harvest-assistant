"""Web Search Agent - LangGraph-based agent for real-time data retrieval."""

import logging
from typing import Optional
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

load_dotenv()
logger = logging.getLogger(__name__)


def create_web_search_agent():
    """
    Create a LangGraph-based ReAct agent equipped with web search capability.
    
    Returns a LangGraph agent that can autonomously search the web for agricultural information.
    Uses the modern LangGraph framework (not deprecated AgentExecutor).
    """
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.3")),
        max_tokens=2000,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    # Initialize search tool
    search_tool = DuckDuckGoSearchRun()
    tools = [search_tool]
    
    # Define system prompt for the agent
    system_prompt = """You are an expert agricultural assistant with access to real-time web search.

When answering agricultural questions, particularly those about:
- Current crop prices and market conditions
- Recent agricultural news and developments
- Live weather forecasts for farming
- Real-time disease outbreaks or pest warnings
- Recent agricultural research or innovations

You should search the web to find the most current and accurate information. 
Synthesize the search results into a clear, actionable answer for farmers.
Always cite sources and indicate the recency of information when relevant."""
    
    # Create prompt with message history placeholder
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input}"),
        ]
    )

    # Create ReAct agent using LangGraph (modern approach)
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    logger.info("LangGraph-based web search agent created successfully")
    return agent


def search_agriculture_web(question: str, agent: Optional[object] = None) -> str:
    """
    Use the LangGraph web search agent to answer an agricultural question with real-time data.
    
    Args:
        question: The user's agricultural question
        agent: Optional pre-created LangGraph agent. If None, creates a new one.
    
    Returns:
        The synthesized answer from web search results.
    """
    try:
        if agent is None:
            agent = create_web_search_agent()
        
        # Invoke the LangGraph agent with proper input format
        result = agent.invoke({
            "input": f"Please search for current information to answer: {question}"
        })
        
        # Extract output from the result
        # LangGraph returns output in the "output" key
        output = result.get("output", "")
        
        if not output:
            logger.warning(f"Agent returned empty output for question: {question}")
            return "Unable to retrieve information from web search."
        
        logger.info(f"Successfully retrieved web search results for question: {question[:50]}...")
        return output
        
    except Exception as e:
        logger.error(f"Error in web search agent: {e}", exc_info=True)
        raise RuntimeError(f"Web search agent failed: {str(e)}") from e
