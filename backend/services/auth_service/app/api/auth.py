"""
Auth API Routes

Endpoints:
- POST /register - Create new user account
- POST /verify-otp - Verify email with OTP
- POST /login - Authenticate and get tokens (coming soon)
- POST /refresh - Refresh access token (coming soon)
- POST /logout - End session (coming soon)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Dependencies
from app.dependencies import get_db

# Schemas (request/response validation)
from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    ErrorResponse,
)

# Service (business logic)
from app.services import AuthService

# Logger
from app.logger import logger


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
    
    try:
        # Call business logic
        result = auth_service.register_user(data)
        return result
        
    except ValueError as e:
        # Business logic errors (email exists, etc.)
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


# =============================================================================
# VERIFY OTP ENDPOINT
# =============================================================================

@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
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
    
    try:
        result = auth_service.verify_otp(data)
        return result
        
    except ValueError as e:
        error_msg = str(e)
        
        # Check if it's a rate limit error (429) vs validation error (400)
        if "Too many attempts" in error_msg or "try again in" in error_msg.lower():
            logger.warning(f"OTP verify rate limited: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg,
            )
        
        # Check if it's a block error
        if "blocked" in error_msg.lower():
            logger.warning(f"OTP verify blocked: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        
        # Generic validation error
        logger.warning(f"OTP verify failed: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
        
    except Exception as e:
        logger.error(f"OTP verify error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )
