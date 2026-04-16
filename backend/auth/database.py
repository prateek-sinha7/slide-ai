"""Database connection and user table management."""
import sqlite3
from datetime import datetime
from typing import Optional
from pathlib import Path
from auth.models import User


class UserDatabase:
    """Database manager for user operations."""
    
    def __init__(self, db_path: str = "users.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and users table if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
            """)
            conn.commit()
    
    def create_user(self, user: User) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User instance to create
            
        Returns:
            Created User instance
            
        Raises:
            sqlite3.IntegrityError: If username already exists
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, created_at, last_login)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.id,
                user.username,
                user.password_hash,
                user.created_at.isoformat(),
                user.last_login.isoformat() if user.last_login else None
            ))
            conn.commit()
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, created_at, last_login
                FROM users
                WHERE username = ?
            """, (username,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    password_hash=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    last_login=datetime.fromisoformat(row[4]) if row[4] else None
                )
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User instance if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, created_at, last_login
                FROM users
                WHERE id = ?
            """, (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    password_hash=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    last_login=datetime.fromisoformat(row[4]) if row[4] else None
                )
            return None
    
    def update_last_login(self, user_id: str, login_time: datetime) -> None:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID to update
            login_time: New login timestamp
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET last_login = ?
                WHERE id = ?
            """, (login_time.isoformat(), user_id))
            conn.commit()
    
    def username_exists(self, username: str) -> bool:
        """
        Check if a username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        return self.get_user_by_username(username) is not None
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from the database.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0


# Global database instance
_db_instance: Optional[UserDatabase] = None


def get_database() -> UserDatabase:
    """
    Get or create the global database instance.
    
    Returns:
        UserDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = UserDatabase()
    return _db_instance
