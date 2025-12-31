#!/usr/bin/env python3
"""
Network Generation Demo

Demonstrates FTex's network/graph generation capabilities:
- Building knowledge graphs from entities
- Relationship extraction
- Relationship inference
- Network metrics calculation
"""

import requests
from typing import Dict, List

API_BASE_URL = "http://localhost:8000/api"


def demo_network_generation():
    """Demonstrate network generation from entities."""
    
    print("=" * 60)
    print("FTex Network Generation Demo")
    print("=" * 60)
    print("""
    Creating a knowledge graph from entities and relationships:
    - Explicit relationships (known connections)
    - Inferred relationships (discovered patterns)
    - Network metrics and risk propagation
    """)
    
    # Define nodes (entities)
    nodes = [
        {
            "id": "E001",
            "entity_type": "individual",
            "name": "John Smith",
            "attributes": {"occupation": "CEO", "country": "SG"},
            "risk_score": 0.3
        },
        {
            "id": "E002",
            "entity_type": "organization",
            "name": "Acme Trading Corp",
            "attributes": {"industry": "Trading", "country": "SG"},
            "risk_score": 0.4
        },
        {
            "id": "E003",
            "entity_type": "individual",
            "name": "Jane Doe",
            "attributes": {"occupation": "CFO", "country": "SG"},
            "risk_score": 0.2
        },
        {
            "id": "E004",
            "entity_type": "organization",
            "name": "Global Investments Ltd",
            "attributes": {"industry": "Investment", "country": "KY"},
            "risk_score": 0.8
        },
        {
            "id": "E005",
            "entity_type": "individual",
            "name": "Bob Johnson",
            "attributes": {"occupation": "Director", "country": "US"},
            "risk_score": 0.5
        },
        {
            "id": "E006",
            "entity_type": "account",
            "name": "ACC-001-2024",
            "attributes": {"type": "corporate", "currency": "USD"},
            "risk_score": 0.3
        }
    ]
    
    # Define explicit relationships
    edges = [
        {
            "source_id": "E001",
            "target_id": "E002",
            "relationship_type": "controls",
            "attributes": {"role": "CEO", "since": "2020-01-01"}
        },
        {
            "source_id": "E003",
            "target_id": "E002",
            "relationship_type": "employed_by",
            "attributes": {"role": "CFO", "since": "2021-06-15"}
        },
        {
            "source_id": "E002",
            "target_id": "E004",
            "relationship_type": "transacted_with",
            "attributes": {"total_amount": 5000000, "count": 12}
        },
        {
            "source_id": "E005",
            "target_id": "E004",
            "relationship_type": "controls",
            "attributes": {"role": "Director", "ownership": 0.35}
        },
        {
            "source_id": "E002",
            "target_id": "E006",
            "relationship_type": "owns",
            "attributes": {"account_type": "operating"}
        }
    ]
    
    # Sample transactions for inference
    transactions = [
        {
            "sender_id": "E002",
            "receiver_id": "E004",
            "amount": 500000,
            "date": "2024-01-15"
        },
        {
            "sender_id": "E004",
            "receiver_id": "E002",
            "amount": 450000,
            "date": "2024-01-20"
        },
        {
            "sender_id": "E001",
            "receiver_id": "E003",
            "amount": 10000,
            "date": "2024-01-25"
        }
    ]
    
    print("\n--- Input Entities ---")
    for node in nodes:
        icon = "👤" if node["entity_type"] == "individual" else "🏢" if node["entity_type"] == "organization" else "💳"
        print(f"  {icon} {node['id']}: {node['name']} (Risk: {node['risk_score']:.2f})")
    
    print("\n--- Explicit Relationships ---")
    for edge in edges:
        print(f"  {edge['source_id']} --[{edge['relationship_type']}]--> {edge['target_id']}")
    
    print("\n" + "-" * 40)
    print("Generating network...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/network/generate",
            json={
                "nodes": nodes,
                "edges": edges,
                "transactions": transactions,
                "run_inference": True
            }
        )
        response.raise_for_status()
        result = response.json()
        
        display_network_result(result)
        
    except requests.exceptions.ConnectionError:
        demo_mode_network(nodes, edges)


def display_network_result(result: Dict):
    """Display network generation result."""
    
    summary = result.get('summary', {})
    
    print("\n" + "=" * 60)
    print("NETWORK GENERATION RESULT")
    print("=" * 60)
    
    print("\n📊 Summary:")
    print(f"  Nodes: {summary.get('node_count', 0)}")
    print(f"  Edges: {summary.get('edge_count', 0)}")
    print(f"  Communities: {summary.get('communities', 0)}")
    
    print(f"\n🔍 Inferred Relationships: {result.get('inferred_relationships', 0)}")
    
    if 'network' in result:
        network = result['network']
        
        print("\n📈 Network Metrics:")
        if 'metrics' in network:
            metrics = network['metrics']
            print(f"  Density: {metrics.get('density', 0):.3f}")
            print(f"  Avg Clustering: {metrics.get('avg_clustering', 0):.3f}")
            print(f"  Connected Components: {metrics.get('components', 1)}")
        
        print("\n🔗 Relationship Types:")
        if 'edge_types' in network:
            for rel_type, count in network['edge_types'].items():
                print(f"  • {rel_type}: {count}")


def demo_mode_network(nodes: List[Dict], edges: List[Dict]):
    """Demo mode network output."""
    
    print("\n[Demo Mode - Simulated Network Generation]")
    print("\n" + "=" * 60)
    print("NETWORK GENERATION RESULT")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Explicit Edges: {len(edges)}")
    print(f"  Inferred Edges: 3")  # Simulated
    print(f"  Total Edges: {len(edges) + 3}")
    
    print(f"\n🔍 Inferred Relationships:")
    print("  • E001 --[shared_address]--> E003 (same registered address)")
    print("  • E002 --[circular_flow]--> E004 (bidirectional transactions)")
    print("  • E001 --[associated_with]--> E005 (shared business interests)")
    
    print("\n📈 Network Metrics:")
    print("  Density: 0.467")
    print("  Avg Clustering: 0.583")
    print("  Connected Components: 1")
    
    print("\n🔗 Relationship Types:")
    print("  • controls: 2")
    print("  • employed_by: 1")
    print("  • transacted_with: 1")
    print("  • owns: 1")
    print("  • shared_address: 1 (inferred)")
    print("  • circular_flow: 1 (inferred)")
    print("  • associated_with: 1 (inferred)")


def demo_entity_network_analysis():
    """Demonstrate network analysis for a specific entity."""
    
    print("\n\n" + "=" * 60)
    print("Entity Network Analysis")
    print("=" * 60)
    print("""
    Analyzing network around a specific entity:
    - Immediate connections
    - Extended network (multi-hop)
    - Risk exposure from network
    """)
    
    entity_id = "E002"  # Acme Trading Corp
    
    print(f"\nAnalyzing network for entity: {entity_id}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ftex/network/analyze/{entity_id}",
            params={"depth": 2}
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\n📊 Network Metrics:")
        metrics = result.get('metrics', {})
        print(f"  Degree Centrality: {metrics.get('degree_centrality', 0):.3f}")
        print(f"  Clustering Coefficient: {metrics.get('clustering_coefficient', 0):.3f}")
        print(f"  Risk Exposure: {metrics.get('risk_exposure', 0):.3f}")
        
    except requests.exceptions.ConnectionError:
        print("\n[Demo Mode]")
        print(f"\n📊 Network Metrics for {entity_id}:")
        print("  Degree Centrality: 0.750 (highly connected)")
        print("  Clustering Coefficient: 0.667")
        print("  Risk Exposure: 0.45 (moderate - connected to high-risk entity)")
        
        print("\n🔗 Connected Entities (depth=2):")
        print("  └─ E001 (John Smith) - controls")
        print("  └─ E003 (Jane Doe) - employed_by")
        print("  └─ E004 (Global Investments) - transacted_with ⚠️ HIGH RISK")
        print("     └─ E005 (Bob Johnson) - controls")
        print("  └─ E006 (ACC-001-2024) - owns")
        
        print("\n⚠️  Risk Propagation:")
        print("  High-risk connection: E004 (Global Investments Ltd)")
        print("  Risk score: 0.80")
        print("  Relationship: transacted_with (12 transactions, $5M total)")
        print("  Propagated risk impact: +0.15 to entity risk score")


def demo_shortest_path():
    """Demonstrate shortest path finding."""
    
    print("\n\n" + "=" * 60)
    print("Shortest Path Analysis")
    print("=" * 60)
    print("""
    Finding the shortest connection path between two entities.
    Useful for:
    - Investigation trails
    - Understanding relationship chains
    - Money flow analysis
    """)
    
    source = "E001"  # John Smith
    target = "E004"  # Global Investments
    
    print(f"\nFinding path: {source} → {target}")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/ftex/network/path",
            params={"source_id": source, "target_id": target, "max_depth": 6}
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('path_found'):
            print(f"\n✅ Path found (length: {result['path_length']})")
            for step in result['path']:
                print(f"  → {step}")
        else:
            print("\n❌ No path found within max depth")
            
    except requests.exceptions.ConnectionError:
        print("\n[Demo Mode]")
        print(f"\n✅ Path found (length: 2)")
        print("\n  E001 (John Smith)")
        print("    │")
        print("    └──[controls]──→")
        print("                     E002 (Acme Trading Corp)")
        print("                       │")
        print("                       └──[transacted_with]──→")
        print("                                              E004 (Global Investments Ltd)")


def demo_network_visualization():
    """Show network visualization output format."""
    
    print("\n\n" + "=" * 60)
    print("Network Visualization Data")
    print("=" * 60)
    print("""
    FTex exports network data in formats compatible with:
    - Neo4j graph database
    - D3.js visualization
    - Vis.js network charts
    - Cytoscape
    """)
    
    print("\n📊 Neo4j Export Format:")
    print("""
    // Nodes
    CREATE (e1:Individual {id: 'E001', name: 'John Smith', risk_score: 0.3})
    CREATE (e2:Organization {id: 'E002', name: 'Acme Trading', risk_score: 0.4})
    CREATE (e4:Organization {id: 'E004', name: 'Global Investments', risk_score: 0.8})
    
    // Relationships
    CREATE (e1)-[:CONTROLS {role: 'CEO', since: '2020-01-01'}]->(e2)
    CREATE (e2)-[:TRANSACTED_WITH {amount: 5000000}]->(e4)
    """)
    
    print("\n📊 D3.js/Vis.js Format:")
    print("""
    {
      "nodes": [
        {"id": "E001", "label": "John Smith", "group": "individual", "risk": 0.3},
        {"id": "E002", "label": "Acme Trading", "group": "organization", "risk": 0.4},
        {"id": "E004", "label": "Global Investments", "group": "organization", "risk": 0.8}
      ],
      "edges": [
        {"from": "E001", "to": "E002", "label": "controls", "arrows": "to"},
        {"from": "E002", "to": "E004", "label": "transacted_with", "arrows": "to"}
      ]
    }
    """)


if __name__ == "__main__":
    demo_network_generation()
    demo_entity_network_analysis()
    demo_shortest_path()
    demo_network_visualization()

