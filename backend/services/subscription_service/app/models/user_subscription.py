"""User Subscription Model - Links users to their subscribed plans."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.dependencies import Base


class UserSubscription(Base):
    """
    User's subscription to a plan.
    
    Key fields:
    - locked_price: Price at subscription time (doesn't change even if plan_prices changes)
    - current_period_start/end: Current billing period (for access control)
    - next_billing_date: When to charge next (NULL for one-time purchases)
    - sub_status: State machine for subscription lifecycle
    """
    
    __tablename__ = "user_subscriptions"
    
    # Primary Key
    sub_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User (cross-service reference, no FK constraint)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Plan and Price
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.plan_id"), nullable=False)
    price_id = Column(UUID(as_uuid=True), ForeignKey("plan_prices.price_id"), nullable=False)
    
    # Payment method for recurring charges (nullable for free plans)
    payment_method_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_methods.payment_method_id"), 
        nullable=True
    )
    
    # Locked price at subscription time (won't change even if plan price changes)
    locked_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    
    # Subscription Status
    # Values: trial, active, paused, past_due, cancelled, expired
    sub_status = Column(String(20), nullable=False, default="active")
    
    # Billing Period
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    
    # Next billing date (NULL for one-time, has value for recurring)
    next_billing_date = Column(DateTime, nullable=True)
    
    # Scheduled changes (for downgrades that take effect at period end)
    scheduled_plan_id = Column(UUID(as_uuid=True), nullable=True)
    scheduled_price_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paused_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    price = relationship("PlanPrice", back_populates="subscriptions")
    payment_method = relationship("PaymentMethod", back_populates="subscriptions")
    transactions = relationship("PaymentTransaction", back_populates="subscription")
    
    def __repr__(self):
        return f"<UserSubscription(sub_id={self.sub_id}, user_id={self.user_id}, status={self.sub_status})>"
