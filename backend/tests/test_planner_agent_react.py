"""Tests for Planner Agent with ReAct pattern."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from orchestrator.planner_agent import PlannerAgent
from orchestrator.memory import ConversationMemory, IntermediateResultsCache
from orchestrator.models import SlideOutline, SlideOutlineItem
from orchestrator.config import config


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    llm = Mock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def memory():
    """Create conversation memory for testing."""
    return ConversationMemory(agent_name="planner")


@pytest.fixture
def cache():
    """Create intermediate results cache for testing."""
    return IntermediateResultsCache()


@pytest.fixture
def planner_agent(mock_llm, memory, cache):
    """Create Planner Agent instance for testing."""
    return PlannerAgent(llm=mock_llm, memory=memory, cache=cache)


class TestPlannerAgentInitialization:
    """Test Planner Agent initialization with ReAct components."""
    
    def test_agent_initializes_with_tools(self, planner_agent):
        """Test that agent initializes with correct tools."""
        assert planner_agent.tools is not None
        assert len(planner_agent.tools) == 3
        
        tool_names = [tool.name for tool in planner_agent.tools]
        assert "web_search" in tool_names
        assert "structure_validator" in tool_names
        assert "outline_quality_checker" in tool_names
    
    def test_agent_initializes_with_memory(self, planner_agent, memory):
        """Test that agent initializes with memory."""
        assert planner_agent.memory is not None
        assert planner_agent.memory.agent_name == "planner"
    
    def test_agent_initializes_with_cache(self, planner_agent, cache):
        """Test that agent initializes with cache."""
        assert planner_agent.cache is not None
    
    def test_agent_has_react_components(self, planner_agent):
        """Test that agent has ReAct components."""
        assert planner_agent.agent is not None
        assert planner_agent.agent_executor is not None
    
    def test_agent_has_fallback_chain(self, planner_agent):
        """Test that agent has fallback chain."""
        assert planner_agent.fallback_prompt is not None
        assert planner_agent.fallback_chain is not None


class TestPlannerAgentMemoryIntegration:
    """Test memory integration with Planner Agent."""
    
    def test_memory_stores_interactions(self, memory):
        """Test that memory stores interactions."""
        memory.add_message("human", "Create outline for AI presentation")
        memory.add_message("ai", "I'll research the topic first")
        
        assert len(memory) == 2
        context = memory.get_context()
        assert "Create outline" in context
        assert "research" in context
    
    def test_cache_stores_outline(self, cache):
        """Test that cache stores outline."""
        outline = SlideOutline(
            title="Test Presentation",
            subtitle="Test Subtitle",
            outline=[
                SlideOutlineItem(
                    slide_number=i,
                    title=f"Slide {i}",
                    key_points=["Point 1", "Point 2", "Point 3"]
                )
                for i in range(1, 6)
            ],
            summary_points=["Summary 1", "Summary 2", "Summary 3"]
        )
        
        cache.store("outline", outline, agent_name="planner")
        
        assert cache.has("outline")
        retrieved = cache.retrieve("outline")
        assert retrieved.title == "Test Presentation"


class TestPlannerAgentFallback:
    """Test fallback generation when ReAct fails."""
    
    def test_fallback_chain_exists(self, planner_agent):
        """Test that fallback chain is properly initialized."""
        assert planner_agent.fallback_chain is not None
        assert planner_agent.fallback_prompt is not None


class TestPlannerAgentConfiguration:
    """Test agent configuration and settings."""
    
    def test_agent_respects_max_iterations(self, planner_agent):
        """Test that agent executor respects max iterations config."""
        assert planner_agent.agent_executor.max_iterations == config.MAX_ITERATIONS
    
    def test_agent_has_verbose_logging(self, planner_agent):
        """Test that agent executor has verbose logging enabled."""
        assert planner_agent.agent_executor.verbose is True
    
    def test_agent_handles_parsing_errors(self, planner_agent):
        """Test that agent executor handles parsing errors."""
        assert planner_agent.agent_executor.handle_parsing_errors is True


class TestPlannerAgentTools:
    """Test tool creation and registration."""
    
    def test_tools_are_langchain_tools(self, planner_agent):
        """Test that tools are proper LangChain Tool instances."""
        from langchain.tools import Tool
        
        for tool in planner_agent.tools:
            assert isinstance(tool, Tool)
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'func')
    
    def test_web_search_tool_exists(self, planner_agent):
        """Test that web search tool is registered."""
        tool_names = [tool.name for tool in planner_agent.tools]
        assert "web_search" in tool_names
    
    def test_structure_validator_tool_exists(self, planner_agent):
        """Test that structure validator tool is registered."""
        tool_names = [tool.name for tool in planner_agent.tools]
        assert "structure_validator" in tool_names
    
    def test_quality_checker_tool_exists(self, planner_agent):
        """Test that quality checker tool is registered."""
        tool_names = [tool.name for tool in planner_agent.tools]
        assert "outline_quality_checker" in tool_names


class TestPlannerAgentOutputValidation:
    """Test output validation and caching."""
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, cache):
        """Test that cache can store and retrieve outlines."""
        # Create a valid outline
        mock_outline = SlideOutline(
            title="Test Presentation",
            subtitle="Test Subtitle",
            outline=[
                SlideOutlineItem(
                    slide_number=i,
                    title=f"Slide {i}",
                    key_points=[f"Point {j}" for j in range(1, 4)]
                )
                for i in range(1, 6)
            ],
            summary_points=["Summary 1", "Summary 2", "Summary 3"]
        )
        
        # Store in cache
        cache.store("outline", mock_outline, agent_name="planner")
        
        # Retrieve from cache
        assert cache.has("outline")
        cached_outline = cache.retrieve("outline")
        assert cached_outline.title == "Test Presentation"
        assert len(cached_outline.outline) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
