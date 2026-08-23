"""
UserSession Model - Tracks user login sessions and devices
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import sys
sys.path.append("/app")
from shared.database.base import Base


class UserSession(Base):
    """
    User session table.
    
    Tracks login sessions per device.
    Supports:
    - Single device login (delete old sessions on new login)
    - Multi-device login (configurable limit)
    - Login history (soft delete)
    """
    
    __tablename__ = "user_sessions"
    
    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    session_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique session identifier"
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
    # Device Info
    # -------------------------------------------------------------------------
    device_id = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Device identifier - stored in JWT for validation"
    )
    device_name = Column(
        String(100),
        nullable=True,
        comment="Human readable device name - Chrome on Windows"
    )
    
    # -------------------------------------------------------------------------
    # Session Status
    # -------------------------------------------------------------------------
    is_session_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active session or ended (soft delete)"
    )
    
    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    session_started_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Login time"
    )
    session_ended_at = Column(
        DateTime,
        nullable=True,
        comment="Logout time (null if still active)"
    )
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Last refresh token usage"
    )
    
    # -------------------------------------------------------------------------
    # Relationship - Back to User
    # -------------------------------------------------------------------------
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(session_id={self.session_id}, device={self.device_name})>"
