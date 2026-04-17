"""Manual test script for LLM Orchestrator.

This script tests the complete multi-agent pipeline with a real LLM.
Requires OPENAI_API_KEY environment variable to be set.

Usage:
    cd backend
    source venv/bin/activate
    export OPENAI_API_KEY=your-key-here
    python -m orchestrator.test_orchestrator_manual
"""
import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.orchestrator import LLMOrchestrator
from orchestrator.config import config


async def test_orchestrator():
    """Test the complete orchestrator pipeline."""
    print("=" * 70)
    print("LLM Orchestrator Manual Test")
    print("=" * 70)
    
    # Validate configuration
    try:
        config.validate()
        print(f"\n✓ Configuration validated")
        print(f"  - Provider: {config.LLM_PROVIDER}")
        print(f"  - Model: {config.LLM_MODEL}")
        print(f"  - Temperature: {config.LLM_TEMPERATURE}")
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease set OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY=your-key-here")
        return
    
    # Create orchestrator
    orchestrator = LLMOrchestrator()
    print(f"\n✓ Orchestrator initialized")
    
    # Test parameters
    topic = "The Future of Artificial Intelligence"
    tone = "professional"
    slide_count = 5
    
    print(f"\n{'─' * 70}")
    print(f"Test Parameters:")
    print(f"  - Topic: {topic}")
    print(f"  - Tone: {tone}")
    print(f"  - Slide Count: {slide_count}")
    print(f"{'─' * 70}\n")
    
    try:
        # Generate presentation content
        print("Starting generation pipeline...\n")
        
        presentation = await orchestrator.generate_presentation_content(
            topic=topic,
            tone=tone,
            slide_count=slide_count
        )
        
        print(f"\n{'=' * 70}")
        print("✓ Generation Successful!")
        print(f"{'=' * 70}\n")
        
        # Display results
        print(f"Title: {presentation.title.main_title}")
        if presentation.title.subtitle:
            print(f"Subtitle: {presentation.title.subtitle}")
        
        print(f"\nAgenda ({len(presentation.agenda.items)} items):")
        for i, item in enumerate(presentation.agenda.items, 1):
            print(f"  {i}. {item}")
        
        print(f"\nContent Slides ({len(presentation.slides)} slides):")
        for slide in presentation.slides:
            print(f"\n  Slide {presentation.slides.index(slide) + 1}: {slide.title}")
            print(f"    Layout: {slide.layout}")
            print(f"    Type: {slide.slide_type}")
            print(f"    Bullets: {len(slide.content)}")
            for bullet in slide.content[:2]:  # Show first 2 bullets
                print(f"      - {bullet}")
            if len(slide.content) > 2:
                print(f"      ... and {len(slide.content) - 2} more")
            if slide.notes:
                print(f"    Notes: {slide.notes[:80]}...")
        
        print(f"\nSummary: {presentation.summary.title}")
        print(f"  Takeaways: {len(presentation.summary.takeaways)}")
        for i, takeaway in enumerate(presentation.summary.takeaways, 1):
            print(f"    {i}. {takeaway}")
        
        # Test serialization
        print(f"\n{'─' * 70}")
        print("Testing serialization...")
        
        serialized = presentation.to_dict()
        print(f"✓ Serialized to dict ({len(json.dumps(serialized))} bytes)")
        
        deserialized = type(presentation).from_dict(serialized)
        print(f"✓ Deserialized from dict")
        
        # Verify round-trip
        assert deserialized.title.main_title == presentation.title.main_title
        assert len(deserialized.slides) == len(presentation.slides)
        print(f"✓ Round-trip serialization verified")
        
        print(f"\n{'=' * 70}")
        print("All tests passed! ✓")
        print(f"{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"✗ Generation Failed")
        print(f"{'=' * 70}")
        print(f"\nError: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        if hasattr(e, 'agent'):
            print(f"Agent: {e.agent}")
        if hasattr(e, 'retryable'):
            print(f"Retryable: {e.retryable}")
        
        import traceback
        print(f"\nTraceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
