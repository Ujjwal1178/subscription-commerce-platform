"""
Auth API Routes

Endpoints:
- POST /register - Create new user account
- POST /verify-otp - Verify email with OTP
- POST /login - Authenticate and get tokens
- POST /refresh - Refresh access token (coming soon)
- POST /logout - End session (coming soon)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Dependencies
from app.dependencies import get_db, get_current_user

# Schemas (request/response validation)
from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    LoginRequest,
    LoginResponse,
    ResendOTPRequest,
    ResendOTPResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ErrorResponse,
    GetProfileResponse,
    UserProfile,
)

# Service (business logic)
from app.services import AuthService

# Logger
from app.logger import logger

# Custom Exceptions (now we use these instead of HTTPException!)
import sys
sys.path.append("/app")
from shared.exceptions import AppException, ErrorCode


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(
    prefix="/api/v1/auth",    # All routes start with /api/v1/auth
    tags=["Authentication"],   # Swagger UI grouping
)


# =============================================================================
# REGISTER ENDPOINT
# =============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Validation error", "model": ErrorResponse},
        409: {"description": "Email already registered", "model": ErrorResponse},
    },
    summary="Register new user",
    description="""
    Create a new user account.
    
    **Flow:**
    1. Validates input (email format, password strength)
    2. Checks if email already exists
    3. Creates user with hashed password
    4. Generates OTP and sends to email
    5. Returns success with masked email
    
    **Note:** User must verify OTP before they can login.
    """,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    """
    Register a new user.
    
    Args:
        data: RegisterRequest with user_name, email, phone_number, password
        db: Database session (injected by FastAPI)
        
    Returns:
        RegisterResponse with success message and OTP expiry time
        
    Raises:
        HTTPException 409: If email already registered
        HTTPException 400: If validation fails
    """
    
    # Create service instance with db session
    auth_service = AuthService(db)
    
    # Service layer raises AppException - handler catches it automatically!
    result = auth_service.register_user(data)
    return result


# =============================================================================
# VERIFY OTP ENDPOINT
# =============================================================================

@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    response_model_exclude_none=True,  # Don't include null fields!
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP verified successfully"},
        400: {"description": "Invalid OTP or validation error", "model": ErrorResponse},
        429: {"description": "Too many attempts", "model": ErrorResponse},
    },
    summary="Verify OTP",
    description="""
    Verify email using OTP sent during registration.
    
    **Flow:**
    1. Rate limit check (5 attempts/minute via Redis)
    2. Find user by email
    3. Validate OTP record (not expired, not blocked, attempts left)
    4. Verify OTP hash match
    5. If correct: Mark email as verified
    6. If wrong: Decrement attempts, block after 3 failures
    
    **Security:**
    - OTP expires in 10 minutes
    - Max 3 wrong attempts, then blocked for 20 minutes
    - Rate limited: 5 attempts per minute (Redis)
    """,
)
def verify_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db),
) -> VerifyOTPResponse:
    """
    Verify OTP for email verification.
    
    Args:
        data: VerifyOTPRequest with email and otp
        db: Database session (injected by FastAPI)
        
    Returns:
        VerifyOTPResponse with success status
        
    Raises:
        HTTPException 400: Invalid OTP, expired, blocked
        HTTPException 429: Rate limit exceeded
    """
    
    auth_service = AuthService(db)
    
    # Service layer raises AppException - handler catches it automatically!
    result = auth_service.verify_otp(data)
    return result


# =============================================================================
# LOGIN ENDPOINT
# =============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful or OTP required"},
        400: {"description": "Invalid credentials", "model": ErrorResponse},
        429: {"description": "Too many login attempts", "model": ErrorResponse},
    },
    summary="User login",
    description="""
    Authenticate user with email and password.
    
    **Flow:**
    1. Rate limit check (10 attempts/minute)
    2. Find user by email
    3. Verify password
    4. Check if email is verified:
       - Not verified → Send OTP, return `requires_otp=True`
       - Verified → Generate JWT tokens
    5. Create/Update session (single device login)
    6. Return tokens
    
    **Single Device Login:**
    New login invalidates previous device's session.
    Old device's refresh token will stop working.
    """,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens.
    
    Args:
        data: LoginRequest with email and password
        db: Database session (injected by FastAPI)
        
    Returns:
        LoginResponse with tokens or OTP redirect
        
    Raises:
        HTTPException 400: Invalid credentials
        HTTPException 429: Rate limit exceeded
    """
    
    auth_service = AuthService(db)
    
    # Service layer raises AppException - handler catches it automatically!
    result = auth_service.login(data)
    return result


# =============================================================================
# RESEND OTP ENDPOINT
# =============================================================================

@router.post(
    "/resend-otp",
    response_model=ResendOTPResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP sent (if email registered)"},
        403: {"description": "User blocked", "model": ErrorResponse},
        429: {"description": "Too many requests / cooldown active", "model": ErrorResponse},
    },
    summary="Resend OTP",
    description="""
    Resend OTP for email verification.
    
    **Flow:**
    1. Rate limit check (3 attempts per 10 minutes)
    2. Find user by email
    3. Check if already verified → Return success message
    4. Check if blocked → Return error with retry_after
    5. Check cooldown (60 seconds between resends)
    6. Generate and send new OTP
    
    **Security:**
    - Rate limited: 3 attempts per 10 minutes (Redis)
    - 60 second cooldown between resends
    - Generic response for non-existent emails (prevents enumeration)
    
    **Edge Cases:**
    - User doesn't exist → Generic success (security)
    - User already verified → Success with "can login" message
    - User blocked → 403 with retry time
    - Cooldown active → 200 with `can_resend_in` field
    """,
)
def resend_otp(
    data: ResendOTPRequest,
    db: Session = Depends(get_db),
) -> ResendOTPResponse:
    """
    Resend OTP for email verification.
    
    Args:
        data: ResendOTPRequest with email
        db: Database session (injected by FastAPI)
        
    Returns:
        ResendOTPResponse with success status and timing info
        
    Raises:
        HTTPException 403: User blocked
        HTTPException 429: Rate limit exceeded
    """
    
    auth_service = AuthService(db)
    
    # Service layer raises AppException - handler catches it automatically!
    result = auth_service.resend_otp(data)
    return result


# =============================================================================
# REFRESH TOKEN ENDPOINT
# =============================================================================

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired session", "model": ErrorResponse},
    },
    summary="Refresh access token",
    description="""
    Get a new access token using a valid refresh token.
    
    **Flow:**
    1. Verify refresh token (signature, expiry, type)
    2. Check user exists and is active
    3. Check session exists with matching device_id
    4. Generate new access token
    5. Update last_activity_at
    
    **Security:**
    - No new refresh token (strict 2-hour session limit)
    - Device ID validation (single device login)
    - Generic error messages (security)
    
    **When to call:**
    - When access token expires (HTTP 401)
    - Proactively before expiry (check exp claim)
    """,
)
def refresh(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> RefreshTokenResponse:
    """
    Refresh access token.
    
    Args:
        data: RefreshTokenRequest with refresh_token
        db: Database session (injected by FastAPI)
        
    Returns:
        RefreshTokenResponse with new access_token
        
    Raises:
        HTTPException 401: Invalid/expired token or session
    """
    
    auth_service = AuthService(db)
    
    # Service layer raises AppException - handler catches it automatically!
    result = auth_service.refresh_token(data)
    return result


# =============================================================================
# LOGOUT ENDPOINT
# =============================================================================

@router.post(
    "/logout",
    response_model=LogoutResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logged out successfully"},
        401: {"description": "Invalid or expired token", "model": ErrorResponse},
    },
    summary="Logout user",
    description="""
    End the current user session.
    
    **Requires:** Valid access token in Authorization header
    
    **Flow:**
    1. Verify access token
    2. Extract user_id and device_id
    3. Find active session
    4. Mark session as ended (is_session_active = false)
    
    **Idempotent:** 
    Calling logout twice returns success both times.
    (Already logged out = still logged out)
    
    **After logout:**
    - Access token will still work until it expires (stateless)
    - Refresh token will fail (session check)
    """,
)
def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """
    Logout user and end session.
    
    Args:
        current_user: User info from access token (injected by dependency)
        db: Database session (injected by FastAPI)
        
    Returns:
        LogoutResponse with success message
    """
    
    auth_service = AuthService(db)
    
    result = auth_service.logout(
        user_id=current_user["user_id"],
        device_id=current_user["device_id"]
    )
    
    return LogoutResponse(
        success=result["success"],
        message=result["message"]
    )


# =============================================================================
# FORGOT PASSWORD (Step 1: Request OTP)
# =============================================================================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP sent (if email registered)"},
        403: {"description": "User blocked", "model": ErrorResponse},
    },
    summary="Request password reset OTP",
    description="""
    Step 1 of password reset flow.
    
    **Flow:**
    1. Enter email address
    2. If email not verified → Returns `requires_email_verification=true`
    3. If verified → Sends password reset OTP
    
    **Security:**
    - Generic response for non-existent emails
    - Reuses existing OTP if within cooldown
    - Rate limited
    """,
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    """Request password reset OTP."""
    
    auth_service = AuthService(db)
    result = auth_service.forgot_password(data)
    return result


# =============================================================================
# VERIFY RESET OTP (Step 2: Get Temp Token)
# =============================================================================

@router.post(
    "/verify-reset-otp",
    response_model=VerifyResetOTPResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "OTP verified, reset token returned"},
        400: {"description": "Invalid OTP", "model": ErrorResponse},
        403: {"description": "User blocked", "model": ErrorResponse},
    },
    summary="Verify password reset OTP",
    description="""
    Step 2 of password reset flow.
    
    **Flow:**
    1. Submit email + OTP
    2. If valid → Returns temporary `reset_token` (10 minutes)
    3. Use reset_token in Step 3 to set new password
    
    **Security:**
    - OTP is invalidated after successful verification (one-time use)
    - Reset token is short-lived (10 minutes)
    - Reset token can ONLY be used for password reset
    """,
)
def verify_reset_otp(
    data: VerifyResetOTPRequest,
    db: Session = Depends(get_db),
) -> VerifyResetOTPResponse:
    """Verify OTP and get reset token."""
    
    auth_service = AuthService(db)
    result = auth_service.verify_reset_otp(data)
    return result


# =============================================================================
# RESET PASSWORD (Step 3: Set New Password)
# =============================================================================

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password reset successful"},
        400: {"description": "Invalid reset token", "model": ErrorResponse},
    },
    summary="Reset password with temp token",
    description="""
    Step 3 of password reset flow.
    
    **Flow:**
    1. Submit reset_token (from Step 2) + new_password
    2. Password is updated
    3. ALL sessions are invalidated (security)
    4. User must login with new password
    
    **Security:**
    - Reset token verified (signature, expiry, type)
    - All existing sessions terminated
    - User must re-authenticate
    """,
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """Set new password using reset token."""
    
    auth_service = AuthService(db)
    result = auth_service.reset_password(data)
    return result


# =============================================================================
# GET PROFILE (Protected Route)
# =============================================================================

@router.get(
    "/me",
    response_model=GetProfileResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Invalid or expired token", "model": ErrorResponse},
        403: {"description": "Account deactivated", "model": ErrorResponse},
        404: {"description": "User not found", "model": ErrorResponse},
    },
    summary="Get current user profile",
    description="""
    Get the authenticated user's profile information.
    
    **Requires:** Valid access token in Authorization header
    
    **Returns:**
    - user_id, user_name
    - email, phone_number (decrypted)
    - is_email_verified
    - subscription_id, subscription_name (null for now)
    - address, pincode, preferences
    - created_at
    
    **Security checks:**
    - Token signature and expiry verified
    - User must still be active (could be banned after login)
    
    **Note:** 
    - Email verification check not needed (unverified users can't login)
    - Subscription info will be populated when subscription service is ready
    """,
)
def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GetProfileResponse:
    """
    Get current user's profile.
    
    Args:
        current_user: User info from access token (injected by dependency)
        db: Database session (injected by FastAPI)
        
    Returns:
        GetProfileResponse with user profile data
    """
    
    auth_service = AuthService(db)
    
    profile_data = auth_service.get_profile(
        user_id=current_user["user_id"]
    )
    
    return GetProfileResponse(
        success=True,
        user=UserProfile(**profile_data)
    )
