"""Integration tests for user registration endpoint functionality."""
import pytest
import os
import tempfile
from auth.service import register_user, authenticate_user, AuthenticationError, ValidationError
from auth.database import UserDatabase
from auth.jwt import validate_token


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db = UserDatabase(db_path)
    
    import auth.database
    original_db = auth.database._db_instance
    auth.database._db_instance = db
    
    yield db
    
    auth.database._db_instance = original_db
    
    try:
        os.unlink(db_path)
    except:
        pass


def test_registration_returns_valid_jwt(test_db):
    """Test that registration returns a valid JWT token."""
    # Register user
    token = register_user("john_doe", "securepass123")
    
    # Validate token
    payload = validate_token(token)
    
    # Verify payload contains correct data
    assert payload["username"] == "john_doe"
    assert "user_id" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_registration_creates_user_in_database(test_db):
    """Test that registration creates a user record in the database."""
    # Register user
    token = register_user("jane_smith", "password456")
    
    # Verify user exists in database
    user = test_db.get_user_by_username("jane_smith")
    assert user is not None
    assert user.username == "jane_smith"
    assert user.password_hash is not None
    assert user.password_hash != "password456"  # Should be hashed
    assert user.id is not None
    assert user.created_at is not None


def test_registration_token_allows_immediate_authentication(test_db):
    """Test that the JWT token from registration can be used immediately."""
    # Register user
    token = register_user("alice", "mypassword")
    
    # Validate the token (simulating API authentication)
    payload = validate_token(token)
    
    # Verify we can look up the user with the token's user_id
    user = test_db.get_user_by_id(payload["user_id"])
    assert user is not None
    assert user.username == "alice"


def test_registration_followed_by_login(test_db):
    """Test that a registered user can immediately log in."""
    # Register user
    register_token = register_user("bob", "bobspassword")
    
    # Login with same credentials
    login_token = authenticate_user("bob", "bobspassword")
    
    # Both tokens should be valid
    register_payload = validate_token(register_token)
    login_payload = validate_token(login_token)
    
    # Should refer to same user
    assert register_payload["user_id"] == login_payload["user_id"]
    assert register_payload["username"] == login_payload["username"]


def test_registration_enforces_username_uniqueness(test_db):
    """Test that duplicate usernames are rejected."""
    # Register first user
    register_user("charlie", "password123")
    
    # Attempt to register with same username should fail
    with pytest.raises(AuthenticationError) as exc_info:
        register_user("charlie", "differentpass")
    
    assert exc_info.value.code == "AUTH_USERNAME_EXISTS"


def test_registration_enforces_password_length(test_db):
    """Test that short passwords are rejected."""
    # Attempt to register with short password
    with pytest.raises(ValidationError) as exc_info:
        register_user("david", "short")
    
    assert exc_info.value.code == "VALIDATION_PASSWORD_LENGTH"
    assert exc_info.value.field == "password"


def test_multiple_user_registrations(test_db):
    """Test that multiple users can register successfully."""
    # Register multiple users
    token1 = register_user("user1", "password1")
    token2 = register_user("user2", "password2")
    token3 = register_user("user3", "password3")
    
    # All tokens should be valid
    payload1 = validate_token(token1)
    payload2 = validate_token(token2)
    payload3 = validate_token(token3)
    
    # All should have different user IDs
    assert payload1["user_id"] != payload2["user_id"]
    assert payload2["user_id"] != payload3["user_id"]
    assert payload1["user_id"] != payload3["user_id"]
    
    # All should have correct usernames
    assert payload1["username"] == "user1"
    assert payload2["username"] == "user2"
    assert payload3["username"] == "user3"


def test_registration_with_edge_case_usernames(test_db):
    """Test registration with various username formats."""
    # Test with underscores
    token1 = register_user("user_name", "password123")
    assert validate_token(token1)["username"] == "user_name"
    
    # Test with hyphens
    token2 = register_user("user-name", "password123")
    assert validate_token(token2)["username"] == "user-name"
    
    # Test with numbers
    token3 = register_user("user123", "password123")
    assert validate_token(token3)["username"] == "user123"
    
    # Test with mixed
    token4 = register_user("user_123-test", "password123")
    assert validate_token(token4)["username"] == "user_123-test"


def test_registration_password_not_stored_in_plain_text(test_db):
    """Test that passwords are hashed and not stored in plain text."""
    password = "mysecretpassword"
    register_user("security_test", password)
    
    # Get user from database
    user = test_db.get_user_by_username("security_test")
    
    # Password hash should not equal the original password
    assert user.password_hash != password
    
    # Password hash should be bcrypt format
    assert user.password_hash.startswith("$2b$")
    assert len(user.password_hash) == 60  # bcrypt hash length
