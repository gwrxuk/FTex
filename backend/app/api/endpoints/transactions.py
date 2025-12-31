"""
Transaction Monitoring API endpoints.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    TransactionCreate, 
    TransactionResponse, 
    TransactionListResponse,
    TransactionStats
)


router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    transaction_type: Optional[TransactionType] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    currency: Optional[str] = None,
    sender_country: Optional[str] = None,
    receiver_country: Optional[str] = None,
    is_flagged: Optional[bool] = None,
    risk_score_min: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List transactions with comprehensive filtering.
    
    Supports filtering by type, amount range, currency, countries,
    flagged status, risk score, and date range.
    """
    query = select(Transaction)
    
    # Apply filters
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)
    if currency:
        query = query.where(Transaction.currency == currency.upper())
    if sender_country:
        query = query.where(Transaction.sender_country == sender_country.upper())
    if receiver_country:
        query = query.where(Transaction.receiver_country == receiver_country.upper())
    if is_flagged is not None:
        query = query.where(Transaction.is_flagged == (1 if is_flagged else 0))
    if risk_score_min is not None:
        query = query.where(Transaction.risk_score >= risk_score_min)
    if date_from:
        query = query.where(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.where(Transaction.transaction_date <= date_to)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Transaction.transaction_date.desc())
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t.to_dict()) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.get("/stats", response_model=TransactionStats)
async def get_transaction_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction statistics for the specified period.
    
    Returns aggregated metrics including total volume, count,
    flagged transactions, and risk distribution.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total transactions
    total_query = select(func.count()).select_from(Transaction).where(
        Transaction.transaction_date >= start_date
    )
    total_count = await db.scalar(total_query) or 0
    
    # Total volume
    volume_query = select(func.sum(Transaction.amount)).where(
        Transaction.transaction_date >= start_date
    )
    total_volume = await db.scalar(volume_query) or 0
    
    # Flagged transactions
    flagged_query = select(func.count()).select_from(Transaction).where(
        and_(
            Transaction.transaction_date >= start_date,
            Transaction.is_flagged == 1
        )
    )
    flagged_count = await db.scalar(flagged_query) or 0
    
    # Average risk score
    avg_risk_query = select(func.avg(Transaction.risk_score)).where(
        Transaction.transaction_date >= start_date
    )
    avg_risk = await db.scalar(avg_risk_query) or 0
    
    # High risk transactions (risk > 0.7)
    high_risk_query = select(func.count()).select_from(Transaction).where(
        and_(
            Transaction.transaction_date >= start_date,
            Transaction.risk_score >= 0.7
        )
    )
    high_risk_count = await db.scalar(high_risk_query) or 0
    
    return TransactionStats(
        period_days=days,
        total_transactions=total_count,
        total_volume=float(total_volume),
        flagged_transactions=flagged_count,
        high_risk_transactions=high_risk_count,
        average_risk_score=float(avg_risk),
        flagged_rate=flagged_count / total_count if total_count > 0 else 0
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific transaction by ID."""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse.model_validate(transaction.to_dict())


@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new transaction record."""
    transaction = Transaction(**transaction_data.model_dump())
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    return TransactionResponse.model_validate(transaction.to_dict())


@router.post("/{transaction_id}/flag")
async def flag_transaction(
    transaction_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Flag a transaction for investigation."""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    transaction.is_flagged = 1
    indicators = transaction.risk_indicators or []
    indicators.append({"type": "manual_flag", "reason": reason, "timestamp": datetime.utcnow().isoformat()})
    transaction.risk_indicators = indicators
    
    await db.commit()
    
    return {"message": "Transaction flagged successfully", "transaction_id": transaction_id}


@router.get("/{transaction_id}/related")
async def get_related_transactions(
    transaction_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Find related transactions based on parties, amounts, and timing.
    
    Returns transactions that share sender/receiver or similar patterns.
    """
    # Get the original transaction
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Find related by same sender or receiver
    related_query = select(Transaction).where(
        and_(
            Transaction.id != transaction_id,
            (
                (Transaction.sender_entity_id == transaction.sender_entity_id) |
                (Transaction.receiver_entity_id == transaction.receiver_entity_id) |
                (Transaction.sender_entity_id == transaction.receiver_entity_id) |
                (Transaction.receiver_entity_id == transaction.sender_entity_id)
            )
        )
    ).limit(limit).order_by(Transaction.transaction_date.desc())
    
    result = await db.execute(related_query)
    related = result.scalars().all()
    
    return {
        "transaction_id": transaction_id,
        "related_transactions": [TransactionResponse.model_validate(t.to_dict()) for t in related]
    }

