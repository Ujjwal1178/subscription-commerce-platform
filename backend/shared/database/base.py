"""
Shared Database Configuration

This module provides:
1. Base class for all SQLAlchemy models
2. Database session management
3. Common database utilities
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------------------------------------------------------
# Base Class
# -----------------------------------------------------------------------------
# All models inherit from this Base
# Example: class User(Base): ...
# -----------------------------------------------------------------------------
Base = declarative_base()


# -----------------------------------------------------------------------------
# Database Engine & Session Factory
# -----------------------------------------------------------------------------
def get_engine(database_url: str):
    """
    Create database engine.
    
    Args:
        database_url: PostgreSQL connection string
                     Format: postgresql://user:password@host:port/dbname
    
    Returns:
        SQLAlchemy Engine
    """
    return create_engine(
        database_url,
        pool_size=5,           # Connection pool size
        max_overflow=10,       # Extra connections when pool is full
        pool_pre_ping=True,    # Check connection health before using
    )


def get_session_factory(engine):
    """
    Create session factory for database operations.
    
    Returns:
        SessionLocal class to create sessions
    """
    return sessionmaker(
        autocommit=False,      # Manual commit required
        autoflush=False,       # Manual flush required
        bind=engine,
    )
