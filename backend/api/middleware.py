"""Authentication middleware for FastAPI."""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
import logging

from auth.jwt import validate_token, TokenValidationError
from api.exceptions import AuthenticationError


logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> dict:
    """
    Extract and validate JWT token from request.
    
    This function extracts the JWT token from the Authorization header,
    validates it, and returns the user information from the token payload.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (automatically extracted by FastAPI)
        
    Returns:
        Dictionary containing user_id and username from the token payload
        
    Raises:
        AuthenticationError: If token is missing, invalid, or expired
        
    Example:
        >>> # In a route handler:
        >>> user = await get_current_user(request, credentials)
        >>> user_id = user["user_id"]
        >>> username = user["username"]
    """
    # Check if Authorization header is present
    if credentials is None:
        logger.warning(
            "Missing Authorization header",
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
        raise AuthenticationError("Missing authentication token")
    
    # Extract token from credentials
    token = credentials.credentials
    
    if not token:
        logger.warning(
            "Empty token in Authorization header",
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
        raise AuthenticationError("Missing authentication token")
    
    # Validate token and extract payload
    try:
        payload = validate_token(token)
        
        logger.info(
            f"User authenticated: {payload.get('username')}",
            extra={
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return {
            "user_id": payload["user_id"],
            "username": payload["username"]
        }
        
    except TokenValidationError as e:
        logger.warning(
            f"Token validation failed: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
        raise AuthenticationError(f"Invalid or expired token: {str(e)}")


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a route handler.
    
    This decorator can be used to protect route handlers by ensuring
    a valid JWT token is present in the request.
    
    Usage:
        @app.get("/protected")
        @require_auth
        async def protected_route(request: Request):
            user = request.state.user
            return {"message": f"Hello {user['username']}"}
    
    Args:
        func: The route handler function to protect
        
    Returns:
        Wrapped function that validates authentication before calling the handler
    """
    async def wrapper(request: Request, *args, **kwargs):
        # Extract credentials from request
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing authentication token")
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            payload = validate_token(token)
            # Store user info in request state for access in route handler
            request.state.user = {
                "user_id": payload["user_id"],
                "username": payload["username"]
            }
        except TokenValidationError as e:
            raise AuthenticationError(f"Invalid or expired token: {str(e)}")
        
        # Call the original route handler
        return await func(request, *args, **kwargs)
    
    return wrapper
