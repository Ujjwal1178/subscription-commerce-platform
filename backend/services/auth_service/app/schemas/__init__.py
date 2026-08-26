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
    
    # Resend OTP
    ResendOTPRequest,
    ResendOTPResponse,
    
    # Refresh Token
    RefreshTokenRequest,
    RefreshTokenResponse,
    
    # Logout
    LogoutRequest,
    LogoutResponse,
    
    # Forgot Password (3-step flow)
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
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
    "ResendOTPRequest",
    "ResendOTPResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "LogoutResponse",
    
    # Forgot Password (3-step flow)
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "VerifyResetOTPRequest",
    "VerifyResetOTPResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    
    # Common
    "ErrorDetail",
    "ErrorResponse",
    "MessageResponse",
    
    # User
    "UserProfile",
    "GetProfileResponse",
    "UpdateProfileRequest",
    "UpdateProfileResponse",
]
