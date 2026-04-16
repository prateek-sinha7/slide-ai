"""User data model and database schema."""
import uuid
from datetime import datetime, timezone
from typing import Optional


class User:
    """User model for authentication and user management."""
    
    def __init__(
        self,
        username: str,
        password_hash: str,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None
    ):
        """
        Initialize a User instance.
        
        Args:
            username: Unique username (3-50 characters)
            password_hash: Hashed password (bcrypt/argon2)
            id: UUID string (generated if not provided)
            created_at: Account creation timestamp (current time if not provided)
            last_login: Last login timestamp (None for new users)
        """
        self.id = id or str(uuid.uuid4())
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now(timezone.utc)
        self.last_login = last_login
    
    def to_dict(self) -> dict:
        """
        Convert User instance to dictionary.
        
        Returns:
            Dictionary representation of the user
        """
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    @staticmethod
    def from_dict(data: dict) -> "User":
        """
        Create User instance from dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User instance
        """
        return User(
            id=data.get("id"),
            username=data["username"],
            password_hash=data["password_hash"],
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None
        )
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"User(id={self.id}, username={self.username}, created_at={self.created_at})"
