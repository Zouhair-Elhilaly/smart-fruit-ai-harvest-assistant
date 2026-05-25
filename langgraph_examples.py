"""
LangGraph-Based Web Search Agent - Complete Working Example

This demonstrates the modern LangGraph approach to building agentic systems.
It replaces the old (broken) AgentExecutor pattern with the new LangGraph framework.
"""

import logging
from typing import Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_direct_agent_usage():
    """
    Example 1: Direct usage of LangGraph agent
    
    This shows the raw agent creation and invocation without the wrapper.
    Useful for understanding how LangGraph works under the hood.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Direct LangGraph Agent Usage")
    print("="*80)
    
    try:
        from langchain_groq import ChatGroq
        from langchain_community.tools import DuckDuckGoSearchRun
        from langchain_core.prompts import ChatPromptTemplate
        from langgraph.prebuilt import create_react_agent
        import os
        
        load_dotenv()
        
        # Step 1: Initialize LLM
        llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.3,
            max_tokens=1000,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        print("✓ LLM initialized")
        
        # Step 2: Create tools list
        search_tool = DuckDuckGoSearchRun()
        tools = [search_tool]
        print("✓ Search tool loaded")
        
        # Step 3: Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert agricultural assistant. Use web search to find current information."),
            ("user", "{input}"),
        ])
        print("✓ Prompt template created")
        
        # Step 4: Create agent (LangGraph-based)
        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        print("✓ LangGraph ReAct agent created")
        
        # Step 5: Invoke the agent
        print("\n📋 Invoking agent with question...")
        result = agent.invoke({
            "input": "What are recent developments in precision agriculture?"
        })
        print("✓ Agent execution complete")
        
        # Step 6: Extract and display output
        output = result.get("output", "No output received")
        print(f"\n✨ Agent Response:\n{output[:300]}...\n")
        
    except Exception as e:
        logger.error(f"Error in Example 1: {e}", exc_info=True)
        print(f"✗ Failed: {e}")


def example_2_wrapper_function():
    """
    Example 2: Using the wrapper function (recommended for applications)
    
    This is the recommended way to use the agent in your applications.
    It abstracts away the details and provides error handling.
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Using the Wrapper Function (Recommended)")
    print("="*80)
    
    try:
        from rag.web_search_agent import create_web_search_agent, search_agriculture_web
        
        # Create agent once
        print("Creating web search agent...")
        agent = create_web_search_agent()
        print("✓ Agent created")
        
        # Use it for multiple queries
        questions = [
            "What are current organic farming trends?",
            "How is AI being used in crop prediction?",
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            try:
                result = search_agriculture_web(question, agent)
                print(f"✓ Answer received ({len(result)} chars)")
                print(f"   Preview: {result[:150]}...")
            except Exception as e:
                print(f"✗ Error: {e}")
        
    except Exception as e:
        logger.error(f"Error in Example 2: {e}", exc_info=True)
        print(f"✗ Failed: {e}")


def example_3_with_pipeline():
    """
    Example 3: Using the agent within the full agentic RAG pipeline
    
    This shows how the web search agent is integrated into the complete
    RAG pipeline for intelligent query routing.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Agent in Full RAG Pipeline")
    print("="*80)
    
    try:
        from rag.agentic_rag_pipeline import run_agentic_rag
        
        questions = [
            # This will likely use web_search route
            "What are current wheat prices in the market?",
            # This will likely use vector_db route
            "What are the best practices for preventing powdery mildew?",
            # This will be rejected
            "What is Python programming?",
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            try:
                result = run_agentic_rag(question)
                
                print(f"   Route: {result['route']}")
                print(f"   Is Agriculture: {result['is_agriculture']}")
                print(f"   Reasoning: {result['reasoning']}")
                
                if result['route'] == "rejected":
                    print(f"   Response: {result['answer']}")
                else:
                    print(f"   Answer: {result['answer'][:150]}...")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
    except Exception as e:
        logger.error(f"Error in Example 3: {e}", exc_info=True)
        print(f"✗ Failed: {e}")


def example_4_error_handling():
    """
    Example 4: Proper error handling with the agent
    
    Demonstrates how to handle various error scenarios gracefully.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Error Handling")
    print("="*80)
    
    try:
        from rag.web_search_agent import search_agriculture_web
        
        test_cases = [
            ("Normal query", "What is sustainable agriculture?"),
            ("Empty query", ""),
            ("Very long query", "A" * 10000),
        ]
        
        for case_name, question in test_cases:
            print(f"\n🧪 Test: {case_name}")
            print(f"   Query: {question[:50]}{'...' if len(question) > 50 else ''}")
            
            try:
                result = search_agriculture_web(question)
                print(f"   ✓ Success: Got {len(result)} characters")
            except ValueError as e:
                print(f"   ⚠️  Input error: {e}")
            except RuntimeError as e:
                print(f"   ✗ Runtime error: {e}")
            except Exception as e:
                print(f"   ✗ Unexpected error: {type(e).__name__}: {e}")
        
    except Exception as e:
        logger.error(f"Error in Example 4: {e}", exc_info=True)
        print(f"✗ Failed: {e}")


def example_5_component_testing():
    """
    Example 5: Testing individual components of the agent pipeline
    
    Shows how to debug and test each component independently.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Component Testing")
    print("="*80)
    
    try:
        # Test 1: LLM connectivity
        print("\n1️⃣  Testing LLM Connectivity...")
        try:
            from langchain_groq import ChatGroq
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            llm = ChatGroq(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                api_key=os.getenv("GROQ_API_KEY"),
            )
            response = llm.invoke("Say 'LLM works!' in one sentence")
            print(f"   ✓ LLM working: {response.content[:50]}")
        except Exception as e:
            print(f"   ✗ LLM error: {e}")
        
        # Test 2: Search tool
        print("\n2️⃣  Testing Search Tool...")
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            search = DuckDuckGoSearchRun()
            result = search.run("python programming")
            print(f"   ✓ Search tool working ({len(result)} chars)")
        except Exception as e:
            print(f"   ✗ Search error: {e}")
        
        # Test 3: Prompt template
        print("\n3️⃣  Testing Prompt Template...")
        try:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Test system"),
                ("user", "{input}"),
            ])
            formatted = prompt.invoke({"input": "test"})
            print(f"   ✓ Prompt template working")
        except Exception as e:
            print(f"   ✗ Prompt error: {e}")
        
        # Test 4: Agent creation
        print("\n4️⃣  Testing Agent Creation...")
        try:
            from rag.web_search_agent import create_web_search_agent
            agent = create_web_search_agent()
            print(f"   ✓ Agent created successfully")
        except Exception as e:
            print(f"   ✗ Agent creation error: {e}")
        
    except Exception as e:
        logger.error(f"Error in Example 5: {e}", exc_info=True)
        print(f"✗ Failed: {e}")


def example_6_performance_comparison():
    """
    Example 6: Performance characteristics
    
    Shows response times and resource usage for different query types.
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Performance Characteristics")
    print("="*80)
    
    import time
    
    try:
        from rag.agentic_rag_pipeline import AgenticRAGPipeline
        
        pipeline = AgenticRAGPipeline()
        
        queries = [
            ("Vector DB", "What causes nitrogen deficiency in crops?"),
            ("Web Search", "What are current tomato prices?"),
        ]
        
        print("\n⏱️  Response Time Measurements:\n")
        
        for query_type, question in queries:
            start_time = time.time()
            try:
                response = pipeline.process(question)
                elapsed = time.time() - start_time
                
                print(f"{query_type}:")
                print(f"  Time: {elapsed:.2f} seconds")
                print(f"  Route: {response.route}")
                print(f"  Answer length: {len(response.answer)} chars")
                print()
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"{query_type}: Failed after {elapsed:.2f}s - {e}\n")
        
    except Exception as e:
        logger.error(f"Error in Example 6: {e}", exc_info=True)
        print(f"✗ Failed: {e}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  LangGraph-Based Web Search Agent - Complete Examples".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    print("\n📚 Available Examples:")
    print("  1. Direct LangGraph Agent Usage")
    print("  2. Using Wrapper Function (Recommended)")
    print("  3. Agent in Full RAG Pipeline")
    print("  4. Error Handling")
    print("  5. Component Testing")
    print("  6. Performance Characteristics")
    
    examples = {
        "1": example_1_direct_agent_usage,
        "2": example_2_wrapper_function,
        "3": example_3_with_pipeline,
        "4": example_4_error_handling,
        "5": example_5_component_testing,
        "6": example_6_performance_comparison,
    }
    
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num in examples:
            examples[example_num]()
        else:
            print(f"\n✗ Unknown example: {example_num}")
            print("\nUsage: python langgraph_examples.py [1-6]")
    else:
        # Run all examples
        for example_func in examples.values():
            try:
                example_func()
            except Exception as e:
                logger.error(f"Error running example: {e}")
    
    print("\n" + "="*80)
    print("✅ Examples completed!")
    print("="*80 + "\n")
