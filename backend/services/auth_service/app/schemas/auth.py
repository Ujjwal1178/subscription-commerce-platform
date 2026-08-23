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
from pydantic import BaseModel, Field, EmailStr, field_validator


# =============================================================================
# REGISTER
# =============================================================================

class RegisterRequest(BaseModel):
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


class RegisterResponse(BaseModel):
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

class LoginRequest(BaseModel):
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
        description="Device name for session tracking",
        examples=["Chrome on Windows", "iPhone 15"]
    )


class LoginResponse(BaseModel):
    """Response after successful login."""
    
    success: bool = True
    message: str = "Login successful"
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(
        default=420,
        description="Access token validity in seconds (7 minutes)"
    )


# =============================================================================
# VERIFY OTP
# =============================================================================

class VerifyOTPRequest(BaseModel):
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


class VerifyOTPResponse(BaseModel):
    """Response after OTP verification."""
    
    success: bool
    message: str
    
    # Only present on successful verification
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    
    # Only present on failure
    attempts_remaining: Optional[int] = None
    retry_after: Optional[int] = None  # Seconds until unblock


class OTPStatusResponse(BaseModel):
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
# REFRESH TOKEN
# =============================================================================

class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    
    refresh_token: str = Field(
        description="Valid refresh token"
    )


class RefreshTokenResponse(BaseModel):
    """Response after successful token refresh."""
    
    success: bool = True
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 420


# =============================================================================
# LOGOUT
# =============================================================================

class LogoutRequest(BaseModel):
    """Request body for logout."""
    
    device_id: Optional[str] = Field(
        default=None,
        description="Specific device to logout. If not provided, logout all devices."
    )


class LogoutResponse(BaseModel):
    """Response after successful logout."""
    
    success: bool = True
    message: str = "Logged out successfully"


# =============================================================================
# FORGOT PASSWORD
# =============================================================================

class ForgotPasswordRequest(BaseModel):
    """Request body for forgot password."""
    
    email: EmailStr = Field(
        description="Email to send reset OTP"
    )


class ForgotPasswordResponse(BaseModel):
    """Response after forgot password request."""
    
    success: bool = True
    message: str = "If email exists, OTP has been sent"
    # Note: Same response whether email exists or not (prevent enumeration)


# =============================================================================
# RESET PASSWORD
# =============================================================================

class ResetPasswordRequest(BaseModel):
    """Request body for password reset."""
    
    email: EmailStr = Field(
        description="Email address"
    )
    
    otp: str = Field(
        min_length=6,
        max_length=6,
        description="6-digit OTP from email"
    )
    
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password"
    )
    
    device_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Device name for new session"
    )
    
    @field_validator('otp')
    @classmethod
    def validate_otp_format(cls, v: str) -> str:
        """OTP must be 6 digits only."""
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v
    
    # Reuse password validation from RegisterRequest
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


class ResetPasswordResponse(BaseModel):
    """Response after successful password reset."""
    
    success: bool = True
    message: str = "Password reset successful"
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 420


# =============================================================================
# COMMON ERROR RESPONSE
# =============================================================================

class ErrorDetail(BaseModel):
    """Individual field error."""
    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    success: bool = False
    message: str
    errors: Optional[list[ErrorDetail]] = None  # For validation errors


# =============================================================================
# MESSAGE RESPONSE (Generic)
# =============================================================================

class MessageResponse(BaseModel):
    """Generic success/failure response."""
    
    success: bool
    message: str
