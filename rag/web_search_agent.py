"""Web Search Agent - LangChain agent for real-time data retrieval."""

from typing import Optional
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import DuckDuckGoSearchRun
import os
from dotenv import load_dotenv

load_dotenv()


def create_web_search_agent() -> AgentExecutor:
    """
    Create a LangChain agent equipped with web search capability.
    
    Returns an AgentExecutor that can autonomously search the web for agricultural information.
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
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create executor with a reasonable max iterations
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=5,
        handle_parsing_errors=True,
    )
    
    return agent_executor


def search_agriculture_web(question: str, agent: Optional[AgentExecutor] = None) -> str:
    """
    Use the web search agent to answer an agricultural question with real-time data.
    
    Args:
        question: The user's agricultural question
        agent: Optional pre-created agent executor. If None, creates a new one.
    
    Returns:
        The synthesized answer from web search results.
    """
    if agent is None:
        agent = create_web_search_agent()
    
    result = agent.invoke({
        "input": f"Please search for current information to answer: {question}"
    })
    
    return result.get("output", "")
