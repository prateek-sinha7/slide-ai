"""Integration tests for presentation generation and download endpoints."""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from main import app, presentations_storage, cleanup_expired_presentations
from auth.database import UserDatabase
from orchestrator.models import PresentationContent, TitleSlide, AgendaSlide, SlideContent, SummarySlide
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
def auth_token(client):
    """Register a user and return auth token."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    return response.json()["token"]


@pytest.fixture
def mock_presentation_content():
    """Create mock presentation content."""
    return PresentationContent(
        title=TitleSlide(
            main_title="Test Presentation",
            subtitle="A test subtitle"
        ),
        agenda=AgendaSlide(
            items=["Topic 1", "Topic 2", "Topic 3"]
        ),
        slides=[
            SlideContent(
                title="Slide 1",
                content=["Point 1", "Point 2", "Point 3"],
                notes="Speaker notes for slide 1"
            ),
            SlideContent(
                title="Slide 2",
                content=["Point A", "Point B", "Point C"],
                notes="Speaker notes for slide 2"
            )
        ],
        summary=SummarySlide(
            title="Key Takeaways",
            takeaways=["Takeaway 1", "Takeaway 2", "Takeaway 3"]
        )
    )


@pytest.fixture(autouse=True)
def cleanup_storage():
    """Clean up presentations storage after each test."""
    yield
    presentations_storage.clear()


# ============================================================================
# POST /api/presentations/generate Tests
# ============================================================================

def test_generate_presentation_success(client, auth_token, mock_presentation_content):
    """Test successful presentation generation with valid inputs."""
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.return_value = b"fake pptx data"
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "AI in Healthcare",
                "tone": "professional",
                "slide_count": 8
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "presentation_id" in data
        assert "filename" in data
        assert "download_url" in data
        assert "generated_at" in data
        
        # Verify filename format
        assert data["filename"].endswith(".pptx")
        assert "AI_in_Healthcare" in data["filename"] or "AI" in data["filename"]
        
        # Verify download URL
        assert data["download_url"].startswith("/api/presentations/download/")
        assert data["presentation_id"] in data["download_url"]
        
        # Verify orchestrator was called with correct parameters
        mock_orchestrator.assert_called_once()
        call_args = mock_orchestrator.call_args
        assert call_args[1]["topic"] == "AI in Healthcare"
        assert call_args[1]["tone"] == "professional"
        assert call_args[1]["slide_count"] == 8


def test_generate_presentation_with_defaults(client, auth_token, mock_presentation_content):
    """Test presentation generation with default tone and slide_count."""
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.return_value = b"fake pptx data"
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Machine Learning Basics"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify defaults were applied
        call_args = mock_orchestrator.call_args
        assert call_args[1]["tone"] == "professional"
        assert call_args[1]["slide_count"] == 8


def test_generate_presentation_missing_auth(client):
    """Test generation without authentication returns 401."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": "Test Topic"
        }
    )
    
    assert response.status_code == 403  # FastAPI returns 403 for missing auth


def test_generate_presentation_invalid_token(client):
    """Test generation with invalid token returns 401."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": "Test Topic"
        },
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_generate_presentation_missing_topic(client, auth_token):
    """Test generation without topic returns 400."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "tone": "formal"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_generate_presentation_empty_topic(client, auth_token):
    """Test generation with empty topic returns 400."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": ""
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_generate_presentation_topic_too_long(client, auth_token):
    """Test generation with topic exceeding 500 characters returns 400."""
    long_topic = "x" * 501
    
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": long_topic
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_generate_presentation_invalid_tone(client, auth_token):
    """Test generation with invalid tone returns 400."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": "Test Topic",
            "tone": "invalid_tone"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "tone" in data["message"].lower()


def test_generate_presentation_slide_count_too_low(client, auth_token):
    """Test generation with slide_count < 5 returns 400."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": "Test Topic",
            "slide_count": 3
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_generate_presentation_slide_count_too_high(client, auth_token):
    """Test generation with slide_count > 20 returns 400."""
    response = client.post(
        "/api/presentations/generate",
        json={
            "topic": "Test Topic",
            "slide_count": 25
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_generate_presentation_timeout(client, auth_token):
    """Test generation timeout returns 408."""
    from orchestrator.exceptions import GenerationTimeoutError
    
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator:
        mock_orchestrator.side_effect = GenerationTimeoutError("Timeout", agent="Pipeline")
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 408
        data = response.json()
        assert "timeout" in data["message"].lower()


def test_generate_presentation_llm_unavailable(client, auth_token):
    """Test LLM service unavailable returns 500."""
    from orchestrator.exceptions import LLMServiceUnavailableError
    
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator:
        mock_orchestrator.side_effect = LLMServiceUnavailableError("Service unavailable", agent="Pipeline")
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "unavailable" in data["message"].lower()
        assert data["retryable"] == True


def test_generate_presentation_generation_error(client, auth_token):
    """Test generation error returns 500."""
    from orchestrator.exceptions import GenerationError as OrchestratorGenerationError
    
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator:
        mock_orchestrator.side_effect = OrchestratorGenerationError("Generation failed", agent="Content")
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "retryable" in data


def test_generate_presentation_ppt_error(client, auth_token, mock_presentation_content):
    """Test PPT generation error returns 500."""
    from ppt_generator.generator import PPTGeneratorError
    
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.side_effect = PPTGeneratorError("PPT creation failed")
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "retryable" in data


def test_generate_presentation_stores_metadata(client, auth_token, mock_presentation_content):
    """Test that presentation metadata is stored correctly."""
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.return_value = b"fake pptx data"
        
        response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic",
                "tone": "formal",
                "slide_count": 10
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        presentation_id = data["presentation_id"]
        
        # Verify metadata is stored
        assert presentation_id in presentations_storage
        metadata = presentations_storage[presentation_id]
        
        assert metadata["id"] == presentation_id
        assert "user_id" in metadata
        assert metadata["topic"] == "Test Topic"
        assert metadata["filename"] == data["filename"]
        assert os.path.exists(metadata["file_path"])
        assert "created_at" in metadata
        assert "expires_at" in metadata


# ============================================================================
# GET /api/presentations/download/{id} Tests
# ============================================================================

def test_download_presentation_success(client, auth_token, mock_presentation_content):
    """Test successful presentation download."""
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.return_value = b"fake pptx data"
        
        # Generate presentation
        gen_response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert gen_response.status_code == 200
        presentation_id = gen_response.json()["presentation_id"]
        
        # Download presentation
        download_response = client.get(
            f"/api/presentations/download/{presentation_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert "attachment" in download_response.headers["content-disposition"]
        assert ".pptx" in download_response.headers["content-disposition"]


def test_download_presentation_missing_auth(client):
    """Test download without authentication returns 403."""
    response = client.get(
        "/api/presentations/download/fake-id"
    )
    
    assert response.status_code == 403


def test_download_presentation_invalid_token(client):
    """Test download with invalid token returns 401."""
    response = client.get(
        "/api/presentations/download/fake-id",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_download_presentation_not_found(client, auth_token):
    """Test download with non-existent ID returns 404."""
    response = client.get(
        "/api/presentations/download/nonexistent-id",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()


def test_download_presentation_expired(client, auth_token, mock_presentation_content):
    """Test download of expired presentation returns 404."""
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.return_value = b"fake pptx data"
        
        # Generate presentation
        gen_response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert gen_response.status_code == 200
        presentation_id = gen_response.json()["presentation_id"]
        
        # Manually expire the presentation
        presentations_storage[presentation_id]["expires_at"] = datetime.utcnow() - timedelta(hours=1)
        
        # Try to download
        download_response = client.get(
            f"/api/presentations/download/{presentation_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert download_response.status_code == 404
        data = download_response.json()
        assert "expired" in data["message"].lower()


def test_download_presentation_file_missing(client, auth_token, mock_presentation_content):
    """Test download when file is missing from disk returns 404."""
    with patch('backend.main.orchestrator.generate_presentation_content', new_callable=AsyncMock) as mock_orchestrator, \
         patch('backend.main.ppt_generator.create_presentation') as mock_generator:
        
        mock_orchestrator.return_value = mock_presentation_content
        mock_generator.return_value = b"fake pptx data"
        
        # Generate presentation
        gen_response = client.post(
            "/api/presentations/generate",
            json={
                "topic": "Test Topic"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert gen_response.status_code == 200
        presentation_id = gen_response.json()["presentation_id"]
        
        # Delete the file from disk
        metadata = presentations_storage[presentation_id]
        if os.path.exists(metadata["file_path"]):
            os.remove(metadata["file_path"])
        
        # Try to download
        download_response = client.get(
            f"/api/presentations/download/{presentation_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert download_response.status_code == 404


# ============================================================================
# Cleanup Tests
# ============================================================================

def test_cleanup_expired_presentations():
    """Test that cleanup removes expired presentations."""
    # Create mock expired presentation
    presentation_id = "test-id"
    fd, temp_file = tempfile.mkstemp(suffix=".pptx")
    os.close(fd)
    
    presentations_storage[presentation_id] = {
        "id": presentation_id,
        "user_id": "user123",
        "topic": "Test",
        "filename": "test.pptx",
        "file_path": temp_file,
        "created_at": datetime.utcnow() - timedelta(hours=2),
        "expires_at": datetime.utcnow() - timedelta(hours=1)
    }
    
    # Verify file exists
    assert os.path.exists(temp_file)
    
    # Run cleanup
    cleanup_expired_presentations()
    
    # Verify presentation was removed
    assert presentation_id not in presentations_storage
    
    # Verify file was deleted
    assert not os.path.exists(temp_file)


def test_cleanup_keeps_valid_presentations():
    """Test that cleanup keeps non-expired presentations."""
    # Create mock valid presentation
    presentation_id = "test-id"
    fd, temp_file = tempfile.mkstemp(suffix=".pptx")
    os.close(fd)
    
    presentations_storage[presentation_id] = {
        "id": presentation_id,
        "user_id": "user123",
        "topic": "Test",
        "filename": "test.pptx",
        "file_path": temp_file,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    
    # Run cleanup
    cleanup_expired_presentations()
    
    # Verify presentation still exists
    assert presentation_id in presentations_storage
    assert os.path.exists(temp_file)
    
    # Cleanup
    os.remove(temp_file)
    presentations_storage.clear()
