"""Plan Price Model - Pricing options for each plan (monthly, yearly, etc.)."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.dependencies import Base


class PlanPrice(Base):
    """
    Pricing options for plans.
    
    One plan can have multiple prices:
    - Monthly recurring (₹149/month, auto-renews)
    - Monthly one-time (₹149, expires after 1 month)
    - Yearly one-time (₹1499, full payment upfront)
    - Yearly recurring (₹149/month for 12 months commitment)
    """
    
    __tablename__ = "plan_prices"
    
    # Primary Key
    price_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key to Plan
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.plan_id"), nullable=False)
    
    # Pricing Info
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly, quarterly
    duration_months = Column(Integer, nullable=False)    # 1, 3, 6, 12
    amount = Column(Numeric(10, 2), nullable=False)      # Price per payment
    currency = Column(String(3), nullable=False, default="INR")
    
    # Is this a recurring subscription or one-time purchase?
    is_recurring = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    plan = relationship("Plan", back_populates="prices")
    subscriptions = relationship("UserSubscription", back_populates="price")
    
    def __repr__(self):
        return f"<PlanPrice(price_id={self.price_id}, billing_cycle={self.billing_cycle}, amount={self.amount})>"
