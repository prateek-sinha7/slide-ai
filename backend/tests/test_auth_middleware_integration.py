"""Integration tests for authentication middleware with FastAPI."""
import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer

from api.middleware import get_current_user
from api.error_handlers import register_error_handlers
from auth.jwt import generate_jwt


# Create test app
app = FastAPI()
register_error_handlers(app)
security = HTTPBearer()


@app.get("/public")
async def public_route():
    """Public route that doesn't require authentication."""
    return {"message": "This is public"}


async def get_user_dependency(
    request: Request,
    credentials: HTTPBearer = Depends(security)
):
    """Dependency function for getting current user."""
    return await get_current_user(request, credentials)


@app.get("/protected")
async def protected_route(
    user: dict = Depends(get_user_dependency)
):
    """Protected route that requires authentication."""
    return {
        "message": "This is protected",
        "user_id": user["user_id"],
        "username": user["username"]
    }


@app.get("/admin")
async def admin_route(
    user: dict = Depends(get_user_dependency)
):
    """Another protected route."""
    return {
        "message": "Admin area",
        "user": user
    }


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Generate a valid JWT token."""
    return generate_jwt("test-user-123", "testuser")


@pytest.fixture
def auth_headers(valid_token):
    """Create authorization headers with valid token."""
    return {"Authorization": f"Bearer {valid_token}"}


class TestPublicRoutes:
    """Tests for public routes that don't require authentication."""
    
    def test_public_route_accessible_without_token(self, client):
        """Test that public routes are accessible without authentication."""
        response = client.get("/public")
        
        assert response.status_code == 200
        assert response.json() == {"message": "This is public"}


class TestProtectedRoutes:
    """Tests for protected routes that require authentication."""
    
    def test_protected_route_without_token(self, client):
        """Test that protected route returns 403 without token."""
        response = client.get("/protected")
        
        # FastAPI's HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403
        assert "detail" in response.json() or "error" in response.json()
    
    def test_protected_route_with_valid_token(self, client, auth_headers):
        """Test that protected route is accessible with valid token."""
        response = client.get("/protected", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "This is protected"
        assert data["user_id"] == "test-user-123"
        assert data["username"] == "testuser"
    
    def test_protected_route_with_invalid_token(self, client):
        """Test that protected route returns 401 with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/protected", headers=headers)
        
        assert response.status_code == 401
        assert "error" in response.json()
    
    def test_protected_route_with_malformed_header(self, client):
        """Test that protected route returns 403 with malformed header."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/protected", headers=headers)
        
        # FastAPI's HTTPBearer returns 403 for malformed headers
        assert response.status_code == 403
        assert "detail" in response.json() or "error" in response.json()
    
    def test_protected_route_with_empty_token(self, client):
        """Test that protected route returns 403 with empty token."""
        headers = {"Authorization": "Bearer "}
        response = client.get("/protected", headers=headers)
        
        # FastAPI's HTTPBearer returns 403 for empty tokens
        assert response.status_code == 403
        assert "detail" in response.json() or "error" in response.json()


class TestMultipleProtectedRoutes:
    """Tests for multiple protected routes with same token."""
    
    def test_same_token_works_for_multiple_routes(self, client, auth_headers):
        """Test that same token can access multiple protected routes."""
        # Access first protected route
        response1 = client.get("/protected", headers=auth_headers)
        assert response1.status_code == 200
        assert response1.json()["user_id"] == "test-user-123"
        
        # Access second protected route with same token
        response2 = client.get("/admin", headers=auth_headers)
        assert response2.status_code == 200
        assert response2.json()["user"]["user_id"] == "test-user-123"
    
    def test_different_tokens_for_different_users(self, client):
        """Test that different tokens provide access to different user data."""
        # Create tokens for two different users
        token1 = generate_jwt("user-1", "alice")
        token2 = generate_jwt("user-2", "bob")
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Access route with first user's token
        response1 = client.get("/protected", headers=headers1)
        assert response1.status_code == 200
        assert response1.json()["username"] == "alice"
        
        # Access route with second user's token
        response2 = client.get("/protected", headers=headers2)
        assert response2.status_code == 200
        assert response2.json()["username"] == "bob"


class TestErrorResponses:
    """Tests for error response format."""
    
    def test_401_error_response_format(self, client):
        """Test that authentication errors have correct format."""
        response = client.get("/protected")
        
        # FastAPI's HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403
        data = response.json()
        
        # Check that error information is present
        assert "detail" in data or "error" in data
    
    def test_401_error_with_invalid_token_format(self, client):
        """Test error format when token is invalid."""
        headers = {"Authorization": "Bearer invalid.token"}
        response = client.get("/protected", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["message"]
    
    def test_401_error_with_missing_token_format(self, client):
        """Test error format when token is missing."""
        response = client.get("/protected")
        
        # FastAPI's HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data or "error" in data


class TestTokenExpiration:
    """Tests for token expiration handling."""
    
    def test_expired_token_returns_401(self, client):
        """Test that expired token returns 401."""
        # Create an expired token (issued in the past)
        from unittest.mock import patch
        import time
        
        # Create token with past timestamp
        with patch('time.time', return_value=time.time() - 86401):  # 24 hours + 1 second ago
            expired_token = generate_jwt("user-123", "testuser")
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/protected", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["message"]


class TestConcurrentRequests:
    """Tests for concurrent requests with authentication."""
    
    def test_concurrent_requests_with_same_token(self, client, auth_headers):
        """Test that same token can be used for concurrent requests."""
        # Simulate concurrent requests
        responses = []
        for _ in range(5):
            response = client.get("/protected", headers=auth_headers)
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["user_id"] == "test-user-123"
    
    def test_concurrent_requests_with_different_tokens(self, client):
        """Test concurrent requests with different user tokens."""
        tokens = [
            generate_jwt(f"user-{i}", f"user{i}")
            for i in range(3)
        ]
        
        responses = []
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/protected", headers=headers)
            responses.append((i, response))
        
        # Each request should return correct user data
        for i, response in responses:
            assert response.status_code == 200
            assert response.json()["username"] == f"user{i}"
