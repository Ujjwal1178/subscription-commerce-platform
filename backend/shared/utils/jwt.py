"""JWT Utilities - Create and verify access, refresh, and password reset tokens."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError, ExpiredSignatureError

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-use-strong-random")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 7))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 120))


class TokenType:
    """Token type identifiers stored in JWT payload."""
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"


def create_access_token(user_id: str, user_name: str, device_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create short-lived access token (default 7 min) for API authentication."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "user_id": user_id,
        "user_name": user_name,
        "device_id": device_id,
        "type": TokenType.ACCESS,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, device_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create long-lived refresh token (default 2 hours) for getting new access tokens."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    payload = {
        "user_id": user_id,
        "device_id": device_id,
        "type": TokenType.REFRESH,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_password_reset_token(user_id: str, expires_minutes: int = 10) -> str:
    """Create temporary password reset token (default 10 min)."""
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "user_id": user_id,
        "type": TokenType.PASSWORD_RESET,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str, token_type: str) -> Dict[str, Any]:
    """Verify JWT signature, expiry, and type. Raises ValueError if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise ValueError(f"Invalid token type. Expected {token_type}")
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify access token. Returns payload with user_id, user_name, device_id."""
    return verify_token(token, TokenType.ACCESS)


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Verify refresh token. Returns payload with user_id, device_id."""
    return verify_token(token, TokenType.REFRESH)


def verify_password_reset_token(token: str) -> Dict[str, Any]:
    """Verify password reset token. Returns payload with user_id."""
    return verify_token(token, TokenType.PASSWORD_RESET)


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """Decode token WITHOUT verification. Use only for debugging."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_signature": False, "verify_exp": False})
    except JWTError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get expiry time from token (without verification)."""
    payload = decode_token_unsafe(token)
    return datetime.fromtimestamp(payload["exp"]) if payload and "exp" in payload else None


def is_token_expired(token: str) -> bool:
    """Check if token is expired."""
    expiry = get_token_expiry(token)
    return expiry is None or datetime.utcnow() > expiry
