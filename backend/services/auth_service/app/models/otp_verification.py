"""OTPVerification Model - Tracks OTP for email verification and password reset."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import sys
sys.path.append("/app")
from shared.database.base import Base


class OTPVerification(Base):
    """OTP verification table. Stores hashed OTP with attempt tracking and blocking."""
    
    __tablename__ = "otp_verifications"
    
    # Primary Key
    otp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # OTP Data
    otp_hash = Column(String(64), nullable=False)
    verification_type = Column(String(20), nullable=False)  # email_verification or password_reset
    
    # Attempt Tracking
    remaining_retry = Column(Integer, default=3, nullable=False)
    is_user_blocked = Column(Boolean, default=False, nullable=False)
    blocked_at = Column(DateTime, nullable=True)
    
    # OTP Validity
    otp_created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    otp_expires_at = Column(DateTime, nullable=False)
    is_otp_valid = Column(Boolean, default=True, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="otp_records")
    
    def __repr__(self):
        return f"<OTPVerification(otp_id={self.otp_id}, type={self.verification_type})>"
