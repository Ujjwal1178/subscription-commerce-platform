"""Custom Exceptions - Centralized error handling across all microservices."""

from enum import Enum
from typing import Optional, Any


class ErrorCode(str, Enum):
    """Standardized error codes for frontend logic."""
    
    # Authentication Errors
    INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    EMAIL_NOT_VERIFIED = "AUTH_EMAIL_NOT_VERIFIED"
    ACCOUNT_DISABLED = "AUTH_ACCOUNT_DISABLED"
    SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    DEVICE_MISMATCH = "AUTH_DEVICE_MISMATCH"
    
    # OTP Errors
    OTP_INVALID = "OTP_INVALID"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_MAX_ATTEMPTS = "OTP_MAX_ATTEMPTS"
    
    # Rate Limiting
    RATE_LIMITED = "RATE_LIMITED"
    
    # User Errors
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    EMAIL_ALREADY_REGISTERED = "USER_EMAIL_ALREADY_REGISTERED"
    USER_INACTIVE = "USER_INACTIVE"
    
    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "VALIDATION_INVALID_INPUT"
    
    # Server Errors
    INTERNAL_ERROR = "SERVER_INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVER_SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "SERVER_DATABASE_ERROR"


class AppException(Exception):
    """Base exception for all application errors."""
    
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
        response = {"success": False, "message": self.message, "error_code": self.error_code}
        if self.details:
            response.update(self.details)
        return response


class AuthenticationError(AppException):
    """Authentication related errors."""
    def __init__(self, message: str = "Authentication failed", error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS, details: Optional[dict] = None):
        super().__init__(message=message, error_code=error_code, status_code=401, details=details)


class RateLimitError(AppException):
    """Rate limiting errors."""
    def __init__(self, message: str = "Too many requests", retry_after: int = 60):
        super().__init__(message=message, error_code=ErrorCode.RATE_LIMITED, status_code=429, details={"retry_after": retry_after})


class ValidationError(AppException):
    """Input validation errors."""
    def __init__(self, message: str = "Invalid input", field_errors: Optional[list[dict]] = None):
        super().__init__(message=message, error_code=ErrorCode.VALIDATION_ERROR, status_code=422, details={"errors": field_errors} if field_errors else None)


class NotFoundError(AppException):
    """Resource not found errors."""
    def __init__(self, message: str = "Resource not found", error_code: ErrorCode = ErrorCode.USER_NOT_FOUND):
        super().__init__(message=message, error_code=error_code, status_code=404)


class ConflictError(AppException):
    """Resource conflict errors (duplicate, etc.)."""
    def __init__(self, message: str = "Resource already exists", error_code: ErrorCode = ErrorCode.USER_ALREADY_EXISTS):
        super().__init__(message=message, error_code=error_code, status_code=409)
