"""
Search API endpoints using OpenSearch for full-text search.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.services.opensearch_service import OpenSearchService


router = APIRouter()


@router.get("/entities")
async def search_entities(
    q: str = Query(..., min_length=2, description="Search query"),
    entity_types: Optional[List[str]] = Query(None),
    risk_min: Optional[float] = Query(None, ge=0, le=1),
    risk_max: Optional[float] = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Full-text search for entities using OpenSearch.
    
    Supports filtering by entity type and risk score range.
    """
    opensearch_service = OpenSearchService()
    
    # Build filters
    filters = {}
    if entity_types:
        filters["entity_type"] = entity_types
    if risk_min is not None or risk_max is not None:
        filters["risk_score"] = {
            "min": risk_min or 0,
            "max": risk_max or 1
        }
    
    try:
        results = await opensearch_service.search_entities(
            query=q,
            filters=filters,
            from_=(page - 1) * page_size,
            size=page_size
        )
        return results
    except Exception as e:
        return {
            "hits": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/transactions")
async def search_transactions(
    q: str = Query(..., min_length=2),
    amount_min: Optional[float] = Query(None, ge=0),
    amount_max: Optional[float] = Query(None, ge=0),
    currency: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Full-text search for transactions.
    """
    opensearch_service = OpenSearchService()
    
    filters = {}
    if amount_min is not None or amount_max is not None:
        filters["amount"] = {
            "min": amount_min,
            "max": amount_max
        }
    if currency:
        filters["currency"] = currency.upper()
    
    try:
        results = await opensearch_service.search_transactions(
            query=q,
            filters=filters,
            from_=(page - 1) * page_size,
            size=page_size
        )
        return results
    except Exception as e:
        return {
            "hits": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/alerts")
async def search_alerts(
    q: str = Query(..., min_length=2),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Full-text search for alerts.
    """
    opensearch_service = OpenSearchService()
    
    filters = {}
    if severity:
        filters["severity"] = severity.lower()
    if status:
        filters["status"] = status.lower()
    
    try:
        results = await opensearch_service.search_alerts(
            query=q,
            filters=filters,
            from_=(page - 1) * page_size,
            size=page_size
        )
        return results
    except Exception as e:
        return {
            "hits": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/global")
async def global_search(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """
    Search across all document types (entities, transactions, alerts, cases).
    
    Returns aggregated results from all indices.
    """
    opensearch_service = OpenSearchService()
    
    try:
        results = await opensearch_service.global_search(
            query=q,
            from_=(page - 1) * page_size,
            size=page_size
        )
        return results
    except Exception as e:
        return {
            "entities": [],
            "transactions": [],
            "alerts": [],
            "cases": [],
            "error": str(e)
        }


@router.get("/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get search suggestions for autocomplete functionality.
    """
    opensearch_service = OpenSearchService()
    
    try:
        suggestions = await opensearch_service.get_suggestions(q, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        return {
            "suggestions": [],
            "error": str(e)
        }


@router.post("/screening")
async def sanctions_screening(
    names: List[str],
    threshold: float = Query(0.8, ge=0.5, le=1.0)
):
    """
    Screen a list of names against sanctions and watchlists.
    
    Returns potential matches with confidence scores.
    """
    opensearch_service = OpenSearchService()
    
    results = []
    for name in names:
        try:
            matches = await opensearch_service.screen_name(name, threshold)
            results.append({
                "input": name,
                "matches": matches
            })
        except Exception as e:
            results.append({
                "input": name,
                "matches": [],
                "error": str(e)
            })
    
    return {"screening_results": results}

