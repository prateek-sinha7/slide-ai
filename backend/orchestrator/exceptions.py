"""Custom exceptions for LLM Orchestrator."""


class GenerationError(Exception):
    """Base exception for generation errors."""
    
    def __init__(self, message: str, agent: str = None, retryable: bool = False):
        """
        Initialize GenerationError.
        
        Args:
            message: Error message
            agent: Name of the agent that failed (optional)
            retryable: Whether the error is retryable
        """
        self.message = message
        self.agent = agent
        self.retryable = retryable
        super().__init__(self.message)
    
    def __str__(self):
        if self.agent:
            return f"{self.agent}: {self.message}"
        return self.message


class GenerationTimeoutError(GenerationError):
    """Exception raised when generation exceeds timeout."""
    
    def __init__(self, message: str, agent: str = None):
        super().__init__(message, agent, retryable=True)


class LLMServiceUnavailableError(GenerationError):
    """Exception raised when LLM service is unavailable."""
    
    def __init__(self, message: str, agent: str = None):
        super().__init__(message, agent, retryable=True)


class MalformedResponseError(GenerationError):
    """Exception raised when LLM returns malformed response."""
    
    def __init__(self, message: str, agent: str = None):
        super().__init__(message, agent, retryable=True)


class ValidationError(GenerationError):
    """Exception raised when output validation fails."""
    
    def __init__(self, message: str, agent: str = None):
        super().__init__(message, agent, retryable=False)
