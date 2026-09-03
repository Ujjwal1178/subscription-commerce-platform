"""Plan Model - Subscription plans like Free, Basic, Premium, Family."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.dependencies import Base


class Plan(Base):
    """Subscription plan definitions (what features user gets)."""
    
    __tablename__ = "plans"
    
    # Primary Key
    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Plan Info
    plan_name = Column(String(50), nullable=False, unique=True)
    plan_type = Column(String(30), nullable=True)  # basic, premium, family (for grouping)
    description = Column(String(500), nullable=True)
    
    # Features stored as JSON for flexibility
    # Example: {"screens": 4, "quality": "4k", "downloads": 25, "ads": false}
    plan_features = Column(JSONB, nullable=False, default={})
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    prices = relationship("PlanPrice", back_populates="plan", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan(plan_id={self.plan_id}, plan_name={self.plan_name})>"
