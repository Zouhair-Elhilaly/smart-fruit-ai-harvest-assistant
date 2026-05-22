"""Final Synthesizer - Generate comprehensive answers from aggregated context."""

from typing import List, Optional
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()


def create_final_synthesizer() -> callable:
    """
    Create a final answer synthesis chain.
    
    Returns a function that takes context and original question, returns comprehensive answer.
    """
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.3")),
        max_tokens=1500,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    system_prompt = """You are an expert agricultural assistant providing comprehensive, well-structured answers.

Guidelines:
1. Use the provided context to ground your answer in reliable information
2. Structure your answer clearly with sections if needed
3. Provide practical, actionable advice
4. Include specific recommendations when relevant
5. Indicate when information comes from the context vs general knowledge
6. Keep the answer focused and farmer-friendly
7. Mention any caveats or conditions important for the recommendation"""
    
    prompt = PromptTemplate(
        template="""Context Information:
{context}

User Question:
{question}

Based on the context provided and your agricultural expertise, generate a comprehensive and well-structured answer that directly addresses the user's question. Ensure your answer is practical, accurate, and helpful for an agricultural context.""",
        input_variables=["context", "question"],
    )
    
    chain = prompt | llm
    
    def synthesize_answer(context: str, question: str) -> str:
        """Generate final synthesized answer."""
        response = chain.invoke({
            "context": context,
            "question": question,
        })
        return response.content if hasattr(response, 'content') else str(response)
    
    return synthesize_answer


def format_vector_db_context(search_results: List[dict]) -> str:
    """
    Format vector database search results into context string.
    
    Args:
        search_results: List of search results with 'text' and metadata
    
    Returns:
        Formatted context string
    """
    if not search_results:
        return "[No relevant documents were retrieved from the knowledge base.]"
    
    sections = []
    for idx, result in enumerate(search_results, start=1):
        text = result.get('text', '')
        metadata = result.get('metadata', {})
        score = result.get('score', 0)
        
        filename = metadata.get('filename', 'unknown')
        page = metadata.get('page', -1)
        page_text = "" if page in (None, -1, "-1") else f", page {page}"
        
        sections.append(
            f"[Source {idx}: {filename}{page_text} (relevance: {score:.2f})]\n{text}"
        )
    
    return "\n\n".join(sections)


def format_web_search_context(web_results: str) -> str:
    """
    Format web search results into context string.
    
    Args:
        web_results: Raw web search agent output
    
    Returns:
        Formatted context string
    """
    if not web_results or not web_results.strip():
        return "[No web search results were found.]"
    
    return f"Web Search Results:\n{web_results}"
