"""UserSession Model - Tracks user login sessions and devices."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import sys
sys.path.append("/app")
from shared.database.base import Base


class UserSession(Base):
    """User session table. Tracks login sessions per device for single/multi-device login."""
    
    __tablename__ = "user_sessions"
    
    # Primary Key
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Device Info
    device_id = Column(String(50), nullable=False, unique=True, index=True)
    device_name = Column(String(100), nullable=True)
    
    # Session Status
    is_session_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    session_started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_ended_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(session_id={self.session_id}, device={self.device_name})>"
