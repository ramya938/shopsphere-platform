from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import jwt
from src.config import settings
from src.core.exceptions import TokenExpiredException, InvalidTokenException

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError, AttributeError):
        return False

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of the plain text password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

import uuid

def create_access_token(subject: str | Any, role: str | None = None, expires_delta: timedelta | None = None) -> str:
    """Generate an Access JWT."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    if role:
        to_encode["role"] = str(role)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Generate a Refresh JWT."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises domain-specific exceptions on failure."""
    try:
        return jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid token signature or format")
