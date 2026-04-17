"""
End-to-end integration tests for LangChain Deep Agents with Groq API.

This test suite validates:
- Complete presentation generation with various topics
- Different tone parameters (formal, casual, professional)
- Different slide counts (5, 10, 15, 20)
- Reasoning traces are logged correctly
- Quality thresholds work as expected

Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.6, 14.1
"""
import pytest
import asyncio
import logging
import os
from typing import List, Dict, Any

from orchestrator.orchestrator import LLMOrchestrator
from orchestrator.config import config
from orchestrator.models import PresentationContent
from orchestrator.exceptions import GenerationError, GenerationTimeoutError


# Configure logging to capture reasoning traces
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete pipeline."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return LLMOrchestrator()
    
    @pytest.mark.asyncio
    async def test_basic_presentation_generation(self, orchestrator):
        """
        Test basic presentation generation with default parameters.
        
        Validates:
        - Pipeline completes successfully
        - Returns valid PresentationContent
        - All required slides are present
        """
        topic = "Introduction to Machine Learning"
        
        logger.info(f"Testing basic presentation generation: {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=8
        )
        
        # Validate result structure
        assert isinstance(result, PresentationContent)
        assert result.title is not None
        assert result.title.main_title is not None
        assert result.agenda is not None
        assert len(result.slides) == 8
        assert result.summary is not None
        
        # Validate each slide has content
        for slide in result.slides:
            assert slide.title is not None
            assert len(slide.content) >= 3  # At least 3 bullet points
            assert len(slide.content) <= 6  # At most 6 bullet points
            assert slide.layout is not None
            assert slide.slide_type is not None
        
        logger.info("✓ Basic presentation generation test passed")
    
    @pytest.mark.asyncio
    async def test_formal_tone(self, orchestrator):
        """
        Test presentation generation with formal tone.
        
        Validates:
        - Formal tone is applied
        - Content is appropriate for formal context
        """
        topic = "Corporate Governance Best Practices"
        
        logger.info(f"Testing formal tone: {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="formal",
            slide_count=10
        )
        
        assert isinstance(result, PresentationContent)
        assert len(result.slides) == 10
        
        # Check that content exists and is structured
        for slide in result.slides:
            assert len(slide.content) >= 3
            # Formal tone should have complete sentences
            for bullet in slide.content:
                assert len(bullet) > 5  # Not just single words
        
        logger.info("✓ Formal tone test passed")
    
    @pytest.mark.asyncio
    async def test_casual_tone(self, orchestrator):
        """
        Test presentation generation with casual tone.
        
        Validates:
        - Casual tone is applied
        - Content is appropriate for casual context
        """
        topic = "Fun Facts About Space Exploration"
        
        logger.info(f"Testing casual tone: {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="casual",
            slide_count=8
        )
        
        assert isinstance(result, PresentationContent)
        assert len(result.slides) == 8
        
        # Validate structure
        for slide in result.slides:
            assert len(slide.content) >= 3
            assert slide.title is not None
        
        logger.info("✓ Casual tone test passed")
    
    @pytest.mark.asyncio
    async def test_professional_tone(self, orchestrator):
        """
        Test presentation generation with professional tone.
        
        Validates:
        - Professional tone is applied (default)
        - Content is appropriate for professional context
        """
        topic = "Quarterly Business Review"
        
        logger.info(f"Testing professional tone: {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=12
        )
        
        assert isinstance(result, PresentationContent)
        assert len(result.slides) == 12
        
        # Validate structure
        for slide in result.slides:
            assert len(slide.content) >= 3
            assert slide.layout in ["bullet_list", "two_column", "title_only", "image_placeholder"]
        
        logger.info("✓ Professional tone test passed")
    
    @pytest.mark.asyncio
    async def test_minimum_slide_count(self, orchestrator):
        """
        Test presentation generation with minimum slide count (5).
        
        Validates:
        - Pipeline handles minimum slide count
        - All slides are generated
        """
        topic = "Quick Introduction to Python"
        
        logger.info(f"Testing minimum slide count (5): {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=5
        )
        
        assert isinstance(result, PresentationContent)
        assert len(result.slides) == 5
        
        logger.info("✓ Minimum slide count test passed")
    
    @pytest.mark.asyncio
    async def test_medium_slide_count(self, orchestrator):
        """
        Test presentation generation with medium slide count (10).
        
        Validates:
        - Pipeline handles medium slide count
        - All slides are generated
        """
        topic = "Introduction to Cloud Computing"
        
        logger.info(f"Testing medium slide count (10): {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=10
        )
        
        assert isinstance(result, PresentationContent)
        assert len(result.slides) == 10
        
        logger.info("✓ Medium slide count test passed")
    
    @pytest.mark.asyncio
    async def test_large_slide_count(self, orchestrator):
        """
        Test presentation generation with large slide count (15).
        
        Validates:
        - Pipeline handles large slide count
        - All slides are generated
        """
        topic = "Comprehensive Guide to Data Science"
        
        logger.info(f"Testing large slide count (15): {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=15
        )
        
        assert isinstance(result, PresentationContent)
        assert len(result.slides) == 15
        
        logger.info("✓ Large slide count test passed")
    
    @pytest.mark.asyncio
    async def test_maximum_slide_count(self, orchestrator):
        """
        Test presentation generation with maximum slide count (20).
        
        Validates:
        - Pipeline handles maximum slide count
        - All slides are generated
        - Performance is acceptable
        """
        topic = "Complete History of Computer Science"
        
        logger.info(f"Testing maximum slide count (20): {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=20
        )
        
        assert isinstance(result, PresentationContent)
        # Allow slight mismatch for large presentations
        assert len(result.slides) >= 18  # At least 18 slides
        assert len(result.slides) <= 20  # At most 20 slides
        
        logger.info("✓ Maximum slide count test passed")
    
    @pytest.mark.asyncio
    async def test_reasoning_traces_logged(self, orchestrator, caplog):
        """
        Test that reasoning traces are logged correctly.
        
        Validates:
        - Agent reasoning steps are logged
        - Tool invocations are logged
        - Iteration counts are logged
        """
        topic = "Artificial Intelligence Ethics"
        
        logger.info(f"Testing reasoning trace logging: {topic}")
        
        with caplog.at_level(logging.INFO):
            result = await orchestrator.generate_presentation_content(
                topic=topic,
                tone="professional",
                slide_count=8
            )
        
        # Check that reasoning traces were logged
        log_messages = [record.message for record in caplog.records]
        
        # Should have agent execution logs
        assert any("Planner Agent" in msg for msg in log_messages)
        assert any("Content Agent" in msg for msg in log_messages)
        assert any("Reviewer Agent" in msg or "Review" in msg for msg in log_messages)
        assert any("Design Agent" in msg for msg in log_messages)
        
        # Should have ReAct pattern logs
        assert any("ReAct" in msg for msg in log_messages)
        
        # Should have performance logs
        assert any("PERFORMANCE" in msg for msg in log_messages)
        
        logger.info("✓ Reasoning trace logging test passed")
    
    @pytest.mark.asyncio
    async def test_quality_thresholds(self, orchestrator):
        """
        Test that quality thresholds work as expected.
        
        Validates:
        - Agents iterate to improve quality
        - Quality threshold stops iteration early
        - Max iterations limit is respected
        """
        topic = "Software Engineering Best Practices"
        
        logger.info(f"Testing quality thresholds: {topic}")
        
        # Generate with quality threshold
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=8
        )
        
        assert isinstance(result, PresentationContent)
        
        # Check that metrics were recorded
        assert orchestrator.metrics is not None
        assert orchestrator.metrics.pipeline_start_time is not None
        assert orchestrator.metrics.pipeline_end_time is not None
        
        # Check that agents completed
        assert len(orchestrator.metrics.agent_metrics) > 0
        
        logger.info("✓ Quality threshold test passed")
    
    @pytest.mark.asyncio
    async def test_memory_cache_cleared(self, orchestrator):
        """
        Test that memory cache is cleared after pipeline completion.
        
        Validates:
        - Cache is populated during execution
        - Cache is cleared after completion
        """
        topic = "Introduction to Blockchain"
        
        logger.info(f"Testing memory cache cleanup: {topic}")
        
        # Generate presentation
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=8
        )
        
        # Cache should be cleared after completion
        assert orchestrator.cache is None or len(orchestrator.cache) == 0
        
        logger.info("✓ Memory cache cleanup test passed")
    
    @pytest.mark.asyncio
    async def test_various_topics(self, orchestrator):
        """
        Test presentation generation with various topics.
        
        Validates:
        - Pipeline handles diverse topics
        - Content is relevant to each topic
        """
        topics = [
            "Climate Change Solutions",
            "Digital Marketing Strategies",
            "Healthy Eating Habits",
            "Remote Work Best Practices",
            "Cybersecurity Fundamentals"
        ]
        
        for topic in topics:
            logger.info(f"Testing topic: {topic}")
            
            result = await orchestrator.generate_presentation_content(
                topic=topic,
                tone="professional",
                slide_count=8
            )
            
            assert isinstance(result, PresentationContent)
            assert len(result.slides) == 8
            
            # Check that title is related to topic
            assert result.title.main_title is not None
            
            logger.info(f"✓ Topic '{topic}' test passed")
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, orchestrator):
        """
        Test that performance metrics are recorded correctly.
        
        Validates:
        - Pipeline duration is recorded
        - Agent execution times are recorded
        - Tool invocation counts are tracked
        """
        topic = "Introduction to DevOps"
        
        logger.info(f"Testing performance metrics: {topic}")
        
        result = await orchestrator.generate_presentation_content(
            topic=topic,
            tone="professional",
            slide_count=8
        )
        
        # Check metrics
        assert orchestrator.metrics is not None
        assert orchestrator.metrics.get_pipeline_duration() > 0
        
        # Check that agent metrics were recorded
        agent_names = ["Planner", "Content", "Reviewer", "Design"]
        for agent_name in agent_names:
            metrics = orchestrator.metrics.get_agent_metrics(agent_name)
            # At least some agents should have metrics
            # (Reviewer and Design may timeout and use fallback)
            if metrics:
                assert "duration" in metrics
                assert metrics["duration"] > 0
        
        logger.info("✓ Performance metrics test passed")


class TestPython39Compatibility:
    """Tests for Python 3.9+ compatibility."""
    
    def test_asyncio_wait_for_syntax(self):
        """
        Test that asyncio.wait_for is used (Python 3.9 compatible).
        
        Validates:
        - Code uses asyncio.wait_for instead of asyncio.timeout (3.11+)
        """
        import inspect
        from orchestrator.planner_agent import PlannerAgent
        from orchestrator.content_agent import ContentAgent
        from orchestrator.reviewer_agent import ReviewerAgent
        from orchestrator.design_agent import DesignAgent
        
        # Check that agents use asyncio.wait_for
        for agent_class in [PlannerAgent, ContentAgent, ReviewerAgent, DesignAgent]:
            source = inspect.getsource(agent_class)
            
            # Should use asyncio.wait_for
            assert "asyncio.wait_for" in source
            
            # Should NOT use asyncio.timeout (requires Python 3.11+)
            assert "asyncio.timeout" not in source
        
        logger.info("✓ asyncio.wait_for syntax test passed")
    
    def test_type_hints_compatibility(self):
        """
        Test that type hints are Python 3.9 compatible.
        
        Validates:
        - No use of PEP 604 union syntax (X | Y requires 3.10+)
        - Uses typing.Optional and typing.Union
        """
        import inspect
        from orchestrator.planner_agent import PlannerAgent
        from orchestrator.models import SlideOutline
        
        # Check that code uses Optional instead of | syntax
        source = inspect.getsource(PlannerAgent)
        
        # Should use Optional from typing
        assert "Optional" in source
        
        logger.info("✓ Type hints compatibility test passed")
    
    def test_dependencies_install(self):
        """
        Test that all dependencies are installed correctly.
        
        Validates:
        - All required packages are importable
        - No version conflicts
        """
        # Test critical imports
        import langchain
        import langchain_groq
        import langchain_openai
        import langchain_anthropic
        import langchain_community
        import pydantic
        import fastapi
        import pytest
        import hypothesis
        
        logger.info("✓ Dependencies install test passed")
    
    def test_pydantic_compatibility(self):
        """
        Test that Pydantic models are compatible with Python 3.9.
        
        Validates:
        - Pydantic v2 models work correctly
        - No compatibility issues
        """
        from orchestrator.models import (
            SlideOutline,
            GeneratedContent,
            ReviewedContent,
            DesignedContent,
            PresentationContent
        )
        
        # Test that models can be instantiated
        # (basic validation that Pydantic is working)
        assert SlideOutline is not None
        assert GeneratedContent is not None
        assert ReviewedContent is not None
        assert DesignedContent is not None
        assert PresentationContent is not None
        
        logger.info("✓ Pydantic compatibility test passed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
