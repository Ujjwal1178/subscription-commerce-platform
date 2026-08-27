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
- Custom Exceptions (AppException for consistent error handling)
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
    ResendOTPRequest,
    ResendOTPResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

# Shared utilities
import sys
sys.path.append("/app")  # For Docker
from shared.utils.security import hash_password, verify_password
from shared.utils.encryption import encrypt_data, decrypt_data, generate_hash, mask_email
from shared.utils.otp import generate_otp, hash_otp, verify_otp
from shared.utils.rate_limiter import check_rate_limit, RateLimitAction
from shared.utils.jwt import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_refresh_token,
    verify_password_reset_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)

# Custom Exceptions - raise these instead of ValueError!
from shared.exceptions import AppException, ErrorCode

# For generating device_id
import uuid

# Config
from app.config import (
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_BLOCK_MINUTES,
    IS_DEV_MODE,
    OTP_VERIFY_RATE_LIMIT,
    OTP_VERIFY_RATE_WINDOW,
    LOGIN_RATE_LIMIT,
    LOGIN_RATE_WINDOW,
    OTP_RESEND_RATE_LIMIT,
    OTP_RESEND_RATE_WINDOW,
    OTP_RESEND_COOLDOWN,
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
            raise AppException(
                message="Email already registered",
                error_code=ErrorCode.EMAIL_ALREADY_REGISTERED,
                status_code=409
            )
        
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
            raise AppException(
                message=f"Too many attempts. Please try again in {rate_result.retry_after} seconds.",
                error_code=ErrorCode.RATE_LIMITED,
                status_code=429,
                details={"retry_after": rate_result.retry_after}
            )
        
        # -----------------------------------------------------------------
        # Step 2: Find User
        # -----------------------------------------------------------------
        email_hash = generate_hash(email_lower)
        user = self._get_user_by_email_hash(email_hash)
        
        if not user:
            # Don't reveal if user exists or not (security)
            logger.warning(f"OTP verify attempt for non-existent email: {mask_email(email_lower)}")
            raise AppException(
                message="Invalid OTP or email.",
                error_code=ErrorCode.OTP_INVALID,
                status_code=400
            )
        
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
            raise AppException(
                message="No active OTP found. Please request a new one.",
                error_code=ErrorCode.OTP_EXPIRED,
                status_code=400
            )
        
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
                    raise AppException(
                        message=f"Account temporarily blocked. Try again in {remaining_minutes} minutes.",
                        error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                        status_code=403,
                        details={"retry_after_minutes": remaining_minutes}
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
            raise AppException(
                message="OTP has expired. Please request a new one.",
                error_code=ErrorCode.OTP_EXPIRED,
                status_code=400
            )
        
        # Any attempts left?
        if otp_record.remaining_retry <= 0:
            # Block the user
            otp_record.is_user_blocked = True
            otp_record.blocked_at = datetime.utcnow()
            self.db.commit()
            logger.warning(f"User {user.user_id} blocked due to max OTP attempts")
            raise AppException(
                message=f"Maximum attempts exceeded. Account blocked for {OTP_BLOCK_MINUTES} minutes.",
                error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                status_code=403,
                details={"blocked_for_minutes": OTP_BLOCK_MINUTES}
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
                raise AppException(
                    message=f"Maximum attempts exceeded. Account blocked for {OTP_BLOCK_MINUTES} minutes.",
                    error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                    status_code=403,
                    details={"blocked_for_minutes": OTP_BLOCK_MINUTES}
                )
            
            self.db.commit()
            logger.info(f"Wrong OTP for user {user.user_id}, {remaining} attempts left")
            raise AppException(
                message=f"Invalid OTP. {remaining} attempts remaining.",
                error_code=ErrorCode.OTP_INVALID,
                status_code=400,
                details={"attempts_remaining": remaining}
            )
        
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

    # =========================================================================
    # LOGIN
    # =========================================================================
    
    def login(self, data: LoginRequest) -> LoginResponse:
        """
        Authenticate user and return JWT tokens.
        
        Flow:
        1. Rate limit check (Redis) - 10 attempts/minute
        2. Find user by email
        3. Verify password
        4. Check if email is verified
           - No → Send OTP, return "verify email first"
           - Yes → Continue
        5. Create/Update session (device_id)
        6. Generate JWT tokens
        7. Return tokens
        
        Args:
            data: LoginRequest with email and password
            
        Returns:
            LoginResponse with tokens or OTP redirect
            
        Raises:
            ValueError: Invalid credentials, rate limited, etc.
        """
        email_lower = data.email.lower()
        
        # -----------------------------------------------------------------
        # Step 1: Rate Limit Check (Redis)
        # -----------------------------------------------------------------
        rate_result = check_rate_limit(
            action=RateLimitAction.LOGIN,
            identifier=email_lower,
            limit=LOGIN_RATE_LIMIT,
            window_seconds=LOGIN_RATE_WINDOW
        )
        
        if not rate_result.allowed:
            logger.warning(
                f"Login rate limited for {mask_email(email_lower)}, "
                f"retry after {rate_result.retry_after}s"
            )
            raise AppException(
                message=f"Too many login attempts. Please try again in {rate_result.retry_after} seconds.",
                error_code=ErrorCode.RATE_LIMITED,
                status_code=429,
                details={"retry_after": rate_result.retry_after}
            )
        
        # -----------------------------------------------------------------
        # Step 2: Find User
        # -----------------------------------------------------------------
        email_hash = generate_hash(email_lower)
        user = self._get_user_by_email_hash(email_hash)
        
        if not user:
            # Don't reveal if user exists (security - prevent enumeration)
            logger.warning(f"Login attempt for non-existent email: {mask_email(email_lower)}")
            raise AppException(
                message="Invalid email or password.",
                error_code=ErrorCode.INVALID_CREDENTIALS,
                status_code=400
            )
        
        # -----------------------------------------------------------------
        # Step 3: Verify Password
        # -----------------------------------------------------------------
        if not verify_password(data.password, user.password_hash):
            logger.warning(f"Invalid password for user {user.user_id}")
            raise AppException(
                message="Invalid email or password.",
                error_code=ErrorCode.INVALID_CREDENTIALS,
                status_code=400
            )
        
        # -----------------------------------------------------------------
        # Step 4: Check Email Verification
        # -----------------------------------------------------------------
        if not user.is_email_verified:
            # Check if valid OTP already exists
            existing_otp = self._get_active_otp(
                user_id=user.user_id,
                verification_type="email_verification"
            )
            
            if existing_otp:
                # Check if user is blocked
                if existing_otp.is_user_blocked:
                    if existing_otp.blocked_at:
                        unblock_time = existing_otp.blocked_at + timedelta(minutes=OTP_BLOCK_MINUTES)
                        if datetime.utcnow() < unblock_time:
                            remaining_minutes = int((unblock_time - datetime.utcnow()).total_seconds() / 60) + 1
                            logger.warning(f"Login blocked - user {user.user_id} is OTP blocked")
                            raise AppException(
                                message=f"Too many failed attempts. Try again in {remaining_minutes} minutes.",
                                error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                                status_code=403,
                                details={"retry_after_minutes": remaining_minutes}
                            )
                        else:
                            # Block period passed, unblock
                            existing_otp.is_user_blocked = False
                            existing_otp.blocked_at = None
                            existing_otp.remaining_retry = OTP_MAX_ATTEMPTS
                
                # Check if OTP is still valid (not expired)
                if datetime.utcnow() < existing_otp.otp_expires_at:
                    # OTP still valid - reuse it, don't generate new
                    remaining_seconds = int((existing_otp.otp_expires_at - datetime.utcnow()).total_seconds())
                    
                    logger.info(f"Login blocked - reusing existing OTP for user {user.user_id}, {remaining_seconds}s remaining")
                    
                    return LoginResponse(
                        success=False,
                        message="Please verify your email. OTP already sent.",
                        requires_otp=True,
                        masked_email=mask_email(email_lower),
                        otp_expires_in=remaining_seconds,
                    )
            
            # No valid OTP exists OR OTP expired - generate new one
            otp = generate_otp()
            self._create_otp_record(
                user_id=user.user_id,
                otp=otp,
                verification_type="email_verification"
            )
            self.db.commit()
            
            # Log OTP (dev mode only)
            log_otp_generated(
                email=email_lower,
                otp=otp,
                user_id=str(user.user_id)
            )
            
            logger.info(f"Login blocked - new OTP generated for user {user.user_id}")
            
            # Return response indicating OTP verification needed
            return LoginResponse(
                success=False,
                message="Please verify your email first. OTP has been sent.",
                requires_otp=True,
                masked_email=mask_email(email_lower),
                otp_expires_in=OTP_EXPIRY_MINUTES * 60,
            )
        
        # -----------------------------------------------------------------
        # Step 5: Create/Update Session (Device ID)
        # -----------------------------------------------------------------
        device_id = str(uuid.uuid4())  # Generate new device_id
        
        # Update or create session
        # Single device login: Replace existing session
        session = self._create_or_update_session(
            user_id=user.user_id,
            device_id=device_id,
            device_name=data.device_name  # From frontend (optional)
        )
        
        # -----------------------------------------------------------------
        # Step 6: Generate JWT Tokens
        # -----------------------------------------------------------------
        access_token = create_access_token(
            user_id=str(user.user_id),
            user_name=user.user_name,
            device_id=device_id
        )
        
        refresh_token = create_refresh_token(
            user_id=str(user.user_id),
            device_id=device_id
        )
        
        self.db.commit()
        
        logger.info(f"User {user.user_id} logged in successfully")
        
        # -----------------------------------------------------------------
        # Step 7: Return Success Response
        # -----------------------------------------------------------------
        return LoginResponse(
            success=True,
            message="Login successful.",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # In seconds
            user_name=user.user_name,
        )
    
    def _create_or_update_session(
        self,
        user_id: UUID,
        device_id: str,
        device_name: Optional[str] = None
    ) -> UserSession:
        """
        Create new session and deactivate old ones.
        
        Single Device Login:
        - Deactivate ALL existing active sessions (mark ended)
        - Create NEW session row (preserves history!)
        
        Why new row instead of update?
        - Preserves login history (audit trail)
        - Can show "Recent login activity" to user
        - Each session has its own session_id, timestamps
        
        Args:
            user_id: User's UUID
            device_id: New device identifier
            device_name: Human readable device name (e.g., 'Chrome on Windows')
            
        Returns:
            New UserSession object
        """
        # Step 1: Deactivate ALL existing active sessions for this user
        # This logs out the old device automatically
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_session_active == True
        ).update({
            "is_session_active": False,
            "session_ended_at": datetime.utcnow()
        })
        
        logger.info(f"Deactivated previous sessions for user {user_id}")
        
        # Step 2: Create NEW session (always create, never update!)
        session = UserSession(
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            is_session_active=True,
            session_started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
        )
        self.db.add(session)
        
        logger.info(f"New session created for user {user_id}, device: {device_name or 'Unknown'}")
        
        return session

    # =========================================================================
    # RESEND OTP
    # =========================================================================
    
    def resend_otp(self, data: ResendOTPRequest) -> ResendOTPResponse:
        """
        Resend OTP for email verification.
        
        Edge Cases Handled:
        1. Rate limiting - 3 attempts per 10 minutes (Redis)
        2. Cooldown - Minimum 60 seconds between resends
        3. User not found - Generic response (security)
        4. Already verified - Return success message
        5. User blocked - Return error with retry_after
        6. Recent OTP still valid - Return remaining time instead of new OTP
        
        Args:
            data: ResendOTPRequest with email
            
        Returns:
            ResendOTPResponse with success status and timing info
        """
        email_lower = data.email.lower()
        
        # -----------------------------------------------------------------
        # Step 1: Rate Limit Check (Redis) - 3 per 10 minutes
        # -----------------------------------------------------------------
        rate_result = check_rate_limit(
            action=RateLimitAction.OTP_RESEND,
            identifier=email_lower,
            limit=OTP_RESEND_RATE_LIMIT,
            window_seconds=OTP_RESEND_RATE_WINDOW
        )
        
        if not rate_result.allowed:
            logger.warning(
                f"OTP resend rate limited for {mask_email(email_lower)}, "
                f"retry after {rate_result.retry_after}s"
            )
            raise AppException(
                message=f"Too many resend requests. Please try again in {rate_result.retry_after} seconds.",
                error_code=ErrorCode.RATE_LIMITED,
                status_code=429,
                details={"retry_after": rate_result.retry_after}
            )
        
        # -----------------------------------------------------------------
        # Step 2: Find User
        # -----------------------------------------------------------------
        email_hash = generate_hash(email_lower)
        user = self._get_user_by_email_hash(email_hash)
        
        # Generic message for ALL cases (security - prevent enumeration)
        generic_message = "If the email is registered, a new OTP will be sent."
        
        if not user:
            # Don't reveal if user exists (security - prevent enumeration)
            # Return SAME response as success case
            logger.warning(f"OTP resend for non-existent email: {mask_email(email_lower)}")
            return ResendOTPResponse(
                success=True,
                message=generic_message,
                masked_email=mask_email(email_lower),
                otp_expires_in=OTP_EXPIRY_MINUTES * 60,
                can_resend_in=OTP_RESEND_COOLDOWN,  # Same as real response!
            )
        
        # -----------------------------------------------------------------
        # Step 3: Already verified?
        # -----------------------------------------------------------------
        if user.is_email_verified:
            logger.info(f"OTP resend for already verified user {user.user_id}")
            return ResendOTPResponse(
                success=True,
                message="Email already verified. You can login.",
                masked_email=mask_email(email_lower),
            )
        
        # -----------------------------------------------------------------
        # Step 4: Check existing OTP status
        # -----------------------------------------------------------------
        existing_otp = self._get_active_otp(
            user_id=user.user_id,
            verification_type="email_verification"
        )
        
        if existing_otp:
            # Check if user is blocked
            if existing_otp.is_user_blocked:
                if existing_otp.blocked_at:
                    unblock_time = existing_otp.blocked_at + timedelta(minutes=OTP_BLOCK_MINUTES)
                    if datetime.utcnow() < unblock_time:
                        remaining_minutes = int((unblock_time - datetime.utcnow()).total_seconds() / 60) + 1
                        logger.warning(f"OTP resend blocked - user {user.user_id} is blocked")
                        raise AppException(
                            message=f"Too many failed attempts. Try again in {remaining_minutes} minutes.",
                            error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                            status_code=403,
                            details={"retry_after_minutes": remaining_minutes}
                        )
                    else:
                        # Block period passed, unblock
                        existing_otp.is_user_blocked = False
                        existing_otp.blocked_at = None
                        existing_otp.remaining_retry = OTP_MAX_ATTEMPTS
            
            # Check cooldown - can't resend too quickly
            time_since_created = (datetime.utcnow() - existing_otp.otp_created_at).total_seconds()
            if time_since_created < OTP_RESEND_COOLDOWN:
                wait_seconds = int(OTP_RESEND_COOLDOWN - time_since_created)
                logger.info(f"OTP resend cooldown for user {user.user_id}, wait {wait_seconds}s")
                
                # Return remaining time for existing OTP
                remaining_seconds = int((existing_otp.otp_expires_at - datetime.utcnow()).total_seconds())
                
                return ResendOTPResponse(
                    success=False,
                    message=f"Please wait {wait_seconds} seconds before requesting a new OTP.",
                    masked_email=mask_email(email_lower),
                    otp_expires_in=max(remaining_seconds, 0),
                    can_resend_in=wait_seconds,
                )
        
        # -----------------------------------------------------------------
        # Step 5: Generate and send new OTP
        # -----------------------------------------------------------------
        otp = generate_otp()
        self._create_otp_record(
            user_id=user.user_id,
            otp=otp,
            verification_type="email_verification"
        )
        self.db.commit()
        
        # Log OTP (dev mode only)
        log_otp_generated(
            email=email_lower,
            otp=otp,
            user_id=str(user.user_id)
        )
        
        logger.info(f"New OTP generated via resend for user {user.user_id}")
        
        # TODO: Publish Kafka event to send OTP email
        # kafka_producer.send("notification.send_otp", {
        #     "email": email_lower,
        #     "otp": otp,
        #     "type": "email_verification"
        # })
        
        return ResendOTPResponse(
            success=True,
            message=generic_message,  # Same generic message for security!
            masked_email=mask_email(email_lower),
            otp_expires_in=OTP_EXPIRY_MINUTES * 60,
            can_resend_in=OTP_RESEND_COOLDOWN,
        )

    # =========================================================================
    # REFRESH TOKEN
    # =========================================================================
    
    def refresh_token(self, data: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Refresh access token using a valid refresh token.
        
        Flow:
        1. Verify JWT (signature, expiry, type)
        2. Extract user_id and device_id from token
        3. Check user exists and is_active
        4. Check session exists and is_active with matching device_id
        5. Generate new access token
        6. Update last_activity_at
        
        Security:
        - Generic error messages (don't reveal why it failed)
        - No new refresh token (strict 2-hour session limit)
        - Device ID validation (single device login)
        
        Args:
            data: RefreshTokenRequest with refresh_token
            
        Returns:
            RefreshTokenResponse with new access_token
        """
        
        # -----------------------------------------------------------------
        # Step 1: Verify JWT
        # -----------------------------------------------------------------
        try:
            payload = verify_refresh_token(data.refresh_token)
        except ValueError as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            raise AppException(
                message="Session expired. Please login again.",
                error_code=ErrorCode.SESSION_EXPIRED,
                status_code=401
            )
        
        # -----------------------------------------------------------------
        # Step 2: Extract user_id and device_id
        # -----------------------------------------------------------------
        user_id = payload.get("user_id")
        device_id = payload.get("device_id")
        
        if not user_id or not device_id:
            logger.warning("Refresh token missing user_id or device_id")
            raise AppException(
                message="Session expired. Please login again.",
                error_code=ErrorCode.SESSION_EXPIRED,
                status_code=401
            )
        
        # -----------------------------------------------------------------
        # Step 3: Check user exists and is_active
        # -----------------------------------------------------------------
        user = self.db.query(User).filter(
            User.user_id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            logger.warning(f"Refresh attempt for non-existent/inactive user: {user_id}")
            raise AppException(
                message="Session expired. Please login again.",
                error_code=ErrorCode.SESSION_EXPIRED,
                status_code=401
            )
        
        # -----------------------------------------------------------------
        # Step 4: Check session exists with matching device_id
        # -----------------------------------------------------------------
        session = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.device_id == device_id,
            UserSession.is_session_active == True
        ).first()
        
        if not session:
            logger.warning(f"Refresh attempt with invalid session/device: user={user_id}, device={device_id}")
            raise AppException(
                message="Session expired. Please login again.",
                error_code=ErrorCode.SESSION_EXPIRED,
                status_code=401
            )
        
        # -----------------------------------------------------------------
        # Step 5: Generate new access token
        # -----------------------------------------------------------------
        new_access_token = create_access_token(
            user_id=str(user.user_id),
            user_name=user.user_name,
            device_id=device_id
        )
        
        # -----------------------------------------------------------------
        # Step 6: Update last_activity_at
        # -----------------------------------------------------------------
        session.last_activity_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Token refreshed for user {user_id}")
        
        return RefreshTokenResponse(
            success=True,
            message="Token refreshed successfully",
            access_token=new_access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


    # =========================================================================
    # LOGOUT
    # =========================================================================
    
    def logout(self, user_id: str, device_id: str) -> dict:
        """
        Logout user by deactivating their session.
        
        Flow:
        1. Find active session for user_id + device_id
        2. Mark session as ended
        3. Return success
        
        Note: We receive user_id and device_id from the verified access token
        (extracted by the API layer dependency).
        
        Args:
            user_id: User's UUID (from access token)
            device_id: Device identifier (from access token)
            
        Returns:
            Dict with success status
        """
        # Find the active session
        session = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.device_id == device_id,
            UserSession.is_session_active == True
        ).first()
        
        if not session:
            # Session already ended or doesn't exist
            # Return success anyway (idempotent - logout twice = still logged out)
            logger.info(f"Logout called for already ended session: user={user_id}")
            return {
                "success": True,
                "message": "Logged out successfully"
            }
        
        # Deactivate session
        session.is_session_active = False
        session.session_ended_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"User {user_id} logged out successfully")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }


    # =========================================================================
    # FORGOT PASSWORD (Step 1: Request OTP)
    # =========================================================================
    
    def forgot_password(self, data: ForgotPasswordRequest) -> ForgotPasswordResponse:
        """
        Step 1 of password reset flow - Request OTP.
        
        Flow:
        1. Find user by email
        2. If user not found → Generic response (security)
        3. If email not verified → Send verification OTP, indicate redirect
        4. If verified → Send password reset OTP
        
        Args:
            data: ForgotPasswordRequest with email
            
        Returns:
            ForgotPasswordResponse
        """
        email_lower = data.email.lower()
        
        # Generic message for security (same for all cases)
        generic_message = "If the email is registered, you will receive an OTP."
        
        # -----------------------------------------------------------------
        # Step 1: Find User
        # -----------------------------------------------------------------
        email_hash = generate_hash(email_lower)
        user = self._get_user_by_email_hash(email_hash)
        
        if not user:
            # Don't reveal if user exists
            logger.warning(f"Forgot password for non-existent email: {mask_email(email_lower)}")
            return ForgotPasswordResponse(
                success=True,
                message=generic_message,
                masked_email=mask_email(email_lower),
                otp_expires_in=OTP_EXPIRY_MINUTES * 60,
            )
        
        # -----------------------------------------------------------------
        # Step 2: Check if email is verified
        # -----------------------------------------------------------------
        if not user.is_email_verified:
            # Email not verified - send verification OTP first
            existing_otp = self._get_active_otp(
                user_id=user.user_id,
                verification_type="email_verification"
            )
            
            # Check if blocked
            if existing_otp and existing_otp.is_user_blocked:
                if existing_otp.blocked_at:
                    unblock_time = existing_otp.blocked_at + timedelta(minutes=OTP_BLOCK_MINUTES)
                    if datetime.utcnow() < unblock_time:
                        remaining_minutes = int((unblock_time - datetime.utcnow()).total_seconds() / 60) + 1
                        raise AppException(
                            message=f"Too many failed attempts. Try again in {remaining_minutes} minutes.",
                            error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                            status_code=403,
                            details={"retry_after_minutes": remaining_minutes}
                        )
            
            # Reuse existing OTP if valid
            if existing_otp and datetime.utcnow() < existing_otp.otp_expires_at:
                remaining_seconds = int((existing_otp.otp_expires_at - datetime.utcnow()).total_seconds())
                logger.info(f"Forgot password - reusing verification OTP for user {user.user_id}")
                
                return ForgotPasswordResponse(
                    success=False,
                    message="Please verify your email first. OTP already sent.",
                    requires_email_verification=True,
                    masked_email=mask_email(email_lower),
                    otp_expires_in=remaining_seconds,
                )
            
            # Generate new verification OTP
            otp = generate_otp()
            self._create_otp_record(
                user_id=user.user_id,
                otp=otp,
                verification_type="email_verification"
            )
            self.db.commit()
            
            log_otp_generated(email=email_lower, otp=otp, user_id=str(user.user_id))
            logger.info(f"Forgot password - new verification OTP for user {user.user_id}")
            
            return ForgotPasswordResponse(
                success=False,
                message="Please verify your email first. OTP has been sent.",
                requires_email_verification=True,
                masked_email=mask_email(email_lower),
                otp_expires_in=OTP_EXPIRY_MINUTES * 60,
            )
        
        # -----------------------------------------------------------------
        # Step 3: Email verified - Send password reset OTP
        # -----------------------------------------------------------------
        
        # Check for existing valid password reset OTP
        existing_reset_otp = self._get_active_otp(
            user_id=user.user_id,
            verification_type="password_reset"
        )
        
        # Check if blocked
        if existing_reset_otp and existing_reset_otp.is_user_blocked:
            if existing_reset_otp.blocked_at:
                unblock_time = existing_reset_otp.blocked_at + timedelta(minutes=OTP_BLOCK_MINUTES)
                if datetime.utcnow() < unblock_time:
                    remaining_minutes = int((unblock_time - datetime.utcnow()).total_seconds() / 60) + 1
                    raise AppException(
                        message=f"Too many failed attempts. Try again in {remaining_minutes} minutes.",
                        error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                        status_code=403,
                        details={"retry_after_minutes": remaining_minutes}
                    )
        
        # Reuse existing OTP if valid and within cooldown
        if existing_reset_otp and datetime.utcnow() < existing_reset_otp.otp_expires_at:
            time_since_created = (datetime.utcnow() - existing_reset_otp.otp_created_at).total_seconds()
            if time_since_created < OTP_RESEND_COOLDOWN:
                remaining_seconds = int((existing_reset_otp.otp_expires_at - datetime.utcnow()).total_seconds())
                logger.info(f"Forgot password - reusing reset OTP for user {user.user_id}")
                
                return ForgotPasswordResponse(
                    success=True,
                    message="OTP already sent. Please check your email.",
                    masked_email=mask_email(email_lower),
                    otp_expires_in=remaining_seconds,
                )
        
        # Generate new password reset OTP
        otp = generate_otp()
        self._create_otp_record(
            user_id=user.user_id,
            otp=otp,
            verification_type="password_reset"  # Different type!
        )
        self.db.commit()
        
        log_otp_generated(email=email_lower, otp=otp, user_id=str(user.user_id))
        logger.info(f"Forgot password - new reset OTP for user {user.user_id}")
        
        # TODO: Send password reset email via Kafka
        
        return ForgotPasswordResponse(
            success=True,
            message=generic_message,
            masked_email=mask_email(email_lower),
            otp_expires_in=OTP_EXPIRY_MINUTES * 60,
        )

    # =========================================================================
    # VERIFY RESET OTP (Step 2: Verify OTP, Get Temp Token)
    # =========================================================================
    
    def verify_reset_otp(self, data: VerifyResetOTPRequest) -> VerifyResetOTPResponse:
        """
        Step 2 of password reset flow - Verify OTP and get temp token.
        
        Flow:
        1. Find user by email
        2. Find active password_reset OTP
        3. Verify OTP (same logic as email verification)
        4. If valid → Generate temp reset token (10 min)
        5. Invalidate OTP (one-time use)
        
        Args:
            data: VerifyResetOTPRequest with email and otp
            
        Returns:
            VerifyResetOTPResponse with reset_token
        """
        email_lower = data.email.lower()
        
        # -----------------------------------------------------------------
        # Step 1: Find User
        # -----------------------------------------------------------------
        email_hash = generate_hash(email_lower)
        user = self._get_user_by_email_hash(email_hash)
        
        if not user:
            logger.warning(f"Verify reset OTP for non-existent email: {mask_email(email_lower)}")
            raise AppException(
                message="Invalid OTP or email.",
                error_code=ErrorCode.OTP_INVALID,
                status_code=400
            )
        
        # -----------------------------------------------------------------
        # Step 2: Find Active Password Reset OTP
        # -----------------------------------------------------------------
        otp_record = self._get_active_otp(
            user_id=user.user_id,
            verification_type="password_reset"
        )
        
        if not otp_record:
            logger.warning(f"No active reset OTP for user {user.user_id}")
            raise AppException(
                message="No active OTP found. Please request a new one.",
                error_code=ErrorCode.OTP_EXPIRED,
                status_code=400
            )
        
        # -----------------------------------------------------------------
        # Step 3: Check OTP Status
        # -----------------------------------------------------------------
        
        # Is user blocked?
        if otp_record.is_user_blocked:
            if otp_record.blocked_at:
                unblock_time = otp_record.blocked_at + timedelta(minutes=OTP_BLOCK_MINUTES)
                if datetime.utcnow() < unblock_time:
                    remaining_minutes = int((unblock_time - datetime.utcnow()).total_seconds() / 60) + 1
                    raise AppException(
                        message=f"Account temporarily blocked. Try again in {remaining_minutes} minutes.",
                        error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                        status_code=403,
                        details={"retry_after_minutes": remaining_minutes}
                    )
                else:
                    # Unblock
                    otp_record.is_user_blocked = False
                    otp_record.blocked_at = None
                    otp_record.remaining_retry = OTP_MAX_ATTEMPTS
        
        # Is OTP expired?
        if datetime.utcnow() > otp_record.otp_expires_at:
            logger.warning(f"Reset OTP expired for user {user.user_id}")
            raise AppException(
                message="OTP has expired. Please request a new one.",
                error_code=ErrorCode.OTP_EXPIRED,
                status_code=400
            )
        
        # Any attempts left?
        if otp_record.remaining_retry <= 0:
            otp_record.is_user_blocked = True
            otp_record.blocked_at = datetime.utcnow()
            self.db.commit()
            raise AppException(
                message=f"Maximum attempts exceeded. Account blocked for {OTP_BLOCK_MINUTES} minutes.",
                error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                status_code=403,
                details={"blocked_for_minutes": OTP_BLOCK_MINUTES}
            )
        
        # -----------------------------------------------------------------
        # Step 4: Verify OTP
        # -----------------------------------------------------------------
        is_valid = verify_otp(data.otp, otp_record.otp_hash)
        
        if not is_valid:
            otp_record.remaining_retry -= 1
            remaining = otp_record.remaining_retry
            
            if remaining <= 0:
                otp_record.is_user_blocked = True
                otp_record.blocked_at = datetime.utcnow()
                self.db.commit()
                raise AppException(
                    message=f"Maximum attempts exceeded. Account blocked for {OTP_BLOCK_MINUTES} minutes.",
                    error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                    status_code=403,
                    details={"blocked_for_minutes": OTP_BLOCK_MINUTES}
                )
            
            self.db.commit()
            raise AppException(
                message=f"Invalid OTP. {remaining} attempts remaining.",
                error_code=ErrorCode.OTP_INVALID,
                status_code=400,
                details={"attempts_remaining": remaining}
            )
        
        # -----------------------------------------------------------------
        # Step 5: OTP Valid - Generate Reset Token
        # -----------------------------------------------------------------
        
        # Invalidate OTP (one-time use)
        otp_record.is_otp_valid = False
        self.db.commit()
        
        # Generate temp token (10 minutes)
        reset_token = create_password_reset_token(
            user_id=str(user.user_id),
            expires_minutes=10
        )
        
        logger.info(f"Reset OTP verified for user {user.user_id}, temp token issued")
        
        return VerifyResetOTPResponse(
            success=True,
            message="OTP verified. You can now reset your password.",
            reset_token=reset_token,
            expires_in=600,  # 10 minutes
        )

    # =========================================================================
    # RESET PASSWORD (Step 3: Set New Password)
    # =========================================================================
    
    def reset_password(self, data: ResetPasswordRequest) -> ResetPasswordResponse:
        """
        Step 3 of password reset flow - Set new password.
        
        Flow:
        1. Verify reset_token (JWT)
        2. Find user
        3. Update password hash
        4. Invalidate all sessions (security)
        
        Args:
            data: ResetPasswordRequest with reset_token and new_password
            
        Returns:
            ResetPasswordResponse
        """
        
        # -----------------------------------------------------------------
        # Step 1: Verify Reset Token
        # -----------------------------------------------------------------
        try:
            payload = verify_password_reset_token(data.reset_token)
        except ValueError as e:
            logger.warning(f"Invalid reset token: {str(e)}")
            raise AppException(
                message="Invalid or expired reset link. Please request a new one.",
                error_code=ErrorCode.INVALID_TOKEN,
                status_code=400
            )
        
        user_id = payload.get("user_id")
        
        # -----------------------------------------------------------------
        # Step 2: Find User
        # -----------------------------------------------------------------
        user = self.db.query(User).filter(
            User.user_id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            logger.warning(f"Reset password for non-existent user: {user_id}")
            raise AppException(
                message="Invalid or expired reset link. Please request a new one.",
                error_code=ErrorCode.INVALID_TOKEN,
                status_code=400
            )
        
        # -----------------------------------------------------------------
        # Step 3: Update Password
        # -----------------------------------------------------------------
        user.password_hash = hash_password(data.new_password)
        
        # -----------------------------------------------------------------
        # Step 4: Invalidate All Sessions (Security)
        # -----------------------------------------------------------------
        # After password change, log out from all devices
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_session_active == True
        ).update({
            "is_session_active": False,
            "session_ended_at": datetime.utcnow()
        })
        
        self.db.commit()
        
        logger.info(f"Password reset successful for user {user_id}, all sessions invalidated")
        
        return ResetPasswordResponse(
            success=True,
            message="Password reset successful. Please login with your new password."
        )

    # =========================================================================
    # GET PROFILE (Protected Route)
    # =========================================================================
    
    def get_profile(self, user_id: str) -> dict:
        """
        Get user profile by user_id.
        
        Called from protected endpoint - user_id comes from verified JWT.
        
        Flow:
        1. Find user by user_id
        2. Check if user is_active (could be banned after login)
        3. Decrypt PII (email, phone)
        4. Return profile data
        
        Note: No need to check is_email_verified because:
        - Unverified user cannot login
        - Cannot get valid JWT without login
        - If they reach here, they're verified
        
        Args:
            user_id: User's UUID (from access token)
            
        Returns:
            Dict with user profile data
        """
        # -----------------------------------------------------------------
        # Step 1: Find User
        # -----------------------------------------------------------------
        user = self.db.query(User).filter(
            User.user_id == user_id
        ).first()
        
        if not user:
            logger.warning(f"Get profile for non-existent user: {user_id}")
            raise AppException(
                message="User not found.",
                error_code=ErrorCode.USER_NOT_FOUND,
                status_code=404
            )
        
        # -----------------------------------------------------------------
        # Step 2: Check if user is active
        # -----------------------------------------------------------------
        if not user.is_active:
            logger.warning(f"Get profile for inactive/banned user: {user_id}")
            raise AppException(
                message="Account has been deactivated. Please contact support.",
                error_code=ErrorCode.USER_INACTIVE,
                status_code=403
            )
        
        # -----------------------------------------------------------------
        # Step 3: Decrypt PII
        # -----------------------------------------------------------------
        decrypted_email = decrypt_data(user.email_encrypted)
        decrypted_phone = decrypt_data(user.phone_encrypted) if user.phone_encrypted else None
        
        # -----------------------------------------------------------------
        # Step 4: Build and Return Profile
        # -----------------------------------------------------------------
        profile = {
            "user_id": str(user.user_id),
            "user_name": user.user_name,
            "email": decrypted_email,
            "phone_number": decrypted_phone,
            "is_email_verified": user.is_email_verified,
            "subscription_id": None,  # TODO: Fetch from subscription service
            "subscription_name": None,  # TODO: Fetch from subscription service
            "address": user.address,
            "pincode": user.pincode,
            "preferences": user.preferences,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        
        logger.info(f"Profile fetched for user {user_id}")
        
        return profile