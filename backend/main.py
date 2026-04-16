"""Main FastAPI application entry point."""
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from config import config
from api.error_handlers import register_error_handlers
from api.exceptions import (
    ValidationError as APIValidationError, 
    ConflictError, 
    AuthenticationError as APIAuthenticationError,
    GenerationError,
    TimeoutError as APITimeoutError,
    NotFoundError
)
from api.validation import validate_presentation_request, sanitize_input
from api.middleware import get_current_user, security
from auth.service import register_user, authenticate_user, AuthenticationError, ValidationError as AuthValidationError
from auth.jwt import decode_jwt
from orchestrator.orchestrator import LLMOrchestrator
from orchestrator.exceptions import (
    GenerationTimeoutError,
    LLMServiceUnavailableError,
    GenerationError as OrchestratorGenerationError
)
from ppt_generator.generator import PPTGenerator, generate_filename, PPTGeneratorError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI PowerPoint Generator API",
    description="API for generating PowerPoint presentations from text prompts",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Lazy-load LLM Orchestrator and PPT Generator
# These will be initialized on first use to avoid requiring API keys at import time
_orchestrator = None
_ppt_generator = None

def get_orchestrator():
    """Get or create LLM Orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LLMOrchestrator()
    return _orchestrator

def get_ppt_generator():
    """Get or create PPT Generator instance."""
    global _ppt_generator
    if _ppt_generator is None:
        _ppt_generator = PPTGenerator()
    return _ppt_generator

# In-memory storage for presentation metadata
# Key: presentation_id, Value: dict with metadata
presentations_storage = {}


def cleanup_expired_presentations():
    """
    Clean up expired presentation files.
    
    This function removes presentation files that have exceeded the
    FILE_EXPIRATION_HOURS limit. It should be called periodically
    as a background task.
    
    Requirements:
        - 7.3: Implement 1-hour auto-cleanup for temporary files
    """
    now = datetime.utcnow()
    expired_ids = []
    
    for presentation_id, metadata in presentations_storage.items():
        if now > metadata["expires_at"]:
            expired_ids.append(presentation_id)
            
            # Delete file from disk
            if os.path.exists(metadata["file_path"]):
                try:
                    os.remove(metadata["file_path"])
                    logger.info(
                        f"Cleaned up expired presentation file: {presentation_id}",
                        extra={"presentation_id": presentation_id}
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to delete expired file: {presentation_id}",
                        extra={"presentation_id": presentation_id, "error": str(e)}
                    )
    
    # Remove from storage
    for presentation_id in expired_ids:
        del presentations_storage[presentation_id]
    
    if expired_ids:
        logger.info(
            f"Cleaned up {len(expired_ids)} expired presentations",
            extra={"count": len(expired_ids)}
        )


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Ensures temp directory exists and starts background cleanup task.
    """
    # Ensure temp directory exists
    os.makedirs(config.TEMP_FILE_DIR, exist_ok=True)
    logger.info(f"Temp directory initialized: {config.TEMP_FILE_DIR}")
    
    # Note: In production, use a proper background task scheduler
    # like APScheduler or Celery for periodic cleanup
    logger.info("Application startup complete")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str = Field(..., min_length=1, max_length=50, description="Unique username")
    password: str = Field(..., min_length=1, description="User password (min 8 characters)")


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="User password")


class AuthResponse(BaseModel):
    """Response model for authentication endpoints."""
    token: str = Field(..., description="JWT authentication token")
    user: dict = Field(..., description="User information")


class GeneratePresentationRequest(BaseModel):
    """Request model for presentation generation."""
    topic: str = Field(..., min_length=1, max_length=500, description="Presentation topic")
    tone: Optional[str] = Field(None, description="Presentation tone: formal, casual, fun, professional")
    slide_count: Optional[int] = Field(None, ge=5, le=20, description="Number of slides (5-20)", alias="slideCount")
    
    class Config:
        populate_by_name = True  # Allow both slide_count and slideCount


class PresentationResponse(BaseModel):
    """Response model for presentation generation."""
    presentation_id: str = Field(..., description="Unique presentation ID", alias="presentationId")
    filename: str = Field(..., description="Generated filename")
    download_url: str = Field(..., description="URL to download the presentation", alias="downloadUrl")
    generated_at: str = Field(..., description="ISO8601 timestamp of generation", alias="generatedAt")
    
    model_config = {
        "populate_by_name": True,  # Allow both snake_case and camelCase
        "by_alias": True  # Serialize using aliases (camelCase)
    }


# ============================================================================
# PUBLIC ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI PowerPoint Generator API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.post("/api/auth/register", response_model=AuthResponse, status_code=201)
async def register(request_data: RegisterRequest):
    """
    Register a new user account.
    
    Creates a new user with the provided username and password.
    Returns a JWT token for immediate authentication.
    
    Args:
        request_data: RegisterRequest with username and password
        
    Returns:
        AuthResponse with JWT token and user information
        
    Raises:
        ValidationError (400): If password is too short (< 8 characters)
        ConflictError (409): If username already exists
        
    Requirements:
        - 1.1: Create new user account with unique username and valid password
        - 1.2: Validate username uniqueness
        - 1.3: Return error for duplicate username
        - 1.8: Return JWT token on successful registration
        - 1.9: Provide registration form endpoint
    """
    try:
        # Call auth service to register user
        token = register_user(request_data.username, request_data.password)
        
        # Decode token to get user information
        payload = decode_jwt(token)
        
        logger.info(
            f"User registered successfully: {request_data.username}",
            extra={"username": request_data.username, "user_id": payload["user_id"]}
        )
        
        # Return 201 with token and user info
        return AuthResponse(
            token=token,
            user={
                "id": payload["user_id"],
                "username": payload["username"]
            }
        )
        
    except AuthValidationError as e:
        # Convert auth validation error to API validation error (400)
        logger.warning(
            f"Registration validation failed: {e.message}",
            extra={"username": request_data.username, "field": e.field}
        )
        raise APIValidationError(message=e.message, field=e.field)
        
    except AuthenticationError as e:
        # Convert username exists error to conflict error (409)
        if e.code == "AUTH_USERNAME_EXISTS":
            logger.warning(
                f"Registration failed - username exists: {request_data.username}",
                extra={"username": request_data.username}
            )
            raise ConflictError(message=e.message)
        else:
            # Re-raise other authentication errors
            logger.error(
                f"Registration failed with auth error: {e.message}",
                extra={"username": request_data.username, "code": e.code}
            )
            raise


@app.post("/api/auth/login", response_model=AuthResponse, status_code=200)
async def login(request_data: LoginRequest):
    """
    Authenticate a user and return a JWT token.
    
    Validates the provided username and password credentials.
    Returns a JWT token for authenticated session.
    
    Args:
        request_data: LoginRequest with username and password
        
    Returns:
        AuthResponse with JWT token and user information
        
    Raises:
        AuthenticationError (401): If credentials are invalid
        
    Requirements:
        - 2.1: Return JWT token for valid credentials
        - 2.2: Return authentication error for invalid credentials
    """
    try:
        # Call auth service to authenticate user
        token = authenticate_user(request_data.username, request_data.password)
        
        # Decode token to get user information
        payload = decode_jwt(token)
        
        logger.info(
            f"User logged in successfully: {request_data.username}",
            extra={"username": request_data.username, "user_id": payload["user_id"]}
        )
        
        # Return 200 with token and user info
        return AuthResponse(
            token=token,
            user={
                "id": payload["user_id"],
                "username": payload["username"]
            }
        )
        
    except AuthenticationError as e:
        # Convert auth service exception to API exception (401)
        logger.warning(
            f"Login failed: {e.message}",
            extra={"username": request_data.username, "code": e.code}
        )
        raise APIAuthenticationError(message=e.message)


# ============================================================================
# PRESENTATION GENERATION ROUTES
# ============================================================================

@app.post("/api/presentations/generate", response_model=PresentationResponse, response_model_by_alias=True, status_code=200)
async def generate_presentation(
    request_data: GeneratePresentationRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate a PowerPoint presentation from a topic and parameters.
    
    Requires authentication via JWT token in Authorization header.
    Validates input parameters, generates content using LLM Orchestrator,
    creates .pptx file using PPT Generator, and returns download metadata.
    
    Args:
        request_data: GeneratePresentationRequest with topic, tone, slide_count
        request: FastAPI request object
        credentials: JWT credentials from Authorization header
        
    Returns:
        PresentationResponse with presentation_id, filename, download_url, generated_at
        
    Raises:
        ValidationError (400): If input validation fails
        AuthenticationError (401): If JWT token is invalid or missing
        TimeoutError (408): If generation exceeds timeout
        GenerationError (500): If generation fails
        
    Requirements:
        - 4.5: Accept topic, tone, slide_count parameters
        - 5.1: Generate presentation content
        - 6.1: Create .pptx file
        - 7.1: Store presentation metadata
        - 7.2: Generate descriptive filename
        - 10.1: Require authentication
        - 10.2: Validate topic length (1-500 chars)
        - 10.3: Validate slide count (5-20)
        - 10.4: Validate tone enum
    """
    # Authenticate user
    user = await get_current_user(request, credentials)
    
    # Sanitize topic input
    sanitized_topic = sanitize_input(request_data.topic)
    
    # Validate request parameters
    try:
        validate_presentation_request(
            topic=sanitized_topic,
            tone=request_data.tone,
            slide_count=request_data.slide_count
        )
    except APIValidationError as e:
        logger.warning(
            f"Presentation generation validation failed: {e.message}",
            extra={"user_id": user["user_id"], "topic_length": len(request_data.topic)}
        )
        raise
    
    # Set defaults
    tone = request_data.tone or "professional"
    slide_count = request_data.slide_count or config.DEFAULT_SLIDE_COUNT
    
    logger.info(
        f"Starting presentation generation for user {user['username']}",
        extra={
            "user_id": user["user_id"],
            "topic": sanitized_topic[:50],
            "tone": tone,
            "slide_count": slide_count
        }
    )
    
    try:
        # Generate presentation content using LLM Orchestrator
        orchestrator = get_orchestrator()
        presentation_content = await orchestrator.generate_presentation_content(
            topic=sanitized_topic,
            tone=tone,
            slide_count=slide_count
        )
        
        logger.info(
            f"Content generation completed for user {user['username']}",
            extra={"user_id": user["user_id"]}
        )
        
        # Create .pptx file using PPT Generator
        ppt_generator = get_ppt_generator()
        pptx_bytes = ppt_generator.create_presentation(
            content=presentation_content,
            template="professional"
        )
        
        logger.info(
            f"PPT file created for user {user['username']}",
            extra={"user_id": user["user_id"], "file_size": len(pptx_bytes)}
        )
        
        # Generate presentation ID and filename
        presentation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        filename = generate_filename(sanitized_topic, timestamp)
        
        # Ensure temp directory exists
        os.makedirs(config.TEMP_FILE_DIR, exist_ok=True)
        
        # Save file to temporary storage
        file_path = os.path.join(config.TEMP_FILE_DIR, f"{presentation_id}.pptx")
        with open(file_path, "wb") as f:
            f.write(pptx_bytes)
        
        # Store presentation metadata
        presentations_storage[presentation_id] = {
            "id": presentation_id,
            "user_id": user["user_id"],
            "topic": sanitized_topic,
            "filename": filename,
            "file_path": file_path,
            "created_at": timestamp,
            "expires_at": timestamp + timedelta(hours=config.FILE_EXPIRATION_HOURS)
        }
        
        logger.info(
            f"Presentation generated successfully for user {user['username']}",
            extra={
                "user_id": user["user_id"],
                "presentation_id": presentation_id,
                "ppt_filename": filename
            }
        )
        
        # Return presentation metadata
        return PresentationResponse(
            presentation_id=presentation_id,
            filename=filename,
            download_url=f"/api/presentations/download/{presentation_id}",
            generated_at=timestamp.isoformat()
        )
        
    except GenerationTimeoutError as e:
        logger.error(
            f"Presentation generation timeout for user {user['username']}: {str(e)}",
            extra={"user_id": user["user_id"], "agent": e.agent}
        )
        raise APITimeoutError(
            message=f"Presentation generation exceeded timeout limit. Please try again with fewer slides."
        )
        
    except LLMServiceUnavailableError as e:
        logger.error(
            f"LLM service unavailable for user {user['username']}: {str(e)}",
            extra={"user_id": user["user_id"]}
        )
        raise GenerationError(
            message="AI service is temporarily unavailable. Please try again in a moment.",
            retryable=True
        )
        
    except OrchestratorGenerationError as e:
        logger.error(
            f"Content generation failed for user {user['username']}: {str(e)}",
            extra={"user_id": user["user_id"], "agent": e.agent}
        )
        raise GenerationError(
            message=f"Failed to generate presentation content: {str(e)}",
            retryable=True
        )
        
    except PPTGeneratorError as e:
        logger.error(
            f"PPT file creation failed for user {user['username']}: {str(e)}",
            extra={"user_id": user["user_id"]}
        )
        raise GenerationError(
            message=f"Failed to create presentation file: {str(e)}",
            retryable=False
        )
        
    except Exception as e:
        logger.exception(
            f"Unexpected error during presentation generation for user {user['username']}: {str(e)}",
            extra={"user_id": user["user_id"]},
            exc_info=e
        )
        raise GenerationError(
            message="An unexpected error occurred during presentation generation",
            retryable=True
        )


@app.get("/api/presentations/download/{presentation_id}")
async def download_presentation(
    presentation_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Download a generated presentation file.
    
    Requires authentication via JWT token in Authorization header.
    Retrieves the .pptx file by presentation ID and returns it with
    appropriate headers for browser download.
    
    Args:
        presentation_id: Unique presentation ID
        request: FastAPI request object
        credentials: JWT credentials from Authorization header
        
    Returns:
        FileResponse with .pptx file and download headers
        
    Raises:
        AuthenticationError (401): If JWT token is invalid or missing
        NotFoundError (404): If presentation not found or expired
        
    Requirements:
        - 7.3: Retrieve .pptx file by presentation ID
        - 8.1: Return binary file data
        - 8.2: Set Content-Disposition header with filename
        - 8.3: Set correct Content-Type header
    """
    # Authenticate user
    user = await get_current_user(request, credentials)
    
    logger.info(
        f"Download request for presentation {presentation_id}",
        extra={"user_id": user["user_id"], "presentation_id": presentation_id}
    )
    
    # Check if presentation exists
    if presentation_id not in presentations_storage:
        logger.warning(
            f"Presentation not found: {presentation_id}",
            extra={"user_id": user["user_id"], "presentation_id": presentation_id}
        )
        raise NotFoundError(message="Presentation not found or has expired")
    
    metadata = presentations_storage[presentation_id]
    
    # Check if presentation has expired
    if datetime.utcnow() > metadata["expires_at"]:
        logger.warning(
            f"Presentation expired: {presentation_id}",
            extra={"user_id": user["user_id"], "presentation_id": presentation_id}
        )
        # Clean up expired file
        if os.path.exists(metadata["file_path"]):
            os.remove(metadata["file_path"])
        del presentations_storage[presentation_id]
        raise NotFoundError(message="Presentation has expired")
    
    # Check if file exists on disk
    if not os.path.exists(metadata["file_path"]):
        logger.error(
            f"Presentation file missing: {presentation_id}",
            extra={"user_id": user["user_id"], "presentation_id": presentation_id}
        )
        del presentations_storage[presentation_id]
        raise NotFoundError(message="Presentation file not found")
    
    logger.info(
        f"Serving presentation file: {metadata['filename']}",
        extra={
            "user_id": user["user_id"],
            "presentation_id": presentation_id,
            "ppt_filename": metadata["filename"]
        }
    )
    
    # Return file with appropriate headers
    return FileResponse(
        path=metadata["file_path"],
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=metadata["filename"],
        headers={
            "Content-Disposition": f'attachment; filename="{metadata["filename"]}"'
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
