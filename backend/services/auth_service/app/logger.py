"""
Logger Configuration for Auth Service

Proper logging instead of print() statements.
- Development: Shows detailed logs including OTP
- Production: Minimal logs, no sensitive data
"""

import logging
import sys
import os

# Get config from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
IS_DEV_MODE = os.getenv("IS_DEV_MODE", "False").lower() == "true"
SERVICE_NAME = os.getenv("SERVICE_NAME", "auth-service")


def setup_logger(name: str = SERVICE_NAME) -> logging.Logger:
    """
    Create and configure logger.
    
    Args:
        name: Logger name (usually service name)
        
    Returns:
        Configured logger instance
        
    Usage:
        from app.logger import logger
        logger.info("User registered", extra={"user_id": "123"})
        logger.error("Failed to send OTP", exc_info=True)
    """
    
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Format based on environment
    if IS_DEV_MODE:
        # Development: Detailed, human-readable
        formatter = logging.Formatter(
            "\n%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d\n"
            "%(message)s\n"
        )
    else:
        # Production: JSON-like, machine-parseable
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"service": "%(name)s", "message": "%(message)s"}'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Create default logger instance
logger = setup_logger()


# =============================================================================
# HELPER FUNCTIONS FOR SENSITIVE DATA
# =============================================================================

def log_otp_generated(email: str, otp: str, user_id: str):
    """
    Log OTP generation.
    
    In DEV mode: Shows actual OTP (for testing)
    In PROD mode: Only logs that OTP was generated (no actual value)
    """
    masked_email = _mask_email(email)
    
    if IS_DEV_MODE:
        logger.info(
            f"[DEV] OTP Generated\n"
            f"  User ID: {user_id}\n"
            f"  Email: {masked_email}\n"
            f"  OTP: {otp}\n"
            f"  (OTP visible only in dev mode)"
        )
    else:
        logger.info(f"OTP generated for user {user_id}")


def log_user_registered(user_id: str, email: str):
    """Log successful user registration."""
    masked_email = _mask_email(email)
    logger.info(f"User registered: {user_id} ({masked_email})")


def log_login_attempt(email: str, success: bool, reason: str = None):
    """Log login attempt."""
    masked_email = _mask_email(email)
    if success:
        logger.info(f"Login successful: {masked_email}")
    else:
        logger.warning(f"Login failed: {masked_email} - {reason}")


def log_otp_verified(user_id: str, success: bool):
    """Log OTP verification attempt."""
    if success:
        logger.info(f"OTP verified successfully for user {user_id}")
    else:
        logger.warning(f"OTP verification failed for user {user_id}")


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _mask_email(email: str) -> str:
    """Mask email for logging. Example: ujjwal@gmail.com -> uj****@gmail.com"""
    if not email or '@' not in email:
        return '****'
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = local[0] + '****'
    else:
        masked_local = local[:2] + '****'
    
    return f"{masked_local}@{domain}"
