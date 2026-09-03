"""Subscription Service Configuration - All configurable values from environment."""

import os

# App Mode
IS_DEV_MODE = os.getenv("IS_DEV_MODE", "False").lower() == "true"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database - Separate DB for subscription service (microservice pattern)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://postgres:postgres@postgres:5432/subscription_db"
)

# JWT Configuration (for validating tokens from Auth Service)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Subscription Configuration
DEFAULT_PLAN_NAME = os.getenv("DEFAULT_PLAN_NAME", "Free")
TRIAL_PERIOD_DAYS = int(os.getenv("TRIAL_PERIOD_DAYS", 7))
GRACE_PERIOD_DAYS = int(os.getenv("GRACE_PERIOD_DAYS", 3))

# Payment Provider (Stripe)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxxxx")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxxxx")

# Rate Limiting
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", 100))
API_RATE_WINDOW = int(os.getenv("API_RATE_WINDOW", 60))

# Service Info
SERVICE_NAME = "subscription-service"
SERVICE_VERSION = "1.0.0"
