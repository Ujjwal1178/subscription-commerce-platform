"""User Model - Database table for user accounts."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

import sys
sys.path.append("/app")
from shared.database.base import Base


class User(Base):
    """User account table. PII (email, phone) stored encrypted with hash for lookups."""
    
    __tablename__ = "users"
    
    # Primary Key
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Info
    user_name = Column(String(100), nullable=False)
    
    # Email (Encrypted + Hashed for lookups)
    email_hash = Column(String(64), nullable=False, unique=True, index=True)
    email_encrypted = Column(Text, nullable=False)
    
    # Phone (Encrypted only)
    phone_encrypted = Column(Text, nullable=False)
    
    # Password
    password_hash = Column(String(255), nullable=False)
    
    # Status Flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    
    # Optional Fields
    address = Column(Text, nullable=True)
    pincode = Column(String(10), nullable=True)
    preferences = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    otp_records = relationship("OTPVerification", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name={self.user_name})>"
