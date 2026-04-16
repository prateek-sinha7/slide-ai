"""PPT Generator package for creating PowerPoint presentations."""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ppt_generator.generator import (
    PPTGenerator,
    PPTGeneratorError,
    TemplateNotFoundError,
    FileCreationError,
    generate_filename,
    sanitize_topic
)

__all__ = [
    'PPTGenerator',
    'PPTGeneratorError',
    'TemplateNotFoundError',
    'FileCreationError',
    'generate_filename',
    'sanitize_topic'
]
