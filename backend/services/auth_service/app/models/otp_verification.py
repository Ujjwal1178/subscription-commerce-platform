"""
OTPVerification Model - Tracks OTP for email verification and password reset
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import sys
sys.path.append("/app")
from shared.database.base import Base


class OTPVerification(Base):
    """
    OTP verification table.
    
    Stores OTP records for:
    - Email verification (after registration)
    - Password reset (forgot password flow)
    
    Security features:
    - OTP stored as hash (not plain text)
    - Max 3 attempts before blocking
    - 20 minute block after 3 failures
    - 10 minute OTP expiry
    """
    
    __tablename__ = "otp_verifications"
    
    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    otp_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique OTP record identifier"
    )
    
    # -------------------------------------------------------------------------
    # Foreign Key - Link to User
    # -------------------------------------------------------------------------
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to user"
    )
    
    # -------------------------------------------------------------------------
    # OTP Data
    # -------------------------------------------------------------------------
    otp_hash = Column(
        String(64),
        nullable=False,
        comment="SHA256 hash of OTP (never store plain OTP!)"
    )
    verification_type = Column(
        String(20),
        nullable=False,
        comment="Type: email_verification or password_reset"
    )
    
    # -------------------------------------------------------------------------
    # Security - Attempt Tracking
    # -------------------------------------------------------------------------
    remaining_retry = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Attempts remaining (0 = blocked)"
    )
    is_user_blocked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Blocked after 3 failed attempts"
    )
    blocked_at = Column(
        DateTime,
        nullable=True,
        comment="When user was blocked"
    )
    
    # -------------------------------------------------------------------------
    # OTP Validity
    # -------------------------------------------------------------------------
    otp_created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="OTP generation time"
    )
    otp_expires_at = Column(
        DateTime,
        nullable=False,
        comment="OTP expiry time (10 min from creation)"
    )
    is_otp_valid = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="False when used or new OTP generated"
    )
    
    # -------------------------------------------------------------------------
    # Relationship - Back to User
    # -------------------------------------------------------------------------
    user = relationship("User", back_populates="otp_records")
    
    def __repr__(self):
        return f"<OTPVerification(otp_id={self.otp_id}, type={self.verification_type})>"
