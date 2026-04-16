"""Custom exception classes for the API."""


class APIException(Exception):
    """Base exception for all API errors."""
    
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIException):
    """Exception raised when request validation fails."""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400
        )


class AuthenticationError(APIException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTH_FAILED",
            status_code=401
        )


class ConflictError(APIException):
    """Exception raised when a resource conflict occurs."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409
        )


class NotFoundError(APIException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404
        )


class GenerationError(APIException):
    """Exception raised when presentation generation fails."""
    
    def __init__(self, message: str, retryable: bool = True):
        self.retryable = retryable
        super().__init__(
            message=message,
            code="GENERATION_FAILED",
            status_code=500
        )


class TimeoutError(APIException):
    """Exception raised when an operation times out."""
    
    def __init__(self, message: str = "Request timeout"):
        super().__init__(
            message=message,
            code="TIMEOUT",
            status_code=408
        )


class ServiceUnavailableError(APIException):
    """Exception raised when a service is unavailable."""
    
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503
        )
