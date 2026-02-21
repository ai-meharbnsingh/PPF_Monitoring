"""
Unit tests: auth_service.py
Tests JWT creation/validation, password hashing, password strength validation.
"""

import pytest

from src.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from src.utils.constants import UserRole


class TestPasswordHashing:
    def test_hash_returns_different_string(self):
        pwd = "TestPass@123"
        assert hash_password(pwd) != pwd

    def test_verify_correct_password(self):
        pwd = "TestPass@123"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("TestPass@123")
        assert verify_password("WrongPass@456", hashed) is False

    def test_different_hashes_for_same_password(self):
        pwd = "TestPass@123"
        assert hash_password(pwd) != hash_password(pwd)  # bcrypt salts each hash


class TestPasswordStrength:
    # validate_password_strength returns tuple[bool, str] — (is_valid, error_msg)

    def test_strong_password_passes(self):
        valid, msg = validate_password_strength("StrongPass@1")
        assert valid is True
        assert msg == ""

    def test_too_short_fails(self):
        valid, msg = validate_password_strength("Short1")
        assert valid is False
        assert "character" in msg.lower() or "short" in msg.lower() or msg != ""

    def test_no_uppercase_fails(self):
        valid, msg = validate_password_strength("nouppercasepass1")
        assert valid is False
        assert msg != ""

    def test_no_digit_fails(self):
        valid, msg = validate_password_strength("NoDigitsPass")
        assert valid is False
        assert msg != ""

    def test_minimum_valid_password(self):
        valid, msg = validate_password_strength("Passw0rd")
        assert valid is True


class TestJWT:
    def test_create_and_decode_token(self):
        token = create_access_token(
            user_id=42,
            username="testuser",
            role=UserRole.STAFF.value,
            workshop_id=5,
        )
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["username"] == "testuser"
        assert payload["role"] == UserRole.STAFF.value
        assert payload["workshop_id"] == 5

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError):
            decode_access_token("this.is.not.a.valid.jwt")

    def test_tampered_token_raises(self):
        token = create_access_token(1, "user", UserRole.OWNER.value, 1)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError):
            decode_access_token(tampered)
