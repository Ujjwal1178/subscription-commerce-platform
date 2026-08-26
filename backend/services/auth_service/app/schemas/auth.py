"""
Auth Schemas - Request/Response validation for Auth APIs

Pydantic models for:
- Register
- Login  
- Verify OTP
- Refresh Token
- Forgot/Reset Password
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict


# =============================================================================
# BASE CLASSES - Shared configuration
# =============================================================================

class StrictRequest(BaseModel):
    """
    Base class for all request schemas.
    
    - extra='forbid': Reject requests with unknown fields
    - This prevents accidental data leakage and ensures API strictness
    """
    model_config = ConfigDict(extra='forbid')


class CleanResponse(BaseModel):
    """
    Base class for all response schemas.
    
    Responses will exclude None values when serialized.
    This keeps API responses clean without null fields.
    """
    
    def model_dump(self, **kwargs):
        """Override to exclude None by default."""
        kwargs.setdefault('exclude_none', True)
        return super().model_dump(**kwargs)


# =============================================================================
# REGISTER
# =============================================================================

class RegisterRequest(StrictRequest):
    """
    Request body for user registration.
    
    All fields required at registration.
    Optional fields (address, pincode, preferences) added via profile update.
    """
    
    user_name: str = Field(
        min_length=2, 
        max_length=100,
        description="User's full name",
        examples=["Ujjwal Thakur"]
    )
    
    email: EmailStr = Field(
        description="User's email address (must be unique)",
        examples=["ujjwal@gmail.com"]
    )
    
    phone_number: str = Field(
        min_length=10, 
        max_length=15,
        description="Phone number with country code",
        examples=["+919876543210"]
    )
    
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password with complexity requirements",
        examples=["Secret@123"]
    )
    
    # -------------------------------------------------------------------------
    # Custom Validators
    # -------------------------------------------------------------------------
    
    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Password must have:
        - At least 8 characters (handled by Field)
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        errors = []
        
        if not re.search(r'[A-Z]', v):
            errors.append("at least 1 uppercase letter")
        
        if not re.search(r'[a-z]', v):
            errors.append("at least 1 lowercase letter")
            
        if not re.search(r'\d', v):
            errors.append("at least 1 digit")
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("at least 1 special character (!@#$%^&*(),.?\":{}|<>)")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """
        Phone number validation:
        - Must start with + or digit
        - Only digits after country code
        """
        # Remove spaces and dashes for validation
        cleaned = re.sub(r'[\s\-]', '', v)
        
        # Check format: +91XXXXXXXXXX or 91XXXXXXXXXX or XXXXXXXXXX
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError("Invalid phone number format. Use: +919876543210")
        
        return cleaned  # Return cleaned version
    
    @field_validator('user_name')
    @classmethod
    def validate_user_name(cls, v: str) -> str:
        """
        User name validation:
        - Strip whitespace
        - No special characters except space
        """
        v = v.strip()
        
        if not re.match(r'^[a-zA-Z\s]+$', v):
            raise ValueError("Name can only contain letters and spaces")
        
        return v


class RegisterResponse(CleanResponse):
    """Response after successful registration."""
    
    success: bool = True
    message: str = "Registration successful. Please verify your email."
    otp_expires_in: int = Field(
        default=300,
        description="OTP validity in seconds"
    )
    masked_email: str = Field(
        description="Masked email for display",
        examples=["uj****@gmail.com"]
    )


# =============================================================================
# LOGIN
# =============================================================================

class LoginRequest(StrictRequest):
    """Request body for user login."""
    
    email: EmailStr = Field(
        description="Registered email address"
    )
    
    password: str = Field(
        min_length=1,  # Don't reveal password requirements on login
        description="User password"
    )
    
    device_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Human readable device name (e.g., 'Chrome on Windows', 'iPhone 15')"
    )


class LoginResponse(CleanResponse):
    """
    Response after login attempt.
    
    Two possible outcomes:
    1. Success: returns JWT tokens
    2. Email not verified: returns requires_otp=True with masked_email
    """
    
    success: bool
    message: str
    
    # Present on successful login
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None  # Access token validity in seconds
    user_name: Optional[str] = None
    
    # Present when email not verified (OTP required)
    requires_otp: Optional[bool] = None
    masked_email: Optional[str] = None
    otp_expires_in: Optional[int] = None  # OTP validity in seconds


# =============================================================================
# VERIFY OTP
# =============================================================================

class VerifyOTPRequest(StrictRequest):
    """
    Request body for OTP verification.
    
    Two modes:
    1. Only email: Get OTP status (for page reload scenario)
    2. Email + OTP: Verify the OTP
    """
    
    email: EmailStr = Field(
        description="Email to verify"
    )
    
    otp: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=6,
        description="6-digit OTP code"
    )
    
    device_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Device name for session (used after successful verification)"
    )
    
    @field_validator('otp')
    @classmethod
    def validate_otp_format(cls, v: Optional[str]) -> Optional[str]:
        """OTP must be 6 digits only."""
        if v is not None:
            if not v.isdigit():
                raise ValueError("OTP must contain only digits")
        return v


class VerifyOTPResponse(CleanResponse):
    """Response after OTP verification."""
    
    success: bool
    message: str
    is_verified: Optional[bool] = None
    
    # Only present on successful verification
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    
    # Only present on failure
    attempts_remaining: Optional[int] = None
    retry_after: Optional[int] = None  # Seconds until unblock


class OTPStatusResponse(CleanResponse):
    """Response for OTP status check (page reload scenario)."""
    
    success: bool = True
    message: str = "If registered, OTP is active. Please enter OTP."
    otp_expires_in: int = Field(
        description="Seconds until OTP expires"
    )
    masked_email: str = Field(
        description="Masked email for display"
    )


# =============================================================================
# RESEND OTP
# =============================================================================

class ResendOTPRequest(StrictRequest):
    """Request body for resending OTP."""
    
    email: EmailStr = Field(
        description="Email to resend OTP"
    )


class ResendOTPResponse(CleanResponse):
    """Response after OTP resend request."""
    
    success: bool
    message: str
    otp_expires_in: Optional[int] = None  # Seconds until OTP expires
    masked_email: Optional[str] = None
    can_resend_in: Optional[int] = None  # Cooldown before next resend (seconds)


# =============================================================================
# REFRESH TOKEN
# =============================================================================

class RefreshTokenRequest(StrictRequest):
    """Request body for token refresh."""
    
    refresh_token: str = Field(
        description="Valid refresh token"
    )


class RefreshTokenResponse(CleanResponse):
    """Response after successful token refresh."""
    
    success: bool = True
    message: str = "Token refreshed successfully"
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 420


# =============================================================================
# LOGOUT
# =============================================================================

class LogoutRequest(StrictRequest):
    """Request body for logout."""
    
    device_id: Optional[str] = Field(
        default=None,
        description="Specific device to logout. If not provided, logout all devices."
    )


class LogoutResponse(CleanResponse):
    """Response after successful logout."""
    
    success: bool = True
    message: str = "Logged out successfully"


# =============================================================================
# FORGOT PASSWORD (Step 1: Request OTP)
# =============================================================================

class ForgotPasswordRequest(StrictRequest):
    """Request body for forgot password - Step 1."""
    
    email: EmailStr = Field(
        description="Email to send reset OTP"
    )


class ForgotPasswordResponse(CleanResponse):
    """Response after forgot password request."""
    
    success: bool
    message: str
    
    # If email not verified, redirect to verify
    requires_email_verification: Optional[bool] = None
    masked_email: Optional[str] = None
    otp_expires_in: Optional[int] = None  # Seconds


# =============================================================================
# VERIFY RESET OTP (Step 2: Verify OTP, Get Temp Token)
# =============================================================================

class VerifyResetOTPRequest(StrictRequest):
    """Request body for verifying password reset OTP - Step 2."""
    
    email: EmailStr = Field(
        description="Email address"
    )
    
    otp: str = Field(
        min_length=6,
        max_length=6,
        description="6-digit OTP from email"
    )
    
    @field_validator('otp')
    @classmethod
    def validate_otp_format(cls, v: str) -> str:
        """OTP must be 6 digits only."""
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v


class VerifyResetOTPResponse(CleanResponse):
    """Response after successful OTP verification - returns temp token."""
    
    success: bool = True
    message: str = "OTP verified. You can now reset your password."
    reset_token: str = Field(
        description="Temporary token for password reset (valid 10 minutes)"
    )
    expires_in: int = Field(
        default=600,
        description="Token validity in seconds (10 minutes)"
    )


# =============================================================================
# RESET PASSWORD (Step 3: Set New Password)
# =============================================================================

class ResetPasswordRequest(StrictRequest):
    """Request body for password reset - Step 3."""
    
    reset_token: str = Field(
        description="Temporary reset token from verify-reset-otp"
    )
    
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Same password rules as registration."""
        errors = []
        
        if not re.search(r'[A-Z]', v):
            errors.append("at least 1 uppercase letter")
        
        if not re.search(r'[a-z]', v):
            errors.append("at least 1 lowercase letter")
            
        if not re.search(r'\d', v):
            errors.append("at least 1 digit")
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("at least 1 special character")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        
        return v


class ResetPasswordResponse(CleanResponse):
    """Response after successful password reset."""
    
    success: bool = True
    message: str = "Password reset successful. Please login with your new password."


# =============================================================================
# COMMON ERROR RESPONSE
# =============================================================================

class ErrorDetail(BaseModel):
    """Individual field error."""
    field: str
    message: str


class ErrorResponse(CleanResponse):
    """Standard error response format."""
    
    success: bool = False
    message: str
    error_code: Optional[str] = None  # Machine-readable error code
    errors: Optional[list[ErrorDetail]] = None  # For validation errors


# =============================================================================
# MESSAGE RESPONSE (Generic)
# =============================================================================

class MessageResponse(CleanResponse):
    """Generic success/failure response."""
    
    success: bool
    message: str
