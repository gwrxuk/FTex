"""
Transaction Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    """Base schema for transaction data."""
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    sender_entity_id: Optional[str] = None
    receiver_entity_id: Optional[str] = None
    sender_account: Optional[str] = None
    receiver_account: Optional[str] = None
    sender_country: Optional[str] = Field(None, min_length=2, max_length=3)
    receiver_country: Optional[str] = Field(None, min_length=2, max_length=3)


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    reference_number: Optional[str] = None
    transaction_date: datetime
    settlement_date: Optional[datetime] = None
    channel: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: str
    transaction_type: str
    reference_number: Optional[str] = None
    amount: float
    currency: str
    sender_entity_id: Optional[str] = None
    receiver_entity_id: Optional[str] = None
    sender_account: Optional[str] = None
    receiver_account: Optional[str] = None
    sender_country: Optional[str] = None
    receiver_country: Optional[str] = None
    risk_score: float
    risk_indicators: Optional[List[Dict[str, Any]]] = None
    is_flagged: bool
    status: str
    transaction_date: Optional[str] = None
    settlement_date: Optional[str] = None
    channel: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TransactionStats(BaseModel):
    """Schema for transaction statistics."""
    period_days: int
    total_transactions: int
    total_volume: float
    flagged_transactions: int
    high_risk_transactions: int
    average_risk_score: float
    flagged_rate: float

