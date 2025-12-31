"""
Case Management API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.case import Case, CaseStatus
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseListResponse


router = APIRouter()


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    status: Optional[CaseStatus] = None,
    case_type: Optional[str] = None,
    category: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List investigation cases with filtering and pagination.
    """
    query = select(Case)
    
    # Apply filters
    if status:
        query = query.where(Case.status == status)
    if case_type:
        query = query.where(Case.case_type == case_type)
    if category:
        query = query.where(Case.category == category)
    if assigned_to:
        query = query.where(Case.assigned_to == assigned_to)
    if priority:
        query = query.where(Case.priority == priority)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        Case.priority.asc(),
        Case.opened_at.desc()
    )
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return CaseListResponse(
        items=[CaseResponse.model_validate(c.to_dict()) for c in cases],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.get("/dashboard")
async def get_case_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get case statistics for dashboard display.
    """
    # Count by status
    status_counts = {}
    for status in CaseStatus:
        count = await db.scalar(
            select(func.count()).select_from(Case).where(Case.status == status)
        )
        status_counts[status.value] = count or 0
    
    # Open cases
    open_count = await db.scalar(
        select(func.count()).select_from(Case).where(
            Case.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.PENDING_REVIEW])
        )
    )
    
    # SAR filed
    sar_count = await db.scalar(
        select(func.count()).select_from(Case).where(Case.status == CaseStatus.SAR_FILED)
    )
    
    # Average risk score
    avg_risk = await db.scalar(
        select(func.avg(Case.overall_risk_score))
    )
    
    return {
        "open_cases": open_count or 0,
        "sar_filed": sar_count or 0,
        "average_risk_score": float(avg_risk or 0),
        "by_status": status_counts
    }


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific case by ID."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return CaseResponse.model_validate(case.to_dict())


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(case_data: CaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new investigation case."""
    # Generate case number
    count = await db.scalar(select(func.count()).select_from(Case))
    case_number = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{(count or 0) + 1:05d}"
    
    case = Case(**case_data.model_dump(), case_number=case_number)
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case.to_dict())


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing case."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    update_data = case_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    await db.commit()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case.to_dict())


@router.post("/{case_id}/assign")
async def assign_case(
    case_id: str,
    assigned_to: str,
    team: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Assign a case to an analyst or team."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.assigned_to = assigned_to
    if team:
        case.assigned_team = team
    if case.status == CaseStatus.OPEN:
        case.status = CaseStatus.IN_PROGRESS
    
    await db.commit()
    
    return {"message": "Case assigned", "case_id": case_id, "assigned_to": assigned_to}


@router.post("/{case_id}/file-sar")
async def file_sar(
    case_id: str,
    sar_reference: str,
    db: AsyncSession = Depends(get_db)
):
    """Record SAR filing for a case."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.status = CaseStatus.SAR_FILED
    case.sar_reference = sar_reference
    case.sar_filed_date = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "SAR filed successfully",
        "case_id": case_id,
        "sar_reference": sar_reference
    }


@router.post("/{case_id}/close")
async def close_case(
    case_id: str,
    findings: str,
    recommendation: str,
    action_taken: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Close a case with findings and recommendation."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.status = CaseStatus.CLOSED if action_taken else CaseStatus.CLOSED_NO_ACTION
    case.findings = findings
    case.recommendation = recommendation
    case.closed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Case closed", "case_id": case_id}

