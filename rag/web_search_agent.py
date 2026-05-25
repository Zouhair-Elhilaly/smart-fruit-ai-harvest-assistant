"""Web Search Agent - LangGraph-based agent for real-time data retrieval with custom DuckDuckGo tool."""

import logging
from typing import Optional
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from duckduckgo_search import DDGS

load_dotenv()
logger = logging.getLogger(__name__)


@tool
def agricultural_web_search(query: str) -> str:
    """
    Search the web for agricultural information using DuckDuckGo.
    
    This tool uses the modern duckduckgo-search package to find information about:
    - Crop prices and market conditions
    - Agricultural news and developments
    - Weather forecasts for farming
    - Disease outbreaks or pest warnings
    - Agricultural research and innovations
    
    Searches are performed in French to support Moroccan agricultural context.
    
    Args:
        query: The search query for agricultural information
        
    Returns:
        A string containing the top search results formatted for readability
    """
    try:
        if not query or not query.strip():
            logger.warning("Empty search query received")
            return "No search query provided. Please provide a valid agricultural question."
        
        logger.info(f"Searching for: {query}")
        
        # Use DDGS context manager for proper resource handling
        with DDGS(timeout=30) as ddgs:
            # Search in French for Moroccan agricultural context
            results = list(ddgs.text(
                query,
                lang="fr",      # French language for Morocco context
                region="fr",    # France region settings
                max_results=5   # Get top 5 results
            ))
        
        if not results:
            logger.warning(f"No search results found for query: {query}")
            return f"No results found for your query: {query}"
        
        # Format results into readable string
        formatted_results = []
        for idx, result in enumerate(results, 1):
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            href = result.get("href", "No URL")
            
            formatted_result = f"""
Result {idx}:
Title: {title}
URL: {href}
Summary: {body}
"""
            formatted_results.append(formatted_result)
        
        full_results = "\n".join(formatted_results)
        logger.info(f"Retrieved {len(results)} search results for query: {query[:50]}...")
        return full_results
        
    except Exception as e:
        logger.error(f"Error during agricultural web search: {e}", exc_info=True)
        return f"Error performing search: {str(e)}. Please try a different query."


def create_web_search_agent():
    """
    Create a LangGraph-based ReAct agent equipped with custom web search capability.
    
    Returns a LangGraph agent that can autonomously search the web for agricultural information.
    Uses the modern LangGraph framework with a custom agricultural_web_search tool
    powered by the duckduckgo-search package (no dependency on deprecated ddgs).
    """
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.3")),
        max_tokens=2000,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    # Use the custom agricultural_web_search tool (no LangChain community dependency)
    tools = [agricultural_web_search]
    
    # Define system prompt for the agent with French context for agricultural assistance
    system_prompt = """Vous êtes un expert en agriculture avec accès à des recherches web en temps réel.

Lorsque vous répondez à des questions agricoles, en particulier celles concernant:
- Les prix des cultures et les conditions du marché
- Les actualités et développements agricoles récents
- Les prévisions météorologiques en direct pour l'agriculture
- Les épidémies de maladies ou les avertissements de parasites en temps réel
- Les recherches et innovations agricoles récentes

Vous devez rechercher sur le web pour trouver les informations les plus actuelles et précises.
Synthétisez les résultats de recherche en une réponse claire et exploitable pour les agriculteurs.
Citez toujours les sources et indiquez l'actualité des informations lorsque cela est pertinent.

Adaptez vos réponses au contexte agricole marocain et utilisez des termes agricoles appropriés."""
    
    # Create ReAct agent using LangGraph with the custom tool
    # ✅ CORRECT: create_react_agent only accepts model and tools
    # The system prompt will be passed when invoking the agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
    )

    logger.info("LangGraph-based web search agent created successfully with custom agricultural_web_search tool")
    return agent


def search_agriculture_web(question: str, agent: Optional[object] = None) -> str:
    """
    Use the LangGraph web search agent to answer an agricultural question with real-time data.
    
    This function orchestrates the web search agent to find current information about
    agricultural topics, with special support for French language queries relevant to Morocco.
    
    Args:
        question: The user's agricultural question (will be processed in French context)
        agent: Optional pre-created LangGraph agent. If None, creates a new one.
    
    Returns:
        The synthesized answer from web search results, in French for Moroccan context.
    """
    try:
        if agent is None:
            logger.info("No agent provided, creating new web search agent")
            agent = create_web_search_agent()
        
        if not question or not question.strip():
            logger.warning("Empty question received")
            raise ValueError("Question cannot be empty")
        
        # Define system prompt for each invocation
        system_prompt = """Vous êtes un expert en agriculture avec accès à des recherches web en temps réel.

Lorsque vous répondez à des questions agricoles, en particulier celles concernant:
- Les prix des cultures et les conditions du marché
- Les actualités et développements agricoles récents
- Les prévisions météorologiques en direct pour l'agriculture
- Les épidémies de maladies ou les avertissements de parasites en temps réel
- Les recherches et innovations agricoles récentes

Vous devez rechercher sur le web pour trouver les informations les plus actuelles et précises.
Synthétisez les résultats de recherche en une réponse claire et exploitable pour les agriculteurs.
Citez toujours les sources et indiquez l'actualité des informations lorsque cela est pertinent.

Adaptez vos réponses au contexte agricole marocain et utilisez des termes agricoles appropriés."""
        
        # Invoke the LangGraph agent with proper messages format
        # Include system instruction in the messages
        logger.info(f"Invoking agent with question: {question[:100]}...")
        result = agent.invoke({
            "messages": [
                ("system", system_prompt),
                ("user", f"Veuillez rechercher des informations actuelles pour répondre à: {question}")
            ]
        })
        
        # Extract output from the last message in the result
        # LangGraph returns messages list, get the last message's content
        output = result["messages"][-1].content if result.get("messages") else ""
        
        if not output:
            logger.warning(f"Agent returned empty output for question: {question}")
            return "Impossible de récupérer les informations de la recherche web. Veuillez reformuler votre question."
        
        logger.info(f"Successfully retrieved web search results for question: {question[:50]}...")
        return output
        
    except ValueError as e:
        logger.error(f"Validation error in web search agent: {e}")
        raise ValueError(f"Invalid question: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error in web search agent: {e}", exc_info=True)
        raise RuntimeError(f"Web search agent failed: {str(e)}") from e
