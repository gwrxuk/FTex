"""
Graph Analytics API endpoints for entity relationship visualization.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.neo4j_service import Neo4jService


router = APIRouter()


@router.get("/entity/{entity_id}/network")
async def get_entity_network(
    entity_id: str,
    depth: int = Query(2, ge=1, le=5),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get the relationship network for an entity.
    
    Returns nodes and edges for graph visualization.
    """
    neo4j_service = Neo4jService()
    
    try:
        network = await neo4j_service.get_entity_network(entity_id, depth, limit)
        return network
    except Exception as e:
        return {
            "nodes": [{"id": entity_id, "label": "Entity", "type": "unknown"}],
            "edges": [],
            "error": str(e)
        }


@router.get("/shortest-path")
async def find_shortest_path(
    source_id: str,
    target_id: str,
    max_depth: int = Query(10, ge=1, le=20)
):
    """
    Find the shortest path between two entities.
    """
    neo4j_service = Neo4jService()
    
    try:
        path = await neo4j_service.find_shortest_path(source_id, target_id, max_depth)
        return path
    except Exception as e:
        return {
            "path": [],
            "error": str(e)
        }


@router.get("/community-detection")
async def detect_communities(
    min_size: int = Query(3, ge=2, le=100)
):
    """
    Detect communities/clusters in the entity network.
    
    Uses graph algorithms to identify closely connected groups.
    """
    neo4j_service = Neo4jService()
    
    try:
        communities = await neo4j_service.detect_communities(min_size)
        return communities
    except Exception as e:
        return {
            "communities": [],
            "error": str(e)
        }


@router.get("/centrality")
async def calculate_centrality(
    algorithm: str = Query("pagerank", pattern="^(pagerank|betweenness|degree)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Calculate centrality metrics for entities in the network.
    
    Identifies the most influential or connected entities.
    """
    neo4j_service = Neo4jService()
    
    try:
        results = await neo4j_service.calculate_centrality(algorithm, limit)
        return results
    except Exception as e:
        return {
            "results": [],
            "algorithm": algorithm,
            "error": str(e)
        }


@router.post("/create-relationship")
async def create_relationship(
    source_id: str,
    target_id: str,
    relationship_type: str,
    properties: Optional[dict] = None
):
    """
    Create a relationship between two entities in the graph.
    """
    neo4j_service = Neo4jService()
    
    try:
        result = await neo4j_service.create_relationship(
            source_id, target_id, relationship_type, properties or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-propagation/{entity_id}")
async def analyze_risk_propagation(
    entity_id: str,
    depth: int = Query(3, ge=1, le=5)
):
    """
    Analyze how risk propagates through the network from a source entity.
    
    Returns entities at risk due to their connection to the source.
    """
    neo4j_service = Neo4jService()
    
    try:
        propagation = await neo4j_service.analyze_risk_propagation(entity_id, depth)
        return propagation
    except Exception as e:
        return {
            "source_entity": entity_id,
            "affected_entities": [],
            "error": str(e)
        }


@router.get("/transaction-flow/{entity_id}")
async def get_transaction_flow(
    entity_id: str,
    direction: str = Query("both", pattern="^(incoming|outgoing|both)$"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get transaction flow patterns for an entity.
    
    Shows money flow visualization data.
    """
    neo4j_service = Neo4jService()
    
    try:
        flow = await neo4j_service.get_transaction_flow(entity_id, direction, limit)
        return flow
    except Exception as e:
        return {
            "entity_id": entity_id,
            "flows": [],
            "error": str(e)
        }

