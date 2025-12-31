"""
Entity model for storing resolved entities.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class EntityType(str, Enum):
    """Types of entities in the system."""
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"
    ACCOUNT = "account"
    ADDRESS = "address"
    DEVICE = "device"
    PHONE = "phone"
    EMAIL = "email"


class Entity(Base):
    """
    Entity model representing resolved entities in the decision intelligence platform.
    
    Entities can be individuals, organizations, accounts, or other identifiable
    objects that have been resolved and linked across multiple data sources.
    """
    __tablename__ = "entities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Identification
    external_ids = Column(JSON, default=dict)  # {source: id} mapping
    
    # Risk Assessment
    risk_score = Column(Float, default=0.0, index=True)
    risk_factors = Column(JSON, default=list)
    
    # Status
    is_sanctioned = Column(Integer, default=0, index=True)
    is_pep = Column(Integer, default=0, index=True)  # Politically Exposed Person
    is_adverse_media = Column(Integer, default=0)
    
    # Metadata
    attributes = Column(JSON, default=dict)
    source_systems = Column(JSON, default=list)
    confidence_score = Column(Float, default=1.0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    # Graph reference
    neo4j_node_id = Column(String(50))
    
    def __repr__(self):
        return f"<Entity {self.id}: {self.name} ({self.entity_type})>"
    
    def to_dict(self):
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "external_ids": self.external_ids,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors,
            "is_sanctioned": bool(self.is_sanctioned),
            "is_pep": bool(self.is_pep),
            "is_adverse_media": bool(self.is_adverse_media),
            "attributes": self.attributes,
            "source_systems": self.source_systems,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

