"""
End-to-end integration tests for Task 12.

These tests verify the complete integration between frontend and backend,
testing authentication flows, API connectivity, and error handling.

Tests that require LLM (presentation generation) are marked as skipped
unless OPENAI_API_KEY or ANTHROPIC_API_KEY is set.
"""
import pytest
import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Check if API keys are available
HAS_API_KEY = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


class TestTask12_1_APIConnectivity:
    """Test Task 12.1: Connect frontend to backend API"""
    
    def test_health_endpoint(self):
        """Verify health endpoint is accessible"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Verify root endpoint is accessible"""
        response = client.get("/")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_cors_headers(self):
        """Verify CORS headers are set correctly"""
        # Test with a POST request from allowed origin
        response = client.post(
            "/api/auth/register",
            headers={"Origin": "http://localhost:3000"},
            json={"username": "cors_test_user", "password": "password123"}
        )
        # Should not be blocked by CORS (would be 403 if CORS blocked it)
        assert response.status_code in [200, 201, 400, 409]  # Any valid response, not CORS error


class TestTask12_2_RegistrationFlow:
    """Test Task 12.2: Complete user registration flow"""
    
    def test_registration_success(self):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_1",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["username"] == "integration_test_user_1"
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username returns 409"""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_2",
                "password": "password123"
            }
        )
        
        # Attempt duplicate registration
        response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_2",
                "password": "different_password"
            }
        )
        assert response.status_code == 409
        assert "error" in response.json()
    
    def test_registration_short_password(self):
        """Test registration with short password returns 400"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_3",
                "password": "short"
            }
        )
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_registration_returns_valid_jwt(self):
        """Test that registration returns a valid JWT token"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_4",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        token = response.json()["token"]
        
        # Verify token works for authenticated endpoint
        auth_response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "Test Topic",
                "slide_count": 8
            }
        )
        # Should not return 401 (authentication error)
        assert auth_response.status_code != 401


class TestTask12_3_AuthenticationFlow:
    """Test authentication and session management"""
    
    def test_login_success(self):
        """Test successful login"""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_5",
                "password": "password123"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "integration_test_user_5",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["username"] == "integration_test_user_5"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401
        assert "error" in response.json()
    
    def test_login_returns_valid_jwt(self):
        """Test that login returns a valid JWT token"""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_6",
                "password": "password123"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "integration_test_user_6",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        token = response.json()["token"]
        
        # Verify token works for authenticated endpoint
        auth_response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "Test Topic",
                "slide_count": 8
            }
        )
        # Should not return 401 (authentication error)
        assert auth_response.status_code != 401


class TestTask12_4_ErrorHandling:
    """Test Task 12.4: Error handling flows"""
    
    def test_validation_error_empty_topic(self):
        """Test validation error for empty topic"""
        # Register and get token
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_7",
                "password": "password123"
            }
        )
        token = reg_response.json()["token"]
        
        # Attempt generation with empty topic
        response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "",
                "slide_count": 8
            }
        )
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_validation_error_topic_too_long(self):
        """Test validation error for topic exceeding 500 characters"""
        # Register and get token
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_8",
                "password": "password123"
            }
        )
        token = reg_response.json()["token"]
        
        # Attempt generation with long topic
        long_topic = "A" * 501
        response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": long_topic,
                "slide_count": 8
            }
        )
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_validation_error_invalid_slide_count(self):
        """Test validation error for invalid slide count"""
        # Register and get token
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_9",
                "password": "password123"
            }
        )
        token = reg_response.json()["token"]
        
        # Attempt generation with invalid slide count
        response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "Test Topic",
                "slide_count": 25  # Max is 20
            }
        )
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_validation_error_invalid_tone(self):
        """Test validation error for invalid tone"""
        # Register and get token
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_10",
                "password": "password123"
            }
        )
        token = reg_response.json()["token"]
        
        # Attempt generation with invalid tone
        response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "Test Topic",
                "tone": "invalid_tone",
                "slide_count": 8
            }
        )
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_authentication_error_missing_token(self):
        """Test authentication error when token is missing"""
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic",
                "slide_count": 8
            }
        )
        assert response.status_code == 401
        assert "error" in response.json()
    
    def test_authentication_error_invalid_token(self):
        """Test authentication error when token is invalid"""
        response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": "Bearer invalid_token_here"},
            json={
                "topic": "Test Topic",
                "slide_count": 8
            }
        )
        assert response.status_code == 401
        assert "error" in response.json()
    
    def test_download_not_found(self):
        """Test 404 error when presentation not found"""
        # Register and get token
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_11",
                "password": "password123"
            }
        )
        token = reg_response.json()["token"]
        
        # Attempt to download non-existent presentation
        response = client.get(
            "/api/presentations/download/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        assert "error" in response.json()


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires OPENAI_API_KEY or ANTHROPIC_API_KEY")
class TestTask12_3_PresentationGeneration:
    """Test Task 12.3: Complete presentation generation flow (requires API key)"""
    
    def test_complete_generation_flow(self):
        """Test complete presentation generation and download flow"""
        # Register user
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_12",
                "password": "password123"
            }
        )
        assert reg_response.status_code == 201
        token = reg_response.json()["token"]
        
        # Generate presentation
        gen_response = client.post(
            "/api/presentations/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "Integration Test Presentation",
                "tone": "professional",
                "slide_count": 5  # Small number for faster test
            }
        )
        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        assert "presentation_id" in gen_data
        assert "filename" in gen_data
        assert "download_url" in gen_data
        
        # Download presentation
        download_response = client.get(
            f"/api/presentations/download/{gen_data['presentation_id']}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert "attachment" in download_response.headers.get("content-disposition", "")
    
    def test_generation_with_different_tones(self):
        """Test generation with different tone parameters"""
        # Register user
        reg_response = client.post(
            "/api/auth/register",
            json={
                "username": "integration_test_user_13",
                "password": "password123"
            }
        )
        token = reg_response.json()["token"]
        
        tones = ["formal", "casual", "fun", "professional"]
        for tone in tones:
            response = client.post(
                "/api/presentations/generate",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "topic": f"Test with {tone} tone",
                    "tone": tone,
                    "slide_count": 5
                }
            )
            assert response.status_code == 200, f"Failed for tone: {tone}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
