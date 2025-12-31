"""
Case Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.case import CaseStatus


class CaseBase(BaseModel):
    """Base schema for case data."""
    case_type: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    priority: int = Field(3, ge=1, le=5)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class CaseCreate(CaseBase):
    """Schema for creating a case."""
    primary_entity_id: Optional[str] = None
    subject_entities: Optional[List[str]] = None
    regulatory_category: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class CaseUpdate(BaseModel):
    """Schema for updating a case."""
    status: Optional[CaseStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    summary: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    investigation_notes: Optional[str] = None
    findings: Optional[str] = None
    recommendation: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class CaseResponse(BaseModel):
    """Schema for case response."""
    id: str
    case_number: Optional[str] = None
    case_type: str
    category: Optional[str] = None
    priority: int
    status: Optional[str] = None
    title: str
    description: Optional[str] = None
    summary: Optional[str] = None
    primary_entity_id: Optional[str] = None
    subject_entities: Optional[List[str]] = None
    overall_risk_score: float
    risk_assessment: Optional[Dict[str, Any]] = None
    regulatory_category: Optional[str] = None
    sar_reference: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    opened_at: Optional[str] = None
    due_date: Optional[str] = None
    closed_at: Optional[str] = None
    investigation_notes: Optional[str] = None
    findings: Optional[str] = None
    recommendation: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    """Schema for paginated case list."""
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int
    pages: int

