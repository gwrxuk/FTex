"""
Alert Management API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertListResponse


router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    category: Optional[str] = None,
    assigned_to: Optional[str] = None,
    entity_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List alerts with filtering and pagination.
    
    Supports filtering by status, severity, category, assignment,
    related entity, and detection date range.
    """
    query = select(Alert)
    
    # Apply filters
    if status:
        query = query.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)
    if category:
        query = query.where(Alert.category == category)
    if assigned_to:
        query = query.where(Alert.assigned_to == assigned_to)
    if entity_id:
        query = query.where(Alert.primary_entity_id == entity_id)
    if date_from:
        query = query.where(Alert.detected_at >= date_from)
    if date_to:
        query = query.where(Alert.detected_at <= date_to)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        Alert.severity.desc(),
        Alert.detected_at.desc()
    )
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return AlertListResponse(
        items=[AlertResponse.model_validate(a.to_dict()) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.get("/dashboard")
async def get_alert_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get alert statistics for dashboard display.
    
    Returns counts by status, severity, and category.
    """
    # Count by status
    status_counts = {}
    for status in AlertStatus:
        count = await db.scalar(
            select(func.count()).select_from(Alert).where(Alert.status == status)
        )
        status_counts[status.value] = count or 0
    
    # Count by severity
    severity_counts = {}
    for severity in AlertSeverity:
        count = await db.scalar(
            select(func.count()).select_from(Alert).where(Alert.severity == severity)
        )
        severity_counts[severity.value] = count or 0
    
    # Total counts
    total = await db.scalar(select(func.count()).select_from(Alert))
    open_alerts = await db.scalar(
        select(func.count()).select_from(Alert).where(
            Alert.status.in_([AlertStatus.NEW, AlertStatus.INVESTIGATING])
        )
    )
    
    return {
        "total_alerts": total or 0,
        "open_alerts": open_alerts or 0,
        "by_status": status_counts,
        "by_severity": severity_counts
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific alert by ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert.to_dict())


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(alert_data: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Create a new alert."""
    alert = Alert(**alert_data.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    return AlertResponse.model_validate(alert.to_dict())


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_data: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    update_data = alert_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    await db.commit()
    await db.refresh(alert)
    
    return AlertResponse.model_validate(alert.to_dict())


@router.post("/{alert_id}/assign")
async def assign_alert(
    alert_id: str,
    assigned_to: str,
    db: AsyncSession = Depends(get_db)
):
    """Assign an alert to an analyst."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.assigned_to = assigned_to
    alert.acknowledged_at = datetime.utcnow()
    if alert.status == AlertStatus.NEW:
        alert.status = AlertStatus.INVESTIGATING
    
    await db.commit()
    
    return {"message": "Alert assigned successfully", "alert_id": alert_id, "assigned_to": assigned_to}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution: str,  # "sar" or "false_positive"
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert with a disposition."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if resolution == "sar":
        alert.status = AlertStatus.RESOLVED_SAR
    elif resolution == "false_positive":
        alert.status = AlertStatus.RESOLVED_FALSE_POSITIVE
    else:
        alert.status = AlertStatus.CLOSED
    
    alert.resolved_at = datetime.utcnow()
    if notes:
        alert.investigation_notes = notes
    
    await db.commit()
    
    return {"message": "Alert resolved", "alert_id": alert_id, "resolution": resolution}


@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Escalate an alert for senior review."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = AlertStatus.ESCALATED
    alert.investigation_notes = f"{alert.investigation_notes or ''}\n\nEscalation Reason: {reason}"
    
    await db.commit()
    
    return {"message": "Alert escalated", "alert_id": alert_id}

