from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.config import Settings, get_settings


class InvalidTokenError(Exception):
    """Raised when a Supabase JWT fails verification."""


_ALGORITHMS = ("RS256", "ES256")


@lru_cache(maxsize=1)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    # PyJWKClient caches fetched keys internally and refreshes on kid miss.
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def verify_supabase_jwt(
    token: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    s = settings or get_settings()
    client = _jwks_client(s.supabase_jwks_url)
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=list(_ALGORITHMS),
            audience=s.supabase_jwt_audience,
            issuer=s.supabase_jwt_issuer,
            options={"require": ["exp", "iat", "sub", "aud"]},
        )
    except jwt.PyJWTError as e:
        raise InvalidTokenError(str(e)) from e
