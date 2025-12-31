#!/usr/bin/env python3
"""
FTex API Client Example

Demonstrates basic usage of the FTex API endpoints.
This script can serve as a starting point for integrations.
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class FTexClient:
    """Simple client for the FTex API."""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv("API_URL", "http://localhost:8000/api")
        self.api_key = api_key or os.getenv("API_KEY")
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # ==========================================
    # Entity APIs
    # ==========================================
    
    def list_entities(
        self,
        entity_type: str = None,
        risk_score_min: float = None,
        risk_score_max: float = None,
        is_sanctioned: bool = None,
        is_pep: bool = None,
        search: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """List entities with optional filters."""
        params = {
            "page": page,
            "page_size": page_size
        }
        if entity_type:
            params["entity_type"] = entity_type
        if risk_score_min is not None:
            params["risk_score_min"] = risk_score_min
        if risk_score_max is not None:
            params["risk_score_max"] = risk_score_max
        if is_sanctioned is not None:
            params["is_sanctioned"] = is_sanctioned
        if is_pep is not None:
            params["is_pep"] = is_pep
        if search:
            params["search"] = search
            
        return self._request("GET", "/entities/", params=params)
    
    def get_entity(self, entity_id: str) -> Dict:
        """Get entity details."""
        return self._request("GET", f"/entities/{entity_id}")
    
    def get_entity_relationships(self, entity_id: str, depth: int = 2) -> Dict:
        """Get entity network relationships."""
        return self._request("GET", f"/entities/{entity_id}/relationships", params={"depth": depth})
    
    # ==========================================
    # Transaction APIs
    # ==========================================
    
    def list_transactions(
        self,
        min_amount: float = None,
        max_amount: float = None,
        is_flagged: bool = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """List transactions."""
        params = {"page": page, "page_size": page_size}
        if min_amount:
            params["min_amount"] = min_amount
        if max_amount:
            params["max_amount"] = max_amount
        if is_flagged is not None:
            params["is_flagged"] = is_flagged
            
        return self._request("GET", "/transactions/", params=params)
    
    def get_transaction_stats(self, days: int = 30) -> Dict:
        """Get transaction statistics."""
        return self._request("GET", "/transactions/stats", params={"days": days})
    
    def flag_transaction(self, transaction_id: str, reason: str) -> Dict:
        """Flag a transaction for investigation."""
        return self._request("POST", f"/transactions/{transaction_id}/flag", params={"reason": reason})
    
    # ==========================================
    # Alert APIs
    # ==========================================
    
    def list_alerts(
        self,
        status: str = None,
        severity: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """List alerts."""
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
            
        return self._request("GET", "/alerts/", params=params)
    
    def get_alert_dashboard(self) -> Dict:
        """Get alert dashboard statistics."""
        return self._request("GET", "/alerts/dashboard")
    
    def assign_alert(self, alert_id: str, assigned_to: str) -> Dict:
        """Assign alert to analyst."""
        return self._request("POST", f"/alerts/{alert_id}/assign", params={"assigned_to": assigned_to})
    
    def resolve_alert(self, alert_id: str, resolution: str, notes: str = None) -> Dict:
        """Resolve an alert."""
        params = {"resolution": resolution}
        if notes:
            params["notes"] = notes
        return self._request("POST", f"/alerts/{alert_id}/resolve", params=params)
    
    # ==========================================
    # FTex Core APIs
    # ==========================================
    
    def resolve_entities(
        self,
        records: List[Dict],
        match_threshold: float = 0.75,
        blocking_strategies: List[str] = None
    ) -> Dict:
        """Perform entity resolution."""
        payload = {
            "records": records,
            "match_threshold": match_threshold,
            "blocking_strategies": blocking_strategies or ["soundex", "ngram"]
        }
        return self._request("POST", "/ftex/entity-resolution", json=payload)
    
    def calculate_risk_score(self, entity: Dict, context: Dict = None) -> Dict:
        """Calculate contextual risk score."""
        payload = {"entity": entity, "context": context or {}}
        return self._request("POST", "/ftex/scoring/calculate", json=payload)
    
    def generate_network(self, nodes: List[Dict], edges: List[Dict] = None) -> Dict:
        """Generate entity network."""
        payload = {
            "nodes": nodes,
            "edges": edges or [],
            "run_inference": True
        }
        return self._request("POST", "/ftex/network/generate", json=payload)
    
    def investigate_entity(
        self,
        entity_id: str,
        include_network: bool = True,
        include_transactions: bool = True,
        include_alerts: bool = True
    ) -> Dict:
        """Full entity investigation."""
        params = {
            "include_network": include_network,
            "include_transactions": include_transactions,
            "include_alerts": include_alerts
        }
        return self._request("POST", f"/ftex/decision-intelligence/investigate", 
                           params={"entity_id": entity_id, **params})
    
    # ==========================================
    # Search APIs
    # ==========================================
    
    def global_search(self, query: str, page: int = 1, page_size: int = 10) -> Dict:
        """Global search across all entities."""
        return self._request("GET", "/search/global", 
                           params={"q": query, "page": page, "page_size": page_size})
    
    def screen_names(self, names: List[str], threshold: float = 0.8) -> Dict:
        """Screen names against sanctions/watchlists."""
        return self._request("POST", "/search/screening", 
                           json={"names": names, "threshold": threshold})
    
    # ==========================================
    # RFP/PoC APIs
    # ==========================================
    
    def list_proposals(self, status: str = None, page: int = 1) -> Dict:
        """List RFP/RFI proposals."""
        params = {"page": page}
        if status:
            params["status"] = status
        return self._request("GET", "/rfp/", params=params)
    
    def get_rfp_dashboard(self) -> Dict:
        """Get RFP dashboard statistics."""
        return self._request("GET", "/rfp/dashboard")
    
    def list_engagements(self, status: str = None, page: int = 1) -> Dict:
        """List PoC engagements."""
        params = {"page": page}
        if status:
            params["status"] = status
        return self._request("GET", "/poc/engagements", params=params)


def main():
    """Demonstrate API client usage."""
    
    print("=" * 60)
    print("FTex API Client Demo")
    print("=" * 60)
    
    # Initialize client
    client = FTexClient()
    
    print(f"\nConnecting to: {client.base_url}")
    
    try:
        # Test health endpoint
        print("\n--- Testing API Connection ---")
        health = requests.get(f"{client.base_url.replace('/api', '')}/health")
        print(f"Health check: {health.status_code}")
        
        # List entities
        print("\n--- Listing Entities ---")
        entities = client.list_entities(page_size=5)
        print(f"Total entities: {entities.get('total', 0)}")
        for entity in entities.get('items', [])[:3]:
            print(f"  • {entity.get('name')} (Risk: {entity.get('risk_score', 0):.2f})")
        
        # Get alert dashboard
        print("\n--- Alert Dashboard ---")
        dashboard = client.get_alert_dashboard()
        print(f"Open alerts: {dashboard.get('open_count', 0)}")
        print(f"Critical alerts: {dashboard.get('critical_count', 0)}")
        
        # Test entity resolution
        print("\n--- Entity Resolution ---")
        test_records = [
            {
                "id": "R001",
                "source_system": "crm",
                "entity_type": "individual",
                "attributes": {"name": "John Smith", "email": "john@email.com"}
            },
            {
                "id": "R002",
                "source_system": "kyc",
                "entity_type": "individual",
                "attributes": {"name": "Jon Smith", "email": "johnsmith@email.com"}
            }
        ]
        resolution = client.resolve_entities(test_records)
        print(f"Input records: {resolution.get('input_record_count', 0)}")
        print(f"Resolved entities: {resolution.get('resolved_entity_count', 0)}")
        
        # Test risk scoring
        print("\n--- Risk Scoring ---")
        test_entity = {
            "id": "E001",
            "name": "Test Company",
            "is_sanctioned": False,
            "is_pep": False,
            "country": "SG"
        }
        score = client.calculate_risk_score(test_entity)
        print(f"Risk score: {score.get('overall_score', 0):.3f}")
        print(f"Risk level: {score.get('risk_level', 'unknown')}")
        
        # Test screening
        print("\n--- Name Screening ---")
        names = ["John Smith", "Kim Jong Un"]
        screening = client.screen_names(names)
        for result in screening.get('screening_results', []):
            matches = len(result.get('matches', []))
            print(f"  {result['input']}: {matches} match(es)")
        
        # Get RFP dashboard
        print("\n--- RFP Dashboard ---")
        rfp_dash = client.get_rfp_dashboard()
        print(f"Active proposals: {rfp_dash.get('active_proposals', 0)}")
        print(f"Win rate: {rfp_dash.get('win_rate', 0):.1f}%")
        
        print("\n✅ All API tests passed!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API")
        print("Make sure the platform is running: docker-compose up -d")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API error: {e}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

