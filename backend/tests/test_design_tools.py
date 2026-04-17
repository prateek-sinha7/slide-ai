"""Tests for Design Agent tools."""
import pytest
from orchestrator.tools.design_tools import (
    LayoutRecommenderTool,
    BalanceCheckerTool,
    NotesGeneratorTool
)


class TestLayoutRecommenderTool:
    """Tests for LayoutRecommenderTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = LayoutRecommenderTool()
        assert tool.name == "layout_recommender"
        assert "layout" in tool.description.lower()
        assert "recommend" in tool.description.lower()
    
    def test_execute_with_bullet_content(self):
        """Test layout recommendation with bullet point content."""
        tool = LayoutRecommenderTool()
        content = """
        Project Overview
        - First key point about the project
        - Second important detail
        - Third critical aspect
        - Fourth consideration
        """
        
        result = tool.execute(content)
        
        assert "Layout Recommendation" in result
        assert "Recommended Layout:" in result
        assert "Confidence:" in result
        assert "/100" in result
        assert "bullet_list" in result.lower()
    
    def test_execute_with_minimal_content(self):
        """Test layout recommendation with minimal content."""
        tool = LayoutRecommenderTool()
        content = "Big Impact Statement"
        
        result = tool.execute(content)
        
        assert "Layout Recommendation" in result
        assert "title_only" in result.lower()
    
    def test_execute_with_image_reference(self):
        """Test layout recommendation with image reference."""
        tool = LayoutRecommenderTool()
        content = """
        Visual Data Analysis
        - See the chart below
        - Image shows key trends
        """
        
        result = tool.execute(content)
        
        assert "Layout Recommendation" in result
        # Should recommend image_placeholder or bullet_list
        assert "image_placeholder" in result.lower() or "bullet_list" in result.lower()
    
    def test_execute_with_comparison_content(self):
        """Test layout recommendation with comparison content."""
        tool = LayoutRecommenderTool()
        content = """
        Option A vs Option B
        - Left side features
        - Right side features
        - Comparison of benefits
        """
        
        result = tool.execute(content)
        
        assert "Layout Recommendation" in result
        assert "two_column" in result.lower()
    
    def test_execute_with_empty_content(self):
        """Test layout recommendation with empty content."""
        tool = LayoutRecommenderTool()
        result = tool.execute("")
        
        assert "Error" in result
        assert "non-empty string" in result
    
    def test_execute_with_invalid_content(self):
        """Test layout recommendation with invalid content type."""
        tool = LayoutRecommenderTool()
        result = tool.execute(None)
        
        assert "Error" in result
    
    def test_shows_layout_options(self):
        """Test that result shows available layout options."""
        tool = LayoutRecommenderTool()
        content = "Sample content"
        
        result = tool.execute(content)
        
        assert "bullet_list" in result
        assert "two_column" in result
        assert "title_only" in result
        assert "image_placeholder" in result
    
    def test_provides_reasoning(self):
        """Test that recommendation includes reasoning."""
        tool = LayoutRecommenderTool()
        content = """
        Title
        - Point 1
        - Point 2
        - Point 3
        """
        
        result = tool.execute(content)
        
        assert "Reasoning:" in result
        assert len(result) > 100  # Should have substantial explanation


class TestBalanceCheckerTool:
    """Tests for BalanceCheckerTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = BalanceCheckerTool()
        assert tool.name == "balance_checker"
        assert "balance" in tool.description.lower()
        assert "distribution" in tool.description.lower()
    
    def test_execute_with_balanced_slides(self):
        """Test balance check with well-balanced slides."""
        tool = BalanceCheckerTool()
        content = """
        Slide 1: Introduction
        - Point one with details
        - Point two with details
        - Point three with details
        ---
        Slide 2: Main Content
        - First key aspect
        - Second key aspect
        - Third key aspect
        ---
        Slide 3: Conclusion
        - Summary point one
        - Summary point two
        - Summary point three
        """
        
        result = tool.execute(content)
        
        assert "Balance Score:" in result
        assert "/100" in result
        assert "Slides Analyzed:" in result
        
        # Should have good score for balanced content
        score_line = [line for line in result.split('\n') if 'Balance Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score >= 70  # Should score well for balanced slides
    
    def test_execute_with_imbalanced_slides(self):
        """Test balance check with imbalanced slides."""
        tool = BalanceCheckerTool()
        content = """
        Slide 1: Short
        - One point
        ---
        Slide 2: Very Long Content
        - First point with extensive details and explanations
        - Second point with even more comprehensive information
        - Third point covering multiple aspects in depth
        - Fourth point adding additional context
        - Fifth point with supplementary details
        - Sixth point with extra information
        """
        
        result = tool.execute(content)
        
        assert "Balance Score:" in result
        
        # Should have lower score for imbalanced content
        score_line = [line for line in result.split('\n') if 'Balance Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score < 80  # Should score lower for imbalanced slides
    
    def test_execute_with_single_slide(self):
        """Test balance check with single slide."""
        tool = BalanceCheckerTool()
        content = "Single slide content"
        
        result = tool.execute(content)
        
        assert "N/A" in result or "at least 2 slides" in result
    
    def test_execute_with_empty_content(self):
        """Test balance check with empty content."""
        tool = BalanceCheckerTool()
        result = tool.execute("")
        
        assert "Error" in result
    
    def test_execute_with_invalid_content(self):
        """Test balance check with invalid content type."""
        tool = BalanceCheckerTool()
        result = tool.execute(None)
        
        assert "Error" in result
    
    def test_detects_overloaded_slides(self):
        """Test detection of overloaded slides."""
        tool = BalanceCheckerTool()
        content = """
        Slide 1: Normal
        - Point one
        - Point two
        ---
        Slide 2: Overloaded
        - Point one with lots of text and details
        - Point two with extensive information
        - Point three with comprehensive coverage
        - Point four with additional context
        - Point five with supplementary details
        - Point six with extra information
        - Point seven with more content
        """
        
        result = tool.execute(content)
        
        assert "overloaded" in result.lower() or "Overloaded" in result
    
    def test_provides_recommendations(self):
        """Test that tool provides recommendations."""
        tool = BalanceCheckerTool()
        content = """
        Slide 1: Short
        - One
        ---
        Slide 2: Long content here
        - Many points
        - More details
        - Extra information
        """
        
        result = tool.execute(content)
        
        assert "Recommendations:" in result or "recommendations" in result.lower()
    
    def test_shows_content_distribution(self):
        """Test that result shows content distribution metrics."""
        tool = BalanceCheckerTool()
        content = """
        Slide 1
        - Point
        ---
        Slide 2
        - Point
        """
        
        result = tool.execute(content)
        
        assert "Content Distribution:" in result
        assert "Average Words" in result or "avg" in result.lower()


class TestNotesGeneratorTool:
    """Tests for NotesGeneratorTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = NotesGeneratorTool()
        assert tool.name == "notes_generator"
        assert "notes" in tool.description.lower()
        assert "speaker" in tool.description.lower()
    
    def test_execute_with_standard_slide(self):
        """Test notes generation with standard slide content."""
        tool = NotesGeneratorTool()
        content = """
        Introduction to Machine Learning
        - Machine learning is a subset of AI
        - Algorithms learn from data
        - Applications in various industries
        """
        
        result = tool.execute(content)
        
        assert "Speaker Notes" in result
        assert "Notes:" in result
        assert "Slide:" in result
        assert "Introduction to Machine Learning" in result
        
        # Check that notes are present and reasonable length
        notes_section = result.split("Notes:")[1].split("\n\n")[0]
        word_count = len(notes_section.split())
        assert word_count >= 20  # Should have substantial notes
        assert word_count <= 100  # But not too long
    
    def test_execute_with_bullet_points(self):
        """Test notes generation with bullet point content."""
        tool = NotesGeneratorTool()
        content = """
        Key Benefits
        - Increased efficiency
        - Cost reduction
        - Better outcomes
        """
        
        result = tool.execute(content)
        
        assert "Speaker Notes" in result
        assert "Key Benefits" in result
        
        # Should mention the key points
        notes_section = result.lower()
        assert "efficiency" in notes_section or "cost" in notes_section or "outcomes" in notes_section
    
    def test_execute_with_minimal_content(self):
        """Test notes generation with minimal content."""
        tool = NotesGeneratorTool()
        content = "Simple Title"
        
        result = tool.execute(content)
        
        assert "Speaker Notes" in result
        assert "Simple Title" in result
        # Should still generate some notes
        assert "Notes:" in result
    
    def test_execute_with_empty_content(self):
        """Test notes generation with empty content."""
        tool = NotesGeneratorTool()
        result = tool.execute("")
        
        assert "Error" in result
    
    def test_execute_with_invalid_content(self):
        """Test notes generation with invalid content type."""
        tool = NotesGeneratorTool()
        result = tool.execute(None)
        
        assert "Error" in result
    
    def test_generates_2_3_sentences(self):
        """Test that notes are 2-3 sentences as specified."""
        tool = NotesGeneratorTool()
        content = """
        Project Overview
        - First point
        - Second point
        - Third point
        """
        
        result = tool.execute(content)
        
        # Extract the notes section
        notes_section = result.split("Notes:")[1].split("\n\n")[0].strip()
        
        # Count sentences (split by . ! ?)
        import re
        sentences = [s.strip() for s in re.split(r'[.!?]+', notes_section) if s.strip()]
        
        # Should have 2-3 sentences
        assert 2 <= len(sentences) <= 3
    
    def test_shows_word_count(self):
        """Test that result shows word count."""
        tool = NotesGeneratorTool()
        content = "Sample Slide Title\n- Point one\n- Point two"
        
        result = tool.execute(content)
        
        assert "Word Count:" in result
    
    def test_shows_sentence_count(self):
        """Test that result shows sentence count."""
        tool = NotesGeneratorTool()
        content = "Sample Slide Title\n- Point one\n- Point two"
        
        result = tool.execute(content)
        
        assert "Sentence Count:" in result


class TestToolIntegration:
    """Integration tests for all design tools."""
    
    def test_all_tools_instantiate(self):
        """Test that all tools can be instantiated."""
        tools = [
            LayoutRecommenderTool(),
            BalanceCheckerTool(),
            NotesGeneratorTool()
        ]
        
        assert len(tools) == 3
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)
        assert all(hasattr(tool, 'execute') for tool in tools)
    
    def test_tools_have_unique_names(self):
        """Test that all tools have unique names."""
        tools = [
            LayoutRecommenderTool(),
            BalanceCheckerTool(),
            NotesGeneratorTool()
        ]
        
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))  # All unique
    
    def test_tools_work_with_tool_registry(self):
        """Test that tools can be registered in tool registry."""
        from orchestrator.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Register all design tools
        registry.register(LayoutRecommenderTool(), agent_type="design")
        registry.register(BalanceCheckerTool(), agent_type="design")
        registry.register(NotesGeneratorTool(), agent_type="design")
        
        # Verify registration
        design_tools = registry.get_tools_for_agent("design")
        assert len(design_tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in design_tools]
        assert "layout_recommender" in tool_names
        assert "balance_checker" in tool_names
        assert "notes_generator" in tool_names
    
    def test_tools_inherit_from_base_tool(self):
        """Test that all tools inherit from BaseTool."""
        from orchestrator.tools.base_tool import BaseTool
        
        tools = [
            LayoutRecommenderTool(),
            BalanceCheckerTool(),
            NotesGeneratorTool()
        ]
        
        for tool in tools:
            assert isinstance(tool, BaseTool)
    
    def test_tools_have_execute_method(self):
        """Test that all tools have execute method."""
        tools = [
            LayoutRecommenderTool(),
            BalanceCheckerTool(),
            NotesGeneratorTool()
        ]
        
        for tool in tools:
            assert hasattr(tool, 'execute')
            assert callable(tool.execute)
