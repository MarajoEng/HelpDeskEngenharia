from datetime import timedelta

import pytest

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_and_verify_password_roundtrip() -> None:
    password_hash = hash_password("admin123")

    assert password_hash != "admin123"
    assert verify_password("admin123", password_hash) is True


def test_verify_password_rejects_invalid_password() -> None:
    password_hash = hash_password("admin123")

    assert verify_password("wrong-pass", password_hash) is False


def test_decode_access_token_returns_payload_for_valid_token() -> None:
    token = create_access_token("42", extra_claims={"role": "admin"})

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token("42", expires_delta=timedelta(minutes=-1))

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_access_token_rejects_malformed_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-real-token")
