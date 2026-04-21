from __future__ import annotations

import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import jwt as auth_jwt
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser


def _keypair() -> tuple[bytes, object]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem, key.public_key()


class _FakeSigningKey:
    def __init__(self, public_key: object) -> None:
        self.key = public_key


class _FakeJWKClient:
    def __init__(self, public_key: object) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, _token: str):
        return _FakeSigningKey(self._public_key)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, bytes]:
    pem, public = _keypair()
    auth_jwt._jwks_client.cache_clear()
    monkeypatch.setattr(auth_jwt, "_jwks_client", lambda _url: _FakeJWKClient(public))

    app = FastAPI()

    @app.get("/me")
    def me(user: AuthUser = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(user.id), "email": user.email}

    return TestClient(app), pem


def _mint(pem: bytes, **overrides: object) -> str:
    now = int(time.time())
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "aud": "authenticated",
        "iss": "https://test.supabase.co/auth/v1",
        "iat": now,
        "exp": now + 60,
    }
    claims.update(overrides)
    return jwt.encode(claims, pem, algorithm="RS256", headers={"kid": "test-kid"})


def test_valid_token_populates_user(client: tuple[TestClient, bytes]) -> None:
    c, pem = client
    uid = str(uuid.uuid4())
    token = _mint(pem, sub=uid)
    r = c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == {"id": uid, "email": "user@example.com"}


def test_missing_header_returns_401(client: tuple[TestClient, bytes]) -> None:
    c, _ = client
    r = c.get("/me")
    assert r.status_code == 401


def test_invalid_token_returns_401(client: tuple[TestClient, bytes]) -> None:
    c, _ = client
    r = c.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_non_uuid_sub_returns_401(client: tuple[TestClient, bytes]) -> None:
    c, pem = client
    token = _mint(pem, sub="not-a-uuid")
    r = c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
