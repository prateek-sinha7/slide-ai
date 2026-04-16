"""Unit tests for JWT token generation and validation functions."""
import pytest
import os
import sys
import time
import jwt as pyjwt

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt import generate_jwt, decode_jwt, validate_token, TokenValidationError
from config import config


class TestGenerateJWT:
    """Test cases for JWT token generation."""
    
    def test_generate_jwt_returns_string(self):
        """Test that generate_jwt returns a string token."""
        token = generate_jwt("user123", "john_doe")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_jwt_contains_user_data(self):
        """Test that generated token contains user_id and username."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "john_doe"
        
        token = generate_jwt(user_id, username)
        payload = decode_jwt(token)
        
        assert payload["user_id"] == user_id
        assert payload["username"] == username
    
    def test_generate_jwt_has_issued_at(self):
        """Test that generated token has issued_at timestamp."""
        token = generate_jwt("user123", "john_doe")
        payload = decode_jwt(token)
        
        assert "iat" in payload
        assert isinstance(payload["iat"], int)
        assert payload["iat"] <= int(time.time())
    
    def test_generate_jwt_has_expiration(self):
        """Test that generated token has expiration timestamp."""
        token = generate_jwt("user123", "john_doe")
        payload = decode_jwt(token)
        
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
    
    def test_generate_jwt_expiration_is_24_hours(self):
        """Test that token expiration is exactly 24 hours from issued_at."""
        before_time = int(time.time())
        token = generate_jwt("user123", "john_doe")
        after_time = int(time.time())
        
        payload = decode_jwt(token)
        issued_at = payload["iat"]
        expires_at = payload["exp"]
        
        # Expiration should be 24 hours (86400 seconds) after issued_at
        expected_expiration = issued_at + 86400
        assert expires_at == expected_expiration
        
        # Verify issued_at is within the time window
        assert before_time <= issued_at <= after_time
    
    def test_generate_jwt_with_different_users(self):
        """Test generating tokens for different users produces different tokens."""
        token1 = generate_jwt("user1", "alice")
        token2 = generate_jwt("user2", "bob")
        
        assert token1 != token2
        
        payload1 = decode_jwt(token1)
        payload2 = decode_jwt(token2)
        
        assert payload1["user_id"] == "user1"
        assert payload2["user_id"] == "user2"
        assert payload1["username"] == "alice"
        assert payload2["username"] == "bob"


class TestDecodeJWT:
    """Test cases for JWT token decoding."""
    
    def test_decode_jwt_valid_token(self):
        """Test decoding a valid JWT token."""
        token = generate_jwt("user123", "john_doe")
        payload = decode_jwt(token)
        
        assert payload["user_id"] == "user123"
        assert payload["username"] == "john_doe"
        assert "iat" in payload
        assert "exp" in payload
    
    def test_decode_jwt_invalid_signature(self):
        """Test that decoding token with invalid signature raises error."""
        token = generate_jwt("user123", "john_doe")
        
        # Tamper with the token by changing the last character
        tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")
        
        with pytest.raises(TokenValidationError) as exc:
            decode_jwt(tampered_token)
        
        assert "signature" in str(exc.value).lower()
    
    def test_decode_jwt_malformed_token(self):
        """Test that decoding malformed token raises error."""
        with pytest.raises(TokenValidationError) as exc:
            decode_jwt("not.a.valid.jwt.token")
        
        assert "invalid" in str(exc.value).lower()
    
    def test_decode_jwt_empty_token(self):
        """Test that decoding empty token raises error."""
        with pytest.raises(TokenValidationError):
            decode_jwt("")
    
    def test_decode_jwt_wrong_secret(self):
        """Test that token signed with different secret fails validation."""
        # Create token with different secret
        payload = {
            "user_id": "user123",
            "username": "john_doe",
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400
        }
        wrong_token = pyjwt.encode(payload, "wrong-secret-key", algorithm="HS256")
        
        with pytest.raises(TokenValidationError) as exc:
            decode_jwt(wrong_token)
        
        assert "signature" in str(exc.value).lower()
    
    def test_decode_jwt_does_not_check_expiration(self):
        """Test that decode_jwt does not validate expiration."""
        # Create an expired token
        payload = {
            "user_id": "user123",
            "username": "john_doe",
            "iat": int(time.time()) - 90000,  # Issued 25 hours ago
            "exp": int(time.time()) - 3600    # Expired 1 hour ago
        }
        expired_token = pyjwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
        
        # decode_jwt should succeed even though token is expired
        decoded_payload = decode_jwt(expired_token)
        assert decoded_payload["user_id"] == "user123"


class TestValidateToken:
    """Test cases for JWT token validation."""
    
    def test_validate_token_valid_token(self):
        """Test validating a valid, non-expired token."""
        token = generate_jwt("user123", "john_doe")
        payload = validate_token(token)
        
        assert payload["user_id"] == "user123"
        assert payload["username"] == "john_doe"
    
    def test_validate_token_expired_token(self):
        """Test that validating expired token raises error."""
        # Create an expired token
        payload = {
            "user_id": "user123",
            "username": "john_doe",
            "iat": int(time.time()) - 90000,  # Issued 25 hours ago
            "exp": int(time.time()) - 3600    # Expired 1 hour ago
        }
        expired_token = pyjwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(TokenValidationError) as exc:
            validate_token(expired_token)
        
        assert "expired" in str(exc.value).lower()
    
    def test_validate_token_invalid_signature(self):
        """Test that validating token with invalid signature raises error."""
        token = generate_jwt("user123", "john_doe")
        
        # Tamper with the token
        tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")
        
        with pytest.raises(TokenValidationError) as exc:
            validate_token(tampered_token)
        
        assert "signature" in str(exc.value).lower()
    
    def test_validate_token_malformed_token(self):
        """Test that validating malformed token raises error."""
        with pytest.raises(TokenValidationError) as exc:
            validate_token("not.a.valid.jwt")
        
        assert "invalid" in str(exc.value).lower()
    
    def test_validate_token_just_before_expiration(self):
        """Test validating token that's about to expire but still valid."""
        # Create token that expires in 1 second
        payload = {
            "user_id": "user123",
            "username": "john_doe",
            "iat": int(time.time()),
            "exp": int(time.time()) + 1  # Expires in 1 second
        }
        token = pyjwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
        
        # Should still be valid
        decoded_payload = validate_token(token)
        assert decoded_payload["user_id"] == "user123"
    
    def test_validate_token_just_after_expiration(self):
        """Test validating token that just expired."""
        # Create token that expired 1 second ago
        payload = {
            "user_id": "user123",
            "username": "john_doe",
            "iat": int(time.time()) - 86401,  # Issued 24 hours and 1 second ago
            "exp": int(time.time()) - 1       # Expired 1 second ago
        }
        expired_token = pyjwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(TokenValidationError) as exc:
            validate_token(expired_token)
        
        assert "expired" in str(exc.value).lower()


class TestJWTRoundTrip:
    """Test cases for JWT generation and validation round-trip."""
    
    def test_roundtrip_simple_user(self):
        """Test generate and validate round-trip with simple user data."""
        user_id = "user123"
        username = "john_doe"
        
        # Generate token
        token = generate_jwt(user_id, username)
        
        # Validate token
        payload = validate_token(token)
        
        # Verify data matches
        assert payload["user_id"] == user_id
        assert payload["username"] == username
    
    def test_roundtrip_uuid_user_id(self):
        """Test round-trip with UUID user_id."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "alice"
        
        token = generate_jwt(user_id, username)
        payload = validate_token(token)
        
        assert payload["user_id"] == user_id
        assert payload["username"] == username
    
    def test_roundtrip_special_characters_username(self):
        """Test round-trip with special characters in username."""
        user_id = "user456"
        username = "user_name-123"
        
        token = generate_jwt(user_id, username)
        payload = validate_token(token)
        
        assert payload["user_id"] == user_id
        assert payload["username"] == username
    
    def test_roundtrip_multiple_tokens(self):
        """Test generating and validating multiple tokens."""
        users = [
            ("user1", "alice"),
            ("user2", "bob"),
            ("user3", "charlie")
        ]
        
        tokens = []
        for user_id, username in users:
            token = generate_jwt(user_id, username)
            tokens.append(token)
        
        # Validate all tokens
        for i, token in enumerate(tokens):
            payload = validate_token(token)
            assert payload["user_id"] == users[i][0]
            assert payload["username"] == users[i][1]
    
    def test_roundtrip_decode_vs_validate(self):
        """Test that decode_jwt and validate_token return same data for valid token."""
        token = generate_jwt("user123", "john_doe")
        
        decoded_payload = decode_jwt(token)
        validated_payload = validate_token(token)
        
        # Both should return the same data
        assert decoded_payload["user_id"] == validated_payload["user_id"]
        assert decoded_payload["username"] == validated_payload["username"]
        assert decoded_payload["iat"] == validated_payload["iat"]
        assert decoded_payload["exp"] == validated_payload["exp"]
