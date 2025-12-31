"""
FTex Decision Intelligence API Endpoints

Exposes FTex's core technology capabilities:
- Entity Resolution
- Network Generation  
- Contextual Scoring
- Decision Intelligence
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.entity_resolution_engine import (
    EntityResolutionEngine,
    EntityRecord,
    ResolvedEntity
)
from app.services.network_generation import (
    NetworkGenerationEngine,
    RelationshipType
)
from app.services.contextual_scoring import (
    ContextualScoringEngine,
    RiskScore
)


router = APIRouter()


# ============================================
# Pydantic Models for Request/Response
# ============================================

class EntityRecordInput(BaseModel):
    """Input model for entity records."""
    id: str
    source_system: str
    entity_type: str = "individual"
    attributes: Dict[str, Any]


class EntityResolutionRequest(BaseModel):
    """Request model for entity resolution."""
    records: List[EntityRecordInput]
    match_threshold: float = Field(0.75, ge=0.0, le=1.0)
    blocking_strategies: List[str] = ["soundex", "ngram"]


class ResolvedEntityResponse(BaseModel):
    """Response model for resolved entity."""
    resolved_id: str
    canonical_name: str
    entity_type: str
    confidence_score: float
    source_record_ids: List[str]
    attributes: Dict[str, Any]
    match_scores: Dict[str, float]


class EntityResolutionResponse(BaseModel):
    """Response model for entity resolution."""
    input_record_count: int
    resolved_entity_count: int
    resolution_rate: float
    resolved_entities: List[ResolvedEntityResponse]


class NetworkNodeInput(BaseModel):
    """Input model for network node."""
    id: str
    entity_type: str
    name: str
    attributes: Dict[str, Any] = {}
    risk_score: float = 0.0


class NetworkEdgeInput(BaseModel):
    """Input model for network edge."""
    source_id: str
    target_id: str
    relationship_type: str
    attributes: Dict[str, Any] = {}


class NetworkGenerationRequest(BaseModel):
    """Request model for network generation."""
    nodes: List[NetworkNodeInput]
    edges: Optional[List[NetworkEdgeInput]] = []
    run_inference: bool = True
    transactions: Optional[List[Dict[str, Any]]] = []


class ScoringRequest(BaseModel):
    """Request model for contextual scoring."""
    entity: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class BatchScoringRequest(BaseModel):
    """Request model for batch scoring."""
    entities: List[Dict[str, Any]]


# ============================================
# Entity Resolution Endpoints
# ============================================

@router.post("/entity-resolution", response_model=EntityResolutionResponse)
async def resolve_entities(request: EntityResolutionRequest):
    """
    FTex Entity Resolution
    
    Resolves entities across multiple data sources using:
    - Blocking strategies for efficient candidate generation
    - Multi-algorithm fuzzy matching (Jaro-Winkler, Levenshtein, Jaccard, etc.)
    - Graph-based clustering
    - Canonical record generation with survivorship rules
    
    This is FTex's core capability for creating a single view of entities
    from disparate data sources.
    """
    # Convert input to internal format
    records = [
        EntityRecord(
            id=r.id,
            source_system=r.source_system,
            entity_type=r.entity_type,
            attributes=r.attributes,
            raw_data={}
        )
        for r in request.records
    ]
    
    # Run entity resolution
    engine = EntityResolutionEngine(
        match_threshold=request.match_threshold,
        blocking_strategies=request.blocking_strategies
    )
    
    resolved = engine.resolve(records)
    
    # Convert to response
    response_entities = []
    for entity in resolved:
        response_entities.append(ResolvedEntityResponse(
            resolved_id=entity.resolved_id,
            canonical_name=entity.canonical_name,
            entity_type=entity.entity_type,
            confidence_score=entity.confidence_score,
            source_record_ids=[r.id for r in entity.source_records],
            attributes=entity.attributes,
            match_scores=entity.match_scores
        ))
    
    # Calculate resolution rate (reduction in entities)
    resolution_rate = 1.0 - (len(resolved) / len(records)) if records else 0.0
    
    return EntityResolutionResponse(
        input_record_count=len(records),
        resolved_entity_count=len(resolved),
        resolution_rate=resolution_rate,
        resolved_entities=response_entities
    )


@router.post("/entity-resolution/compare")
async def compare_entities(
    entity_a: Dict[str, Any],
    entity_b: Dict[str, Any]
):
    """
    Compare two entities and return similarity scores.
    
    Uses multiple matching algorithms to determine if
    two records represent the same real-world entity.
    """
    from app.services.entity_resolution_engine import SimilarityScorer
    
    scorer = SimilarityScorer()
    
    name_a = entity_a.get('name', '')
    name_b = entity_b.get('name', '')
    
    scores = {
        'jaro_winkler': scorer.jaro_winkler_similarity(name_a, name_b),
        'levenshtein': scorer.levenshtein_similarity(name_a, name_b),
        'jaccard_bigram': scorer.jaccard_similarity(name_a, name_b, ngram=2),
        'jaccard_trigram': scorer.jaccard_similarity(name_a, name_b, ngram=3),
        'token_based': scorer.token_based_similarity(name_a, name_b),
        'phonetic': scorer.phonetic_similarity(name_a, name_b),
        'composite': scorer.composite_name_score(name_a, name_b)
    }
    
    # Additional attribute comparisons
    if entity_a.get('date_of_birth') and entity_b.get('date_of_birth'):
        scores['date_of_birth'] = 1.0 if entity_a['date_of_birth'] == entity_b['date_of_birth'] else 0.0
    
    if entity_a.get('national_id') and entity_b.get('national_id'):
        scores['national_id'] = 1.0 if entity_a['national_id'] == entity_b['national_id'] else 0.0
    
    # Overall recommendation
    composite_score = scores['composite']
    recommendation = "likely_match" if composite_score >= 0.8 else \
                     "possible_match" if composite_score >= 0.6 else \
                     "unlikely_match"
    
    return {
        'entity_a': name_a,
        'entity_b': name_b,
        'similarity_scores': scores,
        'composite_score': composite_score,
        'recommendation': recommendation
    }


# ============================================
# Network Generation Endpoints
# ============================================

@router.post("/network/generate")
async def generate_network(request: NetworkGenerationRequest):
    """
    FTex Network Generation
    
    Creates a knowledge graph from entities and relationships:
    - Builds nodes from resolved entities
    - Extracts explicit relationships
    - Infers implicit relationships (shared attributes, transaction patterns)
    - Calculates network metrics
    
    This enables FTex's graph-based analytics and visualization.
    """
    engine = NetworkGenerationEngine()
    
    # Create nodes
    for node in request.nodes:
        engine.create_node_from_entity(
            entity_id=node.id,
            entity_type=node.entity_type,
            name=node.name,
            attributes=node.attributes,
            risk_score=node.risk_score
        )
    
    # Create explicit edges
    for edge in request.edges:
        try:
            rel_type = RelationshipType(edge.relationship_type)
        except ValueError:
            rel_type = RelationshipType.RELATED_TO
        
        engine.create_edge(
            source_id=edge.source_id,
            target_id=edge.target_id,
            relationship_type=rel_type,
            attributes=edge.attributes
        )
    
    # Extract from transactions
    if request.transactions:
        engine.extract_relationships_from_transactions(request.transactions)
    
    # Run inference
    inferred_count = 0
    if request.run_inference:
        inferred_edges = engine.run_inference()
        inferred_count = len(inferred_edges)
    
    # Get summary
    summary = engine.get_network_summary()
    
    # Export to visualization format
    export = engine.export_to_neo4j_format()
    
    return {
        'summary': summary,
        'inferred_relationships': inferred_count,
        'network': export
    }


@router.post("/network/analyze/{entity_id}")
async def analyze_entity_network(
    entity_id: str,
    depth: int = Query(2, ge=1, le=5)
):
    """
    Analyze the network around a specific entity.
    
    Returns:
    - Network metrics (centrality, clustering)
    - Connected entities up to specified depth
    - Risk propagation analysis
    """
    engine = NetworkGenerationEngine()
    
    # In a real implementation, this would load from database/Neo4j
    # For demo, return structure
    
    return {
        'entity_id': entity_id,
        'depth': depth,
        'metrics': {
            'degree_centrality': 0.0,
            'clustering_coefficient': 0.0,
            'risk_exposure': 0.0
        },
        'connected_entities': [],
        'risk_propagation': {}
    }


@router.get("/network/path")
async def find_network_path(
    source_id: str,
    target_id: str,
    max_depth: int = Query(6, ge=1, le=10)
):
    """
    Find shortest path between two entities in the network.
    
    Used for:
    - Investigating relationships between entities
    - Understanding money flow paths
    - Compliance investigations
    """
    # Would use Neo4j pathfinding in real implementation
    return {
        'source_id': source_id,
        'target_id': target_id,
        'max_depth': max_depth,
        'path_found': False,
        'path': [],
        'path_length': -1
    }


# ============================================
# Contextual Scoring Endpoints
# ============================================

@router.post("/scoring/calculate")
async def calculate_risk_score(request: ScoringRequest):
    """
    FTex Contextual Scoring
    
    Calculates risk score using network context:
    - Sanctions/watchlist matching
    - PEP status
    - Jurisdiction risk
    - Transaction patterns
    - Network relationships (key FTex differentiator)
    - Behavioral anomalies
    
    Returns explainable risk score with contributing factors.
    """
    engine = ContextualScoringEngine()
    
    score = engine.calculate_score(
        entity=request.entity,
        context=request.context or {}
    )
    
    explanation = engine.explain_score(score)
    
    return {
        'entity_id': score.entity_id,
        'overall_score': score.overall_score,
        'risk_level': score.risk_level,
        'calculated_at': score.calculated_at.isoformat(),
        'explanation': explanation
    }


@router.post("/scoring/batch")
async def batch_calculate_scores(request: BatchScoringRequest):
    """
    Calculate risk scores for multiple entities.
    
    Efficient batch processing for screening large volumes.
    """
    engine = ContextualScoringEngine()
    
    results = []
    for entity in request.entities:
        score = engine.calculate_score(entity, {})
        results.append({
            'entity_id': entity.get('id', 'unknown'),
            'overall_score': score.overall_score,
            'risk_level': score.risk_level,
            'factor_count': len(score.factors)
        })
    
    # Summary statistics
    high_risk = sum(1 for r in results if r['risk_level'] in ['high', 'critical'])
    avg_score = sum(r['overall_score'] for r in results) / len(results) if results else 0
    
    return {
        'entity_count': len(results),
        'high_risk_count': high_risk,
        'average_score': avg_score,
        'scores': results
    }


@router.post("/scoring/explain")
async def explain_risk_score(
    entity_id: str,
    entity: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
):
    """
    Get detailed explanation of risk score.
    
    Provides full transparency into scoring factors and recommendations.
    """
    engine = ContextualScoringEngine()
    
    score = engine.calculate_score(entity, context or {})
    explanation = engine.explain_score(score)
    
    return explanation


# ============================================
# Decision Intelligence Endpoints
# ============================================

@router.post("/decision-intelligence/investigate")
async def investigate_entity(
    entity_id: str,
    include_network: bool = True,
    include_transactions: bool = True,
    include_alerts: bool = True
):
    """
    FTex Decision Intelligence Investigation
    
    Comprehensive view of an entity combining:
    - Resolved entity data (from entity resolution)
    - Network relationships (from network generation)
    - Risk assessment (from contextual scoring)
    - Transaction history
    - Related alerts and cases
    
    This is the complete FTex Decision Intelligence output.
    """
    # In real implementation, aggregate from all services
    return {
        'entity_id': entity_id,
        'entity': {
            'resolved_id': entity_id,
            'canonical_name': 'Entity Name',
            'entity_type': 'individual',
            'source_count': 0
        },
        'risk_assessment': {
            'overall_score': 0.0,
            'risk_level': 'low',
            'factors': []
        },
        'network': {
            'node_count': 0,
            'edge_count': 0,
            'high_risk_connections': 0
        } if include_network else None,
        'transactions': {
            'total_count': 0,
            'total_volume': 0,
            'flagged_count': 0
        } if include_transactions else None,
        'alerts': {
            'open_count': 0,
            'total_count': 0
        } if include_alerts else None,
        'recommendations': []
    }


@router.get("/decision-intelligence/summary")
async def get_platform_summary():
    """
    Get overall Decision Intelligence Platform summary.
    
    Returns metrics across all FTex capabilities.
    """
    return {
        'entity_resolution': {
            'total_source_records': 0,
            'resolved_entities': 0,
            'resolution_rate': 0.0
        },
        'network': {
            'total_nodes': 0,
            'total_edges': 0,
            'communities_detected': 0
        },
        'risk_scoring': {
            'entities_scored': 0,
            'high_risk_entities': 0,
            'average_score': 0.0
        },
        'alerts': {
            'total_alerts': 0,
            'open_alerts': 0,
            'critical_alerts': 0
        }
    }

