"""
Auth Service Schemas

Export all Pydantic models for easy importing.
"""

from .auth import (
    # Register
    RegisterRequest,
    RegisterResponse,
    
    # Login
    LoginRequest,
    LoginResponse,
    
    # Verify OTP
    VerifyOTPRequest,
    VerifyOTPResponse,
    OTPStatusResponse,
    
    # Refresh Token
    RefreshTokenRequest,
    RefreshTokenResponse,
    
    # Logout
    LogoutRequest,
    LogoutResponse,
    
    # Forgot Password
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    
    # Reset Password
    ResetPasswordRequest,
    ResetPasswordResponse,
    
    # Common
    ErrorDetail,
    ErrorResponse,
    MessageResponse,
)

from .user import (
    UserProfile,
    GetProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest", 
    "LoginResponse",
    "VerifyOTPRequest",
    "VerifyOTPResponse",
    "OTPStatusResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "LogoutResponse",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "ErrorDetail",
    "ErrorResponse",
    "MessageResponse",
    
    # User
    "UserProfile",
    "GetProfileResponse",
    "UpdateProfileRequest",
    "UpdateProfileResponse",
]
