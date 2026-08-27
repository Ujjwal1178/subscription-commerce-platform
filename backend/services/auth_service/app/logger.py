"""Logger Configuration - Proper logging with DEV/PROD modes."""

import logging
import sys
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
IS_DEV_MODE = os.getenv("IS_DEV_MODE", "False").lower() == "true"
SERVICE_NAME = os.getenv("SERVICE_NAME", "auth-service")


def setup_logger(name: str = SERVICE_NAME) -> logging.Logger:
    """Create and configure logger instance."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    if IS_DEV_MODE:
        formatter = logging.Formatter(
            "\n%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d\n%(message)s\n"
        )
    else:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": "%(message)s"}'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


def log_otp_generated(email: str, otp: str, user_id: str):
    """Log OTP - shows actual OTP only in dev mode."""
    masked_email = _mask_email(email)
    
    if IS_DEV_MODE:
        logger.info(f"[DEV] OTP Generated | User: {user_id} | Email: {masked_email} | OTP: {otp}")
    else:
        logger.info(f"OTP generated for user {user_id}")


def log_user_registered(user_id: str, email: str):
    """Log successful user registration."""
    logger.info(f"User registered: {user_id} ({_mask_email(email)})")


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


def _mask_email(email: str) -> str:
    """Mask email for logging. Example: ujjwal@gmail.com -> uj****@gmail.com"""
    if not email or '@' not in email:
        return '****'
    
    local, domain = email.split('@', 1)
    masked_local = local[:2] + '****' if len(local) > 2 else local[0] + '****'
    return f"{masked_local}@{domain}"
