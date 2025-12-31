"""
RFP/RFI Model for proposal management.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Enum as SQLEnum, ForeignKey
from app.core.database import Base
import uuid


class ProposalType(str, Enum):
    """Types of proposals."""
    RFP = "rfp"  # Request for Proposal
    RFI = "rfi"  # Request for Information
    RFQ = "rfq"  # Request for Quotation
    EOI = "eoi"  # Expression of Interest


class ProposalStatus(str, Enum):
    """Proposal workflow status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    NO_BID = "no_bid"
    WITHDRAWN = "withdrawn"


class ProposalPriority(str, Enum):
    """Proposal priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Proposal(Base):
    """
    RFP/RFI Proposal model for managing sales proposals.
    
    Tracks the full lifecycle of proposals from initial receipt
    through submission and outcome.
    """
    __tablename__ = "proposals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Proposal Identification
    proposal_number = Column(String(50), unique=True, index=True)
    proposal_type = Column(SQLEnum(ProposalType), nullable=False, index=True)
    
    # Client Information
    client_name = Column(String(255), nullable=False, index=True)
    client_industry = Column(String(100))
    client_country = Column(String(100))
    client_contact_name = Column(String(255))
    client_contact_email = Column(String(255))
    client_contact_phone = Column(String(50))
    
    # Proposal Details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    requirements_summary = Column(Text)
    
    # Classification
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.DRAFT, index=True)
    priority = Column(SQLEnum(ProposalPriority), default=ProposalPriority.MEDIUM, index=True)
    
    # Solution Areas
    solution_areas = Column(JSON, default=list)  # ["AML", "Fraud", "KYC", "Entity Resolution"]
    use_cases = Column(JSON, default=list)
    
    # Timeline
    received_date = Column(DateTime, index=True)
    due_date = Column(DateTime, index=True)
    submitted_date = Column(DateTime)
    decision_date = Column(DateTime)
    
    # Financials
    estimated_deal_value = Column(Float)
    currency = Column(String(3), default="USD")
    
    # Team
    lead_owner = Column(String(100), index=True)  # Primary owner
    team_members = Column(JSON, default=list)  # List of team member IDs
    reviewers = Column(JSON, default=list)
    
    # Content
    response_sections = Column(JSON, default=list)  # Structured response sections
    technical_requirements = Column(JSON, default=list)
    compliance_requirements = Column(JSON, default=list)
    
    # Attachments & Documents
    attachments = Column(JSON, default=list)  # File references
    
    # Evaluation
    win_probability = Column(Float, default=0.5)
    competition = Column(JSON, default=list)  # Known competitors
    differentiators = Column(JSON, default=list)
    risks = Column(JSON, default=list)
    
    # Outcome
    outcome_reason = Column(Text)  # Why won/lost
    lessons_learned = Column(Text)
    
    # Metadata
    tags = Column(JSON, default=list)
    notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    def __repr__(self):
        return f"<Proposal {self.proposal_number}: {self.title[:50]}>"
    
    def to_dict(self):
        """Convert proposal to dictionary."""
        return {
            "id": self.id,
            "proposal_number": self.proposal_number,
            "proposal_type": self.proposal_type.value if self.proposal_type else None,
            "client_name": self.client_name,
            "client_industry": self.client_industry,
            "client_country": self.client_country,
            "client_contact_name": self.client_contact_name,
            "client_contact_email": self.client_contact_email,
            "title": self.title,
            "description": self.description,
            "requirements_summary": self.requirements_summary,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "solution_areas": self.solution_areas,
            "use_cases": self.use_cases,
            "received_date": self.received_date.isoformat() if self.received_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "submitted_date": self.submitted_date.isoformat() if self.submitted_date else None,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "estimated_deal_value": self.estimated_deal_value,
            "currency": self.currency,
            "lead_owner": self.lead_owner,
            "team_members": self.team_members,
            "win_probability": self.win_probability,
            "competition": self.competition,
            "differentiators": self.differentiators,
            "risks": self.risks,
            "outcome_reason": self.outcome_reason,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ProposalSection(Base):
    """
    Individual sections/questions within an RFP/RFI.
    
    Allows tracking of individual response items and their status.
    """
    __tablename__ = "proposal_sections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_id = Column(String(36), ForeignKey("proposals.id"), index=True)
    
    # Section Details
    section_number = Column(String(50))
    title = Column(String(500))
    question = Column(Text)
    
    # Response
    response = Column(Text)
    response_status = Column(String(50), default="pending")  # pending, draft, complete, reviewed
    
    # Assignment
    assigned_to = Column(String(100))
    reviewer = Column(String(100))
    
    # Classification
    category = Column(String(100))  # technical, commercial, compliance, etc.
    is_mandatory = Column(Integer, default=1)
    
    # Scoring
    max_score = Column(Integer)
    weight = Column(Float, default=1.0)
    
    # Attachments
    attachments = Column(JSON, default=list)
    
    # Reusable Content
    content_library_refs = Column(JSON, default=list)  # References to reusable content
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "proposal_id": self.proposal_id,
            "section_number": self.section_number,
            "title": self.title,
            "question": self.question,
            "response": self.response,
            "response_status": self.response_status,
            "assigned_to": self.assigned_to,
            "reviewer": self.reviewer,
            "category": self.category,
            "is_mandatory": bool(self.is_mandatory),
            "max_score": self.max_score,
            "weight": self.weight
        }


class ContentLibrary(Base):
    """
    Reusable content library for RFP/RFI responses.
    
    Stores standard responses that can be reused across proposals.
    """
    __tablename__ = "content_library"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content Details
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Classification
    category = Column(String(100), index=True)  # technical, security, compliance, etc.
    subcategory = Column(String(100))
    solution_area = Column(String(100), index=True)
    
    # Metadata
    tags = Column(JSON, default=list)
    keywords = Column(JSON, default=list)  # For search
    
    # Version Control
    version = Column(String(20), default="1.0")
    is_current = Column(Integer, default=1)
    
    # Usage Stats
    usage_count = Column(Integer, default=0)
    last_used_date = Column(DateTime)
    
    # Review
    last_reviewed_date = Column(DateTime)
    reviewed_by = Column(String(100))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "subcategory": self.subcategory,
            "solution_area": self.solution_area,
            "tags": self.tags,
            "keywords": self.keywords,
            "version": self.version,
            "usage_count": self.usage_count,
            "last_reviewed_date": self.last_reviewed_date.isoformat() if self.last_reviewed_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

