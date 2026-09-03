"""Payment Transaction Model - Complete payment history for audit and debugging."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.dependencies import Base


class PaymentTransaction(Base):
    """
    Payment history for each subscription.
    
    One subscription → Many transactions over time.
    
    Key fields:
    - idempotency_key: Prevents duplicate charges on retry (critical!)
    - provider_transaction_id: Stripe's transaction ID for reconciliation
    - attempt_number: Track retry attempts
    - failure_reason: Why payment failed (for debugging)
    """
    
    __tablename__ = "payment_transactions"
    
    # Primary Key
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Subscription this payment is for
    sub_id = Column(UUID(as_uuid=True), ForeignKey("user_subscriptions.sub_id"), nullable=False)
    
    # User (denormalized for easier queries)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Payment method used
    payment_method_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("payment_methods.payment_method_id"), 
        nullable=True  # Can be null if free plan
    )
    
    # Amount
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    
    # Transaction Status: pending, success, failed, refunded
    status = Column(String(20), nullable=False, default="pending")
    
    # Provider Info (for reconciliation with Stripe/Razorpay)
    provider_transaction_id = Column(String(255), nullable=True)  # pi_3N2abc (Stripe ID)
    
    # Failure Info
    failure_reason = Column(Text, nullable=True)  # "Card declined", "Insufficient funds"
    
    # Retry tracking
    attempt_number = Column(Integer, nullable=False, default=1)
    
    # Idempotency (CRITICAL - prevents duplicate charges)
    # Format: {sub_id}_{period_start}_{attempt}
    idempotency_key = Column(String(255), nullable=False, unique=True, index=True)
    
    # What billing period is this payment for?
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    subscription = relationship("UserSubscription", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    
    def __repr__(self):
        return f"<PaymentTransaction(id={self.transaction_id}, amount={self.amount}, status={self.status})>"
