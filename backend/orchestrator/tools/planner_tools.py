"""Planner Agent tools for presentation outline creation and validation."""
import logging
import re
from typing import Any, Dict, List, Optional
from orchestrator.tools.base_tool import BaseTool
from pydantic import Field


logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Web search tool for researching presentation topics.
    
    Uses DuckDuckGo search to find relevant information about topics.
    Returns search results with titles, snippets, and URLs.
    
    Requirements: 3.1, 3.4, 12.1, 12.4
    """
    
    name: str = "web_search"
    description: str = (
        "Search the web for information about a topic. "
        "Input should be a search query string. "
        "Returns relevant search results with titles and snippets."
    )
    
    def execute(self, query: str) -> str:
        """
        Execute web search for the given query.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results or error message
        """
        if not query or not isinstance(query, str):
            return "Error: Query must be a non-empty string"
        
        try:
            # Import here to avoid dependency issues if not installed
            from langchain_community.tools import DuckDuckGoSearchResults
            
            # Create DuckDuckGo search tool
            search = DuckDuckGoSearchResults(num_results=5)
            
            # Execute search
            results = search.run(query)
            
            if not results or results.strip() == "":
                return f"No results found for query: {query}"
            
            logger.info(f"Web search completed for query: {query}")
            return f"Search results for '{query}':\n\n{results}"
            
        except ImportError:
            error_msg = (
                "DuckDuckGo search not available. "
                "Install with: pip install duckduckgo-search"
            )
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(f"Web search error for query '{query}': {error_msg}")
            return f"Error: {error_msg}"


class StructureValidatorTool(BaseTool):
    """
    Content structure validator for presentation outlines.
    
    Validates logical flow and coherent narrative in presentation outlines.
    Checks for proper introduction, body, and conclusion structure.
    
    Requirements: 3.2, 3.5
    """
    
    name: str = "structure_validator"
    description: str = (
        "Validate the logical flow and structure of a presentation outline. "
        "Input should be a presentation outline with slide titles. "
        "Returns a validation score (0-100) and detailed feedback."
    )
    
    def execute(self, outline: str) -> str:
        """
        Validate the structure of a presentation outline.
        
        Args:
            outline: Presentation outline text with slide titles
            
        Returns:
            Validation score and feedback
        """
        if not outline or not isinstance(outline, str):
            return "Error: Outline must be a non-empty string"
        
        try:
            score = 0
            feedback = []
            max_score = 100
            
            # Extract slide titles (lines that look like titles)
            lines = [line.strip() for line in outline.split('\n') if line.strip()]
            slide_titles = self._extract_slide_titles(lines)
            
            if not slide_titles:
                return (
                    "Validation Score: 0/100\n"
                    "Feedback: No slide titles found in outline. "
                    "Please provide a structured outline with clear slide titles."
                )
            
            # Check 1: Has introduction slide (20 points)
            has_intro = self._has_introduction(slide_titles)
            if has_intro:
                score += 20
                feedback.append("✓ Has clear introduction slide")
            else:
                feedback.append("✗ Missing introduction slide (add 'Introduction' or 'Overview')")
            
            # Check 2: Has conclusion slide (20 points)
            has_conclusion = self._has_conclusion(slide_titles)
            if has_conclusion:
                score += 20
                feedback.append("✓ Has clear conclusion slide")
            else:
                feedback.append("✗ Missing conclusion slide (add 'Conclusion' or 'Summary')")
            
            # Check 3: Logical progression (30 points)
            progression_score = self._check_logical_progression(slide_titles)
            score += progression_score
            if progression_score >= 25:
                feedback.append("✓ Good logical progression between topics")
            elif progression_score >= 15:
                feedback.append("~ Moderate logical flow, could be improved")
            else:
                feedback.append("✗ Weak logical progression, consider reordering slides")
            
            # Check 4: Appropriate length (15 points)
            length_score = self._check_length(slide_titles)
            score += length_score
            if length_score >= 12:
                feedback.append(f"✓ Good slide count ({len(slide_titles)} slides)")
            elif length_score >= 8:
                feedback.append(f"~ Acceptable slide count ({len(slide_titles)} slides)")
            else:
                if len(slide_titles) < 5:
                    feedback.append(f"✗ Too few slides ({len(slide_titles)}), add more content")
                else:
                    feedback.append(f"✗ Too many slides ({len(slide_titles)}), consider condensing")
            
            # Check 5: Title clarity (15 points)
            clarity_score = self._check_title_clarity(slide_titles)
            score += clarity_score
            if clarity_score >= 12:
                feedback.append("✓ Slide titles are clear and descriptive")
            elif clarity_score >= 8:
                feedback.append("~ Some titles could be more descriptive")
            else:
                feedback.append("✗ Many titles are vague, make them more specific")
            
            # Format result
            result = f"Validation Score: {score}/100\n\n"
            result += "Feedback:\n"
            result += "\n".join(f"  {item}" for item in feedback)
            
            logger.info(f"Structure validation completed with score: {score}/100")
            return result
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.error(f"Structure validation error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _extract_slide_titles(self, lines: List[str]) -> List[str]:
        """Extract slide titles from outline lines."""
        titles = []
        for line in lines:
            # Skip empty lines and lines that are clearly not titles
            if not line or line.startswith('-') or line.startswith('*'):
                continue
            # Remove numbering (e.g., "1. Title" -> "Title")
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
            # Remove markdown headers
            cleaned = re.sub(r'^#+\s*', '', cleaned)
            if cleaned:
                titles.append(cleaned)
        return titles
    
    def _has_introduction(self, titles: List[str]) -> bool:
        """Check if outline has an introduction slide."""
        intro_keywords = ['introduction', 'intro', 'overview', 'agenda', 'welcome']
        first_title = titles[0].lower() if titles else ""
        return any(keyword in first_title for keyword in intro_keywords)
    
    def _has_conclusion(self, titles: List[str]) -> bool:
        """Check if outline has a conclusion slide."""
        conclusion_keywords = ['conclusion', 'summary', 'recap', 'takeaway', 'closing', 'thank you']
        last_title = titles[-1].lower() if titles else ""
        return any(keyword in last_title for keyword in conclusion_keywords)
    
    def _check_logical_progression(self, titles: List[str]) -> int:
        """Check logical progression between slides (0-30 points)."""
        if len(titles) < 3:
            return 15  # Neutral score for very short presentations
        
        # Simple heuristic: check for topic coherence
        # Award points if titles seem related and build on each other
        score = 30  # Start with full points
        
        # Penalize if there are duplicate or very similar titles
        unique_titles = set(title.lower() for title in titles)
        if len(unique_titles) < len(titles) * 0.8:
            score -= 10
        
        # Penalize if middle slides have generic titles
        generic_keywords = ['slide', 'content', 'information', 'data', 'stuff']
        middle_titles = titles[1:-1] if len(titles) > 2 else titles
        generic_count = sum(
            1 for title in middle_titles
            if any(keyword in title.lower() for keyword in generic_keywords)
        )
        if generic_count > len(middle_titles) * 0.3:
            score -= 10
        
        return max(0, score)
    
    def _check_length(self, titles: List[str]) -> int:
        """Check if slide count is appropriate (0-15 points)."""
        count = len(titles)
        if 8 <= count <= 15:
            return 15  # Ideal range
        elif 5 <= count <= 20:
            return 10  # Acceptable range
        elif count < 5:
            return 5   # Too short
        else:
            return 5   # Too long
    
    def _check_title_clarity(self, titles: List[str]) -> int:
        """Check if titles are clear and descriptive (0-15 points)."""
        if not titles:
            return 0
        
        score = 15
        vague_count = 0
        
        # Check for vague or too-short titles
        for title in titles:
            words = title.split()
            if len(words) < 2:
                vague_count += 1
            elif len(title) < 10:
                vague_count += 0.5
        
        # Penalize based on vague title ratio
        vague_ratio = vague_count / len(titles)
        if vague_ratio > 0.5:
            score = 5
        elif vague_ratio > 0.3:
            score = 10
        
        return int(score)


class OutlineQualityCheckerTool(BaseTool):
    """
    Outline quality checker for presentation best practices.
    
    Scores outlines against presentation best practices including
    title clarity, flow, completeness, and audience engagement.
    
    Requirements: 3.3, 3.6, 8.1
    """
    
    name: str = "outline_quality_checker"
    description: str = (
        "Check the quality of a presentation outline against best practices. "
        "Input should be a presentation outline with slide titles and optional descriptions. "
        "Returns a quality score (0-100) and improvement suggestions."
    )
    
    def execute(self, outline: str) -> str:
        """
        Check the quality of a presentation outline.
        
        Args:
            outline: Presentation outline text
            
        Returns:
            Quality score and improvement suggestions
        """
        if not outline or not isinstance(outline, str):
            return "Error: Outline must be a non-empty string"
        
        try:
            score = 0
            suggestions = []
            max_score = 100
            
            # Extract slide titles
            lines = [line.strip() for line in outline.split('\n') if line.strip()]
            slide_titles = self._extract_slide_titles(lines)
            
            if not slide_titles:
                return (
                    "Quality Score: 0/100\n"
                    "Suggestions: No slide titles found. "
                    "Create a structured outline with clear slide titles."
                )
            
            # Check 1: Title clarity and specificity (25 points)
            clarity_score, clarity_suggestions = self._check_title_quality(slide_titles)
            score += clarity_score
            suggestions.extend(clarity_suggestions)
            
            # Check 2: Flow and narrative (25 points)
            flow_score, flow_suggestions = self._check_flow(slide_titles)
            score += flow_score
            suggestions.extend(flow_suggestions)
            
            # Check 3: Completeness (25 points)
            completeness_score, completeness_suggestions = self._check_completeness(slide_titles)
            score += completeness_score
            suggestions.extend(completeness_suggestions)
            
            # Check 4: Engagement and impact (25 points)
            engagement_score, engagement_suggestions = self._check_engagement(slide_titles)
            score += engagement_score
            suggestions.extend(engagement_suggestions)
            
            # Format result
            result = f"Quality Score: {score}/100\n\n"
            
            if score >= 80:
                result += "Overall: Excellent outline! 🌟\n\n"
            elif score >= 60:
                result += "Overall: Good outline with room for improvement. ✓\n\n"
            elif score >= 40:
                result += "Overall: Needs improvement. ~\n\n"
            else:
                result += "Overall: Significant improvements needed. ✗\n\n"
            
            if suggestions:
                result += "Improvement Suggestions:\n"
                result += "\n".join(f"  • {item}" for item in suggestions)
            else:
                result += "No major improvements needed!"
            
            logger.info(f"Quality check completed with score: {score}/100")
            return result
            
        except Exception as e:
            error_msg = f"Quality check failed: {str(e)}"
            logger.error(f"Quality check error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _extract_slide_titles(self, lines: List[str]) -> List[str]:
        """Extract slide titles from outline lines."""
        titles = []
        for line in lines:
            if not line or line.startswith('-') or line.startswith('*'):
                continue
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
            cleaned = re.sub(r'^#+\s*', '', cleaned)
            if cleaned:
                titles.append(cleaned)
        return titles
    
    def _check_title_quality(self, titles: List[str]) -> tuple[int, List[str]]:
        """Check title clarity and specificity (0-25 points)."""
        score = 25
        suggestions = []
        
        # Check for vague titles
        vague_keywords = ['slide', 'content', 'information', 'topic', 'section', 'part']
        vague_titles = [
            title for title in titles
            if any(keyword in title.lower() for keyword in vague_keywords)
        ]
        
        if vague_titles:
            score -= min(15, len(vague_titles) * 5)
            suggestions.append(
                f"Replace vague titles with specific ones: {', '.join(vague_titles[:3])}"
            )
        
        # Check for too-short titles
        short_titles = [title for title in titles if len(title.split()) < 2]
        if len(short_titles) > len(titles) * 0.3:
            score -= 10
            suggestions.append("Make titles more descriptive (aim for 3-7 words)")
        
        # Check for too-long titles
        long_titles = [title for title in titles if len(title.split()) > 10]
        if long_titles:
            score -= 5
            suggestions.append("Shorten overly long titles for better readability")
        
        return max(0, score), suggestions
    
    def _check_flow(self, titles: List[str]) -> tuple[int, List[str]]:
        """Check flow and narrative (0-25 points)."""
        score = 25
        suggestions = []
        
        # Check for introduction
        intro_keywords = ['introduction', 'intro', 'overview', 'agenda']
        has_intro = any(
            keyword in titles[0].lower()
            for keyword in intro_keywords
        ) if titles else False
        
        if not has_intro:
            score -= 8
            suggestions.append("Add an introduction or overview slide at the beginning")
        
        # Check for conclusion
        conclusion_keywords = ['conclusion', 'summary', 'takeaway', 'closing']
        has_conclusion = any(
            keyword in titles[-1].lower()
            for keyword in conclusion_keywords
        ) if titles else False
        
        if not has_conclusion:
            score -= 8
            suggestions.append("Add a conclusion or summary slide at the end")
        
        # Check for logical grouping
        if len(titles) > 10:
            # For longer presentations, suggest sections
            suggestions.append("Consider grouping slides into clear sections or chapters")
            score -= 5
        
        return max(0, score), suggestions
    
    def _check_completeness(self, titles: List[str]) -> tuple[int, List[str]]:
        """Check completeness (0-25 points)."""
        score = 25
        suggestions = []
        
        count = len(titles)
        
        # Check slide count
        if count < 5:
            score -= 15
            suggestions.append(f"Add more slides (currently {count}, aim for 8-15)")
        elif count > 20:
            score -= 10
            suggestions.append(f"Consider condensing content (currently {count}, aim for 8-15)")
        elif count < 8:
            score -= 5
            suggestions.append("Consider adding 1-2 more slides for better coverage")
        
        # Check for key components
        has_title_slide = any(
            keyword in titles[0].lower()
            for keyword in ['title', 'introduction', 'welcome']
        ) if titles else False
        
        if not has_title_slide:
            score -= 5
            suggestions.append("Start with a clear title or introduction slide")
        
        return max(0, score), suggestions
    
    def _check_engagement(self, titles: List[str]) -> tuple[int, List[str]]:
        """Check engagement and impact (0-25 points)."""
        score = 25
        suggestions = []
        
        # Check for question-based titles (engaging)
        question_titles = [title for title in titles if '?' in title]
        if question_titles:
            score += 0  # Bonus already in base score
        else:
            suggestions.append("Consider using questions in some titles to engage audience")
            score -= 5
        
        # Check for action-oriented titles
        action_words = ['how', 'why', 'what', 'when', 'where', 'discover', 'learn', 'understand']
        action_titles = [
            title for title in titles
            if any(word in title.lower() for word in action_words)
        ]
        
        if len(action_titles) < len(titles) * 0.3:
            suggestions.append("Use more action-oriented titles (How, Why, What, etc.)")
            score -= 5
        
        # Check for variety in title structure
        unique_starts = set(title.split()[0].lower() for title in titles if title.split())
        if len(unique_starts) < len(titles) * 0.5:
            suggestions.append("Vary title structures to maintain interest")
            score -= 5
        
        # Check for storytelling elements
        story_keywords = ['journey', 'story', 'case', 'example', 'real-world']
        has_story = any(
            keyword in title.lower()
            for title in titles
            for keyword in story_keywords
        )
        
        if not has_story and len(titles) > 8:
            suggestions.append("Consider adding real-world examples or case studies")
            score -= 5
        
        return max(0, score), suggestions
