"""
PoC/Trial and Product Demo Management Models.

Tracks proving engagements, prototypes, trials, and product demonstrations
as mentioned in the job requirements.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Enum as SQLEnum, ForeignKey
from app.core.database import Base
import uuid


class EngagementType(str, Enum):
    """Types of proving engagements."""
    POC = "poc"  # Proof of Concept
    PILOT = "pilot"
    TRIAL = "trial"
    PROTOTYPE = "prototype"
    WORKSHOP = "workshop"
    DEMO = "demo"
    BUSINESS_CASE = "business_case"


class EngagementStatus(str, Enum):
    """Engagement workflow status."""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    SUCCESSFUL = "successful"
    UNSUCCESSFUL = "unsuccessful"
    CANCELLED = "cancelled"


class DemoType(str, Enum):
    """Types of product demonstrations."""
    STANDARD = "standard"
    CUSTOM = "custom"
    DEEP_DIVE = "deep_dive"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    WEBINAR = "webinar"


class ProvingEngagement(Base):
    """
    PoC/Trial/Prototype Engagement tracking.
    
    Manages proving engagements from planning through execution and outcome.
    """
    __tablename__ = "proving_engagements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Engagement Identification
    engagement_number = Column(String(50), unique=True, index=True)
    engagement_type = Column(SQLEnum(EngagementType), nullable=False, index=True)
    
    # Client Information
    client_name = Column(String(255), nullable=False, index=True)
    client_industry = Column(String(100))
    client_country = Column(String(100))
    client_contact_name = Column(String(255))
    client_contact_email = Column(String(255))
    
    # Engagement Details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    objectives = Column(JSON, default=list)  # List of objectives
    success_criteria = Column(JSON, default=list)  # Measurable success criteria
    
    # Status
    status = Column(SQLEnum(EngagementStatus), default=EngagementStatus.PLANNING, index=True)
    
    # Solution Areas
    solution_areas = Column(JSON, default=list)  # ["AML", "Fraud", "KYC", etc.]
    use_cases = Column(JSON, default=list)
    
    # Timeline
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Resources
    team_members = Column(JSON, default=list)
    infrastructure_requirements = Column(JSON, default=dict)
    data_requirements = Column(JSON, default=dict)
    
    # Technical Setup
    environment_type = Column(String(50))  # cloud, on-prem, hybrid
    environment_details = Column(JSON, default=dict)
    data_volumes = Column(JSON, default=dict)  # records, transactions, etc.
    integrations = Column(JSON, default=list)  # Systems to integrate
    
    # Execution
    milestones = Column(JSON, default=list)
    deliverables = Column(JSON, default=list)
    risks = Column(JSON, default=list)
    issues = Column(JSON, default=list)
    
    # Results
    results_summary = Column(Text)
    metrics_achieved = Column(JSON, default=dict)  # Actual vs target
    customer_feedback = Column(Text)
    lessons_learned = Column(Text)
    
    # Follow-up
    next_steps = Column(JSON, default=list)
    proposal_id = Column(String(36))  # Link to RFP if applicable
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "engagement_number": self.engagement_number,
            "engagement_type": self.engagement_type.value if self.engagement_type else None,
            "client_name": self.client_name,
            "client_industry": self.client_industry,
            "client_country": self.client_country,
            "title": self.title,
            "description": self.description,
            "objectives": self.objectives,
            "success_criteria": self.success_criteria,
            "status": self.status.value if self.status else None,
            "solution_areas": self.solution_areas,
            "use_cases": self.use_cases,
            "planned_start_date": self.planned_start_date.isoformat() if self.planned_start_date else None,
            "planned_end_date": self.planned_end_date.isoformat() if self.planned_end_date else None,
            "actual_start_date": self.actual_start_date.isoformat() if self.actual_start_date else None,
            "actual_end_date": self.actual_end_date.isoformat() if self.actual_end_date else None,
            "team_members": self.team_members,
            "environment_type": self.environment_type,
            "milestones": self.milestones,
            "deliverables": self.deliverables,
            "results_summary": self.results_summary,
            "metrics_achieved": self.metrics_achieved,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ProductDemo(Base):
    """
    Product Demonstration management.
    
    Tracks demo configurations, delivery, and feedback.
    """
    __tablename__ = "product_demos"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Demo Identification
    demo_number = Column(String(50), unique=True, index=True)
    demo_type = Column(SQLEnum(DemoType), nullable=False, index=True)
    
    # Client/Prospect
    client_name = Column(String(255), nullable=False)
    client_industry = Column(String(100))
    attendees = Column(JSON, default=list)  # List of attendee details
    audience_type = Column(String(100))  # executive, technical, end-user
    
    # Demo Content
    title = Column(String(500), nullable=False)
    description = Column(Text)
    key_messages = Column(JSON, default=list)
    solution_areas = Column(JSON, default=list)
    use_cases_shown = Column(JSON, default=list)
    
    # Demo Configuration
    demo_environment = Column(String(100))  # Environment used
    dataset_used = Column(String(100))  # Demo data configuration
    customizations = Column(JSON, default=list)  # Custom configs for this demo
    
    # Delivery
    delivery_format = Column(String(50))  # in-person, remote, hybrid
    scheduled_date = Column(DateTime, index=True)
    actual_date = Column(DateTime)
    duration_minutes = Column(Integer)
    location = Column(String(255))
    
    # Presenter
    presenter = Column(String(100), index=True)
    co_presenters = Column(JSON, default=list)
    
    # Status
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled
    
    # Feedback
    attendee_feedback = Column(JSON, default=list)
    overall_rating = Column(Float)  # 1-5
    strengths = Column(JSON, default=list)
    improvements = Column(JSON, default=list)
    follow_up_questions = Column(JSON, default=list)
    
    # Related
    engagement_id = Column(String(36))  # Link to PoC if applicable
    proposal_id = Column(String(36))  # Link to RFP if applicable
    
    # Assets
    presentation_url = Column(String(500))
    recording_url = Column(String(500))
    materials = Column(JSON, default=list)  # Supporting materials
    
    # Outcome
    outcome_notes = Column(Text)
    next_steps = Column(JSON, default=list)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "demo_number": self.demo_number,
            "demo_type": self.demo_type.value if self.demo_type else None,
            "client_name": self.client_name,
            "client_industry": self.client_industry,
            "attendees": self.attendees,
            "audience_type": self.audience_type,
            "title": self.title,
            "description": self.description,
            "key_messages": self.key_messages,
            "solution_areas": self.solution_areas,
            "use_cases_shown": self.use_cases_shown,
            "delivery_format": self.delivery_format,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "duration_minutes": self.duration_minutes,
            "presenter": self.presenter,
            "status": self.status,
            "overall_rating": self.overall_rating,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DemoScenario(Base):
    """
    Reusable demo scenarios/scripts.
    
    Templates for consistent demo delivery across solution areas.
    """
    __tablename__ = "demo_scenarios"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Scenario Details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    solution_area = Column(String(100), index=True)
    target_audience = Column(String(100))  # executive, technical, end-user
    
    # Content
    narrative = Column(Text)  # The story/flow
    demo_steps = Column(JSON, default=list)  # Step-by-step guide
    talking_points = Column(JSON, default=list)
    key_features = Column(JSON, default=list)  # Features to highlight
    
    # Data Requirements
    required_data = Column(JSON, default=dict)
    sample_queries = Column(JSON, default=list)
    
    # Timing
    estimated_duration = Column(Integer)  # minutes
    
    # Usage
    times_used = Column(Integer, default=0)
    avg_rating = Column(Float)
    
    # Version Control
    version = Column(String(20), default="1.0")
    is_active = Column(Integer, default=1)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "solution_area": self.solution_area,
            "target_audience": self.target_audience,
            "narrative": self.narrative,
            "demo_steps": self.demo_steps,
            "talking_points": self.talking_points,
            "key_features": self.key_features,
            "estimated_duration": self.estimated_duration,
            "times_used": self.times_used,
            "avg_rating": self.avg_rating,
            "version": self.version,
            "is_active": bool(self.is_active)
        }

