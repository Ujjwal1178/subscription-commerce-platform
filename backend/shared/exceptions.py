"""
Custom Exceptions for Subscription Commerce Platform

Centralized exception definitions for consistent error handling across all microservices.

Usage:
    from shared.exceptions import AppException, ErrorCode
    
    raise AppException(
        message="Invalid credentials",
        error_code=ErrorCode.INVALID_CREDENTIALS,
        status_code=400
    )
"""

from enum import Enum
from typing import Optional, Any


# =============================================================================
# ERROR CODES - Enum for type safety
# =============================================================================

class ErrorCode(str, Enum):
    """
    Standardized error codes for frontend logic.
    
    Frontend can switch on these codes for specific behaviors:
    - RATE_LIMITED → Show countdown timer
    - EMAIL_NOT_VERIFIED → Redirect to OTP page
    - SESSION_EXPIRED → Redirect to login
    
    Using Enum instead of strings:
    - IDE autocomplete
    - Typo prevention
    - Easy to find all error codes in one place
    """
    
    # -------------------------------------------------------------------------
    # Authentication Errors (AUTH_*)
    # -------------------------------------------------------------------------
    INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    EMAIL_NOT_VERIFIED = "AUTH_EMAIL_NOT_VERIFIED"
    ACCOUNT_DISABLED = "AUTH_ACCOUNT_DISABLED"
    SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    DEVICE_MISMATCH = "AUTH_DEVICE_MISMATCH"
    
    # -------------------------------------------------------------------------
    # OTP Errors (OTP_*)
    # -------------------------------------------------------------------------
    OTP_INVALID = "OTP_INVALID"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_MAX_ATTEMPTS = "OTP_MAX_ATTEMPTS"
    
    # -------------------------------------------------------------------------
    # Rate Limiting (RATE_*)
    # -------------------------------------------------------------------------
    RATE_LIMITED = "RATE_LIMITED"
    
    # -------------------------------------------------------------------------
    # User Errors (USER_*)
    # -------------------------------------------------------------------------
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    EMAIL_ALREADY_REGISTERED = "USER_EMAIL_ALREADY_REGISTERED"
    
    # -------------------------------------------------------------------------
    # Validation Errors (VALIDATION_*)
    # -------------------------------------------------------------------------
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "VALIDATION_INVALID_INPUT"
    
    # -------------------------------------------------------------------------
    # Server Errors (SERVER_*)
    # -------------------------------------------------------------------------
    INTERNAL_ERROR = "SERVER_INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVER_SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "SERVER_DATABASE_ERROR"


# =============================================================================
# BASE EXCEPTION
# =============================================================================

class AppException(Exception):
    """
    Base exception for all application errors.
    
    Attributes:
        message: Human-readable error message (shown to user)
        error_code: Machine-readable code (for frontend logic)
        status_code: HTTP status code
        details: Additional context (optional)
    
    Example:
        raise AppException(
            message="Too many login attempts. Try again in 60 seconds.",
            error_code=ErrorCode.RATE_LIMITED,
            status_code=429,
            details={"retry_after": 60}
        )
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode | str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code.value if isinstance(error_code, ErrorCode) else error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to response dictionary."""
        response = {
            "success": False,
            "message": self.message,
            "error_code": self.error_code,
        }
        
        # Add details if present
        if self.details:
            response.update(self.details)
        
        return response


# =============================================================================
# SPECIFIC EXCEPTIONS (Optional - for cleaner code)
# =============================================================================

class AuthenticationError(AppException):
    """Authentication related errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details
        )


class RateLimitError(AppException):
    """Rate limiting errors."""
    
    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: int = 60
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMITED,
            status_code=429,
            details={"retry_after": retry_after}
        )


class ValidationError(AppException):
    """Input validation errors."""
    
    def __init__(
        self,
        message: str = "Invalid input",
        field_errors: Optional[list[dict]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details={"errors": field_errors} if field_errors else None
        )


class NotFoundError(AppException):
    """Resource not found errors."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: ErrorCode = ErrorCode.USER_NOT_FOUND
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404
        )


class ConflictError(AppException):
    """Resource conflict errors (duplicate, etc.)."""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        error_code: ErrorCode = ErrorCode.USER_ALREADY_EXISTS
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=409
        )
