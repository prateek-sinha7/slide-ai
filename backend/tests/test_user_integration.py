"""Integration tests for User model and database."""
import pytest
import os
import sys
import tempfile
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.models import User
from auth.database import UserDatabase


class TestUserIntegration:
    """Integration tests for complete user workflows."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db = UserDatabase(db_path=path)
        yield db
        os.unlink(path)
    
    def test_complete_user_lifecycle(self, temp_db):
        """Test complete user lifecycle: create, retrieve, update, delete."""
        # Create a new user
        user = User(username="lifecycle_user", password_hash="hashed_pass_123")
        created_user = temp_db.create_user(user)
        
        assert created_user.id is not None
        assert created_user.username == "lifecycle_user"
        assert created_user.last_login is None
        
        # Retrieve user by username
        retrieved_user = temp_db.get_user_by_username("lifecycle_user")
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        
        # Retrieve user by ID
        retrieved_by_id = temp_db.get_user_by_id(created_user.id)
        assert retrieved_by_id is not None
        assert retrieved_by_id.username == "lifecycle_user"
        
        # Update last login
        login_time = datetime.now(timezone.utc)
        temp_db.update_last_login(created_user.id, login_time)
        
        updated_user = temp_db.get_user_by_id(created_user.id)
        assert updated_user.last_login is not None
        # Compare timestamps (allow small difference due to microseconds)
        assert abs((updated_user.last_login - login_time).total_seconds()) < 1
        
        # Delete user
        delete_result = temp_db.delete_user(created_user.id)
        assert delete_result is True
        
        # Verify user is deleted
        deleted_user = temp_db.get_user_by_id(created_user.id)
        assert deleted_user is None
    
    def test_multiple_users(self, temp_db):
        """Test creating and managing multiple users."""
        users = [
            User(username="user1", password_hash="hash1"),
            User(username="user2", password_hash="hash2"),
            User(username="user3", password_hash="hash3"),
        ]
        
        # Create all users
        for user in users:
            temp_db.create_user(user)
        
        # Verify all users exist
        for user in users:
            retrieved = temp_db.get_user_by_username(user.username)
            assert retrieved is not None
            assert retrieved.username == user.username
        
        # Verify username uniqueness check
        assert temp_db.username_exists("user1") is True
        assert temp_db.username_exists("user2") is True
        assert temp_db.username_exists("user3") is True
        assert temp_db.username_exists("nonexistent") is False
    
    def test_user_serialization_roundtrip(self, temp_db):
        """Test user serialization and deserialization."""
        # Create user
        original_user = User(
            username="serialize_user",
            password_hash="hashed_password"
        )
        temp_db.create_user(original_user)
        
        # Serialize to dict
        user_dict = original_user.to_dict()
        
        # Deserialize from dict
        deserialized_user = User.from_dict(user_dict)
        
        # Verify all fields match
        assert deserialized_user.id == original_user.id
        assert deserialized_user.username == original_user.username
        assert deserialized_user.password_hash == original_user.password_hash
        assert deserialized_user.created_at == original_user.created_at
        assert deserialized_user.last_login == original_user.last_login
