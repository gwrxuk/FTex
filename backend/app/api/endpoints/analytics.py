"""
Analytics API endpoints for risk assessment and pattern detection.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.models.entity import Entity
from app.models.transaction import Transaction
from app.models.alert import Alert


router = APIRouter()


@router.get("/risk-distribution")
async def get_risk_distribution(db: AsyncSession = Depends(get_db)):
    """
    Get risk score distribution across all entities.
    
    Returns histogram data for risk visualization.
    """
    # Define risk buckets
    buckets = [
        ("very_low", 0, 0.2),
        ("low", 0.2, 0.4),
        ("medium", 0.4, 0.6),
        ("high", 0.6, 0.8),
        ("critical", 0.8, 1.0)
    ]
    
    distribution = {}
    for name, low, high in buckets:
        count = await db.scalar(
            select(func.count()).select_from(Entity).where(
                and_(Entity.risk_score >= low, Entity.risk_score < high)
            )
        )
        distribution[name] = count or 0
    
    # Handle edge case for score = 1.0
    critical_count = await db.scalar(
        select(func.count()).select_from(Entity).where(Entity.risk_score == 1.0)
    )
    distribution["critical"] = distribution.get("critical", 0) + (critical_count or 0)
    
    return {"distribution": distribution, "buckets": buckets}


@router.get("/transaction-trends")
async def get_transaction_trends(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction volume trends over time.
    
    Returns time series data for charting.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query transactions grouped by date
    query = select(
        func.date(Transaction.transaction_date).label("date"),
        func.count().label("count"),
        func.sum(Transaction.amount).label("volume"),
        func.avg(Transaction.risk_score).label("avg_risk")
    ).where(
        Transaction.transaction_date >= start_date
    ).group_by(
        func.date(Transaction.transaction_date)
    ).order_by(
        func.date(Transaction.transaction_date)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    trends = [
        {
            "date": str(row.date),
            "count": row.count,
            "volume": float(row.volume or 0),
            "avg_risk": float(row.avg_risk or 0)
        }
        for row in rows
    ]
    
    return {"trends": trends, "period_days": days, "granularity": granularity}


@router.get("/alert-patterns")
async def get_alert_patterns(
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze alert patterns and detection rule effectiveness.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Alerts by detection rule
    rule_query = select(
        Alert.detection_rule,
        func.count().label("count"),
        func.avg(Alert.confidence_score).label("avg_confidence")
    ).where(
        Alert.detected_at >= start_date
    ).group_by(
        Alert.detection_rule
    ).order_by(
        func.count().desc()
    ).limit(10)
    
    result = await db.execute(rule_query)
    by_rule = [
        {
            "rule": row.detection_rule,
            "count": row.count,
            "avg_confidence": float(row.avg_confidence or 0)
        }
        for row in result.all()
    ]
    
    # Alerts by category
    category_query = select(
        Alert.category,
        func.count().label("count")
    ).where(
        Alert.detected_at >= start_date
    ).group_by(
        Alert.category
    )
    
    result = await db.execute(category_query)
    by_category = {row.category: row.count for row in result.all()}
    
    return {
        "by_detection_rule": by_rule,
        "by_category": by_category,
        "period_days": days
    }


@router.get("/high-risk-entities")
async def get_high_risk_entities(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get entities with highest risk scores for prioritization.
    """
    query = select(Entity).order_by(Entity.risk_score.desc()).limit(limit)
    result = await db.execute(query)
    entities = result.scalars().all()
    
    return {
        "entities": [
            {
                "id": e.id,
                "name": e.name,
                "entity_type": e.entity_type.value,
                "risk_score": e.risk_score,
                "risk_factors": e.risk_factors,
                "is_sanctioned": bool(e.is_sanctioned),
                "is_pep": bool(e.is_pep)
            }
            for e in entities
        ]
    }


@router.get("/network-statistics")
async def get_network_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get overall network statistics for the entity graph.
    """
    # Total entities
    entity_count = await db.scalar(select(func.count()).select_from(Entity))
    
    # Entity types breakdown
    type_query = select(
        Entity.entity_type,
        func.count().label("count")
    ).group_by(Entity.entity_type)
    
    result = await db.execute(type_query)
    by_type = {row.entity_type.value: row.count for row in result.all()}
    
    # Transaction count
    transaction_count = await db.scalar(select(func.count()).select_from(Transaction))
    
    # Unique senders
    unique_senders = await db.scalar(
        select(func.count(func.distinct(Transaction.sender_entity_id)))
    )
    
    # Unique receivers
    unique_receivers = await db.scalar(
        select(func.count(func.distinct(Transaction.receiver_entity_id)))
    )
    
    return {
        "total_entities": entity_count or 0,
        "entities_by_type": by_type,
        "total_transactions": transaction_count or 0,
        "unique_senders": unique_senders or 0,
        "unique_receivers": unique_receivers or 0
    }


@router.post("/calculate-risk")
async def calculate_entity_risk(
    entity_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Recalculate risk score for an entity based on multiple factors.
    
    Considers:
    - Transaction patterns
    - Associated entities
    - Sanctions/PEP status
    - Historical alerts
    """
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        return {"error": "Entity not found"}
    
    risk_factors = []
    risk_score = 0.0
    
    # Base risk from sanctions/PEP
    if entity.is_sanctioned:
        risk_score += 0.4
        risk_factors.append("sanctioned_entity")
    if entity.is_pep:
        risk_score += 0.2
        risk_factors.append("politically_exposed_person")
    if entity.is_adverse_media:
        risk_score += 0.15
        risk_factors.append("adverse_media_coverage")
    
    # Transaction volume risk
    tx_count = await db.scalar(
        select(func.count()).select_from(Transaction).where(
            (Transaction.sender_entity_id == entity_id) |
            (Transaction.receiver_entity_id == entity_id)
        )
    )
    if (tx_count or 0) > 100:
        risk_score += 0.1
        risk_factors.append("high_transaction_volume")
    
    # Alert history risk
    alert_count = await db.scalar(
        select(func.count()).select_from(Alert).where(
            Alert.primary_entity_id == entity_id
        )
    )
    if (alert_count or 0) > 0:
        risk_score += min(0.15, (alert_count or 0) * 0.03)
        risk_factors.append("previous_alerts")
    
    # Cap at 1.0
    risk_score = min(1.0, risk_score)
    
    # Update entity
    entity.risk_score = risk_score
    entity.risk_factors = risk_factors
    await db.commit()
    
    return {
        "entity_id": entity_id,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "calculation_factors": {
            "transaction_count": tx_count or 0,
            "alert_count": alert_count or 0,
            "is_sanctioned": bool(entity.is_sanctioned),
            "is_pep": bool(entity.is_pep),
            "is_adverse_media": bool(entity.is_adverse_media)
        }
    }

