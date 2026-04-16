"""Test script to verify Ollama integration with local Mistral model."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator.planner_agent import PlannerAgent
from orchestrator.config import config


async def test_ollama_connection():
    """Test connection to local Ollama Mistral model."""
    print("=" * 60)
    print("Testing Ollama Integration with Mistral")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  LLM Provider: {config.LLM_PROVIDER}")
    print(f"  LLM Model: {config.LLM_MODEL}")
    print(f"  Ollama Base URL: {config.OLLAMA_BASE_URL}")
    print(f"  Temperature: {config.LLM_TEMPERATURE}")
    print(f"  Max Tokens: {config.LLM_MAX_TOKENS}")
    
    print("\n" + "=" * 60)
    print("Testing Planner Agent with Mistral")
    print("=" * 60)
    
    try:
        # Create Planner Agent
        planner = PlannerAgent()
        print("✓ Planner Agent created successfully")
        
        # Test outline generation
        print("\nGenerating presentation outline...")
        print("  Topic: Introduction to Machine Learning")
        print("  Slides: 5")
        print("  Tone: professional")
        
        outline = await planner.generate_outline(
            topic="Introduction to Machine Learning",
            slide_count=5,
            tone="professional"
        )
        
        print("\n✓ Outline generated successfully!")
        print(f"\nTitle: {outline.title}")
        print(f"Subtitle: {outline.subtitle}")
        print(f"\nSlides ({len(outline.outline)}):")
        for item in outline.outline:
            print(f"\n  {item.slide_number}. {item.title}")
            print(f"     Key points:")
            for point in item.key_points:
                print(f"       - {point}")
        
        print(f"\nSummary Points:")
        for point in outline.summary_points:
            print(f"  - {point}")
        
        print("\n" + "=" * 60)
        print("✓ Ollama integration test PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ Ollama integration test FAILED!")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print(f"\nError type: {type(e).__name__}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("Troubleshooting:")
        print("=" * 60)
        print("1. Ensure Ollama is running: ollama serve")
        print("2. Verify Mistral model is available: ollama list")
        print("3. Check Ollama is accessible at: http://localhost:11434")
        print("4. Try pulling Mistral: ollama pull mistral:latest")
        
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ollama_connection())
    sys.exit(0 if success else 1)
