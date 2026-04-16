"""Authentication service functions for user registration and login."""
from datetime import datetime, timezone
from typing import Optional
from auth.models import User
from auth.password import hash_password, verify_password, validate_password_length
from auth.jwt import generate_jwt
from auth.database import get_database
import sqlite3


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", field: Optional[str] = None):
        self.message = message
        self.code = code
        self.field = field
        super().__init__(self.message)


def register_user(username: str, password: str) -> str:
    """
    Register a new user with username and password.
    
    This function:
    1. Validates password length (minimum 8 characters)
    2. Checks username uniqueness
    3. Hashes the password using bcrypt
    4. Creates a new user in the database
    5. Returns a JWT token for immediate authentication
    
    Args:
        username: Unique username for the new user
        password: Plain text password (will be hashed)
        
    Returns:
        JWT token string for immediate authentication
        
    Raises:
        ValidationError: If password is too short (< 8 characters)
        AuthenticationError: If username already exists
        
    Example:
        >>> token = register_user("john_doe", "securepass123")
        >>> isinstance(token, str)
        True
        
    Requirements:
        - 1.1: Create new user account with unique username and valid password
        - 1.2: Validate username uniqueness
        - 1.3: Return error for duplicate username
        - 1.8: Return JWT token on successful registration
    """
    # Validate password length (Requirement 1.4, 1.5)
    if not validate_password_length(password):
        raise ValidationError(
            "Password must be at least 8 characters",
            code="VALIDATION_PASSWORD_LENGTH",
            field="password"
        )
    
    # Get database instance
    db = get_database()
    
    # Check username uniqueness (Requirement 1.2)
    if db.username_exists(username):
        raise AuthenticationError(
            "Username already exists",
            code="AUTH_USERNAME_EXISTS"
        )
    
    # Hash password (Requirement 1.6, 1.7)
    password_hash = hash_password(password)
    
    # Create new user
    user = User(
        username=username,
        password_hash=password_hash
    )
    
    # Save user to database
    try:
        db.create_user(user)
    except sqlite3.IntegrityError:
        # Race condition: username was taken between check and insert
        raise AuthenticationError(
            "Username already exists",
            code="AUTH_USERNAME_EXISTS"
        )
    
    # Generate JWT token for immediate authentication (Requirement 1.8)
    token = generate_jwt(user.id, user.username)
    
    return token


def authenticate_user(username: str, password: str) -> str:
    """
    Authenticate a user with username and password.
    
    This function:
    1. Looks up the user by username
    2. Verifies the password against the stored hash
    3. Updates the last login timestamp
    4. Returns a JWT token
    
    Args:
        username: Username to authenticate
        password: Plain text password to verify
        
    Returns:
        JWT token string
        
    Raises:
        AuthenticationError: If credentials are invalid
        
    Example:
        >>> token = authenticate_user("john_doe", "securepass123")
        >>> isinstance(token, str)
        True
        
    Requirements:
        - 2.1: Return JWT token for valid credentials
        - 2.2: Return authentication error for invalid credentials
        - 2.5: Verify password by comparing hash
    """
    # Get database instance
    db = get_database()
    
    # Look up user by username
    user = db.get_user_by_username(username)
    
    # Check if user exists
    if user is None:
        raise AuthenticationError(
            "Invalid username or password",
            code="AUTH_INVALID_CREDENTIALS"
        )
    
    # Verify password (Requirement 2.5)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError(
            "Invalid username or password",
            code="AUTH_INVALID_CREDENTIALS"
        )
    
    # Update last login timestamp
    db.update_last_login(user.id, datetime.now(timezone.utc))
    
    # Generate JWT token (Requirement 2.1)
    token = generate_jwt(user.id, user.username)
    
    return token
