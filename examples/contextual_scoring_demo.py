#!/usr/bin/env python3
"""
Contextual Scoring Demo

Demonstrates FTex's key differentiator: risk scoring based on 
network CONTEXT, not just individual attributes.

This shows how an entity's risk is affected by:
- Their own attributes (sanctions, PEP status)
- Their network connections
- Transaction patterns
- Behavioral anomalies
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"


def demo_basic_scoring():
    """Demonstrate basic risk scoring."""
    
    print("=" * 60)
    print("FTex Contextual Scoring Demo")
    print("=" * 60)
    
    # Scenario 1: Low-risk individual
    print("\n\n--- Scenario 1: Low-Risk Individual ---")
    
    entity = {
        "id": "E001",
        "name": "Alice Johnson",
        "entity_type": "individual",
        "is_sanctioned": False,
        "is_pep": False,
        "country": "SG",
        "occupation": "Software Engineer"
    }
    
    context = {
        "network": {
            "high_risk_connections": 0,
            "sanctioned_connections": 0
        },
        "transaction_stats": {
            "total_volume": 50000,
            "structuring_indicator": 0.1,
            "cross_border_ratio": 0.2
        }
    }
    
    score_entity(entity, context)
    
    # Scenario 2: High-risk due to network
    print("\n\n--- Scenario 2: Risk from Network Connections ---")
    
    entity = {
        "id": "E002",
        "name": "Bob Chen",
        "entity_type": "individual",
        "is_sanctioned": False,
        "is_pep": False,
        "country": "SG",
        "occupation": "Import/Export"
    }
    
    context = {
        "network": {
            "high_risk_connections": 5,
            "sanctioned_connections": 2,
            "clustering_coefficient": 0.8,
            "centrality_score": 0.9,
            "in_circular_flow": True,
            "propagated_risk": 0.6
        },
        "transaction_stats": {
            "total_volume": 2500000,
            "structuring_indicator": 0.75,
            "passthrough_ratio": 0.85,
            "cross_border_ratio": 0.8
        }
    }
    
    score_entity(entity, context)
    
    # Scenario 3: PEP with clean network
    print("\n\n--- Scenario 3: PEP with Clean Network ---")
    
    entity = {
        "id": "E003",
        "name": "Minister David Lee",
        "entity_type": "individual",
        "is_sanctioned": False,
        "is_pep": True,
        "pep_level": "senior_government",
        "pep_position": "Minister of Trade",
        "pep_country": "SG",
        "country": "SG"
    }
    
    context = {
        "network": {
            "high_risk_connections": 0,
            "sanctioned_connections": 0
        },
        "transaction_stats": {
            "total_volume": 500000,
            "structuring_indicator": 0.0
        }
    }
    
    score_entity(entity, context)
    
    # Scenario 4: Sanctioned entity
    print("\n\n--- Scenario 4: Sanctioned Entity ---")
    
    entity = {
        "id": "E004",
        "name": "Restricted Trading Corp",
        "entity_type": "organization",
        "is_sanctioned": True,
        "matched_sanctions_lists": ["OFAC-SDN", "EU"],
        "sanctions_match_type": "exact",
        "country": "IR"
    }
    
    context = {
        "network": {},
        "transaction_stats": {}
    }
    
    score_entity(entity, context)


def score_entity(entity: dict, context: dict):
    """Score an entity and display results."""
    
    print(f"\nEntity: {entity['name']} ({entity['entity_type']})")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/scoring/calculate",
            json={"entity": entity, "context": context}
        )
        response.raise_for_status()
        result = response.json()
        
        display_score_result(result)
        
    except requests.exceptions.ConnectionError:
        # Demo mode - use local engine
        demo_local_scoring(entity, context)


def demo_local_scoring(entity: dict, context: dict):
    """Demo scoring using local engine."""
    
    import sys
    sys.path.insert(0, '../backend')
    
    try:
        from app.services.contextual_scoring import ContextualScoringEngine
        
        engine = ContextualScoringEngine()
        score = engine.calculate_score(entity, context)
        explanation = engine.explain_score(score)
        
        display_score_result(explanation)
        
    except ImportError:
        # Show mock output
        print("[Demo mode - showing expected output]")
        print(f"Overall Score: 0.XX")
        print(f"Risk Level: [calculated based on factors]")


def display_score_result(result: dict):
    """Display formatted scoring result."""
    
    score = result.get('overall_score', 0)
    level = result.get('risk_level', 'unknown')
    
    # Visual risk bar
    bar_length = int(score * 30)
    bar = "█" * bar_length + "░" * (30 - bar_length)
    
    # Color code (using text)
    level_colors = {
        'low': '🟢',
        'medium': '🟡', 
        'high': '🟠',
        'critical': '🔴'
    }
    
    print(f"\nRisk Score: [{bar}] {score:.3f}")
    print(f"Risk Level: {level_colors.get(level, '⚪')} {level.upper()}")
    
    if 'factors' in result and result['factors']:
        print(f"\nContributing Factors:")
        for factor in result['factors'][:5]:
            contrib = factor.get('contribution', factor.get('weighted_score', 0))
            print(f"  • {factor['category']}: {factor['description']}")
            print(f"    Score: {factor['score']:.2f}, Weight: {factor['weight']:.1f}, Contribution: {contrib:.3f}")
    
    if 'recommendations' in result and result['recommendations']:
        print(f"\nRecommendations:")
        for rec in result['recommendations']:
            print(f"  ⚠️  {rec}")


def demo_batch_scoring():
    """Demonstrate batch scoring."""
    
    print("\n\n" + "=" * 60)
    print("Batch Scoring Demo")
    print("=" * 60)
    
    entities = [
        {"id": "B001", "name": "Company A", "country": "SG", "is_sanctioned": False, "is_pep": False},
        {"id": "B002", "name": "Company B", "country": "KP", "is_sanctioned": False, "is_pep": False},
        {"id": "B003", "name": "Company C", "country": "US", "is_sanctioned": True, "is_pep": False},
        {"id": "B004", "name": "Individual D", "country": "SG", "is_sanctioned": False, "is_pep": True},
        {"id": "B005", "name": "Company E", "country": "PA", "is_sanctioned": False, "is_pep": False},
    ]
    
    print(f"\nScoring {len(entities)} entities in batch...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/scoring/batch",
            json={"entities": entities}
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\nResults Summary:")
        print(f"  Total Entities: {result['entity_count']}")
        print(f"  High Risk Count: {result['high_risk_count']}")
        print(f"  Average Score: {result['average_score']:.3f}")
        
        print(f"\nIndividual Scores:")
        for score in result['scores']:
            level_icon = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
            icon = level_icon.get(score['risk_level'], '⚪')
            print(f"  {icon} {score['entity_id']}: {score['overall_score']:.3f} ({score['risk_level']})")
            
    except requests.exceptions.ConnectionError:
        print("[Demo mode - API not available]")


def demo_explain_score():
    """Demonstrate detailed score explanation."""
    
    print("\n\n" + "=" * 60)
    print("Score Explanation Demo")
    print("=" * 60)
    
    entity = {
        "id": "EXP-001",
        "name": "Complex Trading Ltd",
        "entity_type": "organization",
        "is_sanctioned": False,
        "is_pep": False,
        "country": "VG"  # British Virgin Islands
    }
    
    context = {
        "network": {
            "high_risk_connections": 3,
            "sanctioned_connections": 1,
            "clustering_coefficient": 0.75,
            "in_circular_flow": True
        },
        "transaction_stats": {
            "total_volume": 5000000,
            "structuring_indicator": 0.6,
            "passthrough_ratio": 0.9,
            "round_amount_ratio": 0.7,
            "cross_border_ratio": 0.95,
            "cash_ratio": 0.3
        },
        "behavioral": {
            "off_hours_ratio": 0.4,
            "activity_spike": 4.5,
            "pattern_change_score": 0.8
        }
    }
    
    print(f"\nEntity: {entity['name']}")
    print(f"Jurisdiction: {entity['country']} (Tax Haven)")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/scoring/explain",
            params={"entity_id": entity["id"]},
            json={"entity": entity, "context": context}
        )
        response.raise_for_status()
        result = response.json()
        
        display_score_result(result)
        
    except requests.exceptions.ConnectionError:
        demo_local_scoring(entity, context)


if __name__ == "__main__":
    demo_basic_scoring()
    demo_batch_scoring()
    demo_explain_score()

