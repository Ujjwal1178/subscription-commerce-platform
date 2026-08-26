"""
JWT (JSON Web Token) Utility

Handles:
- Access token creation & verification
- Refresh token creation & verification

JWT Structure:
    Header.Payload.Signature
    
    Header: {"alg": "HS256", "typ": "JWT"}
    Payload: {"user_id": "...", "device_id": "...", "exp": ...}
    Signature: HMAC(Header.Payload, SECRET_KEY)

Security:
- Signature prevents tampering (can't modify without SECRET)
- Payload is NOT encrypted (just Base64) - don't store sensitive data!
- Short expiry for access tokens limits damage if stolen

Usage:
    from shared.utils.jwt import create_access_token, verify_token
    
    # Create token
    token = create_access_token(
        user_id="uuid-123",
        user_name="Ujjwal",
        device_id="device-456"
    )
    
    # Verify token
    payload = verify_token(token, token_type="access")
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

# python-jose library for JWT
# Why jose? Battle-tested, supports multiple algorithms, good error handling
from jose import jwt, JWTError, ExpiredSignatureError


# =============================================================================
# CONFIGURATION (from environment)
# =============================================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", 
    "dev-jwt-secret-key-change-in-production-use-strong-random"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Token expiry times (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 7))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 120))  # 2 hours


# =============================================================================
# TOKEN TYPES
# =============================================================================

class TokenType:
    """
    Token type identifiers.
    
    Stored in JWT payload to distinguish between access and refresh tokens.
    Prevents using refresh token as access token!
    """
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"  # Temp token for password reset


# =============================================================================
# TOKEN CREATION
# =============================================================================

def create_access_token(
    user_id: str,
    user_name: str,
    device_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create an access token.
    
    Access Token:
    - Short lived (7 minutes default)
    - Used for API authentication
    - Contains: user_id, user_name, device_id
    - Sent with every API request in Authorization header
    
    Args:
        user_id: User's UUID (as string)
        user_name: User's display name
        device_id: Device/session identifier
        expires_delta: Custom expiry time (optional)
        
    Returns:
        JWT token string
        
    Example:
        token = create_access_token(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            user_name="Ujjwal Thakur",
            device_id="device-123"
        )
        # Returns: "eyJhbGciOiJIUzI1NiI..."
    """
    # Set expiry time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Build payload
    # Note: We DON'T include email (PII) - can be decoded by anyone!
    payload = {
        "user_id": user_id,
        "user_name": user_name,
        "device_id": device_id,
        "type": TokenType.ACCESS,  # Mark as access token
        "exp": expire,  # Expiry time
        "iat": datetime.utcnow(),  # Issued at time
    }
    
    # Create JWT
    # jwt.encode(payload, secret, algorithm) -> token string
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token


def create_refresh_token(
    user_id: str,
    device_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a refresh token.
    
    Refresh Token:
    - Long lived (2 hours default)
    - Used ONLY to get new access tokens
    - Contains: user_id, device_id (minimal data)
    - Stored in HttpOnly cookie (frontend)
    
    Args:
        user_id: User's UUID (as string)
        device_id: Device/session identifier
        expires_delta: Custom expiry time (optional)
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    # Minimal payload for refresh token
    # No user_name needed - we'll fetch fresh data on refresh
    payload = {
        "user_id": user_id,
        "device_id": device_id,
        "type": TokenType.REFRESH,  # Mark as refresh token
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token


def create_password_reset_token(
    user_id: str,
    expires_minutes: int = 10
) -> str:
    """
    Create a temporary token for password reset.
    
    Password Reset Token:
    - Short lived (10 minutes default)
    - Used ONLY for reset-password endpoint
    - Contains: user_id only (minimal data)
    - One-time use (invalidated after password change)
    
    Args:
        user_id: User's UUID (as string)
        expires_minutes: Token validity in minutes (default 10)
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    payload = {
        "user_id": user_id,
        "type": TokenType.PASSWORD_RESET,  # Restricted token type
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token


# =============================================================================
# TOKEN VERIFICATION
# =============================================================================

def verify_token(token: str, token_type: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Verification Steps:
    1. Decode token using SECRET_KEY
    2. Verify signature (tamper detection)
    3. Check expiry (not expired)
    4. Validate token type (access vs refresh)
    
    Args:
        token: JWT token string
        token_type: Expected type (TokenType.ACCESS or TokenType.REFRESH)
        
    Returns:
        Decoded payload dict
        
    Raises:
        ValueError: Invalid token, expired, wrong type, etc.
        
    Example:
        try:
            payload = verify_token(token, TokenType.ACCESS)
            user_id = payload["user_id"]
        except ValueError as e:
            print(f"Invalid token: {e}")
    """
    try:
        # Decode and verify signature
        # jwt.decode() does:
        # 1. Split token into header.payload.signature
        # 2. Recalculate signature using SECRET_KEY
        # 3. Compare with received signature
        # 4. If match, return decoded payload
        # 5. If mismatch or expired, raise exception
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        
        # Validate token type
        # Prevents using refresh token as access token!
        if payload.get("type") != token_type:
            raise ValueError(f"Invalid token type. Expected {token_type}")
        
        return payload
        
    except ExpiredSignatureError:
        # Token has expired (exp < current time)
        raise ValueError("Token has expired")
        
    except JWTError as e:
        # Any other JWT error (invalid signature, malformed, etc.)
        raise ValueError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Convenience function to verify access token.
    
    Returns:
        Payload with: user_id, user_name, device_id, type, exp, iat
    """
    return verify_token(token, TokenType.ACCESS)


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Convenience function to verify refresh token.
    
    Returns:
        Payload with: user_id, device_id, type, exp, iat
    """
    return verify_token(token, TokenType.REFRESH)


def verify_password_reset_token(token: str) -> Dict[str, Any]:
    """
    Verify password reset token.
    
    Returns:
        Payload with: user_id, type, exp, iat
        
    Raises:
        ValueError: If token is invalid, expired, or wrong type
    """
    return verify_token(token, TokenType.PASSWORD_RESET)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode token WITHOUT verification.
    
    WARNING: This does NOT verify the signature!
    Use ONLY for debugging or extracting claims from expired tokens.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid format
    """
    try:
        # options={"verify_signature": False} skips signature check
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except JWTError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get expiry time from token (without full verification).
    
    Useful for frontend to know when to refresh.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiry datetime or None
    """
    payload = decode_token_unsafe(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired.
    
    Args:
        token: JWT token string
        
    Returns:
        True if expired, False if valid
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True
    return datetime.utcnow() > expiry
