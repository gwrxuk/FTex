"""
OpenSearch service for full-text search and analytics.
"""

from typing import List, Dict, Any, Optional
from opensearchpy import AsyncOpenSearch
from app.core.config import settings


class OpenSearchService:
    """Service for interacting with OpenSearch."""
    
    def __init__(self):
        self.client = AsyncOpenSearch(
            hosts=[settings.OPENSEARCH_URL],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False
        )
        self.index_prefix = settings.OPENSEARCH_INDEX_PREFIX
    
    async def initialize_indices(self):
        """Create required indices if they don't exist."""
        indices = {
            f"{self.index_prefix}_entities": {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "entity_type": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard", "fields": {"keyword": {"type": "keyword"}}},
                        "external_ids": {"type": "object"},
                        "risk_score": {"type": "float"},
                        "is_sanctioned": {"type": "boolean"},
                        "is_pep": {"type": "boolean"},
                        "attributes": {"type": "object"},
                        "created_at": {"type": "date"}
                    }
                }
            },
            f"{self.index_prefix}_transactions": {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "transaction_type": {"type": "keyword"},
                        "amount": {"type": "float"},
                        "currency": {"type": "keyword"},
                        "description": {"type": "text"},
                        "risk_score": {"type": "float"},
                        "transaction_date": {"type": "date"}
                    }
                }
            },
            f"{self.index_prefix}_alerts": {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "alert_type": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "detected_at": {"type": "date"}
                    }
                }
            }
        }
        
        for index_name, index_config in indices.items():
            if not await self.client.indices.exists(index=index_name):
                await self.client.indices.create(index=index_name, body=index_config)
    
    async def search_entities(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        from_: int = 0,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search for entities."""
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "attributes.*"],
                    "fuzziness": "AUTO"
                }
            }
        ]
        
        filter_clauses = []
        if filters:
            if "entity_type" in filters:
                filter_clauses.append({"terms": {"entity_type": filters["entity_type"]}})
            if "risk_score" in filters:
                filter_clauses.append({
                    "range": {
                        "risk_score": {
                            "gte": filters["risk_score"].get("min", 0),
                            "lte": filters["risk_score"].get("max", 1)
                        }
                    }
                })
        
        body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            },
            "from": from_,
            "size": size,
            "sort": [{"risk_score": "desc"}, "_score"]
        }
        
        response = await self.client.search(
            index=f"{self.index_prefix}_entities",
            body=body
        )
        
        return {
            "hits": [hit["_source"] for hit in response["hits"]["hits"]],
            "total": response["hits"]["total"]["value"],
            "max_score": response["hits"]["max_score"]
        }
    
    async def search_transactions(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        from_: int = 0,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search for transactions."""
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["description", "reference_number"]
                            }
                        }
                    ]
                }
            },
            "from": from_,
            "size": size
        }
        
        response = await self.client.search(
            index=f"{self.index_prefix}_transactions",
            body=body
        )
        
        return {
            "hits": [hit["_source"] for hit in response["hits"]["hits"]],
            "total": response["hits"]["total"]["value"]
        }
    
    async def search_alerts(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        from_: int = 0,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search for alerts."""
        filter_clauses = []
        if filters:
            if "severity" in filters:
                filter_clauses.append({"term": {"severity": filters["severity"]}})
            if "status" in filters:
                filter_clauses.append({"term": {"status": filters["status"]}})
        
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "description"]
                            }
                        }
                    ],
                    "filter": filter_clauses
                }
            },
            "from": from_,
            "size": size
        }
        
        response = await self.client.search(
            index=f"{self.index_prefix}_alerts",
            body=body
        )
        
        return {
            "hits": [hit["_source"] for hit in response["hits"]["hits"]],
            "total": response["hits"]["total"]["value"]
        }
    
    async def global_search(
        self,
        query: str,
        from_: int = 0,
        size: int = 10
    ) -> Dict[str, Any]:
        """Search across all indices."""
        results = {
            "entities": [],
            "transactions": [],
            "alerts": []
        }
        
        # Search each index
        for doc_type in ["entities", "transactions", "alerts"]:
            try:
                response = await self.client.search(
                    index=f"{self.index_prefix}_{doc_type}",
                    body={
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["*"]
                            }
                        },
                        "from": from_,
                        "size": size
                    }
                )
                results[doc_type] = [hit["_source"] for hit in response["hits"]["hits"]]
            except Exception:
                pass
        
        return results
    
    async def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions."""
        try:
            response = await self.client.search(
                index=f"{self.index_prefix}_entities",
                body={
                    "query": {
                        "prefix": {
                            "name.keyword": {
                                "value": query
                            }
                        }
                    },
                    "size": limit,
                    "_source": ["name"]
                }
            )
            return [hit["_source"]["name"] for hit in response["hits"]["hits"]]
        except Exception:
            return []
    
    async def screen_name(self, name: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Screen a name against sanctions and watchlists."""
        try:
            response = await self.client.search(
                index=f"{self.index_prefix}_entities",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "name": {
                                            "query": name,
                                            "fuzziness": "AUTO"
                                        }
                                    }
                                }
                            ],
                            "filter": [
                                {"term": {"is_sanctioned": True}}
                            ]
                        }
                    },
                    "size": 10
                }
            )
            
            matches = []
            for hit in response["hits"]["hits"]:
                score = hit["_score"] / response["hits"]["max_score"] if response["hits"]["max_score"] else 0
                if score >= threshold:
                    matches.append({
                        "entity": hit["_source"],
                        "confidence": score
                    })
            
            return matches
        except Exception:
            return []
    
    async def index_document(self, index_type: str, doc_id: str, document: Dict[str, Any]):
        """Index a document."""
        await self.client.index(
            index=f"{self.index_prefix}_{index_type}",
            id=doc_id,
            body=document
        )
    
    async def delete_document(self, index_type: str, doc_id: str):
        """Delete a document."""
        await self.client.delete(
            index=f"{self.index_prefix}_{index_type}",
            id=doc_id
        )

