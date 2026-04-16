"""Unit tests for request validation functions."""
import pytest

from api.validation import (
    sanitize_input,
    validate_topic,
    validate_tone,
    validate_slide_count,
    validate_presentation_request,
    VALID_TONES,
    TOPIC_MIN_LENGTH,
    TOPIC_MAX_LENGTH,
    SLIDE_COUNT_MIN,
    SLIDE_COUNT_MAX
)
from api.exceptions import ValidationError


class TestSanitizeInput:
    """Tests for sanitize_input function."""
    
    def test_sanitize_xss_script_tag(self):
        """Test that script tags are HTML escaped."""
        malicious = "<script>alert('xss')</script>"
        sanitized = sanitize_input(malicious)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
    
    def test_sanitize_javascript_protocol(self):
        """Test that javascript: protocol is logged but preserved (escaped)."""
        malicious = "javascript:alert('xss')"
        sanitized = sanitize_input(malicious)
        # HTML escape doesn't affect this, but it's logged
        assert "javascript:" in sanitized
    
    def test_sanitize_path_traversal(self):
        """Test that path traversal sequences are removed."""
        malicious = "../../../etc/passwd"
        sanitized = sanitize_input(malicious)
        assert "../" not in sanitized
        assert "etc/passwd" in sanitized
    
    def test_sanitize_windows_path_traversal(self):
        """Test that Windows path traversal sequences are removed."""
        malicious = "..\\..\\..\\windows\\system32"
        sanitized = sanitize_input(malicious)
        assert "..\\" not in sanitized
        assert "windows\\system32" in sanitized
    
    def test_sanitize_sql_injection(self):
        """Test that SQL injection patterns are logged and escaped."""
        malicious = "'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious)
        # SQL patterns are logged and HTML escaped
        assert "DROP TABLE users" in sanitized
        # Single quotes are HTML escaped
        assert "&#x27;" in sanitized or "&apos;" in sanitized or "'" not in sanitized or sanitized == "&#x27;; DROP TABLE users; --"
    
    def test_sanitize_clean_input(self):
        """Test that clean input is preserved."""
        clean = "AI in Healthcare: A Modern Approach"
        sanitized = sanitize_input(clean)
        assert sanitized == clean
    
    def test_sanitize_non_string_input(self):
        """Test that non-string input is converted to string."""
        number = 12345
        sanitized = sanitize_input(number)
        assert sanitized == "12345"


class TestValidateTopic:
    """Tests for validate_topic function."""
    
    def test_valid_topic(self):
        """Test that valid topic passes validation."""
        errors = validate_topic("AI in Healthcare")
        assert errors == []
    
    def test_topic_at_min_length(self):
        """Test topic with exactly 1 character."""
        errors = validate_topic("A")
        assert errors == []
    
    def test_topic_at_max_length(self):
        """Test topic with exactly 500 characters."""
        topic = "x" * 500
        errors = validate_topic(topic)
        assert errors == []
    
    def test_empty_topic(self):
        """Test that empty topic fails validation."""
        errors = validate_topic("")
        assert len(errors) == 1
        assert "must be between" in errors[0]
    
    def test_topic_too_long(self):
        """Test that topic exceeding 500 characters fails."""
        topic = "x" * 501
        errors = validate_topic(topic)
        assert len(errors) == 1
        assert "must be between" in errors[0]
    
    def test_none_topic(self):
        """Test that None topic fails validation."""
        errors = validate_topic(None)
        assert len(errors) == 1
        assert "required" in errors[0].lower()
    
    def test_non_string_topic(self):
        """Test that non-string topic fails validation."""
        errors = validate_topic(12345)
        assert len(errors) == 1
        assert "must be a string" in errors[0]


class TestValidateTone:
    """Tests for validate_tone function."""
    
    def test_valid_tone_formal(self):
        """Test that 'formal' tone is valid."""
        errors = validate_tone("formal")
        assert errors == []
    
    def test_valid_tone_casual(self):
        """Test that 'casual' tone is valid."""
        errors = validate_tone("casual")
        assert errors == []
    
    def test_valid_tone_fun(self):
        """Test that 'fun' tone is valid."""
        errors = validate_tone("fun")
        assert errors == []
    
    def test_valid_tone_professional(self):
        """Test that 'professional' tone is valid."""
        errors = validate_tone("professional")
        assert errors == []
    
    def test_none_tone_is_valid(self):
        """Test that None tone is valid (optional parameter)."""
        errors = validate_tone(None)
        assert errors == []
    
    def test_invalid_tone(self):
        """Test that invalid tone fails validation."""
        errors = validate_tone("invalid")
        assert len(errors) == 1
        assert "must be one of" in errors[0]
        assert all(tone in errors[0] for tone in VALID_TONES)
    
    def test_case_sensitive_tone(self):
        """Test that tone validation is case-sensitive."""
        errors = validate_tone("FORMAL")
        assert len(errors) == 1
        assert "must be one of" in errors[0]
    
    def test_non_string_tone(self):
        """Test that non-string tone fails validation."""
        errors = validate_tone(123)
        assert len(errors) == 1
        assert "must be a string" in errors[0]


class TestValidateSlideCount:
    """Tests for validate_slide_count function."""
    
    def test_valid_slide_count(self):
        """Test that valid slide count passes validation."""
        errors = validate_slide_count(10)
        assert errors == []
    
    def test_slide_count_at_min(self):
        """Test slide count at minimum (5)."""
        errors = validate_slide_count(5)
        assert errors == []
    
    def test_slide_count_at_max(self):
        """Test slide count at maximum (20)."""
        errors = validate_slide_count(20)
        assert errors == []
    
    def test_none_slide_count_is_valid(self):
        """Test that None slide count is valid (optional parameter)."""
        errors = validate_slide_count(None)
        assert errors == []
    
    def test_slide_count_too_low(self):
        """Test that slide count below 5 fails validation."""
        errors = validate_slide_count(4)
        assert len(errors) == 1
        assert "must be between" in errors[0]
        assert "5" in errors[0]
        assert "20" in errors[0]
    
    def test_slide_count_too_high(self):
        """Test that slide count above 20 fails validation."""
        errors = validate_slide_count(21)
        assert len(errors) == 1
        assert "must be between" in errors[0]
    
    def test_slide_count_zero(self):
        """Test that zero slide count fails validation."""
        errors = validate_slide_count(0)
        assert len(errors) == 1
        assert "must be between" in errors[0]
    
    def test_slide_count_negative(self):
        """Test that negative slide count fails validation."""
        errors = validate_slide_count(-5)
        assert len(errors) == 1
        assert "must be between" in errors[0]
    
    def test_non_integer_slide_count(self):
        """Test that non-integer slide count fails validation."""
        errors = validate_slide_count("10")
        assert len(errors) == 1
        assert "must be an integer" in errors[0]


class TestValidatePresentationRequest:
    """Tests for validate_presentation_request function."""
    
    def test_valid_request_all_parameters(self):
        """Test that valid request with all parameters passes."""
        # Should not raise
        validate_presentation_request("AI in Healthcare", "formal", 10)
    
    def test_valid_request_required_only(self):
        """Test that valid request with only required parameters passes."""
        # Should not raise
        validate_presentation_request("AI in Healthcare")
    
    def test_valid_request_with_tone(self):
        """Test that valid request with topic and tone passes."""
        # Should not raise
        validate_presentation_request("AI in Healthcare", tone="casual")
    
    def test_valid_request_with_slide_count(self):
        """Test that valid request with topic and slide count passes."""
        # Should not raise
        validate_presentation_request("AI in Healthcare", slide_count=15)
    
    def test_invalid_topic_raises_error(self):
        """Test that invalid topic raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_presentation_request("", "formal", 10)
        
        assert "Topic must be between" in str(exc_info.value)
    
    def test_invalid_tone_raises_error(self):
        """Test that invalid tone raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_presentation_request("AI in Healthcare", "invalid", 10)
        
        assert "Tone must be one of" in str(exc_info.value)
    
    def test_invalid_slide_count_raises_error(self):
        """Test that invalid slide count raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_presentation_request("AI in Healthcare", "formal", 100)
        
        assert "Slide count must be between" in str(exc_info.value)
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are combined."""
        with pytest.raises(ValidationError) as exc_info:
            validate_presentation_request("", "invalid", 100)
        
        error_message = str(exc_info.value)
        assert "Topic must be between" in error_message
        assert "Tone must be one of" in error_message
        assert "Slide count must be between" in error_message
    
    def test_validation_error_has_correct_status_code(self):
        """Test that ValidationError has 400 status code."""
        with pytest.raises(ValidationError) as exc_info:
            validate_presentation_request("", "formal", 10)
        
        assert exc_info.value.status_code == 400
    
    def test_validation_error_has_correct_code(self):
        """Test that ValidationError has correct error code."""
        with pytest.raises(ValidationError) as exc_info:
            validate_presentation_request("", "formal", 10)
        
        assert exc_info.value.code == "VALIDATION_ERROR"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_topic_with_special_characters(self):
        """Test that topic with special characters is valid."""
        topic = "AI & ML: The Future of Tech (2024)!"
        errors = validate_topic(topic)
        assert errors == []
    
    def test_topic_with_unicode(self):
        """Test that topic with unicode characters is valid."""
        topic = "人工智能在医疗保健中的应用"
        errors = validate_topic(topic)
        assert errors == []
    
    def test_topic_with_newlines(self):
        """Test that topic with newlines is valid."""
        topic = "AI in Healthcare\nA Modern Approach"
        errors = validate_topic(topic)
        assert errors == []
    
    def test_sanitize_combined_attacks(self):
        """Test sanitization with combined attack vectors."""
        malicious = "<script>alert('xss')</script>'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
