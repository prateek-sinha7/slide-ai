"""Content Agent tools for slide content generation and validation."""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from orchestrator.tools.base_tool import BaseTool
from pydantic import Field


logger = logging.getLogger(__name__)


class FactCheckerTool(BaseTool):
    """
    Fact checker tool for verifying claims in slide content.
    
    Uses web search to verify factual claims against online sources.
    Returns verification results with confidence scores for each claim.
    
    Requirements: 4.1, 4.4, 12.1, 12.4
    """
    
    name: str = "fact_checker"
    description: str = (
        "Verify factual claims in slide content using web search. "
        "Input should be a claim or statement to verify. "
        "Returns verification result with confidence score (0-100) and supporting sources."
    )
    
    def execute(self, claim: str) -> str:
        """
        Verify a factual claim using web search.
        
        Args:
            claim: Factual claim or statement to verify
            
        Returns:
            Verification result with confidence score and sources
        """
        if not claim or not isinstance(claim, str):
            return "Error: Claim must be a non-empty string"
        
        try:
            # Import here to avoid dependency issues if not installed
            from langchain_community.tools import DuckDuckGoSearchResults
            
            # Create DuckDuckGo search tool
            search = DuckDuckGoSearchResults(num_results=3)
            
            # Execute search with the claim
            search_query = f"verify fact: {claim}"
            results = search.run(search_query)
            
            if not results or results.strip() == "":
                return self._format_verification_result(
                    claim=claim,
                    confidence=50,
                    status="UNCERTAIN",
                    reasoning="No search results found to verify this claim.",
                    sources=[]
                )
            
            # Analyze search results to determine confidence
            confidence, status, reasoning = self._analyze_search_results(claim, results)
            
            # Extract sources from results
            sources = self._extract_sources(results)
            
            logger.info(f"Fact check completed for claim: '{claim[:50]}...' - Status: {status}")
            
            return self._format_verification_result(
                claim=claim,
                confidence=confidence,
                status=status,
                reasoning=reasoning,
                sources=sources
            )
            
        except ImportError:
            error_msg = (
                "DuckDuckGo search not available. "
                "Install with: pip install duckduckgo-search"
            )
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Fact check failed: {str(e)}"
            logger.error(f"Fact checker error for claim '{claim[:50]}...': {error_msg}")
            return f"Error: {error_msg}"
    
    def _analyze_search_results(self, claim: str, results: str) -> Tuple[int, str, str]:
        """
        Analyze search results to determine verification confidence.
        
        Args:
            claim: Original claim
            results: Search results text
            
        Returns:
            Tuple of (confidence_score, status, reasoning)
        """
        results_lower = results.lower()
        claim_lower = claim.lower()
        
        # Extract key terms from claim
        claim_words = set(word.lower() for word in re.findall(r'\b\w+\b', claim) if len(word) > 3)
        
        # Count how many claim words appear in results
        matching_words = sum(1 for word in claim_words if word in results_lower)
        match_ratio = matching_words / len(claim_words) if claim_words else 0
        
        # Check for verification indicators
        positive_indicators = ['confirmed', 'verified', 'true', 'correct', 'accurate', 'yes']
        negative_indicators = ['false', 'incorrect', 'wrong', 'debunked', 'myth', 'no']
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in results_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in results_lower)
        
        # Determine confidence and status
        if match_ratio >= 0.6 and positive_count > negative_count:
            confidence = min(85, int(60 + match_ratio * 40))
            status = "VERIFIED"
            reasoning = "Multiple sources support this claim with consistent information."
        elif match_ratio >= 0.6 and negative_count > positive_count:
            confidence = min(80, int(60 + match_ratio * 30))
            status = "DISPUTED"
            reasoning = "Sources found but contain contradictory or negative information."
        elif match_ratio >= 0.4:
            confidence = min(70, int(40 + match_ratio * 50))
            status = "PARTIALLY_VERIFIED"
            reasoning = "Some supporting information found, but verification is incomplete."
        else:
            confidence = 40
            status = "UNCERTAIN"
            reasoning = "Limited relevant information found to verify this claim."
        
        return confidence, status, reasoning
    
    def _extract_sources(self, results: str) -> List[str]:
        """
        Extract source URLs from search results.
        
        Args:
            results: Search results text
            
        Returns:
            List of source URLs
        """
        # Extract URLs using regex
        url_pattern = r'https?://[^\s\])]+'
        urls = re.findall(url_pattern, results)
        
        # Return up to 3 unique URLs
        unique_urls = list(dict.fromkeys(urls))[:3]
        return unique_urls
    
    def _format_verification_result(
        self,
        claim: str,
        confidence: int,
        status: str,
        reasoning: str,
        sources: List[str]
    ) -> str:
        """
        Format verification result for agent consumption.
        
        Args:
            claim: Original claim
            confidence: Confidence score (0-100)
            status: Verification status
            reasoning: Explanation of the verification
            sources: List of source URLs
            
        Returns:
            Formatted verification result
        """
        result = f"Fact Check Result\n"
        result += f"================\n\n"
        result += f"Claim: {claim}\n\n"
        result += f"Status: {status}\n"
        result += f"Confidence: {confidence}/100\n\n"
        result += f"Reasoning: {reasoning}\n"
        
        if sources:
            result += f"\nSources:\n"
            for i, source in enumerate(sources, 1):
                result += f"  {i}. {source}\n"
        else:
            result += f"\nSources: None found\n"
        
        return result


class LengthValidatorTool(BaseTool):
    """
    Content length validator for bullet points.
    
    Ensures bullet points are concise and within the 10-15 word maximum.
    Returns validation results with word counts for each bullet point.
    
    Requirements: 4.2, 4.5
    """
    
    name: str = "length_validator"
    description: str = (
        "Validate the length of bullet points in slide content. "
        "Input should be slide content with bullet points. "
        "Returns validation results with word counts and feedback for each bullet point."
    )
    
    def execute(self, content: str) -> str:
        """
        Validate the length of bullet points in content.
        
        Args:
            content: Slide content with bullet points
            
        Returns:
            Validation results with word counts and feedback
        """
        if not content or not isinstance(content, str):
            return "Error: Content must be a non-empty string"
        
        try:
            # Extract bullet points from content
            bullet_points = self._extract_bullet_points(content)
            
            if not bullet_points:
                return (
                    "Validation Result: No bullet points found\n"
                    "Feedback: Please provide content with bullet points to validate."
                )
            
            # Validate each bullet point
            validations = []
            total_score = 0
            
            for i, bullet in enumerate(bullet_points, 1):
                word_count = len(bullet.split())
                score, status, feedback = self._validate_bullet_length(word_count)
                
                validations.append({
                    'number': i,
                    'text': bullet,
                    'word_count': word_count,
                    'score': score,
                    'status': status,
                    'feedback': feedback
                })
                
                total_score += score
            
            # Calculate average score
            avg_score = int(total_score / len(validations)) if validations else 0
            
            logger.info(
                f"Length validation completed for {len(bullet_points)} bullet points - "
                f"Average score: {avg_score}/100"
            )
            
            return self._format_validation_result(validations, avg_score)
            
        except Exception as e:
            error_msg = f"Length validation failed: {str(e)}"
            logger.error(f"Length validator error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _extract_bullet_points(self, content: str) -> List[str]:
        """
        Extract bullet points from content.
        
        Args:
            content: Content text with bullet points
            
        Returns:
            List of bullet point texts
        """
        bullet_points = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Match common bullet point patterns
            # - Bullet point
            # * Bullet point
            # • Bullet point
            # 1. Bullet point
            # 1) Bullet point
            if re.match(r'^[-*•]\s+', line):
                # Remove bullet marker
                bullet_text = re.sub(r'^[-*•]\s+', '', line).strip()
                if bullet_text:
                    bullet_points.append(bullet_text)
            elif re.match(r'^\d+[\.\)]\s+', line):
                # Remove numbered marker
                bullet_text = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                if bullet_text:
                    bullet_points.append(bullet_text)
        
        return bullet_points
    
    def _validate_bullet_length(self, word_count: int) -> Tuple[int, str, str]:
        """
        Validate a single bullet point's length.
        
        Args:
            word_count: Number of words in the bullet point
            
        Returns:
            Tuple of (score, status, feedback)
        """
        # Ideal range: 10-15 words
        if 10 <= word_count <= 15:
            return 100, "EXCELLENT", "Perfect length for a bullet point"
        
        # Acceptable range: 8-17 words
        elif 8 <= word_count <= 17:
            return 80, "GOOD", "Acceptable length, close to ideal"
        
        # Slightly short: 5-7 words
        elif 5 <= word_count < 8:
            return 60, "SHORT", "Could be more detailed (aim for 10-15 words)"
        
        # Too short: < 5 words
        elif word_count < 5:
            return 30, "TOO_SHORT", "Too brief, add more detail (aim for 10-15 words)"
        
        # Slightly long: 18-20 words
        elif 18 <= word_count <= 20:
            return 60, "LONG", "Slightly too long, consider condensing (aim for 10-15 words)"
        
        # Too long: > 20 words
        else:
            return 30, "TOO_LONG", "Too verbose, break into multiple points or condense (max 15 words)"
    
    def _format_validation_result(
        self,
        validations: List[Dict[str, Any]],
        avg_score: int
    ) -> str:
        """
        Format validation results for agent consumption.
        
        Args:
            validations: List of validation results for each bullet point
            avg_score: Average score across all bullet points
            
        Returns:
            Formatted validation result
        """
        result = f"Length Validation Result\n"
        result += f"=======================\n\n"
        result += f"Overall Score: {avg_score}/100\n"
        result += f"Bullet Points Analyzed: {len(validations)}\n\n"
        
        # Summary by status
        status_counts = {}
        for v in validations:
            status = v['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        result += f"Summary:\n"
        for status, count in sorted(status_counts.items()):
            result += f"  {status}: {count}\n"
        
        result += f"\nDetailed Results:\n"
        result += f"-----------------\n"
        
        for v in validations:
            result += f"\n{v['number']}. {v['text'][:60]}{'...' if len(v['text']) > 60 else ''}\n"
            result += f"   Words: {v['word_count']} | Score: {v['score']}/100 | Status: {v['status']}\n"
            result += f"   Feedback: {v['feedback']}\n"
        
        # Overall recommendation
        result += f"\nRecommendation:\n"
        if avg_score >= 90:
            result += "  ✓ Excellent! All bullet points are well-sized.\n"
        elif avg_score >= 70:
            result += "  ~ Good overall, minor adjustments recommended.\n"
        else:
            result += "  ✗ Significant length issues detected. Revise bullet points to 10-15 words each.\n"
        
        return result



class BulletQualityScorer(BaseTool):
    """
    Bullet point quality scorer for content evaluation.
    
    Evaluates bullet points for clarity, impact, and specificity.
    Returns quality score (0-100) per bullet point with detailed feedback.
    
    Requirements: 4.3, 4.6, 8.1
    """
    
    name: str = "bullet_quality_scorer"
    description: str = (
        "Evaluate the quality of bullet points in slide content. "
        "Input should be slide content with bullet points. "
        "Returns quality scores (0-100) for each bullet point based on clarity, impact, and specificity."
    )
    
    def execute(self, content: str) -> str:
        """
        Evaluate the quality of bullet points in content.
        
        Args:
            content: Slide content with bullet points
            
        Returns:
            Quality scores and feedback for each bullet point
        """
        if not content or not isinstance(content, str):
            return "Error: Content must be a non-empty string"
        
        try:
            # Extract bullet points from content
            bullet_points = self._extract_bullet_points(content)
            
            if not bullet_points:
                return (
                    "Quality Score: N/A\n"
                    "Feedback: No bullet points found. "
                    "Please provide content with bullet points to evaluate."
                )
            
            # Score each bullet point
            scores = []
            total_score = 0
            
            for i, bullet in enumerate(bullet_points, 1):
                clarity_score, clarity_feedback = self._score_clarity(bullet)
                impact_score, impact_feedback = self._score_impact(bullet)
                specificity_score, specificity_feedback = self._score_specificity(bullet)
                
                # Calculate overall score (weighted average)
                overall_score = int(
                    clarity_score * 0.35 +
                    impact_score * 0.35 +
                    specificity_score * 0.30
                )
                
                scores.append({
                    'number': i,
                    'text': bullet,
                    'overall_score': overall_score,
                    'clarity_score': clarity_score,
                    'clarity_feedback': clarity_feedback,
                    'impact_score': impact_score,
                    'impact_feedback': impact_feedback,
                    'specificity_score': specificity_score,
                    'specificity_feedback': specificity_feedback
                })
                
                total_score += overall_score
            
            # Calculate average score
            avg_score = int(total_score / len(scores)) if scores else 0
            
            logger.info(
                f"Quality scoring completed for {len(bullet_points)} bullet points - "
                f"Average score: {avg_score}/100"
            )
            
            return self._format_quality_result(scores, avg_score)
            
        except Exception as e:
            error_msg = f"Quality scoring failed: {str(e)}"
            logger.error(f"Quality scorer error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _extract_bullet_points(self, content: str) -> List[str]:
        """
        Extract bullet points from content.
        
        Args:
            content: Content text with bullet points
            
        Returns:
            List of bullet point texts
        """
        bullet_points = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Match common bullet point patterns
            if re.match(r'^[-*•]\s+', line):
                bullet_text = re.sub(r'^[-*•]\s+', '', line).strip()
                if bullet_text:
                    bullet_points.append(bullet_text)
            elif re.match(r'^\d+[\.\)]\s+', line):
                bullet_text = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                if bullet_text:
                    bullet_points.append(bullet_text)
        
        return bullet_points
    
    def _score_clarity(self, bullet: str) -> Tuple[int, str]:
        """
        Score bullet point clarity (0-100).
        
        Args:
            bullet: Bullet point text
            
        Returns:
            Tuple of (score, feedback)
        """
        score = 100
        feedback_items = []
        
        # Check for clear sentence structure
        if not bullet[0].isupper():
            score -= 10
            feedback_items.append("should start with capital letter")
        
        # Check for vague words
        vague_words = ['thing', 'stuff', 'something', 'various', 'many', 'some', 'etc']
        vague_count = sum(1 for word in vague_words if word in bullet.lower())
        if vague_count > 0:
            score -= min(20, vague_count * 10)
            feedback_items.append("contains vague words")
        
        # Check for jargon or overly complex words
        complex_indicators = len([word for word in bullet.split() if len(word) > 12])
        if complex_indicators > 2:
            score -= 15
            feedback_items.append("may be too complex")
        
        # Check for passive voice indicators
        passive_indicators = ['is being', 'was being', 'has been', 'have been', 'will be']
        if any(indicator in bullet.lower() for indicator in passive_indicators):
            score -= 10
            feedback_items.append("consider active voice")
        
        # Generate feedback
        if score >= 90:
            feedback = "Clear and easy to understand"
        elif score >= 70:
            feedback = "Mostly clear, minor improvements: " + ", ".join(feedback_items)
        else:
            feedback = "Clarity issues: " + ", ".join(feedback_items)
        
        return max(0, score), feedback
    
    def _score_impact(self, bullet: str) -> Tuple[int, str]:
        """
        Score bullet point impact (0-100).
        
        Args:
            bullet: Bullet point text
            
        Returns:
            Tuple of (score, feedback)
        """
        score = 100
        feedback_items = []
        
        # Check for action verbs (strong impact)
        action_verbs = [
            'achieve', 'create', 'deliver', 'drive', 'enable', 'enhance',
            'improve', 'increase', 'optimize', 'reduce', 'transform',
            'accelerate', 'boost', 'maximize', 'streamline'
        ]
        has_action_verb = any(verb in bullet.lower() for verb in action_verbs)
        
        if has_action_verb:
            score += 0  # Already at 100
            feedback_items.append("strong action verb")
        else:
            score -= 15
            feedback_items.append("add action verb for impact")
        
        # Check for quantifiable elements (numbers, percentages, metrics)
        has_numbers = bool(re.search(r'\d+', bullet))
        if has_numbers:
            feedback_items.append("includes quantifiable data")
        else:
            score -= 10
            feedback_items.append("consider adding metrics")
        
        # Check for weak words that reduce impact
        weak_words = ['maybe', 'might', 'could', 'possibly', 'perhaps', 'try']
        weak_count = sum(1 for word in weak_words if word in bullet.lower())
        if weak_count > 0:
            score -= min(20, weak_count * 10)
            feedback_items.append("remove weak/tentative words")
        
        # Check for benefit-oriented language
        benefit_words = ['benefit', 'advantage', 'value', 'result', 'outcome', 'success']
        has_benefit = any(word in bullet.lower() for word in benefit_words)
        if has_benefit:
            feedback_items.append("highlights benefits")
        
        # Generate feedback
        if score >= 90:
            feedback = "Strong impact and compelling"
        elif score >= 70:
            feedback = "Good impact, suggestions: " + ", ".join(feedback_items)
        else:
            feedback = "Low impact, improve by: " + ", ".join(feedback_items)
        
        return max(0, score), feedback
    
    def _score_specificity(self, bullet: str) -> Tuple[int, str]:
        """
        Score bullet point specificity (0-100).
        
        Args:
            bullet: Bullet point text
            
        Returns:
            Tuple of (score, feedback)
        """
        score = 100
        feedback_items = []
        
        # Check for generic/vague terms
        generic_terms = [
            'good', 'bad', 'nice', 'great', 'important', 'interesting',
            'useful', 'helpful', 'effective', 'efficient', 'better'
        ]
        generic_count = sum(1 for term in generic_terms if term in bullet.lower())
        if generic_count > 1:
            score -= min(25, generic_count * 15)
            feedback_items.append("too many generic terms")
        
        # Check for specific details (numbers, names, examples)
        has_numbers = bool(re.search(r'\d+', bullet))
        has_proper_nouns = bool(re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', bullet))
        
        specificity_indicators = sum([has_numbers, has_proper_nouns])
        
        if specificity_indicators == 0:
            score -= 20
            feedback_items.append("add specific details/examples")
        elif specificity_indicators == 1:
            feedback_items.append("good specificity")
        else:
            feedback_items.append("excellent specificity")
        
        # Check for concrete vs abstract language
        abstract_words = ['concept', 'idea', 'theory', 'notion', 'aspect', 'factor']
        abstract_count = sum(1 for word in abstract_words if word in bullet.lower())
        if abstract_count > 1:
            score -= 15
            feedback_items.append("too abstract, use concrete examples")
        
        # Check word count (very short bullets are often too vague)
        word_count = len(bullet.split())
        if word_count < 5:
            score -= 20
            feedback_items.append("too brief to be specific")
        
        # Generate feedback
        if score >= 90:
            feedback = "Highly specific and concrete"
        elif score >= 70:
            feedback = "Reasonably specific, suggestions: " + ", ".join(feedback_items)
        else:
            feedback = "Too vague, improve by: " + ", ".join(feedback_items)
        
        return max(0, score), feedback
    
    def _format_quality_result(
        self,
        scores: List[Dict[str, Any]],
        avg_score: int
    ) -> str:
        """
        Format quality scoring results for agent consumption.
        
        Args:
            scores: List of quality scores for each bullet point
            avg_score: Average score across all bullet points
            
        Returns:
            Formatted quality result
        """
        result = f"Bullet Point Quality Analysis\n"
        result += f"=============================\n\n"
        result += f"Overall Quality Score: {avg_score}/100\n"
        result += f"Bullet Points Analyzed: {len(scores)}\n\n"
        
        # Overall assessment
        if avg_score >= 85:
            result += f"Overall Assessment: EXCELLENT ✓✓✓\n"
        elif avg_score >= 70:
            result += f"Overall Assessment: GOOD ✓✓\n"
        elif avg_score >= 55:
            result += f"Overall Assessment: FAIR ✓\n"
        else:
            result += f"Overall Assessment: NEEDS IMPROVEMENT ✗\n"
        
        result += f"\nDetailed Scores:\n"
        result += f"----------------\n"
        
        for s in scores:
            result += f"\n{s['number']}. {s['text'][:70]}{'...' if len(s['text']) > 70 else ''}\n"
            result += f"   Overall: {s['overall_score']}/100\n"
            result += f"   • Clarity: {s['clarity_score']}/100 - {s['clarity_feedback']}\n"
            result += f"   • Impact: {s['impact_score']}/100 - {s['impact_feedback']}\n"
            result += f"   • Specificity: {s['specificity_score']}/100 - {s['specificity_feedback']}\n"
        
        # Summary recommendations
        result += f"\nKey Recommendations:\n"
        result += f"-------------------\n"
        
        # Collect common issues
        low_clarity = [s for s in scores if s['clarity_score'] < 70]
        low_impact = [s for s in scores if s['impact_score'] < 70]
        low_specificity = [s for s in scores if s['specificity_score'] < 70]
        
        if low_clarity:
            result += f"  • Improve clarity in {len(low_clarity)} bullet point(s)\n"
        if low_impact:
            result += f"  • Strengthen impact in {len(low_impact)} bullet point(s)\n"
        if low_specificity:
            result += f"  • Add specificity to {len(low_specificity)} bullet point(s)\n"
        
        if not (low_clarity or low_impact or low_specificity):
            result += f"  • All bullet points meet quality standards!\n"
        
        return result
