from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenPayload

ALGORITHM = "HS256"


def decode_token(token: str) -> TokenPayload | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except (JWTError, Exception):
        return None
