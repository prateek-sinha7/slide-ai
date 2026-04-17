"""Unit tests for authentication service functions."""
import pytest
import os
import tempfile
from auth.service import register_user, authenticate_user, AuthenticationError, ValidationError
from auth.database import UserDatabase, get_database
from auth.jwt import decode_jwt


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create test database instance
    db = UserDatabase(db_path)
    
    # Replace global database instance with test database
    import auth.database
    original_db = auth.database._db_instance
    auth.database._db_instance = db
    
    yield db
    
    # Restore original database instance
    auth.database._db_instance = original_db
    
    # Clean up temporary database file
    try:
        os.unlink(db_path)
    except:
        pass


def test_register_user_success(test_db):
    """Test successful user registration."""
    # Register a new user
    token = register_user("testuser", "password123")
    
    # Verify token is returned
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Verify token contains correct user data
    payload = decode_jwt(token)
    assert payload["username"] == "testuser"
    assert "user_id" in payload
    
    # Verify user exists in database
    user = test_db.get_user_by_username("testuser")
    assert user is not None
    assert user.username == "testuser"
    assert user.password_hash != "password123"  # Password should be hashed


def test_register_user_password_too_short(test_db):
    """Test registration with password shorter than 8 characters."""
    with pytest.raises(ValidationError) as exc_info:
        register_user("testuser", "short")
    
    assert exc_info.value.code == "VALIDATION_PASSWORD_LENGTH"
    assert "8 characters" in exc_info.value.message
    assert exc_info.value.field == "password"


def test_register_user_duplicate_username(test_db):
    """Test registration with duplicate username."""
    # Register first user
    register_user("testuser", "password123")
    
    # Attempt to register with same username
    with pytest.raises(AuthenticationError) as exc_info:
        register_user("testuser", "differentpass")
    
    assert exc_info.value.code == "AUTH_USERNAME_EXISTS"
    assert "already exists" in exc_info.value.message.lower()


def test_register_user_minimum_password_length(test_db):
    """Test registration with exactly 8 character password."""
    # Should succeed with exactly 8 characters
    token = register_user("testuser", "12345678")
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_register_user_long_password(test_db):
    """Test registration with long password."""
    long_password = "a" * 100
    token = register_user("testuser", long_password)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_authenticate_user_success(test_db):
    """Test successful user authentication."""
    # Register a user first
    register_user("testuser", "password123")
    
    # Authenticate with correct credentials
    token = authenticate_user("testuser", "password123")
    
    # Verify token is returned
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Verify token contains correct user data
    payload = decode_jwt(token)
    assert payload["username"] == "testuser"


def test_authenticate_user_wrong_password(test_db):
    """Test authentication with wrong password."""
    # Register a user first
    register_user("testuser", "password123")
    
    # Attempt to authenticate with wrong password
    with pytest.raises(AuthenticationError) as exc_info:
        authenticate_user("testuser", "wrongpassword")
    
    assert exc_info.value.code == "AUTH_INVALID_CREDENTIALS"
    assert "invalid" in exc_info.value.message.lower()


def test_authenticate_user_nonexistent_username(test_db):
    """Test authentication with nonexistent username."""
    with pytest.raises(AuthenticationError) as exc_info:
        authenticate_user("nonexistent", "password123")
    
    assert exc_info.value.code == "AUTH_INVALID_CREDENTIALS"
    assert "invalid" in exc_info.value.message.lower()


def test_register_and_authenticate_flow(test_db):
    """Test complete registration and authentication flow."""
    # Register a new user
    register_token = register_user("testuser", "password123")
    
    # Authenticate with the same credentials
    auth_token = authenticate_user("testuser", "password123")
    
    # Both tokens should be valid (though different)
    register_payload = decode_jwt(register_token)
    auth_payload = decode_jwt(auth_token)
    
    # Both should have same user data
    assert register_payload["username"] == auth_payload["username"]
    assert register_payload["user_id"] == auth_payload["user_id"]


def test_register_user_special_characters_in_username(test_db):
    """Test registration with special characters in username."""
    token = register_user("test_user-123", "password123")
    
    assert isinstance(token, str)
    user = test_db.get_user_by_username("test_user-123")
    assert user is not None


def test_register_user_special_characters_in_password(test_db):
    """Test registration with special characters in password."""
    special_password = "p@ssw0rd!#$%"
    token = register_user("testuser", special_password)
    
    assert isinstance(token, str)
    
    # Verify authentication works with special characters
    auth_token = authenticate_user("testuser", special_password)
    assert isinstance(auth_token, str)
