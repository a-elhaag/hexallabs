from __future__ import annotations

import uuid

from pydantic import BaseModel


class AuthUser(BaseModel):
    id: uuid.UUID
    email: str
