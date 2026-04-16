"""Timeout utilities for PPT generation."""
import signal
from typing import Callable, Any, TypeVar
from functools import wraps

T = TypeVar('T')


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout."""
    pass


def timeout(seconds: int):
    """
    Decorator to add timeout to a function.
    
    Args:
        seconds: Maximum execution time in seconds
        
    Raises:
        TimeoutError: If function execution exceeds timeout
        
    Example:
        @timeout(10)
        def slow_function():
            # This will raise TimeoutError if it takes > 10 seconds
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Define signal handler
            def timeout_handler(signum, frame):
                raise TimeoutError(
                    f"Function '{func.__name__}' exceeded timeout of {seconds} seconds"
                )
            
            # Set signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Disable alarm and restore old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        return wrapper
    return decorator


def with_timeout(func: Callable[..., T], timeout_seconds: int, *args, **kwargs) -> T:
    """
    Execute a function with a timeout.
    
    Args:
        func: Function to execute
        timeout_seconds: Maximum execution time in seconds
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
        
    Raises:
        TimeoutError: If function execution exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(
            f"Function '{func.__name__}' exceeded timeout of {timeout_seconds} seconds"
        )
    
    # Set signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = func(*args, **kwargs)
    finally:
        # Disable alarm and restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    
    return result
