"""Unit tests for password hashing and validation functions."""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.password import hash_password, verify_password, validate_password_length


class TestPasswordValidation:
    """Test cases for password length validation."""
    
    def test_validate_password_length_too_short(self):
        """Test that passwords shorter than 8 characters are invalid."""
        assert validate_password_length("") is False
        assert validate_password_length("a") is False
        assert validate_password_length("1234567") is False
    
    def test_validate_password_length_exactly_8(self):
        """Test that passwords with exactly 8 characters are valid."""
        assert validate_password_length("12345678") is True
        assert validate_password_length("abcdefgh") is True
    
    def test_validate_password_length_longer_than_8(self):
        """Test that passwords longer than 8 characters are valid."""
        assert validate_password_length("123456789") is True
        assert validate_password_length("verylongpassword123") is True


class TestPasswordHashing:
    """Test cases for password hashing."""
    
    def test_hash_password_returns_different_from_original(self):
        """Test that hashed password is different from original."""
        password = "mypassword123"
        password_hash = hash_password(password)
        
        assert password_hash != password
    
    def test_hash_password_returns_bcrypt_format(self):
        """Test that hash follows bcrypt format."""
        password = "mypassword123"
        password_hash = hash_password(password)
        
        # Bcrypt hashes start with $2b$ and are 60 characters long
        assert password_hash.startswith('$2b$')
        assert len(password_hash) == 60
    
    def test_hash_password_produces_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "mypassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to different salts
        assert hash1 != hash2
    
    def test_hash_password_with_special_characters(self):
        """Test hashing passwords with special characters."""
        password = "p@ssw0rd!#$%"
        password_hash = hash_password(password)
        
        assert password_hash.startswith('$2b$')
        assert len(password_hash) == 60
    
    def test_hash_password_with_unicode(self):
        """Test hashing passwords with unicode characters."""
        password = "pässwörd123"
        password_hash = hash_password(password)
        
        assert password_hash.startswith('$2b$')
        assert len(password_hash) == 60


class TestPasswordVerification:
    """Test cases for password verification."""
    
    def test_verify_password_correct_password(self):
        """Test that correct password verifies successfully."""
        password = "mypassword123"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
    
    def test_verify_password_incorrect_password(self):
        """Test that incorrect password fails verification."""
        password = "mypassword123"
        password_hash = hash_password(password)
        
        assert verify_password("wrongpassword", password_hash) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MyPassword123"
        password_hash = hash_password(password)
        
        assert verify_password("MyPassword123", password_hash) is True
        assert verify_password("mypassword123", password_hash) is False
    
    def test_verify_password_with_special_characters(self):
        """Test verification with special characters."""
        password = "p@ssw0rd!#$%"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("p@ssw0rd!#$", password_hash) is False
    
    def test_verify_password_with_unicode(self):
        """Test verification with unicode characters."""
        password = "pässwörd123"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("password123", password_hash) is False


class TestPasswordRoundTrip:
    """Test cases for password hashing and verification round-trip."""
    
    def test_roundtrip_simple_password(self):
        """Test hash and verify round-trip with simple password."""
        password = "password123"
        password_hash = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, password_hash) is True
        
        # Wrong password should not verify
        assert verify_password("password124", password_hash) is False
    
    def test_roundtrip_complex_password(self):
        """Test hash and verify round-trip with complex password."""
        password = "C0mpl3x!P@ssw0rd#2024"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("C0mpl3x!P@ssw0rd#2023", password_hash) is False
    
    def test_roundtrip_minimum_length_password(self):
        """Test hash and verify round-trip with minimum length password."""
        password = "12345678"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("1234567", password_hash) is False
    
    def test_roundtrip_long_password(self):
        """Test hash and verify round-trip with long password.
        
        Note: bcrypt truncates passwords at 72 bytes, so passwords longer
        than 72 characters may have the same hash.
        """
        password = "a" * 70  # Use 70 to stay under bcrypt's 72-byte limit
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("a" * 69, password_hash) is False
