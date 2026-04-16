"""Test to verify backend setup is correct."""
import pytest


def test_imports():
    """Verify all required packages can be imported."""
    import fastapi
    import uvicorn
    import bcrypt
    import jwt
    import pptx
    import hypothesis
    
    assert fastapi is not None
    assert uvicorn is not None
    assert bcrypt is not None
    assert jwt is not None
    assert pptx is not None
    assert hypothesis is not None


def test_config_loads():
    """Verify configuration loads correctly."""
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir.parent))
    
    from config import config
    
    assert config.SECRET_KEY is not None
    assert config.JWT_EXPIRATION_HOURS == 24
    assert config.MAX_TOPIC_LENGTH == 500
    assert config.MIN_SLIDE_COUNT == 5
    assert config.MAX_SLIDE_COUNT == 20
    assert config.DEFAULT_SLIDE_COUNT == 8
