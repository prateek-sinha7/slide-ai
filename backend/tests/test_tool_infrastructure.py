"""Unit tests for shared tool infrastructure."""
import pytest
from orchestrator.tools.base_tool import BaseTool
from orchestrator.tools.tool_registry import ToolRegistry
from pydantic import Field


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    
    def execute(self, text: str = "") -> str:
        """Execute mock tool."""
        return f"Processed: {text}"


class FailingTool(BaseTool):
    """Mock tool that always fails."""
    
    name: str = "failing_tool"
    description: str = "A tool that always fails"
    
    def execute(self, text: str = "") -> str:
        """Execute failing tool."""
        raise ValueError("Intentional failure")


class TestBaseTool:
    """Test BaseTool abstract class."""
    
    def test_tool_execution(self):
        """Test successful tool execution."""
        tool = MockTool()
        result = tool._run(text="hello")
        assert result == "Processed: hello"
    
    def test_tool_error_handling(self):
        """Test tool error handling."""
        tool = FailingTool()
        result = tool._run(text="test")
        assert "Error in failing_tool" in result
        assert "Intentional failure" in result
    
    def test_tool_metadata(self):
        """Test tool metadata."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
    
    @pytest.mark.asyncio
    async def test_async_execution(self):
        """Test async tool execution."""
        tool = MockTool()
        result = await tool._arun(text="async test")
        assert result == "Processed: async test"


class TestToolRegistry:
    """Test ToolRegistry class."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ToolRegistry()
        assert len(registry) == 0
        assert "planner" in registry._agent_tools
        assert "content" in registry._agent_tools
        assert "reviewer" in registry._agent_tools
        assert "design" in registry._agent_tools
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        assert len(registry) == 1
        assert "mock_tool" in registry
        assert registry.get_tool("mock_tool") == tool
    
    def test_register_tool_with_agent(self):
        """Test tool registration with agent association."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool, agent_type="planner")
        
        planner_tools = registry.get_tools_for_agent("planner")
        assert len(planner_tools) == 1
        assert planner_tools[0] == tool
    
    def test_register_multiple_tools(self):
        """Test registering multiple tools."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = FailingTool()
        
        registry.register_multiple([tool1, tool2], agent_type="content")
        
        assert len(registry) == 2
        content_tools = registry.get_tools_for_agent("content")
        assert len(content_tools) == 2
    
    def test_get_nonexistent_tool(self):
        """Test retrieving non-existent tool."""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None
    
    def test_invalid_agent_type(self):
        """Test invalid agent type."""
        registry = ToolRegistry()
        tool = MockTool()
        
        with pytest.raises(ValueError, match="Invalid agent_type"):
            registry.register(tool, agent_type="invalid")
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = FailingTool()
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert "mock_tool" in tools
        assert "failing_tool" in tools
    
    def test_list_agent_tools(self):
        """Test listing tools for specific agent."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool, agent_type="reviewer")
        
        reviewer_tools = registry.list_agent_tools("reviewer")
        assert len(reviewer_tools) == 1
        assert "mock_tool" in reviewer_tools
    
    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool, agent_type="design")
        
        assert len(registry) == 1
        result = registry.unregister("mock_tool")
        assert result is True
        assert len(registry) == 0
        
        design_tools = registry.get_tools_for_agent("design")
        assert len(design_tools) == 0
    
    def test_unregister_nonexistent_tool(self):
        """Test unregistering non-existent tool."""
        registry = ToolRegistry()
        result = registry.unregister("nonexistent")
        assert result is False
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = FailingTool()
        registry.register(tool1, agent_type="planner")
        registry.register(tool2, agent_type="content")
        
        assert len(registry) == 2
        registry.clear()
        assert len(registry) == 0
        
        planner_tools = registry.get_tools_for_agent("planner")
        assert len(planner_tools) == 0
    
    def test_get_all_tools(self):
        """Test getting all tools."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = FailingTool()
        registry.register(tool1)
        registry.register(tool2)
        
        all_tools = registry.get_all_tools()
        assert len(all_tools) == 2
        assert tool1 in all_tools
        assert tool2 in all_tools
