"""Reviewer Agent tools for content refinement and quality assurance."""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from orchestrator.tools.base_tool import BaseTool
from pydantic import Field


logger = logging.getLogger(__name__)


class GrammarCheckerTool(BaseTool):
    """
    Grammar checker tool for identifying grammatical errors.
    
    Uses simple rule-based grammar checking to identify common errors:
    - Capitalization issues
    - Punctuation problems
    - Subject-verb agreement
    - Common word usage errors
    
    Returns list of errors with suggestions and confidence scores.
    
    Requirements: 5.1, 5.4
    """
    
    name: str = "grammar_checker"
    description: str = (
        "Check text for grammar errors including capitalization, punctuation, "
        "and subject-verb agreement. Input should be text content to check. "
        "Returns list of errors with suggestions and confidence scores (0-100)."
    )
    
    def execute(self, text: str) -> str:
        """
        Check text for grammatical errors.
        
        Args:
            text: Text content to check
            
        Returns:
            List of errors with suggestions and confidence scores
        """
        if not text or not isinstance(text, str):
            return "Error: Text must be a non-empty string"
        
        try:
            errors = []
            
            # Check each sentence
            sentences = self._split_sentences(text)
            
            for i, sentence in enumerate(sentences, 1):
                # Check capitalization
                cap_errors = self._check_capitalization(sentence, i)
                errors.extend(cap_errors)
                
                # Check punctuation
                punct_errors = self._check_punctuation(sentence, i)
                errors.extend(punct_errors)
                
                # Check subject-verb agreement
                agreement_errors = self._check_subject_verb_agreement(sentence, i)
                errors.extend(agreement_errors)
                
                # Check common word errors
                word_errors = self._check_common_word_errors(sentence, i)
                errors.extend(word_errors)
            
            # Format results
            if not errors:
                result = "Grammar Check: PASSED ✓\n"
                result += "No grammatical errors detected."
                logger.info("Grammar check completed - no errors found")
            else:
                result = f"Grammar Check: {len(errors)} issue(s) found\n"
                result += "=" * 50 + "\n\n"
                
                for error in errors:
                    result += f"Sentence {error['sentence_num']}: {error['type']}\n"
                    result += f"  Issue: {error['issue']}\n"
                    result += f"  Suggestion: {error['suggestion']}\n"
                    result += f"  Confidence: {error['confidence']}/100\n\n"
                
                logger.info(f"Grammar check completed - {len(errors)} errors found")
            
            return result
            
        except Exception as e:
            error_msg = f"Grammar check failed: {str(e)}"
            logger.error(f"Grammar checker error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _check_capitalization(self, sentence: str, sentence_num: int) -> List[Dict[str, Any]]:
        """Check for capitalization errors."""
        errors = []
        
        if not sentence:
            return errors
        
        # Check if sentence starts with lowercase letter
        if sentence[0].islower() and sentence[0].isalpha():
            errors.append({
                'sentence_num': sentence_num,
                'type': 'CAPITALIZATION',
                'issue': f'Sentence starts with lowercase: "{sentence[:30]}..."',
                'suggestion': f'Start with capital letter: "{sentence[0].upper()}{sentence[1:30]}..."',
                'confidence': 95
            })
        
        # Check for lowercase 'i' (should be 'I')
        if re.search(r'\bi\b', sentence):
            errors.append({
                'sentence_num': sentence_num,
                'type': 'CAPITALIZATION',
                'issue': 'Lowercase "i" should be capitalized',
                'suggestion': 'Replace "i" with "I"',
                'confidence': 100
            })
        
        return errors
    
    def _check_punctuation(self, sentence: str, sentence_num: int) -> List[Dict[str, Any]]:
        """Check for punctuation errors."""
        errors = []
        
        if not sentence:
            return errors
        
        # Check for double spaces
        if '  ' in sentence:
            errors.append({
                'sentence_num': sentence_num,
                'type': 'PUNCTUATION',
                'issue': 'Multiple consecutive spaces found',
                'suggestion': 'Use single spaces between words',
                'confidence': 100
            })
        
        # Check for space before punctuation
        if re.search(r'\s+[,;:!?]', sentence):
            errors.append({
                'sentence_num': sentence_num,
                'type': 'PUNCTUATION',
                'issue': 'Space before punctuation mark',
                'suggestion': 'Remove space before punctuation',
                'confidence': 95
            })
        
        # Check for missing space after punctuation
        if re.search(r'[,;:][a-zA-Z]', sentence):
            errors.append({
                'sentence_num': sentence_num,
                'type': 'PUNCTUATION',
                'issue': 'Missing space after punctuation',
                'suggestion': 'Add space after comma, semicolon, or colon',
                'confidence': 90
            })
        
        # Check for multiple punctuation marks
        if re.search(r'[!?]{2,}', sentence):
            errors.append({
                'sentence_num': sentence_num,
                'type': 'PUNCTUATION',
                'issue': 'Multiple exclamation or question marks',
                'suggestion': 'Use single punctuation mark for professional tone',
                'confidence': 85
            })
        
        return errors
    
    def _check_subject_verb_agreement(self, sentence: str, sentence_num: int) -> List[Dict[str, Any]]:
        """Check for subject-verb agreement errors."""
        errors = []
        
        # Common subject-verb agreement patterns
        patterns = [
            (r'\b(he|she|it)\s+(are|were)\b', 'Use "is" or "was" with singular subjects', 90),
            (r'\b(they|we)\s+(is|was)\b', 'Use "are" or "were" with plural subjects', 90),
            (r'\b(I)\s+(is|are)\b', 'Use "am" with "I"', 95),
            (r'\b(you)\s+(is|am)\b', 'Use "are" with "you"', 95),
        ]
        
        sentence_lower = sentence.lower()
        
        for pattern, suggestion, confidence in patterns:
            if re.search(pattern, sentence_lower):
                errors.append({
                    'sentence_num': sentence_num,
                    'type': 'SUBJECT_VERB_AGREEMENT',
                    'issue': f'Subject-verb agreement error detected',
                    'suggestion': suggestion,
                    'confidence': confidence
                })
        
        return errors
    
    def _check_common_word_errors(self, sentence: str, sentence_num: int) -> List[Dict[str, Any]]:
        """Check for common word usage errors."""
        errors = []
        
        # Common word confusion patterns
        patterns = [
            (r'\btheir\s+is\b', 'Use "there is" instead of "their is"', 95),
            (r'\btheir\s+are\b', 'Use "there are" instead of "their are"', 95),
            (r'\byour\s+(a|an|the)\b', 'Use "you\'re" (you are) instead of "your"', 85),
            (r'\bits\s+is\b', 'Use "it\'s" (it is) or "it is" instead of "its is"', 90),
            (r'\bshould\s+of\b', 'Use "should have" instead of "should of"', 100),
            (r'\bcould\s+of\b', 'Use "could have" instead of "could of"', 100),
            (r'\bwould\s+of\b', 'Use "would have" instead of "would of"', 100),
        ]
        
        sentence_lower = sentence.lower()
        
        for pattern, suggestion, confidence in patterns:
            if re.search(pattern, sentence_lower):
                errors.append({
                    'sentence_num': sentence_num,
                    'type': 'WORD_USAGE',
                    'issue': 'Common word usage error detected',
                    'suggestion': suggestion,
                    'confidence': confidence
                })
        
        return errors


class RedundancyDetectorTool(BaseTool):
    """
    Redundancy detector tool for identifying repeated information.
    
    Uses text similarity to identify repeated information across slides.
    Calculates similarity scores between slide content and flags redundant sections.
    
    Returns redundancy report with flagged slides and suggestions.
    
    Requirements: 5.2, 5.5
    """
    
    name: str = "redundancy_detector"
    description: str = (
        "Detect redundant or repeated information across slides. "
        "Input should be presentation content with multiple slides. "
        "Returns redundancy report with similarity scores and flagged slides."
    )
    
    def execute(self, content: str) -> str:
        """
        Detect redundant information across slides.
        
        Args:
            content: Presentation content with multiple slides
            
        Returns:
            Redundancy report with flagged slides and suggestions
        """
        if not content or not isinstance(content, str):
            return "Error: Content must be a non-empty string"
        
        try:
            # Parse slides from content
            slides = self._parse_slides(content)
            
            if len(slides) < 2:
                return (
                    "Redundancy Check: N/A\n"
                    "Need at least 2 slides to check for redundancy."
                )
            
            # Calculate similarity between all slide pairs
            redundancies = []
            
            for i in range(len(slides)):
                for j in range(i + 1, len(slides)):
                    similarity = self._calculate_similarity(
                        slides[i]['content'],
                        slides[j]['content']
                    )
                    
                    # Flag if similarity is high (> 60%)
                    if similarity > 60:
                        redundancies.append({
                            'slide1': i + 1,
                            'slide1_title': slides[i]['title'],
                            'slide2': j + 1,
                            'slide2_title': slides[j]['title'],
                            'similarity': similarity,
                            'common_content': self._find_common_content(
                                slides[i]['content'],
                                slides[j]['content']
                            )
                        })
            
            # Format results
            if not redundancies:
                result = "Redundancy Check: PASSED ✓\n"
                result += f"Analyzed {len(slides)} slides - no significant redundancy detected."
                logger.info(f"Redundancy check completed - no issues found across {len(slides)} slides")
            else:
                result = f"Redundancy Check: {len(redundancies)} issue(s) found\n"
                result += "=" * 50 + "\n\n"
                
                # Sort by similarity (highest first)
                redundancies.sort(key=lambda x: x['similarity'], reverse=True)
                
                for red in redundancies:
                    result += f"Slides {red['slide1']} and {red['slide2']}: {red['similarity']}% similar\n"
                    result += f"  Slide {red['slide1']}: {red['slide1_title']}\n"
                    result += f"  Slide {red['slide2']}: {red['slide2_title']}\n"
                    
                    if red['common_content']:
                        result += f"  Common content: {red['common_content'][:100]}...\n"
                    
                    if red['similarity'] >= 80:
                        result += f"  Suggestion: Consider merging these slides or removing duplicate content\n"
                    else:
                        result += f"  Suggestion: Review for overlapping information and consolidate if possible\n"
                    
                    result += "\n"
                
                logger.info(f"Redundancy check completed - {len(redundancies)} redundancies found")
            
            return result
            
        except Exception as e:
            error_msg = f"Redundancy detection failed: {str(e)}"
            logger.error(f"Redundancy detector error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _parse_slides(self, content: str) -> List[Dict[str, str]]:
        """Parse slides from content."""
        slides = []
        
        # Split by common slide delimiters
        # Look for patterns like "Slide 1:", "Slide 2:", "## Title", etc.
        slide_pattern = r'(?:^|\n)\s*(?:Slide\s+\d+:\s*([^\n]+)|##\s+([^\n]+)|###\s+([^\n]+))'
        matches = list(re.finditer(slide_pattern, content, re.MULTILINE | re.IGNORECASE))
        
        if not matches:
            # Fallback: split by double newlines
            sections = content.split('\n\n')
            for i, section in enumerate(sections):
                if section.strip():
                    lines = section.strip().split('\n')
                    title = lines[0] if lines else f"Slide {i+1}"
                    slide_content = '\n'.join(lines[1:]) if len(lines) > 1 else section
                    slides.append({
                        'title': title[:100],
                        'content': slide_content
                    })
        else:
            # Extract slides based on matches
            for i, match in enumerate(matches):
                # Get title from whichever group matched
                title = match.group(1) or match.group(2) or match.group(3) or f"Slide {i+1}"
                title = title.strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                slide_content = content[start:end].strip()
                
                slides.append({
                    'title': title,
                    'content': slide_content
                })
        
        return slides
    
    def _calculate_similarity(self, text1: str, text2: str) -> int:
        """
        Calculate similarity between two texts (0-100).
        
        Uses simple word overlap similarity.
        """
        if not text1 or not text2:
            return 0
        
        # Tokenize and normalize
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = int((intersection / union) * 100) if union > 0 else 0
        
        return similarity
    
    def _find_common_content(self, text1: str, text2: str) -> str:
        """Find common content between two texts."""
        # Find common phrases (3+ words)
        words1 = text1.lower().split()
        words2 = text2.lower().split()
        
        common_phrases = []
        
        # Look for common 3-word sequences
        for i in range(len(words1) - 2):
            phrase = ' '.join(words1[i:i+3])
            if phrase in text2.lower():
                common_phrases.append(phrase)
        
        if common_phrases:
            return common_phrases[0]
        
        # Fallback: return common words
        words1_set = set(words1)
        words2_set = set(words2)
        common_words = words1_set & words2_set
        
        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        common_words = common_words - stop_words
        
        return ' '.join(list(common_words)[:5]) if common_words else ""


class ToneValidatorTool(BaseTool):
    """
    Tone consistency validator for presentation content.
    
    Analyzes tone indicators (formal vs casual language, punctuation style)
    and checks consistency across all slides.
    
    Returns consistency score (0-100) and flagged sections with tone mismatches.
    
    Requirements: 5.3, 5.6, 8.1
    """
    
    name: str = "tone_validator"
    description: str = (
        "Validate tone consistency across presentation slides. "
        "Input should be presentation content with multiple slides. "
        "Returns consistency score (0-100) and flagged sections with tone mismatches."
    )
    
    def execute(self, content: str) -> str:
        """
        Validate tone consistency across slides.
        
        Args:
            content: Presentation content with multiple slides
            
        Returns:
            Consistency score and flagged tone mismatches
        """
        if not content or not isinstance(content, str):
            return "Error: Content must be a non-empty string"
        
        try:
            # Parse slides from content
            slides = self._parse_slides(content)
            
            if len(slides) < 2:
                return (
                    "Tone Validation: N/A\n"
                    "Need at least 2 slides to check tone consistency."
                )
            
            # Analyze tone for each slide
            slide_tones = []
            for i, slide in enumerate(slides):
                tone_analysis = self._analyze_tone(slide['content'])
                slide_tones.append({
                    'slide_num': i + 1,
                    'title': slide['title'],
                    'tone': tone_analysis
                })
            
            # Calculate overall tone and consistency
            overall_tone = self._determine_overall_tone(slide_tones)
            consistency_score, mismatches = self._calculate_consistency(slide_tones, overall_tone)
            
            # Format results
            result = f"Tone Consistency Score: {consistency_score}/100\n"
            result += "=" * 50 + "\n\n"
            result += f"Overall Tone: {overall_tone.upper()}\n\n"
            
            if consistency_score >= 85:
                result += "Assessment: EXCELLENT - Tone is highly consistent ✓✓✓\n\n"
            elif consistency_score >= 70:
                result += "Assessment: GOOD - Tone is mostly consistent ✓✓\n\n"
            elif consistency_score >= 55:
                result += "Assessment: FAIR - Some tone inconsistencies detected ✓\n\n"
            else:
                result += "Assessment: NEEDS IMPROVEMENT - Significant tone inconsistencies ✗\n\n"
            
            if mismatches:
                result += f"Tone Mismatches ({len(mismatches)}):\n"
                result += "-" * 50 + "\n"
                
                for mismatch in mismatches:
                    result += f"\nSlide {mismatch['slide_num']}: {mismatch['title']}\n"
                    result += f"  Expected: {overall_tone}\n"
                    result += f"  Detected: {mismatch['detected_tone']}\n"
                    result += f"  Issues: {', '.join(mismatch['issues'])}\n"
                    result += f"  Suggestion: {mismatch['suggestion']}\n"
            else:
                result += "No tone mismatches detected. All slides maintain consistent tone.\n"
            
            logger.info(f"Tone validation completed - consistency score: {consistency_score}/100")
            return result
            
        except Exception as e:
            error_msg = f"Tone validation failed: {str(e)}"
            logger.error(f"Tone validator error: {error_msg}")
            return f"Error: {error_msg}"
    
    def _parse_slides(self, content: str) -> List[Dict[str, str]]:
        """Parse slides from content."""
        slides = []
        
        # Split by common slide delimiters
        # Look for patterns like "Slide 1:", "Slide 2:", "## Title", etc.
        slide_pattern = r'(?:^|\n)\s*(?:Slide\s+\d+:\s*([^\n]+)|##\s+([^\n]+)|###\s+([^\n]+))'
        matches = list(re.finditer(slide_pattern, content, re.MULTILINE | re.IGNORECASE))
        
        if not matches:
            # Fallback: split by double newlines
            sections = content.split('\n\n')
            for i, section in enumerate(sections):
                if section.strip():
                    lines = section.strip().split('\n')
                    title = lines[0] if lines else f"Slide {i+1}"
                    slide_content = '\n'.join(lines[1:]) if len(lines) > 1 else section
                    slides.append({
                        'title': title[:100],
                        'content': slide_content
                    })
        else:
            # Extract slides based on matches
            for i, match in enumerate(matches):
                # Get title from whichever group matched
                title = match.group(1) or match.group(2) or match.group(3) or f"Slide {i+1}"
                title = title.strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                slide_content = content[start:end].strip()
                
                slides.append({
                    'title': title,
                    'content': slide_content
                })
        
        return slides
    
    def _analyze_tone(self, text: str) -> Dict[str, Any]:
        """
        Analyze tone of text.
        
        Returns dict with tone indicators:
        - formality_score: 0-100 (0=casual, 100=formal)
        - indicators: list of detected tone indicators
        """
        if not text:
            return {'formality_score': 50, 'indicators': []}
        
        text_lower = text.lower()
        formality_score = 50  # Start neutral
        indicators = []
        
        # Formal indicators (increase score)
        formal_patterns = [
            (r'\b(therefore|thus|hence|consequently|furthermore|moreover|nevertheless)\b', 'formal conjunctions', 10),
            (r'\b(utilize|implement|facilitate|demonstrate|establish)\b', 'formal verbs', 8),
            (r'\b(regarding|concerning|pertaining to)\b', 'formal prepositions', 8),
            (r'\b(shall|ought to|must)\b', 'formal modals', 6),
            (r'\b(in conclusion|to summarize|in summary)\b', 'formal transitions', 6),
        ]
        
        for pattern, indicator, score_change in formal_patterns:
            if re.search(pattern, text_lower):
                formality_score += score_change
                indicators.append(f'formal: {indicator}')
        
        # Casual indicators (decrease score)
        casual_patterns = [
            (r'\b(gonna|wanna|gotta|kinda|sorta)\b', 'casual contractions', -15),
            (r'\b(cool|awesome|great|nice|super)\b', 'casual adjectives', -8),
            (r'\b(yeah|yep|nope|ok|okay)\b', 'casual affirmations', -10),
            (r'[!]{2,}', 'excessive exclamation', -8),
            (r'\b(hey|hi|hello there)\b', 'casual greetings', -6),
            (r'\b(stuff|things|lots of|a lot of)\b', 'vague casual terms', -6),
        ]
        
        for pattern, indicator, score_change in casual_patterns:
            if re.search(pattern, text_lower):
                formality_score += score_change
                indicators.append(f'casual: {indicator}')
        
        # Punctuation style
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        if exclamation_count > 2:
            formality_score -= 5
            indicators.append('casual: frequent exclamations')
        
        if question_count > 2:
            formality_score -= 3
            indicators.append('casual: frequent questions')
        
        # Contractions
        contractions = len(re.findall(r"\b\w+'\w+\b", text))
        if contractions > 3:
            formality_score -= 5
            indicators.append('casual: frequent contractions')
        elif contractions == 0 and len(text.split()) > 20:
            formality_score += 5
            indicators.append('formal: no contractions')
        
        # Clamp score to 0-100
        formality_score = max(0, min(100, formality_score))
        
        return {
            'formality_score': formality_score,
            'indicators': indicators
        }
    
    def _determine_overall_tone(self, slide_tones: List[Dict[str, Any]]) -> str:
        """Determine overall tone from all slides."""
        avg_formality = sum(
            slide['tone']['formality_score']
            for slide in slide_tones
        ) / len(slide_tones)
        
        if avg_formality >= 65:
            return "formal"
        elif avg_formality >= 45:
            return "professional"
        else:
            return "casual"
    
    def _calculate_consistency(
        self,
        slide_tones: List[Dict[str, Any]],
        overall_tone: str
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Calculate consistency score and identify mismatches.
        
        Returns:
            Tuple of (consistency_score, mismatches)
        """
        # Define tone ranges
        tone_ranges = {
            'formal': (65, 100),
            'professional': (45, 64),
            'casual': (0, 44)
        }
        
        expected_min, expected_max = tone_ranges[overall_tone]
        
        mismatches = []
        deviation_sum = 0
        
        for slide in slide_tones:
            formality = slide['tone']['formality_score']
            
            # Check if within expected range
            if formality < expected_min or formality > expected_max:
                # Determine detected tone
                if formality >= 65:
                    detected_tone = "formal"
                elif formality >= 45:
                    detected_tone = "professional"
                else:
                    detected_tone = "casual"
                
                # Calculate deviation
                if formality < expected_min:
                    deviation = expected_min - formality
                else:
                    deviation = formality - expected_max
                
                deviation_sum += deviation
                
                # Identify specific issues
                issues = []
                if detected_tone == "formal" and overall_tone != "formal":
                    issues.append("too formal")
                elif detected_tone == "casual" and overall_tone != "casual":
                    issues.append("too casual")
                
                # Add indicator-based issues
                for indicator in slide['tone']['indicators']:
                    if 'formal' in indicator and overall_tone == 'casual':
                        issues.append(indicator.replace('formal: ', ''))
                    elif 'casual' in indicator and overall_tone == 'formal':
                        issues.append(indicator.replace('casual: ', ''))
                
                # Generate suggestion
                if overall_tone == "formal":
                    suggestion = "Use more formal language, avoid contractions and casual expressions"
                elif overall_tone == "casual":
                    suggestion = "Use more casual, conversational language"
                else:
                    suggestion = "Maintain professional tone - balance formal and accessible language"
                
                mismatches.append({
                    'slide_num': slide['slide_num'],
                    'title': slide['title'],
                    'detected_tone': detected_tone,
                    'issues': issues if issues else ['tone mismatch'],
                    'suggestion': suggestion
                })
        
        # Calculate consistency score
        # Start at 100, deduct based on deviations
        consistency_score = 100 - min(100, int(deviation_sum / len(slide_tones) * 2))
        
        return consistency_score, mismatches
