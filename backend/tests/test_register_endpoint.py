"""Integration tests for POST /api/auth/register endpoint."""
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


def test_register_success(client):
    """Test successful user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "token" in data
    assert "user" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 0
    
    # Verify user information
    assert data["user"]["username"] == "testuser"
    assert "id" in data["user"]


def test_register_duplicate_username(client):
    """Test registration with duplicate username returns 409."""
    # Register first user
    client.post(
        "/api/auth/register",
        json={
            "username": "duplicate",
            "password": "password123"
        }
    )
    
    # Attempt to register with same username
    response = client.post(
        "/api/auth/register",
        json={
            "username": "duplicate",
            "password": "differentpass"
        }
    )
    
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "already exists" in data["message"].lower()


def test_register_short_password(client):
    """Test registration with short password returns 400."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "password": "short"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "8 characters" in data["message"]


def test_register_missing_username(client):
    """Test registration without username returns 400."""
    response = client.post(
        "/api/auth/register",
        json={
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_register_missing_password(client):
    """Test registration without password returns 400."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_register_empty_username(client):
    """Test registration with empty username returns 400."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_register_token_is_valid(client):
    """Test that the returned token is valid and can be decoded."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "tokentest",
            "password": "password123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    token = data["token"]
    
    # Verify token can be decoded
    from auth.jwt import decode_jwt
    payload = decode_jwt(token)
    
    assert payload["username"] == "tokentest"
    assert "user_id" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_register_multiple_users(client):
    """Test that multiple users can register successfully."""
    users = [
        ("user1", "password1"),
        ("user2", "password2"),
        ("user3", "password3")
    ]
    
    for username, password in users:
        response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": password
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["username"] == username
