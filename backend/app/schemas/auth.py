from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str          # user id
    email: str | None = None
    name: str | None = None
    exp: int | None = None
