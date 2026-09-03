"""Payment Method Model - User's saved cards/UPI (tokenized, PCI compliant)."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.dependencies import Base


class PaymentMethod(Base):
    """
    User's payment methods (cards, UPI).
    
    IMPORTANT: We NEVER store actual card numbers!
    Only Stripe/Razorpay tokens are stored.
    """
    
    __tablename__ = "payment_methods"
    
    # Primary Key
    payment_method_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User who owns this payment method
    # Note: user_id references auth_db.users (cross-service, no FK constraint)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Payment Provider
    provider = Column(String(20), nullable=False)  # stripe, razorpay
    provider_token = Column(String(255), nullable=False)  # pm_1N2abc3XYZ (Stripe token)
    
    # Payment Type
    type = Column(String(20), nullable=False)  # card, upi, netbanking
    
    # Card Info (for display only, NOT sensitive)
    last_4_digits = Column(String(4), nullable=True)  # 4242
    card_brand = Column(String(20), nullable=True)    # visa, mastercard
    expiry_month = Column(Integer, nullable=True)     # 12
    expiry_year = Column(Integer, nullable=True)      # 2028
    
    # UPI Info
    upi_id = Column(String(100), nullable=True)  # user@okicici
    
    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="payment_method")
    transactions = relationship("PaymentTransaction", back_populates="payment_method")
    
    def __repr__(self):
        return f"<PaymentMethod(id={self.payment_method_id}, type={self.type}, last_4={self.last_4_digits})>"
