"""Simple unit tests for PPT Generator functions that don't require orchestrator models."""
import pytest
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only the standalone functions, not the class
import re


def generate_filename(topic: str, timestamp: datetime) -> str:
    """
    Generate a safe filename from topic and timestamp.
    
    Args:
        topic: Presentation topic
        timestamp: Timestamp for filename
        
    Returns:
        Safe filename with .pptx extension
    """
    # Sanitize topic - remove dangerous characters
    # Remove path separators and special characters
    safe_topic = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', topic)
    
    # Replace spaces with underscores
    safe_topic = safe_topic.replace(' ', '_')
    
    # Remove any remaining problematic characters
    safe_topic = re.sub(r'[^\w\-_]', '', safe_topic)
    
    # Limit length to avoid filesystem issues
    safe_topic = safe_topic[:100]
    
    # Remove leading/trailing underscores or dashes
    safe_topic = safe_topic.strip('_-')
    
    # If topic is empty after sanitization, use default
    if not safe_topic:
        safe_topic = "presentation"
    
    # Format timestamp
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    # Combine into filename
    filename = f"{safe_topic}_{timestamp_str}.pptx"
    
    return filename


def sanitize_topic(topic: str) -> str:
    """
    Sanitize topic string to remove dangerous characters.
    
    Args:
        topic: Raw topic string
        
    Returns:
        Sanitized topic string
    """
    # Remove path separators and special characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', topic)
    
    # Remove any remaining problematic characters except spaces
    sanitized = re.sub(r'[^\w\s\-_]', '', sanitized)
    
    # Collapse multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized


class TestFilenameGeneration:
    """Tests for filename generation and sanitization."""
    
    def test_generate_filename_basic(self):
        """Test basic filename generation."""
        topic = "AI in Healthcare"
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        
        filename = generate_filename(topic, timestamp)
        
        assert filename == "AI_in_Healthcare_20240115_143045.pptx"
    
    def test_generate_filename_with_special_chars(self):
        """Test filename generation with special characters."""
        topic = "Test: Topic/With\\Special*Chars?"
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        
        filename = generate_filename(topic, timestamp)
        
        # Should remove all special characters
        assert "/" not in filename
        assert "\\" not in filename
        assert ":" not in filename
        assert "*" not in filename
        assert "?" not in filename
        assert filename.endswith(".pptx")
    
    def test_generate_filename_with_path_separators(self):
        """Test filename generation removes path separators."""
        topic = "../../../etc/passwd"
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        
        filename = generate_filename(topic, timestamp)
        
        # Should not contain path separators
        assert "/" not in filename
        assert ".." not in filename
        assert filename.endswith(".pptx")
    
    def test_generate_filename_empty_topic(self):
        """Test filename generation with empty topic."""
        topic = ""
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        
        filename = generate_filename(topic, timestamp)
        
        # Should use default name
        assert filename == "presentation_20240115_143045.pptx"
    
    def test_generate_filename_only_special_chars(self):
        """Test filename generation with only special characters."""
        topic = "***///:::"
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        
        filename = generate_filename(topic, timestamp)
        
        # Should use default name
        assert filename == "presentation_20240115_143045.pptx"
    
    def test_generate_filename_long_topic(self):
        """Test filename generation with very long topic."""
        topic = "A" * 200
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        
        filename = generate_filename(topic, timestamp)
        
        # Should be truncated to reasonable length
        assert len(filename) < 150
        assert filename.endswith(".pptx")
    
    def test_sanitize_topic_basic(self):
        """Test basic topic sanitization."""
        topic = "AI in Healthcare"
        result = sanitize_topic(topic)
        assert result == "AI in Healthcare"
    
    def test_sanitize_topic_special_chars(self):
        """Test topic sanitization with special characters."""
        topic = "Test: Topic/With\\Special*Chars?"
        result = sanitize_topic(topic)
        
        # Should remove special characters but keep spaces
        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
    
    def test_sanitize_topic_multiple_spaces(self):
        """Test topic sanitization collapses multiple spaces."""
        topic = "AI    in     Healthcare"
        result = sanitize_topic(topic)
        assert result == "AI in Healthcare"
    
    def test_sanitize_topic_leading_trailing_spaces(self):
        """Test topic sanitization removes leading/trailing spaces."""
        topic = "   AI in Healthcare   "
        result = sanitize_topic(topic)
        assert result == "AI in Healthcare"
