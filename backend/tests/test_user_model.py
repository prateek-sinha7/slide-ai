"""Unit tests for User model and database operations."""
import pytest
import os
import sys
import tempfile
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.models import User
from auth.database import UserDatabase


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation_with_defaults(self):
        """Test creating a user with default values."""
        user = User(username="testuser", password_hash="hashed_password")
        
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.id is not None
        assert len(user.id) == 36  # UUID format
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
        assert user.last_login is None
    
    def test_user_creation_with_explicit_values(self):
        """Test creating a user with explicit values."""
        user_id = "test-id-123"
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        last_login = datetime(2024, 1, 2, 12, 0, 0)
        
        user = User(
            username="testuser",
            password_hash="hashed_password",
            id=user_id,
            created_at=created_at,
            last_login=last_login
        )
        
        assert user.id == user_id
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.created_at == created_at
        assert user.last_login == last_login
    
    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        last_login = datetime(2024, 1, 2, 12, 0, 0)
        
        user = User(
            username="testuser",
            password_hash="hashed_password",
            id="test-id-123",
            created_at=created_at,
            last_login=last_login
        )
        
        user_dict = user.to_dict()
        
        assert user_dict["id"] == "test-id-123"
        assert user_dict["username"] == "testuser"
        assert user_dict["password_hash"] == "hashed_password"
        assert user_dict["created_at"] == created_at.isoformat()
        assert user_dict["last_login"] == last_login.isoformat()
    
    def test_user_from_dict(self):
        """Test creating user from dictionary."""
        user_dict = {
            "id": "test-id-123",
            "username": "testuser",
            "password_hash": "hashed_password",
            "created_at": "2024-01-01T12:00:00",
            "last_login": "2024-01-02T12:00:00"
        }
        
        user = User.from_dict(user_dict)
        
        assert user.id == "test-id-123"
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert user.last_login == datetime(2024, 1, 2, 12, 0, 0)
    
    def test_user_from_dict_without_last_login(self):
        """Test creating user from dictionary without last_login."""
        user_dict = {
            "id": "test-id-123",
            "username": "testuser",
            "password_hash": "hashed_password",
            "created_at": "2024-01-01T12:00:00",
            "last_login": None
        }
        
        user = User.from_dict(user_dict)
        
        assert user.last_login is None
    
    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            username="testuser",
            password_hash="hashed_password",
            id="test-id-123"
        )
        
        repr_str = repr(user)
        assert "test-id-123" in repr_str
        assert "testuser" in repr_str


class TestUserDatabase:
    """Test cases for UserDatabase operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db = UserDatabase(db_path=path)
        yield db
        os.unlink(path)
    
    def test_database_initialization(self, temp_db):
        """Test database and table creation."""
        # Database should be created and accessible
        assert os.path.exists(temp_db.db_path)
    
    def test_create_user(self, temp_db):
        """Test creating a user in the database."""
        user = User(username="testuser", password_hash="hashed_password")
        created_user = temp_db.create_user(user)
        
        assert created_user.id == user.id
        assert created_user.username == user.username
        assert created_user.password_hash == user.password_hash
    
    def test_create_duplicate_username(self, temp_db):
        """Test that duplicate usernames raise an error."""
        user1 = User(username="testuser", password_hash="hash1")
        temp_db.create_user(user1)
        
        user2 = User(username="testuser", password_hash="hash2")
        with pytest.raises(Exception):  # sqlite3.IntegrityError
            temp_db.create_user(user2)
    
    def test_get_user_by_username(self, temp_db):
        """Test retrieving a user by username."""
        user = User(username="testuser", password_hash="hashed_password")
        temp_db.create_user(user)
        
        retrieved_user = temp_db.get_user_by_username("testuser")
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.username == user.username
        assert retrieved_user.password_hash == user.password_hash
    
    def test_get_user_by_username_not_found(self, temp_db):
        """Test retrieving a non-existent user."""
        retrieved_user = temp_db.get_user_by_username("nonexistent")
        assert retrieved_user is None
    
    def test_get_user_by_id(self, temp_db):
        """Test retrieving a user by ID."""
        user = User(username="testuser", password_hash="hashed_password")
        temp_db.create_user(user)
        
        retrieved_user = temp_db.get_user_by_id(user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.username == user.username
    
    def test_get_user_by_id_not_found(self, temp_db):
        """Test retrieving a non-existent user by ID."""
        retrieved_user = temp_db.get_user_by_id("nonexistent-id")
        assert retrieved_user is None
    
    def test_update_last_login(self, temp_db):
        """Test updating user's last login timestamp."""
        user = User(username="testuser", password_hash="hashed_password")
        temp_db.create_user(user)
        
        login_time = datetime(2024, 1, 15, 10, 30, 0)
        temp_db.update_last_login(user.id, login_time)
        
        updated_user = temp_db.get_user_by_id(user.id)
        assert updated_user.last_login == login_time
    
    def test_username_exists(self, temp_db):
        """Test checking if username exists."""
        user = User(username="testuser", password_hash="hashed_password")
        temp_db.create_user(user)
        
        assert temp_db.username_exists("testuser") is True
        assert temp_db.username_exists("nonexistent") is False
    
    def test_delete_user(self, temp_db):
        """Test deleting a user."""
        user = User(username="testuser", password_hash="hashed_password")
        temp_db.create_user(user)
        
        # User should exist
        assert temp_db.get_user_by_id(user.id) is not None
        
        # Delete user
        result = temp_db.delete_user(user.id)
        assert result is True
        
        # User should no longer exist
        assert temp_db.get_user_by_id(user.id) is None
    
    def test_delete_nonexistent_user(self, temp_db):
        """Test deleting a non-existent user."""
        result = temp_db.delete_user("nonexistent-id")
        assert result is False
