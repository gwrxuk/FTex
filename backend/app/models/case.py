"""
Case model for investigation case management.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Float, JSON, Text, Enum as SQLEnum, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class CaseStatus(str, Enum):
    """Case workflow status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    SAR_FILED = "sar_filed"
    CLOSED_NO_ACTION = "closed_no_action"
    CLOSED = "closed"


class Case(Base):
    """
    Case model for financial crime investigations.
    
    Cases consolidate related alerts and entities for comprehensive
    investigation and regulatory reporting.
    """
    __tablename__ = "cases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Case Identification
    case_number = Column(String(50), unique=True, index=True)
    
    # Case Classification
    case_type = Column(String(100), nullable=False, index=True)
    category = Column(String(100), index=True)
    priority = Column(Integer, default=3)  # 1=Highest, 5=Lowest
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.OPEN, index=True)
    
    # Case Details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    summary = Column(Text)
    
    # Related Entities
    primary_entity_id = Column(String(36), index=True)
    subject_entities = Column(JSON, default=list)
    
    # Risk Assessment
    overall_risk_score = Column(Float, default=0.0, index=True)
    risk_assessment = Column(JSON, default=dict)
    
    # Regulatory
    regulatory_category = Column(String(100))  # AML, Fraud, Sanctions, etc.
    sar_reference = Column(String(100))  # SAR filing reference
    sar_filed_date = Column(DateTime)
    
    # Assignment
    assigned_to = Column(String(100), index=True)
    assigned_team = Column(String(100))
    
    # Timeline
    opened_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Investigation
    investigation_notes = Column(Text)
    findings = Column(Text)
    recommendation = Column(Text)
    
    # Metadata
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    def __repr__(self):
        return f"<Case {self.case_number}: {self.title[:50]}>"
    
    def to_dict(self):
        """Convert case to dictionary."""
        return {
            "id": self.id,
            "case_number": self.case_number,
            "case_type": self.case_type,
            "category": self.category,
            "priority": self.priority,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "primary_entity_id": self.primary_entity_id,
            "subject_entities": self.subject_entities,
            "overall_risk_score": self.overall_risk_score,
            "risk_assessment": self.risk_assessment,
            "regulatory_category": self.regulatory_category,
            "sar_reference": self.sar_reference,
            "assigned_to": self.assigned_to,
            "assigned_team": self.assigned_team,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "investigation_notes": self.investigation_notes,
            "findings": self.findings,
            "recommendation": self.recommendation,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

