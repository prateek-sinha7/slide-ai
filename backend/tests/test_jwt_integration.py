"""Integration tests for JWT functions with User model."""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.models import User
from auth.password import hash_password
from auth.jwt import generate_jwt, validate_token, TokenValidationError


class TestJWTUserIntegration:
    """Test JWT functions with User model."""
    
    def test_generate_jwt_from_user(self):
        """Test generating JWT token from User instance."""
        # Create a user
        user = User(username="john_doe", password_hash=hash_password("password123"))
        
        # Generate token from user data
        token = generate_jwt(user.id, user.username)
        
        # Validate token
        payload = validate_token(token)
        
        assert payload["user_id"] == user.id
        assert payload["username"] == user.username
    
    def test_validate_token_returns_user_data(self):
        """Test that validated token can be used to retrieve user data."""
        # Create a user
        user = User(username="alice", password_hash=hash_password("password123"))
        
        # Generate token
        token = generate_jwt(user.id, user.username)
        
        # Validate token and extract user data
        payload = validate_token(token)
        
        # Verify we can reconstruct user identity from token
        assert payload["user_id"] == user.id
        assert payload["username"] == user.username
    
    def test_jwt_workflow_registration(self):
        """Test JWT workflow for user registration."""
        # Simulate registration: create user and return JWT
        username = "new_user"
        password = "password123"
        
        # Create user
        user = User(username=username, password_hash=hash_password(password))
        
        # Generate JWT for immediate authentication (Requirement 1.8)
        token = generate_jwt(user.id, user.username)
        
        # Verify token is valid
        payload = validate_token(token)
        assert payload["user_id"] == user.id
        assert payload["username"] == username
    
    def test_jwt_workflow_login(self):
        """Test JWT workflow for user login."""
        # Simulate login: verify credentials and return JWT
        username = "existing_user"
        password = "password123"
        
        # Create existing user
        user = User(username=username, password_hash=hash_password(password))
        
        # Generate JWT after successful authentication (Requirement 2.1)
        token = generate_jwt(user.id, user.username)
        
        # Verify token is valid
        payload = validate_token(token)
        assert payload["user_id"] == user.id
        assert payload["username"] == username
    
    def test_multiple_users_different_tokens(self):
        """Test that different users get different tokens."""
        # Create multiple users
        user1 = User(username="alice", password_hash=hash_password("password123"))
        user2 = User(username="bob", password_hash=hash_password("password456"))
        
        # Generate tokens
        token1 = generate_jwt(user1.id, user1.username)
        token2 = generate_jwt(user2.id, user2.username)
        
        # Tokens should be different
        assert token1 != token2
        
        # Each token should validate to correct user
        payload1 = validate_token(token1)
        payload2 = validate_token(token2)
        
        assert payload1["user_id"] == user1.id
        assert payload1["username"] == user1.username
        assert payload2["user_id"] == user2.id
        assert payload2["username"] == user2.username
