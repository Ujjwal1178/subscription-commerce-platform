"""
User Model - Database table for user accounts
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

# Import Base from shared
import sys
sys.path.append("/app")  # For Docker
from shared.database.base import Base


class User(Base):
    """
    User account table.
    
    Stores user credentials and profile information.
    PII (email, phone) is stored encrypted with hash for lookups.
    """
    
    __tablename__ = "users"
    
    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    user_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # -------------------------------------------------------------------------
    # Basic Info
    # -------------------------------------------------------------------------
    user_name = Column(
        String(100), 
        nullable=False,
        comment="User's full name"
    )
    
    # -------------------------------------------------------------------------
    # Email (Encrypted + Hashed)
    # -------------------------------------------------------------------------
    email_hash = Column(
        String(64), 
        nullable=False, 
        unique=True, 
        index=True,
        comment="SHA256 hash of email for lookups"
    )
    email_encrypted = Column(
        Text, 
        nullable=False,
        comment="AES encrypted email for display"
    )
    
    # -------------------------------------------------------------------------
    # Phone (Encrypted only, no hash - rare lookups)
    # -------------------------------------------------------------------------
    phone_encrypted = Column(
        Text, 
        nullable=False,
        comment="AES encrypted phone number"
    )
    
    # -------------------------------------------------------------------------
    # Password
    # -------------------------------------------------------------------------
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # -------------------------------------------------------------------------
    # Status Flags
    # -------------------------------------------------------------------------
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Soft delete flag - False means deactivated"
    )
    is_email_verified = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Email verification status"
    )
    
    # -------------------------------------------------------------------------
    # Optional Fields (Future use)
    # -------------------------------------------------------------------------
    address = Column(
        Text, 
        nullable=True,
        comment="User address"
    )
    pincode = Column(
        String(10), 
        nullable=True,
        comment="Postal code"
    )
    preferences = Column(
        JSONB, 
        nullable=True,
        comment="User preferences like theme, notifications etc"
    )
    
    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        comment="Account creation timestamp"
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    # One user can have many sessions
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # One user can have many OTP records
    otp_records = relationship("OTPVerification", back_populates="user", cascade="all, delete-orphan")
    
    # -------------------------------------------------------------------------
    # String representation (for debugging)
    # -------------------------------------------------------------------------
    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name={self.user_name})>"
