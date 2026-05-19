"""Unit tests for shared utilities."""

import pytest
from shared.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False


class TestJWT:
    def test_create_and_decode_access_token(self):
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        data = {"sub": "user-456"}
        token = create_refresh_token(data)
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user-456"
        assert decoded["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        result = decode_token("invalid.token.here")
        assert result is None
