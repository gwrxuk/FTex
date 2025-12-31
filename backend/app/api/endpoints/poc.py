"""
PoC/Trial and Product Demo Management API endpoints.

Manages proving engagements (PoCs, pilots, trials, prototypes) and
product demonstrations as referenced in lines 23 and 25 of plan.txt.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.poc import (
    ProvingEngagement, EngagementType, EngagementStatus,
    ProductDemo, DemoType, DemoScenario
)


router = APIRouter()


# ============================================
# Pydantic Schemas
# ============================================

class EngagementCreate(BaseModel):
    engagement_type: EngagementType
    client_name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    objectives: Optional[List[str]] = []
    success_criteria: Optional[List[str]] = []
    solution_areas: Optional[List[str]] = []
    use_cases: Optional[List[str]] = []
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    team_members: Optional[List[str]] = []
    environment_type: Optional[str] = None


class EngagementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[EngagementStatus] = None
    objectives: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    team_members: Optional[List[str]] = None
    milestones: Optional[List[dict]] = None
    deliverables: Optional[List[dict]] = None
    results_summary: Optional[str] = None
    metrics_achieved: Optional[dict] = None
    lessons_learned: Optional[str] = None


class DemoCreate(BaseModel):
    demo_type: DemoType
    client_name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    key_messages: Optional[List[str]] = []
    solution_areas: Optional[List[str]] = []
    use_cases_shown: Optional[List[str]] = []
    delivery_format: Optional[str] = "remote"
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = 60
    presenter: Optional[str] = None
    audience_type: Optional[str] = None


class DemoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    attendee_feedback: Optional[List[dict]] = None
    overall_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    strengths: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    outcome_notes: Optional[str] = None
    next_steps: Optional[List[str]] = None


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    solution_area: str
    target_audience: Optional[str] = None
    narrative: Optional[str] = None
    demo_steps: Optional[List[dict]] = []
    talking_points: Optional[List[str]] = []
    key_features: Optional[List[str]] = []
    estimated_duration: Optional[int] = 30


# ============================================
# Proving Engagement Endpoints
# ============================================

@router.get("/engagements")
async def list_engagements(
    engagement_type: Optional[EngagementType] = None,
    status: Optional[EngagementStatus] = None,
    client_name: Optional[str] = None,
    solution_area: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List PoC/Trial engagements with filtering.
    
    Supports filtering by type, status, client, solution area, and search.
    """
    query = select(ProvingEngagement)
    
    if engagement_type:
        query = query.where(ProvingEngagement.engagement_type == engagement_type)
    if status:
        query = query.where(ProvingEngagement.status == status)
    if client_name:
        query = query.where(ProvingEngagement.client_name.ilike(f"%{client_name}%"))
    if search:
        query = query.where(
            or_(
                ProvingEngagement.title.ilike(f"%{search}%"),
                ProvingEngagement.client_name.ilike(f"%{search}%")
            )
        )
    
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ProvingEngagement.created_at.desc())
    
    result = await db.execute(query)
    engagements = result.scalars().all()
    
    return {
        "items": [e.to_dict() for e in engagements],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0
    }


@router.get("/engagements/dashboard")
async def get_engagement_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get PoC/Trial dashboard statistics.
    """
    # Count by status
    status_counts = {}
    for status in EngagementStatus:
        count = await db.scalar(
            select(func.count()).select_from(ProvingEngagement).where(
                ProvingEngagement.status == status
            )
        )
        status_counts[status.value] = count or 0
    
    # Count by type
    type_counts = {}
    for etype in EngagementType:
        count = await db.scalar(
            select(func.count()).select_from(ProvingEngagement).where(
                ProvingEngagement.engagement_type == etype
            )
        )
        type_counts[etype.value] = count or 0
    
    # Active engagements
    active = status_counts.get("in_progress", 0)
    
    # Success rate
    successful = status_counts.get("successful", 0)
    completed = status_counts.get("completed", 0) + successful + status_counts.get("unsuccessful", 0)
    success_rate = (successful / completed * 100) if completed > 0 else 0
    
    return {
        "active_engagements": active,
        "success_rate": round(success_rate, 1),
        "by_status": status_counts,
        "by_type": type_counts
    }


@router.get("/engagements/{engagement_id}")
async def get_engagement(engagement_id: str, db: AsyncSession = Depends(get_db)):
    """Get specific engagement details."""
    result = await db.execute(
        select(ProvingEngagement).where(ProvingEngagement.id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    return engagement.to_dict()


@router.post("/engagements", status_code=201)
async def create_engagement(
    data: EngagementCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new PoC/Trial engagement."""
    # Generate engagement number
    count = await db.scalar(select(func.count()).select_from(ProvingEngagement))
    type_prefix = data.engagement_type.value.upper()[:3]
    engagement_number = f"{type_prefix}-{datetime.utcnow().strftime('%Y%m')}-{(count or 0) + 1:04d}"
    
    engagement = ProvingEngagement(
        **data.model_dump(),
        engagement_number=engagement_number
    )
    db.add(engagement)
    await db.commit()
    await db.refresh(engagement)
    
    return engagement.to_dict()


@router.put("/engagements/{engagement_id}")
async def update_engagement(
    engagement_id: str,
    data: EngagementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an engagement."""
    result = await db.execute(
        select(ProvingEngagement).where(ProvingEngagement.id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(engagement, field, value)
    
    await db.commit()
    await db.refresh(engagement)
    
    return engagement.to_dict()


@router.post("/engagements/{engagement_id}/start")
async def start_engagement(engagement_id: str, db: AsyncSession = Depends(get_db)):
    """Start an engagement."""
    result = await db.execute(
        select(ProvingEngagement).where(ProvingEngagement.id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    engagement.status = EngagementStatus.IN_PROGRESS
    engagement.actual_start_date = datetime.utcnow()
    await db.commit()
    
    return {"message": "Engagement started", "engagement_id": engagement_id}


@router.post("/engagements/{engagement_id}/complete")
async def complete_engagement(
    engagement_id: str,
    successful: bool,
    results_summary: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Complete an engagement with outcome."""
    result = await db.execute(
        select(ProvingEngagement).where(ProvingEngagement.id == engagement_id)
    )
    engagement = result.scalar_one_or_none()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    engagement.status = EngagementStatus.SUCCESSFUL if successful else EngagementStatus.UNSUCCESSFUL
    engagement.actual_end_date = datetime.utcnow()
    if results_summary:
        engagement.results_summary = results_summary
    
    await db.commit()
    
    return {"message": f"Engagement marked as {'successful' if successful else 'unsuccessful'}", "engagement_id": engagement_id}


# ============================================
# Product Demo Endpoints
# ============================================

@router.get("/demos")
async def list_demos(
    demo_type: Optional[DemoType] = None,
    status: Optional[str] = None,
    client_name: Optional[str] = None,
    presenter: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List product demonstrations with filtering.
    """
    query = select(ProductDemo)
    
    if demo_type:
        query = query.where(ProductDemo.demo_type == demo_type)
    if status:
        query = query.where(ProductDemo.status == status)
    if client_name:
        query = query.where(ProductDemo.client_name.ilike(f"%{client_name}%"))
    if presenter:
        query = query.where(ProductDemo.presenter == presenter)
    if date_from:
        query = query.where(ProductDemo.scheduled_date >= date_from)
    if date_to:
        query = query.where(ProductDemo.scheduled_date <= date_to)
    
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ProductDemo.scheduled_date.desc())
    
    result = await db.execute(query)
    demos = result.scalars().all()
    
    return {
        "items": [d.to_dict() for d in demos],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0
    }


@router.get("/demos/dashboard")
async def get_demo_dashboard(db: AsyncSession = Depends(get_db)):
    """Get demo statistics."""
    # Total demos
    total = await db.scalar(select(func.count()).select_from(ProductDemo))
    
    # Upcoming demos
    upcoming = await db.scalar(
        select(func.count()).select_from(ProductDemo).where(
            and_(
                ProductDemo.scheduled_date >= datetime.utcnow(),
                ProductDemo.status == "scheduled"
            )
        )
    )
    
    # Average rating
    avg_rating = await db.scalar(
        select(func.avg(ProductDemo.overall_rating)).where(
            ProductDemo.overall_rating.isnot(None)
        )
    )
    
    # By type
    type_counts = {}
    for dtype in DemoType:
        count = await db.scalar(
            select(func.count()).select_from(ProductDemo).where(
                ProductDemo.demo_type == dtype
            )
        )
        type_counts[dtype.value] = count or 0
    
    return {
        "total_demos": total or 0,
        "upcoming_demos": upcoming or 0,
        "average_rating": round(float(avg_rating or 0), 2),
        "by_type": type_counts
    }


@router.get("/demos/{demo_id}")
async def get_demo(demo_id: str, db: AsyncSession = Depends(get_db)):
    """Get specific demo details."""
    result = await db.execute(
        select(ProductDemo).where(ProductDemo.id == demo_id)
    )
    demo = result.scalar_one_or_none()
    
    if not demo:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    return demo.to_dict()


@router.post("/demos", status_code=201)
async def create_demo(
    data: DemoCreate,
    db: AsyncSession = Depends(get_db)
):
    """Schedule a new product demonstration."""
    count = await db.scalar(select(func.count()).select_from(ProductDemo))
    demo_number = f"DEMO-{datetime.utcnow().strftime('%Y%m')}-{(count or 0) + 1:04d}"
    
    demo = ProductDemo(
        **data.model_dump(),
        demo_number=demo_number,
        status="scheduled"
    )
    db.add(demo)
    await db.commit()
    await db.refresh(demo)
    
    return demo.to_dict()


@router.put("/demos/{demo_id}")
async def update_demo(
    demo_id: str,
    data: DemoUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a demo."""
    result = await db.execute(
        select(ProductDemo).where(ProductDemo.id == demo_id)
    )
    demo = result.scalar_one_or_none()
    
    if not demo:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(demo, field, value)
    
    await db.commit()
    await db.refresh(demo)
    
    return demo.to_dict()


@router.post("/demos/{demo_id}/complete")
async def complete_demo(
    demo_id: str,
    overall_rating: Optional[float] = None,
    outcome_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Mark demo as completed."""
    result = await db.execute(
        select(ProductDemo).where(ProductDemo.id == demo_id)
    )
    demo = result.scalar_one_or_none()
    
    if not demo:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    demo.status = "completed"
    demo.actual_date = datetime.utcnow()
    if overall_rating:
        demo.overall_rating = overall_rating
    if outcome_notes:
        demo.outcome_notes = outcome_notes
    
    await db.commit()
    
    return {"message": "Demo completed", "demo_id": demo_id}


# ============================================
# Demo Scenarios (Templates)
# ============================================

@router.get("/scenarios")
async def list_scenarios(
    solution_area: Optional[str] = None,
    target_audience: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List demo scenarios/templates."""
    query = select(DemoScenario).where(DemoScenario.is_active == 1)
    
    if solution_area:
        query = query.where(DemoScenario.solution_area == solution_area)
    if target_audience:
        query = query.where(DemoScenario.target_audience == target_audience)
    if search:
        query = query.where(
            or_(
                DemoScenario.name.ilike(f"%{search}%"),
                DemoScenario.description.ilike(f"%{search}%")
            )
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(DemoScenario.times_used.desc())
    
    result = await db.execute(query)
    scenarios = result.scalars().all()
    
    return {
        "items": [s.to_dict() for s in scenarios],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/scenarios", status_code=201)
async def create_scenario(
    data: ScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new demo scenario template."""
    scenario = DemoScenario(**data.model_dump())
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    
    return scenario.to_dict()


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific scenario."""
    result = await db.execute(
        select(DemoScenario).where(DemoScenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Increment usage count
    scenario.times_used += 1
    await db.commit()
    
    return scenario.to_dict()

