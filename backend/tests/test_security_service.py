import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)


def test_password_hash_and_verify_roundtrip():
    plain_password = "pass-123456"
    hashed_password = get_password_hash(plain_password)

    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_access_token_contains_expected_claims():
    token = create_access_token({"sub": "1"})
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_refresh_token_verification():
    token = create_refresh_token({"sub": "2"})
    payload = await verify_refresh_token(token)

    assert payload is not None
    assert payload["sub"] == "2"
    assert payload["type"] == "refresh"
