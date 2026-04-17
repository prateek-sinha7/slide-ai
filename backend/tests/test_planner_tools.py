"""Tests for Planner Agent tools."""
import pytest
from orchestrator.tools.planner_tools import (
    WebSearchTool,
    StructureValidatorTool,
    OutlineQualityCheckerTool
)


class TestWebSearchTool:
    """Tests for WebSearchTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert "search" in tool.description.lower()
        assert "web" in tool.description.lower()
    
    def test_execute_with_valid_query(self):
        """Test web search with valid query."""
        tool = WebSearchTool()
        result = tool.execute("Python programming")
        
        # Should return results or error message (not empty)
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
    
    def test_execute_with_empty_query(self):
        """Test web search with empty query."""
        tool = WebSearchTool()
        result = tool.execute("")
        
        assert "Error" in result
        assert "non-empty string" in result
    
    def test_execute_with_invalid_query(self):
        """Test web search with invalid query type."""
        tool = WebSearchTool()
        result = tool.execute(None)
        
        assert "Error" in result


class TestStructureValidatorTool:
    """Tests for StructureValidatorTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = StructureValidatorTool()
        assert tool.name == "structure_validator"
        assert "structure" in tool.description.lower()
        assert "validate" in tool.description.lower()
    
    def test_execute_with_good_outline(self):
        """Test validation with well-structured outline."""
        tool = StructureValidatorTool()
        outline = """
        Introduction to AI
        What is Artificial Intelligence?
        Machine Learning Basics
        Deep Learning Overview
        Real-World Applications
        Future of AI
        Conclusion and Summary
        """
        
        result = tool.execute(outline)
        
        assert "Validation Score:" in result
        assert "/100" in result
        assert "Feedback:" in result
        
        # Should have decent score for good outline
        score_line = [line for line in result.split('\n') if 'Validation Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score >= 60  # Should score reasonably well
    
    def test_execute_with_poor_outline(self):
        """Test validation with poorly structured outline."""
        tool = StructureValidatorTool()
        outline = """
        Slide 1
        Content
        More stuff
        """
        
        result = tool.execute(outline)
        
        assert "Validation Score:" in result
        # Should have low score and suggestions
        assert "✗" in result or "Missing" in result
    
    def test_execute_with_empty_outline(self):
        """Test validation with empty outline."""
        tool = StructureValidatorTool()
        result = tool.execute("")
        
        assert "Error" in result or "0/100" in result
    
    def test_detects_introduction(self):
        """Test detection of introduction slide."""
        tool = StructureValidatorTool()
        outline = """
        Introduction
        Main Content
        Conclusion
        """
        
        result = tool.execute(outline)
        assert "introduction" in result.lower()
    
    def test_detects_conclusion(self):
        """Test detection of conclusion slide."""
        tool = StructureValidatorTool()
        outline = """
        Introduction
        Main Content
        Conclusion
        """
        
        result = tool.execute(outline)
        assert "conclusion" in result.lower()


class TestOutlineQualityCheckerTool:
    """Tests for OutlineQualityCheckerTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = OutlineQualityCheckerTool()
        assert tool.name == "outline_quality_checker"
        assert "quality" in tool.description.lower()
        assert "best practices" in tool.description.lower()
    
    def test_execute_with_excellent_outline(self):
        """Test quality check with excellent outline."""
        tool = OutlineQualityCheckerTool()
        outline = """
        Introduction: Welcome to AI
        What is Artificial Intelligence?
        How Does Machine Learning Work?
        Why Deep Learning Matters
        Real-World Applications of AI
        Case Study: AI in Healthcare
        Future Trends in AI
        Key Takeaways
        Conclusion: The AI Revolution
        """
        
        result = tool.execute(outline)
        
        assert "Quality Score:" in result
        assert "/100" in result
        assert "Overall:" in result
        
        # Should have good score for excellent outline
        score_line = [line for line in result.split('\n') if 'Quality Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score >= 50  # Should score reasonably well
    
    def test_execute_with_poor_outline(self):
        """Test quality check with poor outline."""
        tool = OutlineQualityCheckerTool()
        outline = """
        Slide
        Content
        Stuff
        """
        
        result = tool.execute(outline)
        
        assert "Quality Score:" in result
        assert "Improvement Suggestions:" in result or "Suggestions:" in result
        
        # Should have low score
        score_line = [line for line in result.split('\n') if 'Quality Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score < 60  # Should score poorly
    
    def test_execute_with_empty_outline(self):
        """Test quality check with empty outline."""
        tool = OutlineQualityCheckerTool()
        result = tool.execute("")
        
        assert "Error" in result or "0/100" in result
    
    def test_provides_suggestions(self):
        """Test that tool provides improvement suggestions."""
        tool = OutlineQualityCheckerTool()
        outline = """
        Slide 1
        Slide 2
        Slide 3
        """
        
        result = tool.execute(outline)
        
        # Should provide suggestions for improvement
        assert "Suggestions:" in result or "suggestions" in result.lower()
    
    def test_detects_vague_titles(self):
        """Test detection of vague titles."""
        tool = OutlineQualityCheckerTool()
        outline = """
        Introduction
        Content
        Information
        Data
        Conclusion
        """
        
        result = tool.execute(outline)
        
        # Should detect vague titles
        assert "vague" in result.lower() or "specific" in result.lower()
    
    def test_rewards_question_titles(self):
        """Test that question-based titles are recognized."""
        tool = OutlineQualityCheckerTool()
        outline = """
        Introduction
        What is AI?
        How does it work?
        Why does it matter?
        Conclusion
        """
        
        result = tool.execute(outline)
        
        # Should recognize questions as engaging
        score_line = [line for line in result.split('\n') if 'Quality Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score > 30  # Should get some points


class TestToolIntegration:
    """Integration tests for all planner tools."""
    
    def test_all_tools_instantiate(self):
        """Test that all tools can be instantiated."""
        tools = [
            WebSearchTool(),
            StructureValidatorTool(),
            OutlineQualityCheckerTool()
        ]
        
        assert len(tools) == 3
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)
        assert all(hasattr(tool, 'execute') for tool in tools)
    
    def test_tools_have_unique_names(self):
        """Test that all tools have unique names."""
        tools = [
            WebSearchTool(),
            StructureValidatorTool(),
            OutlineQualityCheckerTool()
        ]
        
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))  # All unique
    
    def test_tools_work_with_tool_registry(self):
        """Test that tools can be registered in tool registry."""
        from orchestrator.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Register all planner tools
        registry.register(WebSearchTool(), agent_type="planner")
        registry.register(StructureValidatorTool(), agent_type="planner")
        registry.register(OutlineQualityCheckerTool(), agent_type="planner")
        
        # Verify registration
        planner_tools = registry.get_tools_for_agent("planner")
        assert len(planner_tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in planner_tools]
        assert "web_search" in tool_names
        assert "structure_validator" in tool_names
        assert "outline_quality_checker" in tool_names
