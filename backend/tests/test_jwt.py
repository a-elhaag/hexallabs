from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import jwt as auth_jwt
from app.auth.jwt import InvalidTokenError, verify_supabase_jwt


@dataclass
class _Keypair:
    private_pem: bytes
    public_key: object
    kid: str


def _make_keypair() -> _Keypair:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return _Keypair(private_pem=pem, public_key=key.public_key(), kid="test-kid")


def _mint(payload: dict[str, object], kp: _Keypair) -> str:
    return jwt.encode(payload, kp.private_pem, algorithm="RS256", headers={"kid": kp.kid})


class _FakeSigningKey:
    def __init__(self, public_key: object) -> None:
        self.key = public_key


class _FakeJWKClient:
    def __init__(self, public_key: object) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, _token: str) -> _FakeSigningKey:
        return _FakeSigningKey(self._public_key)


@pytest.fixture(autouse=True)
def _patch_jwks(monkeypatch: pytest.MonkeyPatch) -> _Keypair:
    kp = _make_keypair()
    auth_jwt._jwks_client.cache_clear()
    monkeypatch.setattr(auth_jwt, "_jwks_client", lambda _url: _FakeJWKClient(kp.public_key))
    return kp


def _base_claims() -> dict[str, object]:
    now = int(time.time())
    return {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "aud": "authenticated",
        "iss": "https://test.supabase.co/auth/v1",
        "iat": now,
        "exp": now + 60,
    }


def test_verify_accepts_valid_token(_patch_jwks: _Keypair) -> None:
    claims = _base_claims()
    token = _mint(claims, _patch_jwks)
    decoded = verify_supabase_jwt(token)
    assert decoded["sub"] == claims["sub"]
    assert decoded["email"] == claims["email"]


def test_verify_rejects_expired(_patch_jwks: _Keypair) -> None:
    claims = _base_claims()
    claims["exp"] = int(time.time()) - 10
    claims["iat"] = int(time.time()) - 120
    token = _mint(claims, _patch_jwks)
    with pytest.raises(InvalidTokenError):
        verify_supabase_jwt(token)


def test_verify_rejects_wrong_audience(_patch_jwks: _Keypair) -> None:
    claims = _base_claims()
    claims["aud"] = "service_role"
    token = _mint(claims, _patch_jwks)
    with pytest.raises(InvalidTokenError):
        verify_supabase_jwt(token)


def test_verify_rejects_wrong_issuer(_patch_jwks: _Keypair) -> None:
    claims = _base_claims()
    claims["iss"] = "https://malicious.example.com/auth/v1"
    token = _mint(claims, _patch_jwks)
    with pytest.raises(InvalidTokenError):
        verify_supabase_jwt(token)
