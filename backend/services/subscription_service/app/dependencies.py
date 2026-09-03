"""FastAPI Dependencies - Database session and authentication injection."""

from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import sys

sys.path.append("/app")
from shared.utils.jwt import verify_access_token

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@postgres:5432/subscription_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# HTTPBearer extracts token from "Authorization: Bearer <token>" header
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """Yield database session, auto-close on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Verify access token and return user info (user_id, device_id, user_name)."""
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        return {
            "user_id": payload["user_id"],
            "device_id": payload.get("device_id"),
            "user_name": payload.get("user_name"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any] | None:
    """Optional auth - returns None if no token provided (for public endpoints)."""
    if credentials is None:
        return None
    
    try:
        payload = verify_access_token(credentials.credentials)
        return {
            "user_id": payload["user_id"],
            "device_id": payload.get("device_id"),
            "user_name": payload.get("user_name"),
        }
    except ValueError:
        return None
