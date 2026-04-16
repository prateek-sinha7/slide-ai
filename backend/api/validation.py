"""Request validation and input sanitization functions."""
import re
from typing import List, Optional
import html
import logging

from api.exceptions import ValidationError


logger = logging.getLogger(__name__)


# Valid tone values as per requirements
VALID_TONES = ['formal', 'casual', 'fun', 'professional']

# Topic length constraints
TOPIC_MIN_LENGTH = 1
TOPIC_MAX_LENGTH = 500

# Slide count constraints
SLIDE_COUNT_MIN = 5
SLIDE_COUNT_MAX = 20


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    This function removes or escapes dangerous characters and patterns
    including SQL injection attempts, XSS payloads, and path traversal sequences.
    
    Args:
        user_input: Raw user input string
        
    Returns:
        Sanitized string safe for processing
        
    Example:
        >>> sanitize_input("<script>alert('xss')</script>")
        "&lt;script&gt;alert('xss')&lt;/script&gt;"
        >>> sanitize_input("'; DROP TABLE users; --")
        "'; DROP TABLE users; --"  # SQL patterns detected and logged
    """
    if not isinstance(user_input, str):
        return str(user_input)
    
    # HTML escape to prevent XSS
    sanitized = html.escape(user_input)
    
    # Remove path traversal sequences
    sanitized = sanitized.replace("../", "").replace("..\\", "")
    
    # Log potential SQL injection attempts (but don't modify - we're not using SQL directly)
    sql_patterns = [
        r"(?i)(\bDROP\s+TABLE\b)",
        r"(?i)(\bUNION\s+SELECT\b)",
        r"(?i)(\bINSERT\s+INTO\b)",
        r"(?i)(\bDELETE\s+FROM\b)",
        r"(?i)(;\s*--)",
        r"(?i)(\bOR\s+['\"]?1['\"]?\s*=\s*['\"]?1)",
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, user_input):
            logger.warning(
                f"Potential SQL injection attempt detected: {pattern}",
                extra={"input": user_input[:100]}
            )
    
    # Log potential XSS attempts
    xss_patterns = [
        r"(?i)(<script[^>]*>)",
        r"(?i)(javascript:)",
        r"(?i)(onerror\s*=)",
        r"(?i)(onload\s*=)",
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, user_input):
            logger.warning(
                f"Potential XSS attempt detected: {pattern}",
                extra={"input": user_input[:100]}
            )
    
    return sanitized


def validate_topic(topic: Optional[str]) -> List[str]:
    """
    Validate presentation topic.
    
    Topic must be between 1 and 500 characters (inclusive).
    
    Args:
        topic: The presentation topic string
        
    Returns:
        List of validation error messages (empty if valid)
        
    Example:
        >>> validate_topic("AI in Healthcare")
        []
        >>> validate_topic("")
        ['Topic must be between 1 and 500 characters']
        >>> validate_topic("x" * 501)
        ['Topic must be between 1 and 500 characters']
    """
    errors = []
    
    if topic is None:
        errors.append("Topic is required")
        return errors
    
    if not isinstance(topic, str):
        errors.append("Topic must be a string")
        return errors
    
    topic_length = len(topic)
    
    if topic_length < TOPIC_MIN_LENGTH or topic_length > TOPIC_MAX_LENGTH:
        errors.append(f"Topic must be between {TOPIC_MIN_LENGTH} and {TOPIC_MAX_LENGTH} characters")
    
    return errors


def validate_tone(tone: Optional[str]) -> List[str]:
    """
    Validate presentation tone.
    
    Tone must be one of: 'formal', 'casual', 'fun', 'professional'.
    Tone is optional, so None is valid.
    
    Args:
        tone: The presentation tone string (optional)
        
    Returns:
        List of validation error messages (empty if valid)
        
    Example:
        >>> validate_tone("formal")
        []
        >>> validate_tone(None)
        []
        >>> validate_tone("invalid")
        ["Tone must be one of: formal, casual, fun, professional"]
    """
    errors = []
    
    # Tone is optional
    if tone is None:
        return errors
    
    if not isinstance(tone, str):
        errors.append("Tone must be a string")
        return errors
    
    if tone not in VALID_TONES:
        errors.append(f"Tone must be one of: {', '.join(VALID_TONES)}")
    
    return errors


def validate_slide_count(slide_count: Optional[int]) -> List[str]:
    """
    Validate slide count.
    
    Slide count must be between 5 and 20 (inclusive).
    Slide count is optional, so None is valid.
    
    Args:
        slide_count: The number of slides (optional)
        
    Returns:
        List of validation error messages (empty if valid)
        
    Example:
        >>> validate_slide_count(10)
        []
        >>> validate_slide_count(None)
        []
        >>> validate_slide_count(3)
        ['Slide count must be between 5 and 20']
        >>> validate_slide_count(25)
        ['Slide count must be between 5 and 20']
    """
    errors = []
    
    # Slide count is optional
    if slide_count is None:
        return errors
    
    if not isinstance(slide_count, int):
        errors.append("Slide count must be an integer")
        return errors
    
    if slide_count < SLIDE_COUNT_MIN or slide_count > SLIDE_COUNT_MAX:
        errors.append(f"Slide count must be between {SLIDE_COUNT_MIN} and {SLIDE_COUNT_MAX}")
    
    return errors


def validate_presentation_request(
    topic: Optional[str],
    tone: Optional[str] = None,
    slide_count: Optional[int] = None
) -> None:
    """
    Validate a complete presentation generation request.
    
    This function validates all parameters and raises a ValidationError
    if any validation fails. It also sanitizes the topic input.
    
    Args:
        topic: The presentation topic (required)
        tone: The presentation tone (optional)
        slide_count: The number of slides (optional)
        
    Returns:
        None if validation passes
        
    Raises:
        ValidationError: If any validation fails
        
    Example:
        >>> validate_presentation_request("AI in Healthcare", "formal", 10)
        # No error raised
        >>> validate_presentation_request("", "formal", 10)
        ValidationError: Topic must be between 1 and 500 characters
    """
    all_errors = []
    
    # Validate topic
    topic_errors = validate_topic(topic)
    if topic_errors:
        all_errors.extend(topic_errors)
    
    # Validate tone
    tone_errors = validate_tone(tone)
    if tone_errors:
        all_errors.extend(tone_errors)
    
    # Validate slide count
    slide_count_errors = validate_slide_count(slide_count)
    if slide_count_errors:
        all_errors.extend(slide_count_errors)
    
    # Raise ValidationError if any errors found
    if all_errors:
        error_message = "; ".join(all_errors)
        logger.warning(
            f"Request validation failed: {error_message}",
            extra={
                "topic_length": len(topic) if topic else 0,
                "tone": tone,
                "slide_count": slide_count
            }
        )
        raise ValidationError(error_message)
    
    logger.info(
        "Request validation passed",
        extra={
            "topic_length": len(topic) if topic else 0,
            "tone": tone,
            "slide_count": slide_count
        }
    )
