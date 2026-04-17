"""Configuration for LLM Orchestrator."""
import os
import time
from typing import Literal, Optional, Dict, Any
from groq import RateLimitError, APIError, APITimeoutError


class OrchestratorConfig:
    """Configuration for LLM Orchestrator and agents."""
    
    # LLM Provider Configuration
    LLM_PROVIDER: Literal["openai", "anthropic", "ollama", "groq"] = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # LangSmith Configuration (for tracing and monitoring)
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "slide-ai")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Groq Configuration
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    QUALITY_THRESHOLD: float = float(os.getenv("QUALITY_THRESHOLD", "0.8"))
    
    # Timeout Configuration (seconds)
    PLANNER_TIMEOUT: int = int(os.getenv("PLANNER_TIMEOUT", "30"))
    CONTENT_TIMEOUT: int = int(os.getenv("CONTENT_TIMEOUT", "40"))
    REVIEWER_TIMEOUT: int = int(os.getenv("REVIEWER_TIMEOUT", "40"))
    DESIGN_TIMEOUT: int = int(os.getenv("DESIGN_TIMEOUT", "30"))
    PIPELINE_TIMEOUT: int = int(os.getenv("PIPELINE_TIMEOUT", "120"))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "2"))
    
    # Performance Logging
    ENABLE_PERFORMANCE_LOGGING: bool = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
    
    @classmethod
    def retry_with_exponential_backoff(
        cls,
        func,
        max_retries: Optional[int] = None,
        initial_delay: Optional[int] = None,
        error_messages: Optional[Dict[type, str]] = None
    ):
        """
        Retry a function with exponential backoff for transient failures.
        
        Handles:
        - Rate limit errors (429)
        - Service unavailable errors (503)
        - Timeout errors
        - Other transient API errors
        
        Args:
            func: Function to retry (should be callable)
            max_retries: Maximum number of retries (default: cls.MAX_RETRIES)
            initial_delay: Initial delay in seconds (default: cls.RETRY_DELAY)
            error_messages: Custom error messages for specific exception types
            
        Returns:
            Result from successful function call
            
        Raises:
            Exception: The last exception if all retries fail
        """
        import logging
        logger = logging.getLogger(__name__)
        
        max_retries = max_retries or cls.MAX_RETRIES
        initial_delay = initial_delay or cls.RETRY_DELAY
        error_messages = error_messages or {}
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except RateLimitError as e:
                last_exception = e
                message = error_messages.get(RateLimitError, 
                    "Groq API rate limit exceeded. Please wait a moment and try again.")
                logger.warning(
                    f"Rate limit error on attempt {attempt + 1}/{max_retries}: {message}"
                )
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            except APITimeoutError as e:
                last_exception = e
                message = error_messages.get(APITimeoutError,
                    "Groq API request timed out. The service may be slow or unavailable.")
                logger.warning(
                    f"Timeout error on attempt {attempt + 1}/{max_retries}: {message}"
                )
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            except APIError as e:
                last_exception = e
                # Check if it's a 503 Service Unavailable
                if hasattr(e, 'status_code') and e.status_code == 503:
                    message = error_messages.get(APIError,
                        "Groq API service is temporarily unavailable. Please try again later.")
                    logger.warning(
                        f"Service unavailable on attempt {attempt + 1}/{max_retries}: {message}"
                    )
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2 ** attempt)
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                else:
                    # Non-retryable API error
                    logger.error(f"Non-retryable API error: {str(e)}")
                    raise
            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable error: {str(e)}")
                raise
        
        # All retries exhausted
        logger.error(f"All {max_retries} retry attempts failed")
        raise last_exception
    
    @classmethod
    def validate(cls):
        """
        Validate configuration.
        
        Raises:
            ValueError: If required configuration is missing
        """
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if cls.LLM_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        if cls.LLM_PROVIDER == "ollama":
            # No API key required for Ollama
            pass
    
    @classmethod
    def print_config(cls):
        """Print current configuration for debugging."""
        print("=" * 60)
        print("LLM Orchestrator Configuration")
        print("=" * 60)
        print(f"LLM Provider: {cls.LLM_PROVIDER}")
        print(f"LLM Model: {cls.LLM_MODEL}")
        print(f"Temperature: {cls.LLM_TEMPERATURE}")
        print(f"Max Tokens: {cls.LLM_MAX_TOKENS}")
        print(f"Max Iterations: {cls.MAX_ITERATIONS}")
        print(f"Quality Threshold: {cls.QUALITY_THRESHOLD}")
        if cls.LLM_PROVIDER == "ollama":
            print(f"Ollama Base URL: {cls.OLLAMA_BASE_URL}")
        elif cls.LLM_PROVIDER == "groq":
            print(f"Groq Model: {cls.GROQ_MODEL}")
        print("-" * 60)
        print(f"LangSmith Tracing: {'Enabled' if cls.LANGSMITH_TRACING else 'Disabled'}")
        if cls.LANGSMITH_TRACING:
            print(f"LangSmith Project: {cls.LANGSMITH_PROJECT}")
            print(f"LangSmith Endpoint: {cls.LANGSMITH_ENDPOINT}")
        print("=" * 60)


config = OrchestratorConfig()

# Print configuration on module load
config.print_config()
