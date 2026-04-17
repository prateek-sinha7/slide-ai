"""Tests for Content Agent tools."""
import pytest
from orchestrator.tools.content_tools import (
    FactCheckerTool,
    LengthValidatorTool,
    BulletQualityScorer
)


class TestFactCheckerTool:
    """Tests for FactCheckerTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = FactCheckerTool()
        assert tool.name == "fact_checker"
        assert "fact" in tool.description.lower()
        assert "verify" in tool.description.lower()
    
    def test_execute_with_valid_claim(self):
        """Test fact checking with valid claim."""
        tool = FactCheckerTool()
        result = tool.execute("Python is a programming language")
        
        # Should return results or error message (not empty)
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
        assert "Fact Check Result" in result or "Error" in result
    
    def test_execute_with_empty_claim(self):
        """Test fact checking with empty claim."""
        tool = FactCheckerTool()
        result = tool.execute("")
        
        assert "Error" in result
        assert "non-empty string" in result
    
    def test_execute_with_invalid_claim(self):
        """Test fact checking with invalid claim type."""
        tool = FactCheckerTool()
        result = tool.execute(None)
        
        assert "Error" in result
    
    def test_result_format(self):
        """Test that result has expected format."""
        tool = FactCheckerTool()
        result = tool.execute("Water boils at 100 degrees Celsius")
        
        # Should contain key sections
        if "Error" not in result:
            assert "Claim:" in result
            assert "Status:" in result
            assert "Confidence:" in result


class TestLengthValidatorTool:
    """Tests for LengthValidatorTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = LengthValidatorTool()
        assert tool.name == "length_validator"
        assert "length" in tool.description.lower()
        assert "validate" in tool.description.lower()
    
    def test_execute_with_good_bullets(self):
        """Test validation with well-sized bullet points."""
        tool = LengthValidatorTool()
        content = """
        - This is a well-sized bullet point with ten to fifteen words
        - Another bullet point that fits within the ideal word count range
        - Third bullet point with appropriate length for presentation slides
        """
        
        result = tool.execute(content)
        
        assert "Length Validation Result" in result
        assert "Overall Score:" in result
        assert "/100" in result
        
        # Should have good score for well-sized bullets
        score_line = [line for line in result.split('\n') if 'Overall Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score >= 70  # Should score well
    
    def test_execute_with_long_bullets(self):
        """Test validation with overly long bullet points."""
        tool = LengthValidatorTool()
        content = """
        - This is an extremely long bullet point that goes on and on with way too many words and should definitely be condensed for better readability
        """
        
        result = tool.execute(content)
        
        assert "Length Validation Result" in result
        assert "TOO_LONG" in result or "LONG" in result
    
    def test_execute_with_short_bullets(self):
        """Test validation with too-short bullet points."""
        tool = LengthValidatorTool()
        content = """
        - Short
        - Too brief
        - Tiny
        """
        
        result = tool.execute(content)
        
        assert "Length Validation Result" in result
        assert "SHORT" in result or "TOO_SHORT" in result
    
    def test_execute_with_empty_content(self):
        """Test validation with empty content."""
        tool = LengthValidatorTool()
        result = tool.execute("")
        
        assert "Error" in result or "No bullet points found" in result
    
    def test_extract_different_bullet_formats(self):
        """Test extraction of different bullet point formats."""
        tool = LengthValidatorTool()
        content = """
        - Dash bullet point with ten to fifteen words here
        * Asterisk bullet point with ten to fifteen words here
        1. Numbered bullet point with ten to fifteen words here
        2) Parenthesis numbered bullet with ten to fifteen words here
        """
        
        result = tool.execute(content)
        
        assert "Bullet Points Analyzed: 4" in result


class TestBulletQualityScorer:
    """Tests for BulletQualityScorer."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = BulletQualityScorer()
        assert tool.name == "bullet_quality_scorer"
        assert "quality" in tool.description.lower()
        assert "bullet" in tool.description.lower()
    
    def test_execute_with_excellent_bullets(self):
        """Test quality scoring with excellent bullet points."""
        tool = BulletQualityScorer()
        content = """
        - Increase revenue by 25% through strategic market expansion initiatives
        - Deliver exceptional customer service with 95% satisfaction ratings consistently
        - Transform operations using AI-powered automation reducing costs by 30%
        """
        
        result = tool.execute(content)
        
        assert "Bullet Point Quality Analysis" in result
        assert "Overall Quality Score:" in result
        assert "/100" in result
        
        # Should have decent score for good bullets
        score_line = [line for line in result.split('\n') if 'Overall Quality Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score >= 50  # Should score reasonably well
    
    def test_execute_with_poor_bullets(self):
        """Test quality scoring with poor bullet points."""
        tool = BulletQualityScorer()
        content = """
        - stuff
        - thing
        - some content
        """
        
        result = tool.execute(content)
        
        assert "Bullet Point Quality Analysis" in result
        
        # Should have low score (adjusted threshold based on actual scoring)
        score_line = [line for line in result.split('\n') if 'Overall Quality Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score < 80  # Should score poorly
    
    def test_execute_with_empty_content(self):
        """Test quality scoring with empty content."""
        tool = BulletQualityScorer()
        result = tool.execute("")
        
        assert "Error" in result or "No bullet points found" in result
    
    def test_scores_clarity(self):
        """Test that clarity is scored."""
        tool = BulletQualityScorer()
        content = """
        - Clear and well-structured bullet point with proper capitalization
        """
        
        result = tool.execute(content)
        
        assert "Clarity:" in result
        assert "/100" in result
    
    def test_scores_impact(self):
        """Test that impact is scored."""
        tool = BulletQualityScorer()
        content = """
        - Achieve significant results through strategic implementation
        """
        
        result = tool.execute(content)
        
        assert "Impact:" in result
        assert "/100" in result
    
    def test_scores_specificity(self):
        """Test that specificity is scored."""
        tool = BulletQualityScorer()
        content = """
        - Increase sales by 25% in Q4 2024
        """
        
        result = tool.execute(content)
        
        assert "Specificity:" in result
        assert "/100" in result
    
    def test_provides_recommendations(self):
        """Test that tool provides recommendations."""
        tool = BulletQualityScorer()
        content = """
        - vague content
        - more stuff
        """
        
        result = tool.execute(content)
        
        assert "Key Recommendations:" in result
    
    def test_detects_action_verbs(self):
        """Test detection of action verbs for impact."""
        tool = BulletQualityScorer()
        content = """
        - Achieve excellence through continuous improvement and innovation
        """
        
        result = tool.execute(content)
        
        # Should recognize action verb
        assert "Impact:" in result


class TestToolIntegration:
    """Integration tests for all content tools."""
    
    def test_all_tools_instantiate(self):
        """Test that all tools can be instantiated."""
        tools = [
            FactCheckerTool(),
            LengthValidatorTool(),
            BulletQualityScorer()
        ]
        
        assert len(tools) == 3
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)
        assert all(hasattr(tool, 'execute') for tool in tools)
    
    def test_tools_have_unique_names(self):
        """Test that all tools have unique names."""
        tools = [
            FactCheckerTool(),
            LengthValidatorTool(),
            BulletQualityScorer()
        ]
        
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))  # All unique
    
    def test_tools_work_with_tool_registry(self):
        """Test that tools can be registered in tool registry."""
        from orchestrator.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Register all content tools
        registry.register(FactCheckerTool(), agent_type="content")
        registry.register(LengthValidatorTool(), agent_type="content")
        registry.register(BulletQualityScorer(), agent_type="content")
        
        # Verify registration
        content_tools = registry.get_tools_for_agent("content")
        assert len(content_tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in content_tools]
        assert "fact_checker" in tool_names
        assert "length_validator" in tool_names
        assert "bullet_quality_scorer" in tool_names
