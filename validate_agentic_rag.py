"""
Validation script for Advanced Agentic RAG Pipeline.
This script verifies that all components are correctly implemented.
"""

import sys
from pathlib import Path

def validate_file_structure():
    """Check that all required files exist."""
    print("\n" + "="*70)
    print("STEP 1: FILE STRUCTURE VALIDATION")
    print("="*70)
    
    required_files = [
        "rag/query_analyzer_router.py",
        "rag/query_rewriter.py",
        "rag/web_search_agent.py",
        "rag/final_synthesizer.py",
        "rag/agentic_rag_pipeline.py",
        "agentic_rag_examples.py",
        "quick_start.py",
        "AGENTIC_RAG_README.md",
    ]
    
    all_exist = True
    for file in required_files:
        path = Path(file)
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist


def validate_module_imports():
    """Check that all modules can be imported."""
    print("\n" + "="*70)
    print("STEP 2: MODULE IMPORT VALIDATION")
    print("="*70)
    
    modules_to_test = [
        ("rag.query_analyzer_router", "create_query_analyzer_router"),
        ("rag.query_rewriter", "create_query_rewriter"),
        ("rag.web_search_agent", "create_web_search_agent"),
        ("rag.final_synthesizer", "create_final_synthesizer"),
        ("rag.agentic_rag_pipeline", "AgenticRAGPipeline"),
    ]
    
    all_imported = True
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")
            all_imported = False
    
    return all_imported


def validate_class_structure():
    """Check that classes have required methods."""
    print("\n" + "="*70)
    print("STEP 3: CLASS STRUCTURE VALIDATION")
    print("="*70)
    
    checks = []
    
    # Check QueryAnalysis Pydantic model
    try:
        from rag.query_analyzer_router import QueryAnalysis
        qa = QueryAnalysis(
            is_agriculture=True,
            route="vector_db",
            reasoning="test"
        )
        assert hasattr(qa, 'is_agriculture')
        assert hasattr(qa, 'route')
        assert hasattr(qa, 'reasoning')
        print("✓ QueryAnalysis Pydantic model")
        checks.append(True)
    except Exception as e:
        print(f"✗ QueryAnalysis: {e}")
        checks.append(False)
    
    # Check SubQueries Pydantic model
    try:
        from rag.query_rewriter import SubQueries
        sq = SubQueries(sub_queries=["query1", "query2"])
        assert len(sq.sub_queries) == 2
        print("✓ SubQueries Pydantic model")
        checks.append(True)
    except Exception as e:
        print(f"✗ SubQueries: {e}")
        checks.append(False)
    
    # Check AgenticRAGPipeline class
    try:
        from rag.agentic_rag_pipeline import AgenticRAGPipeline, AgenticRAGResponse
        assert hasattr(AgenticRAGPipeline, 'process')
        assert hasattr(AgenticRAGPipeline, '__init__')
        print("✓ AgenticRAGPipeline class structure")
        checks.append(True)
    except Exception as e:
        print(f"✗ AgenticRAGPipeline: {e}")
        checks.append(False)
    
    return all(checks)


def validate_configuration():
    """Check environment configuration."""
    print("\n" + "="*70)
    print("STEP 4: CONFIGURATION VALIDATION")
    print("="*70)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_env_vars = ["GROQ_API_KEY"]
    all_set = True
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✓ {var} is set ({masked_value})")
        else:
            print(f"✗ {var} is NOT set")
            all_set = False
    
    # Check optional configurations
    optional_vars = ["GROQ_MODEL", "GROQ_TEMPERATURE", "GROQ_MAX_TOKENS"]
    for var in optional_vars:
        value = os.getenv(var, "default")
        print(f"  {var}: {value}")
    
    return all_set


def validate_dependencies():
    """Check that required packages are installed."""
    print("\n" + "="*70)
    print("STEP 5: DEPENDENCY VALIDATION")
    print("="*70)
    
    required_packages = [
        ("langchain_core", "LangChain Core"),
        ("langchain_groq", "LangChain Groq"),
        ("langchain_community", "LangChain Community"),
        ("pydantic", "Pydantic"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "Sentence Transformers"),
        ("groq", "Groq"),
    ]
    
    all_available = True
    for package_name, display_name in required_packages:
        try:
            __import__(package_name)
            print(f"✓ {display_name} ({package_name})")
        except ImportError:
            print(f"✗ {display_name} ({package_name}) - NOT INSTALLED")
            all_available = False
    
    return all_available


def validate_documentation():
    """Check that documentation exists."""
    print("\n" + "="*70)
    print("STEP 6: DOCUMENTATION VALIDATION")
    print("="*70)
    
    docs = {
        "AGENTIC_RAG_README.md": "Architecture and detailed documentation",
        "quick_start.py": "Quick-start guide and examples",
        "agentic_rag_examples.py": "Comprehensive usage examples",
    }
    
    all_exist = True
    for filename, description in docs.items():
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {filename} ({size} bytes) - {description}")
        else:
            print(f"✗ {filename} - MISSING")
            all_exist = False
    
    return all_exist


def print_summary(results):
    """Print validation summary."""
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    checks = [
        ("File Structure", results["files"]),
        ("Module Imports", results["imports"]),
        ("Class Structure", results["classes"]),
        ("Configuration", results["config"]),
        ("Dependencies", results["dependencies"]),
        ("Documentation", results["docs"]),
    ]
    
    print()
    all_passed = True
    for name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    print("="*70)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED!")
        print("="*70)
        print("\nNext steps:")
        print("1. Run quick-start guide: python quick_start.py basic")
        print("2. Review AGENTIC_RAG_README.md")
        print("3. Run examples: python agentic_rag_examples.py")
        print("4. Deploy with FastAPI or Streamlit")
    else:
        print("⚠️  SOME VALIDATIONS FAILED")
        print("="*70)
        print("\nPlease address the issues above before using the pipeline.")
    
    return all_passed


def main():
    """Run all validations."""
    print("\n" + "="*70)
    print("  ADVANCED AGENTIC RAG PIPELINE - VALIDATION SUITE")
    print("="*70)
    
    results = {
        "files": validate_file_structure(),
        "imports": validate_module_imports(),
        "classes": validate_class_structure(),
        "config": validate_configuration(),
        "dependencies": validate_dependencies(),
        "docs": validate_documentation(),
    }
    
    success = print_summary(results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
