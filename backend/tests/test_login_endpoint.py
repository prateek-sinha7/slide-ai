"""Integration tests for POST /api/auth/login endpoint."""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient

from main import app
from auth.database import UserDatabase
import backend.auth.database


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db = UserDatabase(db_path)
    
    original_db = backend.auth.database._db_instance
    backend.auth.database._db_instance = db
    
    yield db
    
    backend.auth.database._db_instance = original_db
    
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Register a test user for login tests."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    return {"username": "testuser", "password": "password123"}


def test_login_success(client, registered_user):
    """Test successful user login with valid credentials."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "token" in data
    assert "user" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 0
    
    # Verify user information
    assert data["user"]["username"] == registered_user["username"]
    assert "id" in data["user"]


def test_login_invalid_username(client, registered_user):
    """Test login with non-existent username returns 401."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "message" in data


def test_login_invalid_password(client, registered_user):
    """Test login with incorrect password returns 401."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": registered_user["username"],
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "message" in data


def test_login_missing_username(client):
    """Test login without username returns 400."""
    response = client.post(
        "/api/auth/login",
        json={
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_login_missing_password(client):
    """Test login without password returns 400."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_login_empty_username(client):
    """Test login with empty username returns 400."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_login_token_is_valid(client, registered_user):
    """Test that the returned token is valid and can be decoded."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    token = data["token"]
    
    # Verify token can be decoded
    from auth.jwt import decode_jwt
    payload = decode_jwt(token)
    
    assert payload["username"] == registered_user["username"]
    assert "user_id" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_login_multiple_times(client, registered_user):
    """Test that a user can login multiple times successfully."""
    for _ in range(3):
        response = client.post(
            "/api/auth/login",
            json={
                "username": registered_user["username"],
                "password": registered_user["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["username"] == registered_user["username"]


def test_login_case_sensitive_username(client, registered_user):
    """Test that username is case-sensitive."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": registered_user["username"].upper(),
            "password": registered_user["password"]
        }
    )
    
    # Should fail because username is case-sensitive
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


def test_login_different_users(client):
    """Test that multiple different users can login."""
    users = [
        ("user1", "password1"),
        ("user2", "password2"),
        ("user3", "password3")
    ]
    
    # Register all users
    for username, password in users:
        client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": password
            }
        )
    
    # Login with each user
    for username, password in users:
        response = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == username
