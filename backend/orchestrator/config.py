"""Configuration for LLM Orchestrator."""
import os
from typing import Literal


class OrchestratorConfig:
    """Configuration for LLM Orchestrator and agents."""
    
    # LLM Provider Configuration
    LLM_PROVIDER: Literal["openai", "anthropic", "ollama", "local"] = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Timeout Configuration (seconds)
    PLANNER_TIMEOUT: int = int(os.getenv("PLANNER_TIMEOUT", "30"))
    CONTENT_TIMEOUT: int = int(os.getenv("CONTENT_TIMEOUT", "40"))
    REVIEWER_TIMEOUT: int = int(os.getenv("REVIEWER_TIMEOUT", "40"))
    DESIGN_TIMEOUT: int = int(os.getenv("DESIGN_TIMEOUT", "30"))
    PIPELINE_TIMEOUT: int = int(os.getenv("PIPELINE_TIMEOUT", "120"))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "2"))
    
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
        if cls.LLM_PROVIDER == "ollama":
            print(f"Ollama Base URL: {cls.OLLAMA_BASE_URL}")
        print("=" * 60)


config = OrchestratorConfig()

# Print configuration on module load
config.print_config()
