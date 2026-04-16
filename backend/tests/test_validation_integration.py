"""Integration tests for request validation in API context."""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Optional

from api.validation import validate_presentation_request, sanitize_input
from api.error_handlers import register_error_handlers


# Create a test FastAPI app
app = FastAPI()
register_error_handlers(app)


class PresentationRequest(BaseModel):
    topic: str
    tone: Optional[str] = None
    slide_count: Optional[int] = None


@app.post("/test/validate")
async def validate_endpoint(request: PresentationRequest):
    """Endpoint that validates presentation requests."""
    # Validate request
    validate_presentation_request(
        request.topic,
        request.tone,
        request.slide_count
    )
    
    # Sanitize topic
    safe_topic = sanitize_input(request.topic)
    
    return {
        "status": "valid",
        "sanitized_topic": safe_topic
    }


client = TestClient(app)


class TestValidationIntegration:
    """Integration tests for validation in API context."""
    
    def test_valid_request_all_parameters(self):
        """Test that valid request with all parameters succeeds."""
        response = client.post("/test/validate", json={
            "topic": "AI in Healthcare",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "valid"
        assert response.json()["sanitized_topic"] == "AI in Healthcare"
    
    def test_valid_request_required_only(self):
        """Test that valid request with only topic succeeds."""
        response = client.post("/test/validate", json={
            "topic": "Machine Learning Basics"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "valid"
    
    def test_invalid_topic_empty(self):
        """Test that empty topic returns 400 error."""
        response = client.post("/test/validate", json={
            "topic": "",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Topic must be between" in response.json()["message"]
    
    def test_invalid_topic_too_long(self):
        """Test that topic exceeding 500 characters returns 400 error."""
        response = client.post("/test/validate", json={
            "topic": "x" * 501,
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Topic must be between" in response.json()["message"]
    
    def test_invalid_tone(self):
        """Test that invalid tone returns 400 error."""
        response = client.post("/test/validate", json={
            "topic": "AI in Healthcare",
            "tone": "invalid_tone",
            "slide_count": 10
        })
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Tone must be one of" in response.json()["message"]
    
    def test_invalid_slide_count_too_low(self):
        """Test that slide count below 5 returns 400 error."""
        response = client.post("/test/validate", json={
            "topic": "AI in Healthcare",
            "tone": "formal",
            "slide_count": 3
        })
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Slide count must be between" in response.json()["message"]
    
    def test_invalid_slide_count_too_high(self):
        """Test that slide count above 20 returns 400 error."""
        response = client.post("/test/validate", json={
            "topic": "AI in Healthcare",
            "tone": "formal",
            "slide_count": 25
        })
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Slide count must be between" in response.json()["message"]
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported."""
        response = client.post("/test/validate", json={
            "topic": "",
            "tone": "invalid",
            "slide_count": 100
        })
        
        assert response.status_code == 400
        error_message = response.json()["message"]
        assert "Topic must be between" in error_message
        assert "Tone must be one of" in error_message
        assert "Slide count must be between" in error_message
    
    def test_xss_sanitization(self):
        """Test that XSS attempts are sanitized."""
        response = client.post("/test/validate", json={
            "topic": "<script>alert('xss')</script>AI in Healthcare",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
        sanitized = response.json()["sanitized_topic"]
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
    
    def test_path_traversal_sanitization(self):
        """Test that path traversal attempts are sanitized."""
        response = client.post("/test/validate", json={
            "topic": "../../../etc/passwd",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
        sanitized = response.json()["sanitized_topic"]
        assert "../" not in sanitized
    
    def test_boundary_topic_length_min(self):
        """Test topic with exactly 1 character."""
        response = client.post("/test/validate", json={
            "topic": "A",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
    
    def test_boundary_topic_length_max(self):
        """Test topic with exactly 500 characters."""
        response = client.post("/test/validate", json={
            "topic": "x" * 500,
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
    
    def test_boundary_slide_count_min(self):
        """Test slide count at minimum (5)."""
        response = client.post("/test/validate", json={
            "topic": "AI in Healthcare",
            "tone": "formal",
            "slide_count": 5
        })
        
        assert response.status_code == 200
    
    def test_boundary_slide_count_max(self):
        """Test slide count at maximum (20)."""
        response = client.post("/test/validate", json={
            "topic": "AI in Healthcare",
            "tone": "formal",
            "slide_count": 20
        })
        
        assert response.status_code == 200
    
    def test_all_valid_tones(self):
        """Test that all valid tones are accepted."""
        valid_tones = ['formal', 'casual', 'fun', 'professional']
        
        for tone in valid_tones:
            response = client.post("/test/validate", json={
                "topic": "AI in Healthcare",
                "tone": tone,
                "slide_count": 10
            })
            
            assert response.status_code == 200, f"Tone '{tone}' should be valid"
    
    def test_unicode_topic(self):
        """Test that unicode characters in topic are handled correctly."""
        response = client.post("/test/validate", json={
            "topic": "人工智能在医疗保健中的应用",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
    
    def test_special_characters_in_topic(self):
        """Test that special characters in topic are handled correctly."""
        response = client.post("/test/validate", json={
            "topic": "AI & ML: The Future (2024)!",
            "tone": "formal",
            "slide_count": 10
        })
        
        assert response.status_code == 200
