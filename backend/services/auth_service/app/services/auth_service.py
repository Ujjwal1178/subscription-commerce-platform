"""
Auth Service - Main Business Logic

Handles:
- User Registration
- User Login
- OTP Verification
- Password Reset
- Session Management

This is the ORCHESTRATOR - it uses:
- Database models (User, UserSession, OTPVerification)
- Shared utilities (password hashing, encryption, OTP)
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

# Models
from app.models import User, UserSession, OTPVerification

# Schemas
from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    OTPStatusResponse,
)

# Shared utilities
import sys
sys.path.append("/app")  # For Docker
from shared.utils.security import hash_password, verify_password
from shared.utils.encryption import encrypt_data, decrypt_data, generate_hash, mask_email
from shared.utils.otp import generate_otp, hash_otp, verify_otp
from shared.utils.rate_limiter import check_rate_limit, RateLimitAction

# Config
from app.config import (
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_BLOCK_MINUTES,
    IS_DEV_MODE,
    OTP_VERIFY_RATE_LIMIT,
    OTP_VERIFY_RATE_WINDOW,
)

# Logger
from app.logger import logger, log_otp_generated, log_user_registered


# =============================================================================
# AUTH SERVICE CLASS
# =============================================================================

class AuthService:
    """
    Main authentication service.
    
    Injected with database session for all DB operations.
    
    Usage:
        auth_service = AuthService(db_session)
        result = auth_service.register_user(register_data)
    """
    
    def __init__(self, db: Session):
        """
        Initialize with database session.
        
        Args:
            db: SQLAlchemy database session (injected by FastAPI dependency)
        """
        self.db = db
    
    # =========================================================================
    # REGISTER
    # =========================================================================
    
    def register_user(self, data: RegisterRequest) -> RegisterResponse:
        """
        Register a new user.
        
        Flow:
        1. Check if email already exists
        2. Hash password
        3. Encrypt email and phone
        4. Create user record
        5. Generate and store OTP
        6. Return success response
        
        Args:
            data: RegisterRequest with user_name, email, phone_number, password
            
        Returns:
            RegisterResponse with success status and masked email
            
        Raises:
            ValueError: If email already registered
        """
        
        # Step 1: Generate email hash for lookup
        email_hash = generate_hash(data.email.lower())  # Lowercase for consistency
        
        # Step 2: Check if email already exists
        existing_user = self._get_user_by_email_hash(email_hash)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Step 3: Hash password
        password_hash = hash_password(data.password)
        
        # Step 4: Encrypt PII (email and phone)
        email_encrypted = encrypt_data(data.email.lower())
        phone_encrypted = encrypt_data(data.phone_number)
        
        # Step 5: Create user record
        user = User(
            user_name=data.user_name,
            email_hash=email_hash,
            email_encrypted=email_encrypted,
            phone_encrypted=phone_encrypted,
            password_hash=password_hash,
            is_active=True,
            is_email_verified=False,  # Will be True after OTP verification
        )
        
        self.db.add(user)
        self.db.flush()  # Get user_id without committing
        
        # Step 6: Generate and store OTP
        otp = generate_otp()
        otp_record = self._create_otp_record(
            user_id=user.user_id,
            otp=otp,
            verification_type="email_verification"
        )
        
        # Step 7: Commit transaction (user + OTP together)
        self.db.commit()
        
        # Step 8: TODO - Publish Kafka event to send OTP email
        # kafka_producer.send("notification.send_otp", {
        #     "email": data.email,
        #     "otp": otp,
        #     "type": "email_verification"
        # })
        
        # Log OTP (visible in dev mode only)
        log_otp_generated(
            email=data.email,
            otp=otp,
            user_id=str(user.user_id)
        )
        
        # Log registration
        log_user_registered(
            user_id=str(user.user_id),
            email=data.email
        )
        
        # Step 9: Return response
        return RegisterResponse(
            success=True,
            message="Registration successful. Please verify your email.",
            otp_expires_in=OTP_EXPIRY_MINUTES * 60,  # Convert to seconds
            masked_email=mask_email(data.email)
        )
    
    # =========================================================================
    # HELPER METHODS (Private)
    # =========================================================================
    
    def _get_user_by_email_hash(self, email_hash: str) -> Optional[User]:
        """
        Find user by email hash.
        
        Args:
            email_hash: SHA256 hash of email
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(
            User.email_hash == email_hash,
            User.is_active == True  # Don't return soft-deleted users
        ).first()
    
    def _create_otp_record(
        self, 
        user_id: UUID, 
        otp: str, 
        verification_type: str
    ) -> OTPVerification:
        """
        Create OTP record in database.
        
        Args:
            user_id: User's UUID
            otp: Plain text OTP (will be hashed before storing)
            verification_type: "email_verification" or "password_reset"
            
        Returns:
            Created OTPVerification object
        """
        # Invalidate any existing OTPs for this user and type
        # is_otp_valid = False means OTP is no longer usable
        self.db.query(OTPVerification).filter(
            OTPVerification.user_id == user_id,
            OTPVerification.verification_type == verification_type,
            OTPVerification.is_otp_valid == True  # Only invalidate active OTPs
        ).update({"is_otp_valid": False})  # Mark old OTPs as used
        
        # Create new OTP record
        # Column names match OTPVerification model:
        # - remaining_retry (not attempts_remaining)
        # - otp_expires_at (not expires_at)
        # - is_otp_valid (not is_verified)
        otp_record = OTPVerification(
            user_id=user_id,
            otp_hash=hash_otp(otp),  # Store hashed, not plain text!
            verification_type=verification_type,
            otp_expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            remaining_retry=OTP_MAX_ATTEMPTS,
            is_otp_valid=True,  # This OTP is active
            is_user_blocked=False,
        )
        
        self.db.add(otp_record)
        return otp_record

    # =========================================================================
    # VERIFY OTP
    # =========================================================================
    
    def verify_otp(self, data: VerifyOTPRequest) -> VerifyOTPResponse:
        """
        Verify OTP for email verification.
        
        Flow:
        1. Rate limit check (Redis) - 5 attempts/minute
        2. Find user by email
        3. Find active OTP record
        4. Check: expired? blocked? attempts left?
        5. Verify OTP hash match
        6. If correct: mark verified, update user
        7. If wrong: decrement attempts, maybe block
        
        Args:
            data: VerifyOTPRequest with email and otp
            
        Returns:
            VerifyOTPResponse with success status
            
        Raises:
            ValueError: Invalid OTP, expired, blocked, etc.
        """
        email_lower = data.email.lower()
        
        # -----------------------------------------------------------------
        # Step 1: Rate Limit Check (Redis)
        # -----------------------------------------------------------------
        rate_result = check_rate_limit(
            action=RateLimitAction.OTP_VERIFY,
            identifier=email_lower,  # Will be hashed internally
            limit=OTP_VERIFY_RATE_LIMIT,
            window_seconds=OTP_VERIFY_RATE_WINDOW
        )
        
        if not rate_result.allowed:
            logger.warning(
                f"OTP verify rate limited for {mask_email(email_lower)}, "
                f"retry after {rate_result.retry_after}s"
            )
            raise ValueError(
                f"Too many attempts. Please try again in {rate_result.retry_after} seconds."
            )
        
        # -----------------------------------------------------------------
        # Step 2: Find User
        # -----------------------------------------------------------------
        email_hash = generate_hash(email_lower)
        user = self._get_user_by_email_hash(email_hash)
        
        if not user:
            # Don't reveal if user exists or not (security)
            logger.warning(f"OTP verify attempt for non-existent email: {mask_email(email_lower)}")
            raise ValueError("Invalid OTP or email.")
        
        # Already verified?
        if user.is_email_verified:
            logger.info(f"User {user.user_id} already verified")
            return VerifyOTPResponse(
                success=True,
                message="Email already verified. You can login.",
                is_verified=True
            )
        
        # -----------------------------------------------------------------
        # Step 3: Find Active OTP Record
        # -----------------------------------------------------------------
        otp_record = self._get_active_otp(
            user_id=user.user_id,
            verification_type="email_verification"
        )
        
        if not otp_record:
            logger.warning(f"No active OTP found for user {user.user_id}")
            raise ValueError("No active OTP found. Please request a new one.")
        
        # -----------------------------------------------------------------
        # Step 4: Check OTP Status
        # -----------------------------------------------------------------
        
        # Is user blocked?
        if otp_record.is_user_blocked:
            # Check if block period has passed
            if otp_record.blocked_at:
                unblock_time = otp_record.blocked_at + timedelta(minutes=OTP_BLOCK_MINUTES)
                if datetime.utcnow() < unblock_time:
                    remaining_minutes = int((unblock_time - datetime.utcnow()).total_seconds() / 60)
                    logger.warning(f"User {user.user_id} is blocked for OTP, {remaining_minutes} min remaining")
                    raise ValueError(
                        f"Account temporarily blocked. Try again in {remaining_minutes} minutes."
                    )
                else:
                    # Block period passed, unblock user
                    otp_record.is_user_blocked = False
                    otp_record.blocked_at = None
                    otp_record.remaining_retry = OTP_MAX_ATTEMPTS
                    logger.info(f"User {user.user_id} unblocked after block period")
        
        # Is OTP expired?
        if datetime.utcnow() > otp_record.otp_expires_at:
            logger.warning(f"OTP expired for user {user.user_id}")
            raise ValueError("OTP has expired. Please request a new one.")
        
        # Any attempts left?
        if otp_record.remaining_retry <= 0:
            # Block the user
            otp_record.is_user_blocked = True
            otp_record.blocked_at = datetime.utcnow()
            self.db.commit()
            logger.warning(f"User {user.user_id} blocked due to max OTP attempts")
            raise ValueError(
                f"Maximum attempts exceeded. Account blocked for {OTP_BLOCK_MINUTES} minutes."
            )
        
        # -----------------------------------------------------------------
        # Step 5: Verify OTP
        # -----------------------------------------------------------------
        is_valid = verify_otp(data.otp, otp_record.otp_hash)
        
        if not is_valid:
            # Decrement attempts
            otp_record.remaining_retry -= 1
            remaining = otp_record.remaining_retry
            
            # Block if no attempts left
            if remaining <= 0:
                otp_record.is_user_blocked = True
                otp_record.blocked_at = datetime.utcnow()
                self.db.commit()
                logger.warning(f"User {user.user_id} blocked after failed OTP attempt")
                raise ValueError(
                    f"Maximum attempts exceeded. Account blocked for {OTP_BLOCK_MINUTES} minutes."
                )
            
            self.db.commit()
            logger.info(f"Wrong OTP for user {user.user_id}, {remaining} attempts left")
            raise ValueError(f"Invalid OTP. {remaining} attempts remaining.")
        
        # -----------------------------------------------------------------
        # Step 6: OTP Correct! Mark as Verified
        # -----------------------------------------------------------------
        
        # Invalidate OTP (can't reuse)
        otp_record.is_otp_valid = False
        
        # Mark user email as verified
        user.is_email_verified = True
        
        self.db.commit()
        
        logger.info(f"Email verified successfully for user {user.user_id}")
        
        return VerifyOTPResponse(
            success=True,
            message="Email verified successfully. You can now login.",
            is_verified=True
        )
    
    def _get_active_otp(
        self,
        user_id: UUID,
        verification_type: str
    ) -> Optional[OTPVerification]:
        """
        Get the most recent active OTP for a user.
        
        Active means:
        - is_otp_valid = True (not used)
        - Not expired (checked in verify_otp method)
        
        Args:
            user_id: User's UUID
            verification_type: "email_verification" or "password_reset"
            
        Returns:
            OTPVerification record or None
        """
        return self.db.query(OTPVerification).filter(
            OTPVerification.user_id == user_id,
            OTPVerification.verification_type == verification_type,
            OTPVerification.is_otp_valid == True
        ).order_by(
            OTPVerification.otp_created_at.desc()  # Most recent first
        ).first()
