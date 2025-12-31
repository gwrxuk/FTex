"""
Entity Pydantic schemas for request/response validation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.entity import EntityType


class EntityBase(BaseModel):
    """Base schema for entity data."""
    entity_type: EntityType
    name: str = Field(..., min_length=1, max_length=255)
    external_ids: Optional[Dict[str, str]] = None
    attributes: Optional[Dict[str, Any]] = None
    source_systems: Optional[List[str]] = None


class EntityCreate(EntityBase):
    """Schema for creating a new entity."""
    risk_score: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    is_sanctioned: Optional[bool] = False
    is_pep: Optional[bool] = False
    is_adverse_media: Optional[bool] = False


class EntityUpdate(BaseModel):
    """Schema for updating an entity."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    external_ids: Optional[Dict[str, str]] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_factors: Optional[List[str]] = None
    is_sanctioned: Optional[bool] = None
    is_pep: Optional[bool] = None
    is_adverse_media: Optional[bool] = None
    attributes: Optional[Dict[str, Any]] = None
    source_systems: Optional[List[str]] = None


class EntityResponse(BaseModel):
    """Schema for entity response."""
    id: str
    entity_type: str
    name: str
    external_ids: Optional[Dict[str, str]] = None
    risk_score: float
    risk_factors: Optional[List[str]] = None
    is_sanctioned: bool
    is_pep: bool
    is_adverse_media: bool
    attributes: Optional[Dict[str, Any]] = None
    source_systems: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class EntityListResponse(BaseModel):
    """Schema for paginated entity list."""
    items: List[EntityResponse]
    total: int
    page: int
    page_size: int
    pages: int

