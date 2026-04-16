"""
Example usage of authentication middleware in FastAPI routes.

This file demonstrates how to use the authentication middleware
to protect routes and access user information.
"""

from fastapi import FastAPI, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from api.middleware import get_current_user
from api.error_handlers import register_error_handlers


# Initialize FastAPI app
app = FastAPI(title="Example API with Authentication")

# Register error handlers
register_error_handlers(app)

# Initialize HTTPBearer security scheme
security = HTTPBearer()


# Create a reusable dependency function
async def get_user_dependency(
    request: Request,
    credentials: HTTPBearer = Depends(security)
):
    """Dependency function to get current authenticated user."""
    return await get_current_user(request, credentials)


# ============================================================================
# PUBLIC ROUTES (No authentication required)
# ============================================================================

@app.get("/")
async def root():
    """Public root endpoint."""
    return {"message": "Welcome to the API"}


@app.get("/health")
async def health_check():
    """Public health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# PROTECTED ROUTES (Authentication required)
# ============================================================================

@app.get("/api/user/profile")
async def get_user_profile(user: dict = Depends(get_user_dependency)):
    """
    Get the current user's profile.
    
    Requires: Valid JWT token in Authorization header
    Returns: User profile information
    """
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "message": "This is your profile"
    }


@app.get("/api/user/settings")
async def get_user_settings(user: dict = Depends(get_user_dependency)):
    """
    Get the current user's settings.
    
    Requires: Valid JWT token in Authorization header
    Returns: User settings
    """
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }


# ============================================================================
# PROTECTED ROUTES WITH REQUEST BODY
# ============================================================================

class PresentationRequest(BaseModel):
    """Request model for presentation generation."""
    topic: str
    tone: str = "professional"
    slide_count: int = 8


@app.post("/api/presentations/generate")
async def generate_presentation(
    request_data: PresentationRequest,
    user: dict = Depends(get_user_dependency)
):
    """
    Generate a presentation for the authenticated user.
    
    Requires: Valid JWT token in Authorization header
    Body: PresentationRequest with topic, tone, slide_count
    Returns: Presentation generation result
    """
    return {
        "message": "Presentation generation started",
        "user_id": user["user_id"],
        "username": user["username"],
        "request": {
            "topic": request_data.topic,
            "tone": request_data.tone,
            "slide_count": request_data.slide_count
        }
    }


@app.get("/api/presentations/{presentation_id}")
async def get_presentation(
    presentation_id: str,
    user: dict = Depends(get_user_dependency)
):
    """
    Get a specific presentation.
    
    Requires: Valid JWT token in Authorization header
    Path: presentation_id
    Returns: Presentation details
    """
    return {
        "presentation_id": presentation_id,
        "user_id": user["user_id"],
        "username": user["username"],
        "status": "completed"
    }


# ============================================================================
# EXAMPLE: Using request object directly
# ============================================================================

@app.get("/api/debug/request-info")
async def get_request_info(
    request: Request,
    user: dict = Depends(get_user_dependency)
):
    """
    Example showing how to access both request and user information.
    
    Requires: Valid JWT token in Authorization header
    Returns: Request and user information
    """
    return {
        "user": user,
        "request": {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else None
        }
    }


# ============================================================================
# EXAMPLE: Multiple dependencies
# ============================================================================

async def get_pagination_params(skip: int = 0, limit: int = 10):
    """Example dependency for pagination."""
    return {"skip": skip, "limit": limit}


@app.get("/api/presentations")
async def list_presentations(
    user: dict = Depends(get_user_dependency),
    pagination: dict = Depends(get_pagination_params)
):
    """
    List presentations for the authenticated user with pagination.
    
    Requires: Valid JWT token in Authorization header
    Query params: skip, limit
    Returns: List of presentations
    """
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "pagination": pagination,
        "presentations": [
            {"id": "1", "topic": "AI in Healthcare"},
            {"id": "2", "topic": "Climate Change"}
        ]
    }


# ============================================================================
# TESTING THE API
# ============================================================================

"""
To test these endpoints:

1. Start the server:
   uvicorn backend.api.USAGE_EXAMPLE:app --reload

2. Test public endpoint (no auth required):
   curl http://localhost:8000/

3. Test protected endpoint without token (should fail with 403):
   curl http://localhost:8000/api/user/profile

4. Get a token (you'll need to implement login endpoint):
   # Assuming you have a login endpoint that returns a token
   TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"password123"}' \
     | jq -r '.token')

5. Test protected endpoint with token (should succeed):
   curl http://localhost:8000/api/user/profile \
     -H "Authorization: Bearer $TOKEN"

6. Test POST endpoint with token:
   curl -X POST http://localhost:8000/api/presentations/generate \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"topic":"AI in Healthcare","tone":"professional","slide_count":10}'
"""


# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

"""
The middleware automatically handles these error cases:

1. Missing Authorization header:
   Response: 403 Forbidden
   Body: {"detail": "Not authenticated"}

2. Invalid token format:
   Response: 403 Forbidden
   Body: {"detail": "Invalid authentication credentials"}

3. Expired token:
   Response: 401 Unauthorized
   Body: {
     "error": "authentication_failed",
     "message": "Invalid or expired token: Token has expired",
     "code": "AUTH_FAILED"
   }

4. Invalid signature:
   Response: 401 Unauthorized
   Body: {
     "error": "authentication_failed",
     "message": "Invalid or expired token: Invalid token signature",
     "code": "AUTH_FAILED"
   }

All errors are handled by the error handlers in backend/api/error_handlers.py
"""
