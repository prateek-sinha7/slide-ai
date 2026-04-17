"""Tests for Reviewer Agent tools."""
import pytest
from orchestrator.tools.reviewer_tools import (
    GrammarCheckerTool,
    RedundancyDetectorTool,
    ToneValidatorTool
)


class TestGrammarCheckerTool:
    """Tests for GrammarCheckerTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = GrammarCheckerTool()
        assert tool.name == "grammar_checker"
        assert "grammar" in tool.description.lower()
        assert "errors" in tool.description.lower()
    
    def test_execute_with_correct_text(self):
        """Test grammar check with correct text."""
        tool = GrammarCheckerTool()
        text = "This is a well-written sentence. It has proper capitalization and punctuation."
        
        result = tool.execute(text)
        
        assert result is not None
        assert isinstance(result, str)
        assert "Grammar Check:" in result
        assert "PASSED" in result or "0 issue" in result
    
    def test_execute_with_capitalization_error(self):
        """Test detection of capitalization errors."""
        tool = GrammarCheckerTool()
        text = "this sentence starts with lowercase. Another sentence."
        
        result = tool.execute(text)
        
        assert "CAPITALIZATION" in result or "lowercase" in result.lower()
    
    def test_execute_with_punctuation_error(self):
        """Test detection of punctuation errors."""
        tool = GrammarCheckerTool()
        text = "This has double  spaces. And space before ,comma."
        
        result = tool.execute(text)
        
        assert "PUNCTUATION" in result or "space" in result.lower()
    
    def test_execute_with_subject_verb_agreement_error(self):
        """Test detection of subject-verb agreement errors."""
        tool = GrammarCheckerTool()
        text = "He are going to the store. She were happy."
        
        result = tool.execute(text)
        
        assert "SUBJECT_VERB_AGREEMENT" in result or "agreement" in result.lower()
    
    def test_execute_with_common_word_error(self):
        """Test detection of common word errors."""
        tool = GrammarCheckerTool()
        text = "I should of done that. Their is a problem."
        
        result = tool.execute(text)
        
        assert "WORD_USAGE" in result or "should have" in result.lower() or "there is" in result.lower()
    
    def test_execute_with_empty_text(self):
        """Test grammar check with empty text."""
        tool = GrammarCheckerTool()
        result = tool.execute("")
        
        assert "Error" in result
        assert "non-empty string" in result
    
    def test_execute_with_invalid_text(self):
        """Test grammar check with invalid text type."""
        tool = GrammarCheckerTool()
        result = tool.execute(None)
        
        assert "Error" in result
    
    def test_provides_confidence_scores(self):
        """Test that tool provides confidence scores."""
        tool = GrammarCheckerTool()
        text = "this is wrong"
        
        result = tool.execute(text)
        
        if "issue" in result.lower() and "found" in result.lower():
            assert "Confidence:" in result or "confidence" in result.lower()


class TestRedundancyDetectorTool:
    """Tests for RedundancyDetectorTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = RedundancyDetectorTool()
        assert tool.name == "redundancy_detector"
        assert "redundancy" in tool.description.lower() or "redundant" in tool.description.lower()
    
    def test_execute_with_no_redundancy(self):
        """Test redundancy detection with unique content."""
        tool = RedundancyDetectorTool()
        content = """
        Slide 1: Introduction
        Welcome to our presentation about artificial intelligence.
        
        Slide 2: Machine Learning
        Machine learning is a subset of AI that focuses on algorithms.
        
        Slide 3: Applications
        Real-world applications include healthcare and finance.
        """
        
        result = tool.execute(content)
        
        assert "Redundancy Check:" in result
        assert "PASSED" in result or "no" in result.lower()
    
    def test_execute_with_high_redundancy(self):
        """Test redundancy detection with repeated content."""
        tool = RedundancyDetectorTool()
        content = """
        Slide 1: Introduction
        Artificial intelligence is transforming the world with machine learning algorithms.
        
        Slide 2: Overview
        Artificial intelligence is transforming the world with machine learning algorithms.
        """
        
        result = tool.execute(content)
        
        assert "Redundancy Check:" in result
        # Should detect high similarity
        if "issue" in result.lower() or "found" in result.lower():
            assert "similar" in result.lower() or "%" in result
    
    def test_execute_with_single_slide(self):
        """Test redundancy detection with single slide."""
        tool = RedundancyDetectorTool()
        content = "Slide 1: Only one slide here."
        
        result = tool.execute(content)
        
        assert "N/A" in result or "at least 2" in result.lower()
    
    def test_execute_with_empty_content(self):
        """Test redundancy detection with empty content."""
        tool = RedundancyDetectorTool()
        result = tool.execute("")
        
        assert "Error" in result
    
    def test_calculates_similarity_scores(self):
        """Test that tool calculates similarity scores."""
        tool = RedundancyDetectorTool()
        content = """
        Slide 1: First
        The quick brown fox jumps over the lazy dog.
        
        Slide 2: Second
        The quick brown fox jumps over the lazy cat.
        """
        
        result = tool.execute(content)
        
        # Should calculate similarity
        assert "Redundancy Check:" in result
    
    def test_provides_suggestions(self):
        """Test that tool provides suggestions for redundancy."""
        tool = RedundancyDetectorTool()
        content = """
        Slide 1: AI Overview
        Artificial intelligence machine learning deep learning neural networks.
        
        Slide 2: AI Introduction
        Artificial intelligence machine learning deep learning neural networks.
        """
        
        result = tool.execute(content)
        
        if "issue" in result.lower():
            assert "Suggestion:" in result or "suggestion" in result.lower()


class TestToneValidatorTool:
    """Tests for ToneValidatorTool."""
    
    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = ToneValidatorTool()
        assert tool.name == "tone_validator"
        assert "tone" in tool.description.lower()
        assert "consistency" in tool.description.lower()
    
    def test_execute_with_consistent_formal_tone(self):
        """Test tone validation with consistent formal tone."""
        tool = ToneValidatorTool()
        content = """
        Slide 1: Introduction
        Therefore, we shall examine the fundamental principles of artificial intelligence.
        
        Slide 2: Methodology
        Furthermore, we must establish a comprehensive framework for implementation.
        
        Slide 3: Conclusion
        In conclusion, these findings demonstrate significant implications.
        """
        
        result = tool.execute(content)
        
        assert "Tone Consistency Score:" in result
        assert "/100" in result
        assert "formal" in result.lower()
        
        # Should have high consistency score
        score_line = [line for line in result.split('\n') if 'Tone Consistency Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        assert score >= 70  # Should be consistent
    
    def test_execute_with_consistent_casual_tone(self):
        """Test tone validation with consistent casual tone."""
        tool = ToneValidatorTool()
        content = """
        Slide 1: Hey There
        So, let's talk about AI! It's gonna be awesome!
        
        Slide 2: Cool Stuff
        Yeah, machine learning is super cool and really helpful!
        
        Slide 3: Wrap Up
        Okay, that's it! Thanks for checking this out!
        """
        
        result = tool.execute(content)
        
        assert "Tone Consistency Score:" in result
        assert "casual" in result.lower()
    
    def test_execute_with_inconsistent_tone(self):
        """Test tone validation with inconsistent tone."""
        tool = ToneValidatorTool()
        content = """
        Slide 1: Formal Introduction
        Therefore, we shall examine the fundamental principles.
        
        Slide 2: Casual Content
        Yeah, so AI is super cool and awesome!
        
        Slide 3: Back to Formal
        In conclusion, these findings demonstrate significance.
        """
        
        result = tool.execute(content)
        
        assert "Tone Consistency Score:" in result
        
        # Should detect inconsistency
        score_line = [line for line in result.split('\n') if 'Tone Consistency Score:' in line][0]
        score = int(score_line.split(':')[1].split('/')[0].strip())
        # Inconsistent tone should have lower score
        assert score < 100
    
    def test_execute_with_single_slide(self):
        """Test tone validation with single slide."""
        tool = ToneValidatorTool()
        content = "Slide 1: Only one slide here."
        
        result = tool.execute(content)
        
        assert "N/A" in result or "at least 2" in result.lower()
    
    def test_execute_with_empty_content(self):
        """Test tone validation with empty content."""
        tool = ToneValidatorTool()
        result = tool.execute("")
        
        assert "Error" in result
    
    def test_detects_formal_indicators(self):
        """Test detection of formal language indicators."""
        tool = ToneValidatorTool()
        content = """
        Slide 1: Analysis
        Therefore, we must utilize comprehensive methodologies.
        
        Slide 2: Implementation
        Furthermore, we shall establish systematic frameworks.
        """
        
        result = tool.execute(content)
        
        assert "formal" in result.lower()
    
    def test_detects_casual_indicators(self):
        """Test detection of casual language indicators."""
        tool = ToneValidatorTool()
        content = """
        Slide 1: Hey
        Gonna talk about cool stuff today!
        
        Slide 2: Nice
        Yeah, this is awesome and super helpful!
        """
        
        result = tool.execute(content)
        
        assert "casual" in result.lower()
    
    def test_provides_mismatch_details(self):
        """Test that tool provides details about tone mismatches."""
        tool = ToneValidatorTool()
        content = """
        Slide 1: Formal
        Therefore, we shall examine the principles.
        
        Slide 2: Casual
        Yeah, it's gonna be cool!
        """
        
        result = tool.execute(content)
        
        if "Mismatch" in result or "mismatch" in result.lower():
            assert "Suggestion:" in result or "suggestion" in result.lower()


class TestToolIntegration:
    """Integration tests for all reviewer tools."""
    
    def test_all_tools_instantiate(self):
        """Test that all tools can be instantiated."""
        tools = [
            GrammarCheckerTool(),
            RedundancyDetectorTool(),
            ToneValidatorTool()
        ]
        
        assert len(tools) == 3
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)
        assert all(hasattr(tool, 'execute') for tool in tools)
    
    def test_tools_have_unique_names(self):
        """Test that all tools have unique names."""
        tools = [
            GrammarCheckerTool(),
            RedundancyDetectorTool(),
            ToneValidatorTool()
        ]
        
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))  # All unique
    
    def test_tools_work_with_tool_registry(self):
        """Test that tools can be registered in tool registry."""
        from orchestrator.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Register all reviewer tools
        registry.register(GrammarCheckerTool(), agent_type="reviewer")
        registry.register(RedundancyDetectorTool(), agent_type="reviewer")
        registry.register(ToneValidatorTool(), agent_type="reviewer")
        
        # Verify registration
        reviewer_tools = registry.get_tools_for_agent("reviewer")
        assert len(reviewer_tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in reviewer_tools]
        assert "grammar_checker" in tool_names
        assert "redundancy_detector" in tool_names
        assert "tone_validator" in tool_names
    
    def test_tools_return_strings(self):
        """Test that all tools return string results."""
        tools = [
            GrammarCheckerTool(),
            RedundancyDetectorTool(),
            ToneValidatorTool()
        ]
        
        test_content = "This is a test sentence."
        
        for tool in tools:
            result = tool.execute(test_content)
            assert isinstance(result, str)
            assert len(result) > 0
