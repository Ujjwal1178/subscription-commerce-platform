"""
Alembic Environment Configuration

This file configures Alembic for database migrations.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our models and Base
from shared.database.base import Base
from app.models import User, UserSession, OTPVerification

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------------------------------------------------------
# IMPORTANT: Set target_metadata to our Base.metadata
# This enables 'autogenerate' - Alembic reads our models and creates migrations
# -----------------------------------------------------------------------------
target_metadata = Base.metadata

# -----------------------------------------------------------------------------
# Get database URL from environment variable
# -----------------------------------------------------------------------------
def get_url():
    """Get database URL from environment."""
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@postgres:5432/auth_db"
    )
    # Ensure we use psycopg (v3) driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This generates SQL without connecting to database.
    Useful for generating migration scripts to run manually.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Connects to database and runs migrations directly.
    """
    # Override sqlalchemy.url with our environment variable
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
