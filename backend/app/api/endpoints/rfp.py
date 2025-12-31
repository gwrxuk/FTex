"""
RFP/RFI Management API endpoints.

Manages the full lifecycle of Request for Proposals (RFPs) and 
Request for Information (RFIs) including:
- Proposal creation and tracking
- Response section management
- Content library for reusable responses
- Team collaboration
- Win/loss analysis
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.core.database import get_db
from app.models.rfp import (
    Proposal, ProposalType, ProposalStatus, ProposalPriority,
    ProposalSection, ContentLibrary
)
from app.schemas.rfp import (
    ProposalCreate, ProposalUpdate, ProposalResponse, ProposalListResponse,
    SectionCreate, SectionUpdate, SectionResponse,
    ContentCreate, ContentUpdate, ContentResponse, ContentListResponse
)


router = APIRouter()


# ============================================
# Proposal Management
# ============================================

@router.get("/", response_model=ProposalListResponse)
async def list_proposals(
    proposal_type: Optional[ProposalType] = None,
    status: Optional[ProposalStatus] = None,
    priority: Optional[ProposalPriority] = None,
    client_name: Optional[str] = None,
    lead_owner: Optional[str] = None,
    solution_area: Optional[str] = None,
    due_before: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List RFPs/RFIs with filtering and pagination.
    
    Supports filtering by type, status, priority, client, owner,
    solution area, due date, and full-text search.
    """
    query = select(Proposal)
    
    # Apply filters
    if proposal_type:
        query = query.where(Proposal.proposal_type == proposal_type)
    if status:
        query = query.where(Proposal.status == status)
    if priority:
        query = query.where(Proposal.priority == priority)
    if client_name:
        query = query.where(Proposal.client_name.ilike(f"%{client_name}%"))
    if lead_owner:
        query = query.where(Proposal.lead_owner == lead_owner)
    if due_before:
        query = query.where(Proposal.due_date <= due_before)
    if search:
        query = query.where(
            or_(
                Proposal.title.ilike(f"%{search}%"),
                Proposal.client_name.ilike(f"%{search}%"),
                Proposal.description.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        Proposal.due_date.asc(),
        Proposal.priority.desc()
    )
    
    result = await db.execute(query)
    proposals = result.scalars().all()
    
    return ProposalListResponse(
        items=[ProposalResponse.model_validate(p.to_dict()) for p in proposals],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.get("/dashboard")
async def get_rfp_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get RFP/RFI dashboard statistics.
    
    Returns counts by status, priority, and type, plus key metrics.
    """
    # Count by status
    status_counts = {}
    for status in ProposalStatus:
        count = await db.scalar(
            select(func.count()).select_from(Proposal).where(Proposal.status == status)
        )
        status_counts[status.value] = count or 0
    
    # Count by type
    type_counts = {}
    for ptype in ProposalType:
        count = await db.scalar(
            select(func.count()).select_from(Proposal).where(Proposal.proposal_type == ptype)
        )
        type_counts[ptype.value] = count or 0
    
    # Active proposals (not closed)
    active_statuses = [ProposalStatus.DRAFT, ProposalStatus.IN_PROGRESS, ProposalStatus.REVIEW]
    active_count = await db.scalar(
        select(func.count()).select_from(Proposal).where(
            Proposal.status.in_(active_statuses)
        )
    )
    
    # Due this week
    from datetime import timedelta
    week_from_now = datetime.utcnow() + timedelta(days=7)
    due_soon = await db.scalar(
        select(func.count()).select_from(Proposal).where(
            and_(
                Proposal.due_date <= week_from_now,
                Proposal.status.in_(active_statuses)
            )
        )
    )
    
    # Win rate
    won_count = status_counts.get("won", 0)
    lost_count = status_counts.get("lost", 0)
    total_decided = won_count + lost_count
    win_rate = (won_count / total_decided * 100) if total_decided > 0 else 0
    
    # Total deal value (won proposals)
    total_won_value = await db.scalar(
        select(func.sum(Proposal.estimated_deal_value)).where(
            Proposal.status == ProposalStatus.WON
        )
    )
    
    return {
        "active_proposals": active_count or 0,
        "due_this_week": due_soon or 0,
        "win_rate": round(win_rate, 1),
        "total_won_value": float(total_won_value or 0),
        "by_status": status_counts,
        "by_type": type_counts
    }


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific proposal by ID."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    return ProposalResponse.model_validate(proposal.to_dict())


@router.post("/", response_model=ProposalResponse, status_code=201)
async def create_proposal(
    proposal_data: ProposalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new RFP/RFI proposal."""
    # Generate proposal number
    count = await db.scalar(select(func.count()).select_from(Proposal))
    type_prefix = proposal_data.proposal_type.value.upper()
    proposal_number = f"{type_prefix}-{datetime.utcnow().strftime('%Y%m')}-{(count or 0) + 1:04d}"
    
    proposal = Proposal(
        **proposal_data.model_dump(),
        proposal_number=proposal_number
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    
    return ProposalResponse.model_validate(proposal.to_dict())


@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: str,
    proposal_data: ProposalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing proposal."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    update_data = proposal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proposal, field, value)
    
    await db.commit()
    await db.refresh(proposal)
    
    return ProposalResponse.model_validate(proposal.to_dict())


@router.post("/{proposal_id}/submit")
async def submit_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Submit a proposal."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal.status = ProposalStatus.SUBMITTED
    proposal.submitted_date = datetime.utcnow()
    await db.commit()
    
    return {"message": "Proposal submitted successfully", "proposal_id": proposal_id}


@router.post("/{proposal_id}/outcome")
async def record_outcome(
    proposal_id: str,
    outcome: str,  # "won" or "lost"
    reason: Optional[str] = None,
    lessons_learned: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Record proposal outcome (won/lost)."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if outcome == "won":
        proposal.status = ProposalStatus.WON
    elif outcome == "lost":
        proposal.status = ProposalStatus.LOST
    else:
        raise HTTPException(status_code=400, detail="Invalid outcome. Use 'won' or 'lost'")
    
    proposal.decision_date = datetime.utcnow()
    proposal.outcome_reason = reason
    proposal.lessons_learned = lessons_learned
    
    await db.commit()
    
    return {"message": f"Proposal marked as {outcome}", "proposal_id": proposal_id}


@router.delete("/{proposal_id}", status_code=204)
async def delete_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a proposal (soft delete by setting status to withdrawn)."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal.status = ProposalStatus.WITHDRAWN
    await db.commit()


# ============================================
# Proposal Sections
# ============================================

@router.get("/{proposal_id}/sections", response_model=List[SectionResponse])
async def list_sections(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """List all sections for a proposal."""
    result = await db.execute(
        select(ProposalSection)
        .where(ProposalSection.proposal_id == proposal_id)
        .order_by(ProposalSection.section_number)
    )
    sections = result.scalars().all()
    return [SectionResponse.model_validate(s.to_dict()) for s in sections]


@router.post("/{proposal_id}/sections", response_model=SectionResponse, status_code=201)
async def create_section(
    proposal_id: str,
    section_data: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a section to a proposal."""
    # Verify proposal exists
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    section = ProposalSection(
        proposal_id=proposal_id,
        **section_data.model_dump()
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    
    return SectionResponse.model_validate(section.to_dict())


@router.put("/{proposal_id}/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    proposal_id: str,
    section_id: str,
    section_data: SectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a proposal section (add/edit response)."""
    result = await db.execute(
        select(ProposalSection).where(
            and_(
                ProposalSection.id == section_id,
                ProposalSection.proposal_id == proposal_id
            )
        )
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    update_data = section_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)
    
    await db.commit()
    await db.refresh(section)
    
    return SectionResponse.model_validate(section.to_dict())


# ============================================
# Content Library
# ============================================

@router.get("/library/content", response_model=ContentListResponse)
async def list_content(
    category: Optional[str] = None,
    solution_area: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List content library items.
    
    Provides reusable content for RFP/RFI responses.
    """
    query = select(ContentLibrary).where(ContentLibrary.is_current == 1)
    
    if category:
        query = query.where(ContentLibrary.category == category)
    if solution_area:
        query = query.where(ContentLibrary.solution_area == solution_area)
    if search:
        query = query.where(
            or_(
                ContentLibrary.title.ilike(f"%{search}%"),
                ContentLibrary.content.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        ContentLibrary.usage_count.desc()
    )
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(c.to_dict()) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.post("/library/content", response_model=ContentResponse, status_code=201)
async def create_content(
    content_data: ContentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add content to the library."""
    content = ContentLibrary(**content_data.model_dump())
    db.add(content)
    await db.commit()
    await db.refresh(content)
    
    return ContentResponse.model_validate(content.to_dict())


@router.get("/library/content/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific content library item."""
    result = await db.execute(
        select(ContentLibrary).where(ContentLibrary.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Increment usage count
    content.usage_count += 1
    content.last_used_date = datetime.utcnow()
    await db.commit()
    
    return ContentResponse.model_validate(content.to_dict())


@router.put("/library/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_data: ContentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a content library item."""
    result = await db.execute(
        select(ContentLibrary).where(ContentLibrary.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    update_data = content_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    
    # Update version
    major, minor = content.version.split(".")
    content.version = f"{major}.{int(minor) + 1}"
    
    await db.commit()
    await db.refresh(content)
    
    return ContentResponse.model_validate(content.to_dict())


@router.get("/analytics/win-loss")
async def get_win_loss_analytics(
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db)
):
    """
    Get win/loss analytics for proposals.
    
    Analyzes proposal outcomes for insights.
    """
    from datetime import timedelta
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    
    # Win/loss by solution area
    result = await db.execute(
        select(Proposal).where(
            and_(
                Proposal.decision_date >= start_date,
                Proposal.status.in_([ProposalStatus.WON, ProposalStatus.LOST])
            )
        )
    )
    proposals = result.scalars().all()
    
    by_solution_area = {}
    by_client_industry = {}
    total_won_value = 0
    total_lost_value = 0
    
    for p in proposals:
        # By solution area
        for area in (p.solution_areas or []):
            if area not in by_solution_area:
                by_solution_area[area] = {"won": 0, "lost": 0}
            if p.status == ProposalStatus.WON:
                by_solution_area[area]["won"] += 1
            else:
                by_solution_area[area]["lost"] += 1
        
        # By industry
        industry = p.client_industry or "Unknown"
        if industry not in by_client_industry:
            by_client_industry[industry] = {"won": 0, "lost": 0}
        if p.status == ProposalStatus.WON:
            by_client_industry[industry]["won"] += 1
            total_won_value += p.estimated_deal_value or 0
        else:
            by_client_industry[industry]["lost"] += 1
            total_lost_value += p.estimated_deal_value or 0
    
    return {
        "period_months": months,
        "total_proposals": len(proposals),
        "won": sum(1 for p in proposals if p.status == ProposalStatus.WON),
        "lost": sum(1 for p in proposals if p.status == ProposalStatus.LOST),
        "total_won_value": total_won_value,
        "total_lost_value": total_lost_value,
        "by_solution_area": by_solution_area,
        "by_client_industry": by_client_industry
    }

