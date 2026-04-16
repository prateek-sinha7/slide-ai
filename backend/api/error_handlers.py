"""Error handling middleware and exception handlers for FastAPI."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from api.exceptions import (
    APIException,
    ValidationError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    GenerationError,
    TimeoutError,
    ServiceUnavailableError
)
from auth.jwt import TokenValidationError


logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register all error handlers with the FastAPI application."""
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """Handle custom API exceptions."""
        logger.error(
            f"API Exception: {exc.code} - {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        
        response_data = {
            "error": exc.__class__.__name__.replace("Error", "").lower(),
            "message": exc.message,
            "code": exc.code
        }
        
        # Add field information for validation errors
        if isinstance(exc, ValidationError) and exc.field:
            response_data["field"] = exc.field
        
        # Add retryable flag for generation errors
        if isinstance(exc, GenerationError):
            response_data["retryable"] = exc.retryable
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    
    @app.exception_handler(TokenValidationError)
    async def token_validation_error_handler(request: Request, exc: TokenValidationError):
        """Handle JWT token validation errors."""
        logger.warning(
            f"Token validation failed: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "authentication_failed",
                "message": "Invalid or expired token",
                "code": "AUTH_TOKEN_INVALID"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI request validation errors."""
        logger.warning(
            f"Request validation failed: {exc.errors()}",
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
        
        # Extract first error for simplicity
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        field = ".".join(str(loc) for loc in first_error.get("loc", []))
        message = first_error.get("msg", "Validation failed")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "validation_failed",
                "message": message,
                "code": "VALIDATION_ERROR",
                "field": field,
                "details": errors
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            f"HTTP Exception: {exc.status_code} - {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "code": f"HTTP_{exc.status_code}"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.exception(
            f"Unexpected error: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method
            },
            exc_info=exc
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )
