from __future__ import annotations

import uuid

from app.auth.models import AuthUser


_MOCK_USER_ID = uuid.UUID("ea7509a1-0c0c-45c7-9f5c-db45aedf3fd7")

def mock_get_current_user(user_id: str | None = None, email: str | None = None) -> AuthUser:
    """Return mock AuthUser for testing (no JWT validation). Uses fixed test user."""
    return AuthUser(
        id=uuid.UUID(user_id) if user_id else _MOCK_USER_ID,
        email=email or "test@example.com",
    )
