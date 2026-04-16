"""Password hashing and validation functions."""
import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hash string (60 characters, starts with $2b$)
        
    Example:
        >>> hash_password("mypassword123")
        '$2b$12$...'
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    
    # Return hash as string
    return password_hash.decode('utf-8')


def verify_password(password: str, hash: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hash: Bcrypt hash to verify against
        
    Returns:
        True if password matches hash, False otherwise
        
    Example:
        >>> password_hash = hash_password("mypassword123")
        >>> verify_password("mypassword123", password_hash)
        True
        >>> verify_password("wrongpassword", password_hash)
        False
    """
    # Convert password and hash to bytes
    password_bytes = password.encode('utf-8')
    hash_bytes = hash.encode('utf-8')
    
    # Check password against hash
    return bcrypt.checkpw(password_bytes, hash_bytes)


def validate_password_length(password: str) -> bool:
    """
    Validate that a password meets the minimum length requirement.
    
    Args:
        password: Password string to validate
        
    Returns:
        True if password has at least 8 characters, False otherwise
        
    Example:
        >>> validate_password_length("short")
        False
        >>> validate_password_length("longenough")
        True
    """
    return len(password) >= 8
