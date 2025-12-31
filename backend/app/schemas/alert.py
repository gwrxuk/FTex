"""
Alert Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.alert import AlertStatus, AlertSeverity


class AlertBase(BaseModel):
    """Base schema for alert data."""
    alert_type: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    detection_rule: Optional[str] = None
    confidence_score: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    primary_entity_id: Optional[str] = None
    related_entity_ids: Optional[List[str]] = None
    related_transaction_ids: Optional[List[str]] = None
    risk_score: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    risk_factors: Optional[List[str]] = None
    source_system: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    status: Optional[AlertStatus] = None
    severity: Optional[AlertSeverity] = None
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None
    case_id: Optional[str] = None


class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: str
    alert_type: str
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    title: str
    description: Optional[str] = None
    detection_rule: Optional[str] = None
    confidence_score: Optional[float] = None
    primary_entity_id: Optional[str] = None
    related_entity_ids: Optional[List[str]] = None
    related_transaction_ids: Optional[List[str]] = None
    risk_score: float
    risk_factors: Optional[List[str]] = None
    case_id: Optional[str] = None
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None
    detected_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    source_system: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    """Schema for paginated alert list."""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    pages: int

