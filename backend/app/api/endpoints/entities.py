"""
Entity Resolution API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.entity import Entity, EntityType
from app.schemas.entity import EntityCreate, EntityUpdate, EntityResponse, EntityListResponse
from app.services.neo4j_service import Neo4jService


router = APIRouter()


@router.get("/", response_model=EntityListResponse)
async def list_entities(
    entity_type: Optional[EntityType] = None,
    risk_score_min: Optional[float] = None,
    risk_score_max: Optional[float] = None,
    is_sanctioned: Optional[bool] = None,
    is_pep: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List entities with filtering and pagination.
    
    Supports filtering by entity type, risk score range, sanctions status,
    PEP status, and full-text search on name.
    """
    query = select(Entity)
    
    # Apply filters
    if entity_type:
        query = query.where(Entity.entity_type == entity_type)
    if risk_score_min is not None:
        query = query.where(Entity.risk_score >= risk_score_min)
    if risk_score_max is not None:
        query = query.where(Entity.risk_score <= risk_score_max)
    if is_sanctioned is not None:
        query = query.where(Entity.is_sanctioned == (1 if is_sanctioned else 0))
    if is_pep is not None:
        query = query.where(Entity.is_pep == (1 if is_pep else 0))
    if search:
        query = query.where(Entity.name.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Entity.risk_score.desc())
    
    result = await db.execute(query)
    entities = result.scalars().all()
    
    return EntityListResponse(
        items=[EntityResponse.model_validate(e.to_dict()) for e in entities],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific entity by ID."""
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return EntityResponse.model_validate(entity.to_dict())


@router.post("/", response_model=EntityResponse, status_code=201)
async def create_entity(entity_data: EntityCreate, db: AsyncSession = Depends(get_db)):
    """Create a new entity."""
    entity = Entity(**entity_data.model_dump())
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    
    # Also create in Neo4j for graph analytics
    try:
        neo4j_service = Neo4jService()
        await neo4j_service.create_entity_node(entity)
    except Exception:
        pass  # Continue even if Neo4j fails
    
    return EntityResponse.model_validate(entity.to_dict())


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    entity_data: EntityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing entity."""
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    update_data = entity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)
    
    await db.commit()
    await db.refresh(entity)
    
    return EntityResponse.model_validate(entity.to_dict())


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an entity."""
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    await db.delete(entity)
    await db.commit()


@router.get("/{entity_id}/relationships")
async def get_entity_relationships(entity_id: str, depth: int = Query(2, ge=1, le=5)):
    """
    Get related entities using graph traversal.
    
    Returns entities connected to the specified entity up to the given depth.
    """
    neo4j_service = Neo4jService()
    relationships = await neo4j_service.get_entity_relationships(entity_id, depth)
    return {"entity_id": entity_id, "relationships": relationships, "depth": depth}


@router.post("/resolve")
async def resolve_entities(
    names: List[str],
    threshold: float = Query(0.8, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve a list of names to existing entities using fuzzy matching.
    
    Returns potential matches with confidence scores.
    """
    # This would typically use more sophisticated entity resolution
    # For now, doing simple name matching
    results = []
    for name in names:
        query = select(Entity).where(Entity.name.ilike(f"%{name}%")).limit(5)
        result = await db.execute(query)
        matches = result.scalars().all()
        results.append({
            "input": name,
            "matches": [
                {
                    "entity": EntityResponse.model_validate(e.to_dict()),
                    "confidence": 0.9  # Placeholder
                }
                for e in matches
            ]
        })
    
    return {"results": results}

