"""Authentication module for user management and JWT handling."""
from auth.models import User
from auth.database import UserDatabase, get_database
from auth.password import hash_password, verify_password, validate_password_length
from auth.jwt import generate_jwt, decode_jwt, validate_token, TokenValidationError
from auth.service import register_user, authenticate_user, AuthenticationError, ValidationError

__all__ = [
    "User",
    "UserDatabase",
    "get_database",
    "hash_password",
    "verify_password",
    "validate_password_length",
    "generate_jwt",
    "decode_jwt",
    "validate_token",
    "TokenValidationError",
    "register_user",
    "authenticate_user",
    "AuthenticationError",
    "ValidationError"
]
