"""Design Agent tools for slide layout and visual design."""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from orchestrator.tools.base_tool import BaseTool
from pydantic import Field


logger = logging.getLogger(__name__)


class LayoutRecommenderTool(BaseTool):
    """
    Layout recommendation engine for slide design.
    
    Suggests appropriate slide layouts based on content structure.
    Supports layouts: bullet_list, two_column, title_only, image_placeholder.
    
    Requirements: 6.1, 6.4
    """
    
    name: str = "layout_recommender"
    description: str = (
        "Recommend appropriate slide layouts based on content structure. "
        "Input should be slide content with title and body text. "
        "Returns recommended layout type and reasoning."
    )
    
    def execute(self, content: str) -> str:
        """
        Recommend a layout based on slide content structure.
        
        Args:
            content: Slide content with title and body text
            
        Returns:
            Layout recommendation with reasoning
        """
        if not content or not isinstance(content, str):
            return "Error: Content must be a non-empty string"
        
        try:
            # Analyze content structure
            structure = self._analyze_content_structure(content)
            
            # Determine best layout
            layout, confidence, reasoning = self._recommend_layout(structure)
            
            logger.info(
                f"Layout recommendation: {layout} (confidence: {confidence}%) "
                f"for content with {structure['bullet_count']} bullets"
            )
            
            return self._format_recommendation(
                layout=layout,
                confidence=confidence,
                reasoning=reasoning,
                structure=structure
            )
            
        except Exception as e:
            error_msg = f"Layout recommendation failed: {str(e)}"
            logger.error(f"Layout recommender error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze the structure of slide content.
        
        Args:
            content: Slide content text
            
        Returns:
            Dictionary with structure metrics
        """
        lines = content.split('\n')
        
        # Count bullet points
        bullet_count = 0
        for line in lines:
            line = line.strip()
            if re.match(r'^[-*•]\s+', line) or re.match(r'^\d+[\.\)]\s+', line):
                bullet_count += 1
        
        # Count paragraphs (non-bullet text blocks)
        paragraph_count = 0
        in_paragraph = False
        for line in lines:
            line = line.strip()
            is_bullet = bool(re.match(r'^[-*•]\s+', line) or re.match(r'^\d+[\.\)]\s+', line))
            
            if line and not is_bullet:
                if not in_paragraph:
                    paragraph_count += 1
                    in_paragraph = True
            elif not line:
                in_paragraph = False
        
        # Check for image indicators
        image_keywords = ['image', 'photo', 'diagram', 'chart', 'graph', 'figure', 'illustration']
        has_image_reference = any(
            keyword in content.lower()
            for keyword in image_keywords
        )
        
        # Check for comparison/contrast indicators
        comparison_keywords = ['vs', 'versus', 'compared to', 'difference', 'contrast']
        has_comparison = any(
            keyword in content.lower()
            for keyword in comparison_keywords
        )
        
        # Check for columns/sections
        column_indicators = ['left:', 'right:', 'column', 'section']
        has_columns = any(
            indicator in content.lower()
            for indicator in column_indicators
        )
        
        # Calculate text density
        word_count = len(content.split())
        line_count = len([line for line in lines if line.strip()])
        
        return {
            'bullet_count': bullet_count,
            'paragraph_count': paragraph_count,
            'has_image_reference': has_image_reference,
            'has_comparison': has_comparison,
            'has_columns': has_columns,
            'word_count': word_count,
            'line_count': line_count,
            'text_density': word_count / max(line_count, 1)
        }
    
    def _recommend_layout(self, structure: Dict[str, Any]) -> Tuple[str, int, str]:
        """
        Recommend a layout based on content structure.
        
        Args:
            structure: Content structure metrics
            
        Returns:
            Tuple of (layout_type, confidence, reasoning)
        """
        bullet_count = structure['bullet_count']
        paragraph_count = structure['paragraph_count']
        has_image = structure['has_image_reference']
        has_comparison = structure['has_comparison']
        has_columns = structure['has_columns']
        word_count = structure['word_count']
        
        # Decision logic for layout recommendation
        
        # Title only: minimal content
        if word_count < 20 and bullet_count == 0 and paragraph_count <= 1:
            return (
                'title_only',
                95,
                'Minimal content suggests a title-only slide for impact'
            )
        
        # Image placeholder: explicit image reference
        if has_image and bullet_count <= 2:
            return (
                'image_placeholder',
                90,
                'Content references visual elements and has minimal text'
            )
        
        # Two column: comparison or explicit column structure
        if has_comparison or has_columns:
            return (
                'two_column',
                85,
                'Content structure suggests side-by-side comparison or sections'
            )
        
        # Two column: balanced content with moderate bullets
        if bullet_count >= 4 and bullet_count <= 8 and paragraph_count <= 1:
            return (
                'two_column',
                75,
                'Moderate bullet count works well in two-column layout for balance'
            )
        
        # Bullet list: standard bullet points
        if bullet_count >= 3:
            return (
                'bullet_list',
                90,
                f'Content has {bullet_count} bullet points, ideal for bullet list layout'
            )
        
        # Bullet list: some bullets with text
        if bullet_count > 0:
            return (
                'bullet_list',
                80,
                'Content includes bullet points, bullet list layout recommended'
            )
        
        # Image placeholder: longer text that might benefit from visual
        if word_count > 100 and paragraph_count > 2:
            return (
                'image_placeholder',
                70,
                'Dense text content would benefit from supporting visual elements'
            )
        
        # Default: bullet list
        return (
            'bullet_list',
            60,
            'Standard bullet list layout as default for general content'
        )
    
    def _format_recommendation(
        self,
        layout: str,
        confidence: int,
        reasoning: str,
        structure: Dict[str, Any]
    ) -> str:
        """
        Format layout recommendation for agent consumption.
        
        Args:
            layout: Recommended layout type
            confidence: Confidence score (0-100)
            reasoning: Explanation for the recommendation
            structure: Content structure metrics
            
        Returns:
            Formatted recommendation
        """
        result = f"Layout Recommendation\n"
        result += f"====================\n\n"
        result += f"Recommended Layout: {layout}\n"
        result += f"Confidence: {confidence}/100\n\n"
        result += f"Reasoning: {reasoning}\n\n"
        
        result += f"Content Analysis:\n"
        result += f"  • Bullet Points: {structure['bullet_count']}\n"
        result += f"  • Paragraphs: {structure['paragraph_count']}\n"
        result += f"  • Word Count: {structure['word_count']}\n"
        result += f"  • Has Image Reference: {'Yes' if structure['has_image_reference'] else 'No'}\n"
        result += f"  • Has Comparison: {'Yes' if structure['has_comparison'] else 'No'}\n"
        result += f"  • Has Columns: {'Yes' if structure['has_columns'] else 'No'}\n\n"
        
        result += f"Layout Options:\n"
        result += f"  • bullet_list: Standard bullet point layout\n"
        result += f"  • two_column: Side-by-side content sections\n"
        result += f"  • title_only: Minimal text for impact\n"
        result += f"  • image_placeholder: Visual-focused with supporting text\n"
        
        return result


class BalanceCheckerTool(BaseTool):
    """
    Visual balance checker for slide content distribution.
    
    Evaluates content distribution across slides to ensure visual balance.
    Returns balance score (0-100) and recommendations for improvement.
    
    Requirements: 6.2, 6.5, 8.1
    """
    
    name: str = "balance_checker"
    description: str = (
        "Evaluate content distribution and visual balance across slides. "
        "Input should be a list of slides with their content. "
        "Returns balance score (0-100) and recommendations."
    )
    
    def execute(self, slides_content: str) -> str:
        """
        Evaluate visual balance across slides.
        
        Args:
            slides_content: Content from multiple slides (separated by slide markers)
            
        Returns:
            Balance score and recommendations
        """
        if not slides_content or not isinstance(slides_content, str):
            return "Error: Slides content must be a non-empty string"
        
        try:
            # Parse slides from content
            slides = self._parse_slides(slides_content)
            
            if len(slides) < 2:
                return (
                    "Balance Score: N/A\n"
                    "Feedback: Need at least 2 slides to evaluate balance. "
                    "Provide multiple slides separated by '---' or 'Slide N:' markers."
                )
            
            # Analyze balance metrics
            metrics = self._analyze_balance(slides)
            
            # Calculate overall balance score
            score = self._calculate_balance_score(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics)
            
            logger.info(
                f"Balance check completed for {len(slides)} slides - Score: {score}/100"
            )
            
            return self._format_balance_result(
                score=score,
                metrics=metrics,
                recommendations=recommendations,
                slide_count=len(slides)
            )
            
        except Exception as e:
            error_msg = f"Balance check failed: {str(e)}"
            logger.error(f"Balance checker error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _parse_slides(self, content: str) -> List[str]:
        """
        Parse individual slides from combined content.
        
        Args:
            content: Combined slides content
            
        Returns:
            List of individual slide contents
        """
        # Try different slide separators
        if '---' in content:
            slides = content.split('---')
        elif re.search(r'Slide \d+:', content, re.IGNORECASE):
            slides = re.split(r'Slide \d+:', content, flags=re.IGNORECASE)
        elif re.search(r'## Slide \d+', content):
            slides = re.split(r'## Slide \d+', content)
        else:
            # Treat as single slide
            slides = [content]
        
        # Clean up slides
        slides = [slide.strip() for slide in slides if slide.strip()]
        
        return slides
    
    def _analyze_balance(self, slides: List[str]) -> Dict[str, Any]:
        """
        Analyze balance metrics across slides.
        
        Args:
            slides: List of slide contents
            
        Returns:
            Dictionary with balance metrics
        """
        # Calculate word counts per slide
        word_counts = [len(slide.split()) for slide in slides]
        
        # Calculate bullet counts per slide
        bullet_counts = []
        for slide in slides:
            bullets = len(re.findall(r'^[-*•]\s+', slide, re.MULTILINE))
            bullets += len(re.findall(r'^\d+[\.\)]\s+', slide, re.MULTILINE))
            bullet_counts.append(bullets)
        
        # Calculate line counts per slide
        line_counts = [
            len([line for line in slide.split('\n') if line.strip()])
            for slide in slides
        ]
        
        # Calculate statistics
        avg_words = sum(word_counts) / len(word_counts)
        avg_bullets = sum(bullet_counts) / len(bullet_counts)
        avg_lines = sum(line_counts) / len(line_counts)
        
        # Calculate variance (measure of imbalance)
        word_variance = sum((wc - avg_words) ** 2 for wc in word_counts) / len(word_counts)
        bullet_variance = sum((bc - avg_bullets) ** 2 for bc in bullet_counts) / len(bullet_counts)
        
        # Find extremes
        max_words = max(word_counts)
        min_words = min(word_counts)
        max_bullets = max(bullet_counts)
        min_bullets = min(bullet_counts)
        
        # Identify overloaded and sparse slides
        overloaded_slides = [
            i + 1 for i, wc in enumerate(word_counts)
            if wc > avg_words * 1.5
        ]
        sparse_slides = [
            i + 1 for i, wc in enumerate(word_counts)
            if wc < avg_words * 0.5 and wc > 0
        ]
        
        return {
            'word_counts': word_counts,
            'bullet_counts': bullet_counts,
            'line_counts': line_counts,
            'avg_words': avg_words,
            'avg_bullets': avg_bullets,
            'avg_lines': avg_lines,
            'word_variance': word_variance,
            'bullet_variance': bullet_variance,
            'max_words': max_words,
            'min_words': min_words,
            'max_bullets': max_bullets,
            'min_bullets': min_bullets,
            'overloaded_slides': overloaded_slides,
            'sparse_slides': sparse_slides
        }
    
    def _calculate_balance_score(self, metrics: Dict[str, Any]) -> int:
        """
        Calculate overall balance score (0-100).
        
        Args:
            metrics: Balance metrics
            
        Returns:
            Balance score
        """
        score = 100
        
        # Penalize high word count variance
        word_variance = metrics['word_variance']
        avg_words = metrics['avg_words']
        
        if avg_words > 0:
            word_cv = (word_variance ** 0.5) / avg_words  # Coefficient of variation
            if word_cv > 0.5:
                score -= 30
            elif word_cv > 0.3:
                score -= 15
        
        # Penalize extreme differences
        word_range = metrics['max_words'] - metrics['min_words']
        if word_range > 100:
            score -= 20
        elif word_range > 50:
            score -= 10
        
        # Penalize overloaded slides
        overloaded_count = len(metrics['overloaded_slides'])
        if overloaded_count > 0:
            score -= min(20, overloaded_count * 10)
        
        # Penalize sparse slides
        sparse_count = len(metrics['sparse_slides'])
        if sparse_count > 0:
            score -= min(15, sparse_count * 8)
        
        # Penalize bullet count imbalance
        bullet_range = metrics['max_bullets'] - metrics['min_bullets']
        if bullet_range > 5:
            score -= 10
        elif bullet_range > 3:
            score -= 5
        
        return max(0, score)
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations for improving balance.
        
        Args:
            metrics: Balance metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Overloaded slides
        if metrics['overloaded_slides']:
            slides_str = ', '.join(str(s) for s in metrics['overloaded_slides'])
            recommendations.append(
                f"Reduce content on overloaded slides: {slides_str} "
                f"(avg: {int(metrics['avg_words'])} words, these have {int(metrics['max_words'])}+)"
            )
        
        # Sparse slides
        if metrics['sparse_slides']:
            slides_str = ', '.join(str(s) for s in metrics['sparse_slides'])
            recommendations.append(
                f"Add more content to sparse slides: {slides_str} "
                f"(avg: {int(metrics['avg_words'])} words, these have {int(metrics['min_words'])})"
            )
        
        # High variance
        if metrics['word_variance'] > (metrics['avg_words'] * 0.3) ** 2:
            recommendations.append(
                "Content distribution is uneven. Aim for more consistent word counts across slides."
            )
        
        # Bullet imbalance
        bullet_range = metrics['max_bullets'] - metrics['min_bullets']
        if bullet_range > 5:
            recommendations.append(
                f"Bullet point distribution varies widely ({metrics['min_bullets']}-{metrics['max_bullets']}). "
                "Aim for 3-5 bullets per slide consistently."
            )
        
        # All good
        if not recommendations:
            recommendations.append("Content is well-balanced across slides!")
        
        return recommendations
    
    def _format_balance_result(
        self,
        score: int,
        metrics: Dict[str, Any],
        recommendations: List[str],
        slide_count: int
    ) -> str:
        """
        Format balance check results for agent consumption.
        
        Args:
            score: Balance score (0-100)
            metrics: Balance metrics
            recommendations: List of recommendations
            slide_count: Number of slides analyzed
            
        Returns:
            Formatted balance result
        """
        result = f"Visual Balance Analysis\n"
        result += f"======================\n\n"
        result += f"Balance Score: {score}/100\n"
        result += f"Slides Analyzed: {slide_count}\n\n"
        
        # Overall assessment
        if score >= 85:
            result += f"Overall Assessment: EXCELLENT BALANCE ✓✓✓\n"
        elif score >= 70:
            result += f"Overall Assessment: GOOD BALANCE ✓✓\n"
        elif score >= 55:
            result += f"Overall Assessment: FAIR BALANCE ✓\n"
        else:
            result += f"Overall Assessment: NEEDS REBALANCING ✗\n"
        
        result += f"\nContent Distribution:\n"
        result += f"  • Average Words per Slide: {int(metrics['avg_words'])}\n"
        result += f"  • Average Bullets per Slide: {metrics['avg_bullets']:.1f}\n"
        result += f"  • Word Count Range: {metrics['min_words']}-{metrics['max_words']}\n"
        result += f"  • Bullet Count Range: {metrics['min_bullets']}-{metrics['max_bullets']}\n"
        
        if metrics['overloaded_slides']:
            result += f"  • Overloaded Slides: {', '.join(str(s) for s in metrics['overloaded_slides'])}\n"
        
        if metrics['sparse_slides']:
            result += f"  • Sparse Slides: {', '.join(str(s) for s in metrics['sparse_slides'])}\n"
        
        result += f"\nRecommendations:\n"
        for i, rec in enumerate(recommendations, 1):
            result += f"  {i}. {rec}\n"
        
        return result


class NotesGeneratorTool(BaseTool):
    """
    Speaker notes generator for presentation slides.
    
    Generates 2-3 sentence speaker notes for each slide to help presenters.
    Notes provide context, talking points, and transitions.
    
    Requirements: 6.3, 6.6
    """
    
    name: str = "notes_generator"
    description: str = (
        "Generate speaker notes for presentation slides. "
        "Input should be slide content with title and body. "
        "Returns 2-3 sentence speaker notes for the presenter."
    )
    
    def execute(self, slide_content: str) -> str:
        """
        Generate speaker notes for a slide.
        
        Args:
            slide_content: Slide content with title and body
            
        Returns:
            Generated speaker notes (2-3 sentences)
        """
        if not slide_content or not isinstance(slide_content, str):
            return "Error: Slide content must be a non-empty string"
        
        try:
            # Parse slide structure
            title, body = self._parse_slide_content(slide_content)
            
            # Extract key points
            key_points = self._extract_key_points(body)
            
            # Generate notes
            notes = self._generate_notes(title, key_points, body)
            
            logger.info(f"Generated speaker notes for slide: '{title[:50]}...'")
            
            return self._format_notes(notes, title)
            
        except Exception as e:
            error_msg = f"Notes generation failed: {str(e)}"
            logger.error(f"Notes generator error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _parse_slide_content(self, content: str) -> Tuple[str, str]:
        """
        Parse slide content into title and body.
        
        Args:
            content: Slide content
            
        Returns:
            Tuple of (title, body)
        """
        lines = content.split('\n')
        
        # First non-empty line is typically the title
        title = ""
        body_lines = []
        found_title = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if not found_title:
                # Remove markdown headers
                title = re.sub(r'^#+\s*', '', line)
                # Remove "Title:" prefix if present
                title = re.sub(r'^Title:\s*', '', title, flags=re.IGNORECASE)
                found_title = True
            else:
                body_lines.append(line)
        
        body = '\n'.join(body_lines)
        
        return title, body
    
    def _extract_key_points(self, body: str) -> List[str]:
        """
        Extract key points from slide body.
        
        Args:
            body: Slide body text
            
        Returns:
            List of key points
        """
        key_points = []
        lines = body.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract bullet points
            if re.match(r'^[-*•]\s+', line):
                point = re.sub(r'^[-*•]\s+', '', line).strip()
                if point:
                    key_points.append(point)
            elif re.match(r'^\d+[\.\)]\s+', line):
                point = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                if point:
                    key_points.append(point)
        
        # If no bullets, extract sentences
        if not key_points:
            sentences = re.split(r'[.!?]+', body)
            key_points = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        return key_points[:5]  # Limit to top 5 points
    
    def _generate_notes(self, title: str, key_points: List[str], body: str) -> str:
        """
        Generate speaker notes based on slide content.
        
        Args:
            title: Slide title
            key_points: List of key points from the slide
            body: Full slide body text
            
        Returns:
            Generated speaker notes (2-3 sentences)
        """
        notes_sentences = []
        
        # Sentence 1: Introduction/context
        if title:
            intro = f"This slide covers {title.lower()}."
            notes_sentences.append(intro)
        
        # Sentence 2: Key points summary
        if key_points:
            if len(key_points) == 1:
                summary = f"The main point is: {key_points[0][:80]}."
            elif len(key_points) == 2:
                summary = f"Focus on two key aspects: {key_points[0][:40]} and {key_points[1][:40]}."
            else:
                summary = f"Emphasize {len(key_points)} key points including {key_points[0][:40]} and {key_points[1][:40]}."
            notes_sentences.append(summary)
        
        # Sentence 3: Action/transition (if we have room)
        if len(notes_sentences) < 3:
            # Check for action words or next steps
            action_indicators = ['implement', 'achieve', 'create', 'develop', 'ensure', 'improve']
            has_action = any(
                indicator in body.lower()
                for indicator in action_indicators
            )
            
            if has_action:
                action = "Highlight the actionable steps and expected outcomes for the audience."
            else:
                action = "Allow time for questions before moving to the next topic."
            
            notes_sentences.append(action)
        
        # Combine into 2-3 sentences
        notes = ' '.join(notes_sentences[:3])
        
        return notes
    
    def _format_notes(self, notes: str, title: str) -> str:
        """
        Format speaker notes for agent consumption.
        
        Args:
            notes: Generated notes
            title: Slide title
            
        Returns:
            Formatted notes
        """
        result = f"Speaker Notes\n"
        result += f"=============\n\n"
        result += f"Slide: {title}\n\n"
        result += f"Notes:\n{notes}\n\n"
        result += f"Word Count: {len(notes.split())} words\n"
        result += f"Sentence Count: {len([s for s in re.split(r'[.!?]+', notes) if s.strip()])}\n"
        
        return result
