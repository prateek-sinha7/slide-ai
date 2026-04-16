"""JWT token generation and validation functions."""
import jwt
import time
from typing import Optional
from datetime import datetime, timezone
from auth.models import User
from config import config


class TokenValidationError(Exception):
    """Exception raised when token validation fails."""
    pass


def generate_jwt(user_id: str, username: str) -> str:
    """
    Generate a JWT token with 24-hour expiration.
    
    Args:
        user_id: User's unique identifier (UUID)
        username: User's username
        
    Returns:
        JWT token string
        
    Example:
        >>> token = generate_jwt("123e4567-e89b-12d3-a456-426614174000", "john_doe")
        >>> isinstance(token, str)
        True
    """
    # Get current timestamp
    issued_at = int(time.time())
    
    # Calculate expiration (24 hours = 86400 seconds)
    expires_at = issued_at + (config.JWT_EXPIRATION_HOURS * 3600)
    
    # Create payload
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": issued_at,
        "exp": expires_at
    }
    
    # Encode and return JWT
    token = jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
    return token


def decode_jwt(token: str) -> dict:
    """
    Decode and validate JWT token signature.
    
    This function validates the token signature but does NOT check expiration.
    Use validate_token() for full validation including expiration checking.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload as dictionary
        
    Raises:
        TokenValidationError: If token signature is invalid or token is malformed
        
    Example:
        >>> token = generate_jwt("123", "john")
        >>> payload = decode_jwt(token)
        >>> payload["username"]
        'john'
    """
    try:
        # Decode token with signature verification but without expiration check
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": False}  # Don't verify expiration here
        )
        return payload
    except jwt.InvalidSignatureError:
        raise TokenValidationError("Invalid token signature")
    except jwt.DecodeError:
        raise TokenValidationError("Invalid token format")
    except jwt.InvalidTokenError as e:
        raise TokenValidationError(f"Invalid token: {str(e)}")


def validate_token(token: str) -> dict:
    """
    Validate JWT token with signature and expiration checking.
    
    Args:
        token: JWT token string to validate
        
    Returns:
        Decoded token payload as dictionary with user_id and username
        
    Raises:
        TokenValidationError: If token is invalid, expired, or malformed
        
    Example:
        >>> token = generate_jwt("123", "john")
        >>> payload = validate_token(token)
        >>> payload["user_id"]
        '123'
    """
    try:
        # Decode token with full validation including expiration
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": True}  # Verify expiration
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenValidationError("Token has expired")
    except jwt.InvalidSignatureError:
        raise TokenValidationError("Invalid token signature")
    except jwt.DecodeError:
        raise TokenValidationError("Invalid token format")
    except jwt.InvalidTokenError as e:
        raise TokenValidationError(f"Invalid token: {str(e)}")
