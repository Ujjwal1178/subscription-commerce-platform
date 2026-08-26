"""
Auth Service Configuration

All configurable values in one place.
Values come from environment variables.

In Docker: docker-compose injects from backend/.env
Locally: Set env vars or use python-dotenv
"""

import os


# =============================================================================
# APP MODE
# =============================================================================

IS_DEV_MODE = os.getenv("IS_DEV_MODE", "False").lower() == "true"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# =============================================================================
# OTP CONFIGURATION
# =============================================================================

OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", 10))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 3))
OTP_BLOCK_MINUTES = int(os.getenv("OTP_BLOCK_MINUTES", 20))
OTP_LENGTH = int(os.getenv("OTP_LENGTH", 6))


# =============================================================================
# JWT CONFIGURATION
# =============================================================================

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 7))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 120))  # 2 hours
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


# =============================================================================
# RATE LIMITING (Redis-based)
# =============================================================================

# Login: 10 attempts per minute
LOGIN_RATE_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", 10))
LOGIN_RATE_WINDOW = int(os.getenv("LOGIN_RATE_WINDOW", 60))  # seconds

# OTP Verify: 5 attempts per minute
OTP_VERIFY_RATE_LIMIT = int(os.getenv("OTP_VERIFY_RATE_LIMIT", 5))
OTP_VERIFY_RATE_WINDOW = int(os.getenv("OTP_VERIFY_RATE_WINDOW", 60))  # seconds

# OTP Resend: 3 attempts per 10 minutes
OTP_RESEND_RATE_LIMIT = int(os.getenv("OTP_RESEND_RATE_LIMIT", 3))
OTP_RESEND_RATE_WINDOW = int(os.getenv("OTP_RESEND_RATE_WINDOW", 600))  # 10 minutes

# OTP Resend Cooldown: Minimum 60 seconds between resends
OTP_RESEND_COOLDOWN = int(os.getenv("OTP_RESEND_COOLDOWN", 60))  # seconds


# =============================================================================
# DATABASE
# =============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://postgres:postgres@postgres:5432/auth_db"
)


# =============================================================================
# SERVICE INFO
# =============================================================================

SERVICE_NAME = "auth-service"
SERVICE_VERSION = "1.0.0"
