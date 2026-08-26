"""
FastAPI Dependencies

Dependencies are functions that run BEFORE your endpoint.
Used for: Database sessions, authentication, rate limiting, etc.

How it works:
1. Request comes to /register
2. FastAPI sees: def register(db: Session = Depends(get_db))
3. FastAPI calls get_db() first
4. get_db() creates database session, yields it
5. Your endpoint runs with that session
6. After endpoint, get_db() cleanup runs (session closed)
"""

from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import sys

# For shared imports
sys.path.append("/app")
from shared.utils.jwt import verify_access_token
from shared.exceptions import AppException, ErrorCode

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@postgres:5432/auth_db"
)

# Create engine (connection pool to database)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Keep 5 connections ready
    max_overflow=10,       # Allow 10 more if needed
    pool_pre_ping=True,    # Check connection health before using
)

# Session factory - creates new sessions
SessionLocal = sessionmaker(
    autocommit=False,      # Manual commit required
    autoflush=False,       # Manual flush required  
    bind=engine,
)


# =============================================================================
# DATABASE DEPENDENCY
# =============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    
    Usage in endpoint:
        @router.post("/register")
        def register(db: Session = Depends(get_db)):
            # db is ready to use!
            user = db.query(User).first()
    
    How it works:
        1. Creates new session
        2. Yields it to endpoint (endpoint uses it)
        3. After endpoint: closes session (cleanup)
        4. If error: session is still closed (finally block)
    """
    db = SessionLocal()
    try:
        yield db      # Endpoint runs here with db session
    finally:
        db.close()    # Always cleanup, even if error


# =============================================================================
# AUTHENTICATION DEPENDENCY
# =============================================================================

# HTTPBearer extracts token from "Authorization: Bearer <token>" header
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Verify access token and return user info.
    
    Usage in protected endpoint:
        @router.post("/logout")
        def logout(current_user: dict = Depends(get_current_user)):
            user_id = current_user["user_id"]
            device_id = current_user["device_id"]
    
    Flow:
        1. Extract token from Authorization header
        2. Verify JWT signature and expiry
        3. Return payload (user_id, device_id, user_name)
    
    Raises:
        HTTPException 401: Invalid or expired token
    """
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        return {
            "user_id": payload["user_id"],
            "device_id": payload["device_id"],
            "user_name": payload.get("user_name"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
