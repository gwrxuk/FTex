"""
Transaction model for financial transaction monitoring.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Float, JSON, Text, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class TransactionType(str, Enum):
    """Types of financial transactions."""
    WIRE_TRANSFER = "wire_transfer"
    ACH = "ach"
    CARD_PAYMENT = "card_payment"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    INTERNAL_TRANSFER = "internal_transfer"
    CRYPTO = "crypto"
    TRADE = "trade"
    FEE = "fee"
    OTHER = "other"


class Transaction(Base):
    """
    Transaction model for storing and monitoring financial transactions.
    
    Used for AML transaction monitoring, fraud detection, and compliance reporting.
    """
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    
    # Transaction Details
    reference_number = Column(String(100), unique=True, index=True)
    amount = Column(Float, nullable=False, index=True)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Parties
    sender_entity_id = Column(String(36), ForeignKey("entities.id"), index=True)
    receiver_entity_id = Column(String(36), ForeignKey("entities.id"), index=True)
    sender_account = Column(String(100))
    receiver_account = Column(String(100))
    
    # Geographic Info
    sender_country = Column(String(3))
    receiver_country = Column(String(3))
    
    # Risk Assessment
    risk_score = Column(Float, default=0.0, index=True)
    risk_indicators = Column(JSON, default=list)
    is_flagged = Column(Integer, default=0, index=True)
    
    # Status
    status = Column(String(50), default="completed", index=True)
    
    # Timing
    transaction_date = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(DateTime)
    
    # Metadata
    channel = Column(String(50))  # online, branch, atm, mobile
    description = Column(Text)
    metadata = Column(JSON, default=dict)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Transaction {self.id}: {self.amount} {self.currency}>"
    
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            "id": self.id,
            "transaction_type": self.transaction_type.value,
            "reference_number": self.reference_number,
            "amount": self.amount,
            "currency": self.currency,
            "sender_entity_id": self.sender_entity_id,
            "receiver_entity_id": self.receiver_entity_id,
            "sender_account": self.sender_account,
            "receiver_account": self.receiver_account,
            "sender_country": self.sender_country,
            "receiver_country": self.receiver_country,
            "risk_score": self.risk_score,
            "risk_indicators": self.risk_indicators,
            "is_flagged": bool(self.is_flagged),
            "status": self.status,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "settlement_date": self.settlement_date.isoformat() if self.settlement_date else None,
            "channel": self.channel,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

