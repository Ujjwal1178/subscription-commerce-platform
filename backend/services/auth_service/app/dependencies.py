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

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

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
