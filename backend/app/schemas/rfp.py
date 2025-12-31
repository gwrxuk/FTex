"""
RFP/RFI Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.rfp import ProposalType, ProposalStatus, ProposalPriority


class ProposalBase(BaseModel):
    """Base schema for proposal data."""
    proposal_type: ProposalType
    client_name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class ProposalCreate(ProposalBase):
    """Schema for creating a proposal."""
    client_industry: Optional[str] = None
    client_country: Optional[str] = None
    client_contact_name: Optional[str] = None
    client_contact_email: Optional[str] = None
    requirements_summary: Optional[str] = None
    priority: ProposalPriority = ProposalPriority.MEDIUM
    solution_areas: Optional[List[str]] = []
    use_cases: Optional[List[str]] = []
    received_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_deal_value: Optional[float] = None
    currency: str = "USD"
    lead_owner: Optional[str] = None
    team_members: Optional[List[str]] = []
    tags: Optional[List[str]] = []


class ProposalUpdate(BaseModel):
    """Schema for updating a proposal."""
    title: Optional[str] = None
    description: Optional[str] = None
    requirements_summary: Optional[str] = None
    status: Optional[ProposalStatus] = None
    priority: Optional[ProposalPriority] = None
    solution_areas: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    estimated_deal_value: Optional[float] = None
    lead_owner: Optional[str] = None
    team_members: Optional[List[str]] = None
    win_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    competition: Optional[List[str]] = None
    differentiators: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ProposalResponse(BaseModel):
    """Schema for proposal response."""
    id: str
    proposal_number: Optional[str] = None
    proposal_type: Optional[str] = None
    client_name: str
    client_industry: Optional[str] = None
    client_country: Optional[str] = None
    title: str
    description: Optional[str] = None
    requirements_summary: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    solution_areas: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    received_date: Optional[str] = None
    due_date: Optional[str] = None
    submitted_date: Optional[str] = None
    estimated_deal_value: Optional[float] = None
    currency: Optional[str] = None
    lead_owner: Optional[str] = None
    team_members: Optional[List[str]] = None
    win_probability: Optional[float] = None
    competition: Optional[List[str]] = None
    differentiators: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ProposalListResponse(BaseModel):
    """Schema for paginated proposal list."""
    items: List[ProposalResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Proposal Sections

class SectionCreate(BaseModel):
    """Schema for creating a proposal section."""
    section_number: Optional[str] = None
    title: str
    question: Optional[str] = None
    category: Optional[str] = None
    is_mandatory: bool = True
    max_score: Optional[int] = None
    weight: float = 1.0
    assigned_to: Optional[str] = None


class SectionUpdate(BaseModel):
    """Schema for updating a section."""
    response: Optional[str] = None
    response_status: Optional[str] = None
    assigned_to: Optional[str] = None
    reviewer: Optional[str] = None


class SectionResponse(BaseModel):
    """Schema for section response."""
    id: str
    proposal_id: str
    section_number: Optional[str] = None
    title: str
    question: Optional[str] = None
    response: Optional[str] = None
    response_status: str
    assigned_to: Optional[str] = None
    reviewer: Optional[str] = None
    category: Optional[str] = None
    is_mandatory: bool
    max_score: Optional[int] = None
    weight: float

    model_config = {"from_attributes": True}


# Content Library

class ContentCreate(BaseModel):
    """Schema for creating content library item."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    solution_area: Optional[str] = None
    tags: Optional[List[str]] = []
    keywords: Optional[List[str]] = []


class ContentUpdate(BaseModel):
    """Schema for updating content library item."""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    solution_area: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class ContentResponse(BaseModel):
    """Schema for content library response."""
    id: str
    title: str
    content: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    solution_area: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    version: str
    usage_count: int
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    """Schema for paginated content list."""
    items: List[ContentResponse]
    total: int
    page: int
    page_size: int
    pages: int

