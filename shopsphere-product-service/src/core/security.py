from typing import Any
import jwt
from src.config import settings
from src.core.exceptions import TokenExpiredException, InvalidTokenException

def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT using the shared secret key.
    Raises domain-specific exceptions on validation failure.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException("Authentication token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid authentication token signature or format")
