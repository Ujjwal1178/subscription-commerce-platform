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
from app.dependencies import get_db

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
    ErrorResponse,
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
