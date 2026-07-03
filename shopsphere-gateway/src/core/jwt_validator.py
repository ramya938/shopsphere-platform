import jwt
from src.config import settings

def validate_jwt(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Returns the payload if valid. Raises jwt.PyJWTError on failure.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["sub", "role", "exp"]}
    )
    return payload

def get_auth_token(auth_header: str | None) -> str | None:
    """Extracts bearer token from raw Authorization header string."""
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
        
    return parts[1]
