"""Unit tests for authentication middleware."""
import pytest
from fastapi import Request, FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import Mock, patch

from api.middleware import get_current_user, require_auth
from api.exceptions import AuthenticationError
from auth.jwt import generate_jwt, TokenValidationError


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.url.path = "/test"
    request.method = "GET"
    request.headers = {}
    request.state = Mock()
    return request


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing."""
    return generate_jwt("test-user-id", "testuser")


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing."""
    # Create a token with past expiration
    with patch('time.time', return_value=0):
        token = generate_jwt("test-user-id", "testuser")
    return token


class TestGetCurrentUser:
    """Tests for get_current_user function."""
    
    @pytest.mark.asyncio
    async def test_missing_credentials(self, mock_request):
        """Test that missing credentials raises AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(mock_request, credentials=None)
        
        assert "Missing authentication token" in str(exc_info.value.message)
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_empty_token(self, mock_request):
        """Test that empty token raises AuthenticationError."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(mock_request, credentials=credentials)
        
        assert "Missing authentication token" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_valid_token(self, mock_request, valid_token):
        """Test that valid token returns user information."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_token
        )
        
        user = await get_current_user(mock_request, credentials=credentials)
        
        assert user["user_id"] == "test-user-id"
        assert user["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_invalid_token_signature(self, mock_request):
        """Test that token with invalid signature raises AuthenticationError."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.signature"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(mock_request, credentials=credentials)
        
        assert "Invalid or expired token" in str(exc_info.value.message)
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_token(self, mock_request, expired_token):
        """Test that expired token raises AuthenticationError."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(mock_request, credentials=credentials)
        
        assert "Invalid or expired token" in str(exc_info.value.message)
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_malformed_token(self, mock_request):
        """Test that malformed token raises AuthenticationError."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="not-a-jwt-token"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(mock_request, credentials=credentials)
        
        assert "Invalid or expired token" in str(exc_info.value.message)


class TestRequireAuthDecorator:
    """Tests for require_auth decorator."""
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, mock_request):
        """Test that missing Authorization header raises AuthenticationError."""
        @require_auth
        async def protected_route(request: Request):
            return {"message": "success"}
        
        with pytest.raises(AuthenticationError) as exc_info:
            await protected_route(mock_request)
        
        assert "Missing authentication token" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_invalid_authorization_header_format(self, mock_request):
        """Test that invalid Authorization header format raises AuthenticationError."""
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        @require_auth
        async def protected_route(request: Request):
            return {"message": "success"}
        
        with pytest.raises(AuthenticationError) as exc_info:
            await protected_route(mock_request)
        
        assert "Missing authentication token" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_valid_token_allows_access(self, mock_request, valid_token):
        """Test that valid token allows access to protected route."""
        mock_request.headers = {"Authorization": f"Bearer {valid_token}"}
        
        @require_auth
        async def protected_route(request: Request):
            return {
                "message": "success",
                "user_id": request.state.user["user_id"],
                "username": request.state.user["username"]
            }
        
        result = await protected_route(mock_request)
        
        assert result["message"] == "success"
        assert result["user_id"] == "test-user-id"
        assert result["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_expired_token_denies_access(self, mock_request, expired_token):
        """Test that expired token denies access to protected route."""
        mock_request.headers = {"Authorization": f"Bearer {expired_token}"}
        
        @require_auth
        async def protected_route(request: Request):
            return {"message": "success"}
        
        with pytest.raises(AuthenticationError) as exc_info:
            await protected_route(mock_request)
        
        assert "Invalid or expired token" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_invalid_token_denies_access(self, mock_request):
        """Test that invalid token denies access to protected route."""
        mock_request.headers = {"Authorization": "Bearer invalid.token.here"}
        
        @require_auth
        async def protected_route(request: Request):
            return {"message": "success"}
        
        with pytest.raises(AuthenticationError) as exc_info:
            await protected_route(mock_request)
        
        assert "Invalid or expired token" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_user_info_stored_in_request_state(self, mock_request, valid_token):
        """Test that user information is stored in request.state."""
        mock_request.headers = {"Authorization": f"Bearer {valid_token}"}
        
        @require_auth
        async def protected_route(request: Request):
            # Verify user info is accessible in request.state
            assert hasattr(request.state, "user")
            assert request.state.user["user_id"] == "test-user-id"
            assert request.state.user["username"] == "testuser"
            return {"message": "success"}
        
        await protected_route(mock_request)


class TestMiddlewareIntegration:
    """Integration tests for middleware with FastAPI routes."""
    
    @pytest.mark.asyncio
    async def test_401_error_format(self, mock_request):
        """Test that 401 errors have correct format."""
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(mock_request, credentials=None)
        
        error = exc_info.value
        assert error.status_code == 401
        assert error.code == "AUTH_FAILED"
        assert isinstance(error.message, str)
    
    @pytest.mark.asyncio
    async def test_multiple_requests_with_same_token(self, mock_request, valid_token):
        """Test that same token can be used for multiple requests."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_token
        )
        
        # First request
        user1 = await get_current_user(mock_request, credentials=credentials)
        assert user1["user_id"] == "test-user-id"
        
        # Second request with same token
        user2 = await get_current_user(mock_request, credentials=credentials)
        assert user2["user_id"] == "test-user-id"
        
        # Both should return same user info
        assert user1 == user2
    
    @pytest.mark.asyncio
    async def test_different_users_different_tokens(self, mock_request):
        """Test that different tokens return different user information."""
        token1 = generate_jwt("user-1", "alice")
        token2 = generate_jwt("user-2", "bob")
        
        credentials1 = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token1)
        credentials2 = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token2)
        
        user1 = await get_current_user(mock_request, credentials=credentials1)
        user2 = await get_current_user(mock_request, credentials=credentials2)
        
        assert user1["user_id"] == "user-1"
        assert user1["username"] == "alice"
        assert user2["user_id"] == "user-2"
        assert user2["username"] == "bob"
