#!/usr/bin/env python3
"""
Entity Resolution Demo

Demonstrates FTex's entity resolution capabilities:
- Fuzzy name matching
- Multiple blocking strategies
- Similarity scoring
- Canonical record generation
"""

import json
import requests
from typing import List, Dict

API_BASE_URL = "http://localhost:8000/api"


def demo_entity_resolution():
    """Demonstrate entity resolution with sample records."""
    
    print("=" * 60)
    print("FTex Entity Resolution Demo")
    print("=" * 60)
    
    # Sample records from different source systems
    # These represent the same person with variations
    records = [
        {
            "id": "CRM-001",
            "source_system": "crm",
            "entity_type": "individual",
            "attributes": {
                "name": "John Michael Smith",
                "date_of_birth": "1985-03-15",
                "email": "john.smith@email.com",
                "phone": "+65 9123 4567",
                "address": "123 Orchard Road, Singapore 238858"
            }
        },
        {
            "id": "KYC-002",
            "source_system": "kyc_system",
            "entity_type": "individual",
            "attributes": {
                "name": "SMITH, John M.",
                "date_of_birth": "1985-03-15",
                "national_id": "S1234567A",
                "nationality": "US",
                "occupation": "Software Engineer"
            }
        },
        {
            "id": "CORE-003",
            "source_system": "core_banking",
            "entity_type": "individual",
            "attributes": {
                "name": "Jon Smith",  # Typo in first name
                "date_of_birth": "1985-03-15",
                "account_number": "1234-5678-9012",
                "email": "johnsmith@gmail.com"  # Different email
            }
        },
        {
            "id": "TRADE-004",
            "source_system": "trade_system",
            "entity_type": "individual",
            "attributes": {
                "name": "Jane Doe",  # Different person
                "date_of_birth": "1990-07-22",
                "email": "jane.doe@company.com"
            }
        },
        {
            "id": "CRM-005",
            "source_system": "crm",
            "entity_type": "individual",
            "attributes": {
                "name": "J. Doe",
                "date_of_birth": "1990-07-22",
                "phone": "+65 8765 4321"
            }
        }
    ]
    
    print(f"\nInput: {len(records)} records from multiple systems")
    print("-" * 40)
    for record in records:
        print(f"  [{record['source_system']}] {record['id']}: {record['attributes']['name']}")
    
    # Call entity resolution API
    print("\n\nCalling Entity Resolution API...")
    print("-" * 40)
    
    payload = {
        "records": records,
        "match_threshold": 0.75,
        "blocking_strategies": ["soundex", "ngram", "metaphone"]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/entity-resolution",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\nResolution Results:")
        print(f"  Input records: {result['input_record_count']}")
        print(f"  Resolved entities: {result['resolved_entity_count']}")
        print(f"  Resolution rate: {result['resolution_rate']:.1%}")
        
        print("\n\nResolved Entities:")
        print("=" * 60)
        
        for entity in result['resolved_entities']:
            print(f"\n[{entity['resolved_id']}] {entity['canonical_name']}")
            print(f"  Type: {entity['entity_type']}")
            print(f"  Confidence: {entity['confidence_score']:.2f}")
            print(f"  Source records: {', '.join(entity['source_record_ids'])}")
            print(f"  Match scores:")
            for algo, score in entity['match_scores'].items():
                print(f"    - {algo}: {score:.3f}")
                
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the platform is running.")
        print("Run: docker-compose up -d")
        
        # Show what would happen with mock data
        print("\n[Demo mode - showing expected output]")
        demo_offline_resolution(records)


def demo_offline_resolution(records: List[Dict]):
    """Demonstrate resolution logic offline."""
    
    # Import the engine directly for demo
    import sys
    sys.path.insert(0, '../backend')
    
    try:
        from app.services.entity_resolution_engine import (
            EntityResolutionEngine, EntityRecord
        )
        
        # Convert to EntityRecord objects
        entity_records = [
            EntityRecord(
                id=r['id'],
                source_system=r['source_system'],
                entity_type=r['entity_type'],
                attributes=r['attributes'],
                raw_data={}
            )
            for r in records
        ]
        
        # Run resolution
        engine = EntityResolutionEngine(
            match_threshold=0.75,
            blocking_strategies=['soundex', 'ngram']
        )
        
        resolved = engine.resolve(entity_records)
        
        print(f"\nResolved {len(records)} records into {len(resolved)} entities")
        
        for entity in resolved:
            print(f"\n[{entity.resolved_id}] {entity.canonical_name}")
            print(f"  Confidence: {entity.confidence_score:.2f}")
            print(f"  Sources: {[r.id for r in entity.source_records]}")
            
    except ImportError:
        print("Note: Run from project root to import backend modules")


def demo_entity_comparison():
    """Demonstrate comparing two entities."""
    
    print("\n\n" + "=" * 60)
    print("Entity Comparison Demo")
    print("=" * 60)
    
    entity_a = {
        "name": "Mohamed bin Abdullah Al-Rashid",
        "date_of_birth": "1978-05-20",
        "nationality": "SA"
    }
    
    entity_b = {
        "name": "Mohammed Bin Abdallah Al Rasheed",
        "date_of_birth": "1978-05-20",
        "nationality": "SA"
    }
    
    print("\nComparing:")
    print(f"  Entity A: {entity_a['name']}")
    print(f"  Entity B: {entity_b['name']}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/entity-resolution/compare",
            params={
                "entity_a": json.dumps(entity_a),
                "entity_b": json.dumps(entity_b)
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\nSimilarity Scores:")
        for algo, score in result['similarity_scores'].items():
            bar = "█" * int(score * 20)
            print(f"  {algo:20s}: {score:.3f} {bar}")
        
        print(f"\nComposite Score: {result['composite_score']:.3f}")
        print(f"Recommendation: {result['recommendation']}")
        
    except requests.exceptions.ConnectionError:
        print("\n[Demo mode - API not available]")
        print("Expected output: High similarity scores due to:")
        print("  - Same name with transliteration variations")
        print("  - Exact DOB match")
        print("  - Same nationality")


if __name__ == "__main__":
    demo_entity_resolution()
    demo_entity_comparison()

