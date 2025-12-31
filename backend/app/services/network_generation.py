"""
FTex Network Generation Engine

Creates dynamic knowledge graphs from resolved entities and their relationships.
Core FTex capability for building connected data networks.

Features:
- Automatic relationship inference
- Multi-hop network expansion
- Relationship scoring and weighting
- Network schema management
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib
from collections import defaultdict


class RelationshipType(str, Enum):
    """Standard relationship types in the network."""
    # Individual relationships
    OWNS = "OWNS"
    CONTROLS = "CONTROLS"
    DIRECTOR_OF = "DIRECTOR_OF"
    SHAREHOLDER_OF = "SHAREHOLDER_OF"
    EMPLOYEE_OF = "EMPLOYEE_OF"
    RELATED_TO = "RELATED_TO"
    FAMILY_OF = "FAMILY_OF"
    
    # Transaction relationships
    TRANSACTED_WITH = "TRANSACTED_WITH"
    SENT_TO = "SENT_TO"
    RECEIVED_FROM = "RECEIVED_FROM"
    
    # Account relationships
    ACCOUNT_HOLDER = "ACCOUNT_HOLDER"
    AUTHORIZED_SIGNATORY = "AUTHORIZED_SIGNATORY"
    BENEFICIAL_OWNER = "BENEFICIAL_OWNER"
    
    # Address relationships
    REGISTERED_AT = "REGISTERED_AT"
    RESIDES_AT = "RESIDES_AT"
    OPERATES_FROM = "OPERATES_FROM"
    
    # Communication relationships
    CONTACTED = "CONTACTED"
    SHARES_PHONE = "SHARES_PHONE"
    SHARES_EMAIL = "SHARES_EMAIL"
    SHARES_DEVICE = "SHARES_DEVICE"
    
    # Inferred relationships
    CO_LOCATED = "CO_LOCATED"
    SAME_NETWORK = "SAME_NETWORK"
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"


@dataclass
class NetworkNode:
    """A node in the knowledge graph."""
    id: str
    node_type: str  # individual, organization, account, address, etc.
    label: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    source_systems: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NetworkEdge:
    """An edge (relationship) in the knowledge graph."""
    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def key(self) -> Tuple[str, str, str]:
        """Unique key for this edge."""
        return (self.source_id, self.target_id, self.relationship_type.value)


@dataclass 
class Network:
    """A knowledge graph network."""
    nodes: Dict[str, NetworkNode] = field(default_factory=dict)
    edges: Dict[str, NetworkEdge] = field(default_factory=dict)
    
    def add_node(self, node: NetworkNode) -> None:
        """Add a node to the network."""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: NetworkEdge) -> None:
        """Add an edge to the network."""
        self.edges[edge.id] = edge
    
    def get_neighbors(self, node_id: str, depth: int = 1) -> Set[str]:
        """Get neighboring node IDs up to specified depth."""
        if depth < 1:
            return set()
        
        neighbors = set()
        current_level = {node_id}
        
        for _ in range(depth):
            next_level = set()
            for nid in current_level:
                for edge in self.edges.values():
                    if edge.source_id == nid and edge.target_id not in neighbors:
                        next_level.add(edge.target_id)
                        neighbors.add(edge.target_id)
                    elif edge.target_id == nid and edge.source_id not in neighbors:
                        next_level.add(edge.source_id)
                        neighbors.add(edge.source_id)
            current_level = next_level
        
        return neighbors
    
    def get_subgraph(self, node_ids: Set[str]) -> 'Network':
        """Extract a subgraph containing specified nodes."""
        subgraph = Network()
        
        for node_id in node_ids:
            if node_id in self.nodes:
                subgraph.add_node(self.nodes[node_id])
        
        for edge in self.edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                subgraph.add_edge(edge)
        
        return subgraph


class RelationshipInferenceRule:
    """Base class for relationship inference rules."""
    
    def __init__(self, relationship_type: RelationshipType, confidence: float = 0.8):
        self.relationship_type = relationship_type
        self.confidence = confidence
    
    def apply(self, network: Network) -> List[NetworkEdge]:
        """Apply the rule to infer new relationships."""
        raise NotImplementedError


class SharedAttributeRule(RelationshipInferenceRule):
    """Infer relationships based on shared attributes."""
    
    def __init__(
        self, 
        attribute_name: str,
        relationship_type: RelationshipType,
        confidence: float = 0.7
    ):
        super().__init__(relationship_type, confidence)
        self.attribute_name = attribute_name
    
    def apply(self, network: Network) -> List[NetworkEdge]:
        """Find nodes sharing the same attribute value."""
        inferred_edges = []
        
        # Group nodes by attribute value
        attr_groups = defaultdict(list)
        for node in network.nodes.values():
            value = node.attributes.get(self.attribute_name)
            if value:
                attr_groups[value].append(node)
        
        # Create edges for nodes sharing attributes
        for value, nodes in attr_groups.items():
            if len(nodes) < 2:
                continue
            
            for i, node_a in enumerate(nodes):
                for node_b in nodes[i+1:]:
                    edge_id = f"inferred_{node_a.id}_{node_b.id}_{self.attribute_name}"
                    edge = NetworkEdge(
                        id=edge_id,
                        source_id=node_a.id,
                        target_id=node_b.id,
                        relationship_type=self.relationship_type,
                        confidence=self.confidence,
                        evidence=[{
                            "rule": "shared_attribute",
                            "attribute": self.attribute_name,
                            "value": value
                        }]
                    )
                    inferred_edges.append(edge)
        
        return inferred_edges


class TransactionPatternRule(RelationshipInferenceRule):
    """Infer relationships based on transaction patterns."""
    
    def __init__(
        self,
        min_transactions: int = 3,
        time_window_days: int = 30,
        confidence: float = 0.85
    ):
        super().__init__(RelationshipType.TRANSACTED_WITH, confidence)
        self.min_transactions = min_transactions
        self.time_window_days = time_window_days
    
    def apply(self, network: Network) -> List[NetworkEdge]:
        """Analyze transaction edges to infer business relationships."""
        inferred_edges = []
        
        # Count transactions between entity pairs
        tx_counts = defaultdict(int)
        tx_amounts = defaultdict(float)
        
        for edge in network.edges.values():
            if edge.relationship_type in [RelationshipType.SENT_TO, RelationshipType.RECEIVED_FROM]:
                pair = tuple(sorted([edge.source_id, edge.target_id]))
                tx_counts[pair] += 1
                tx_amounts[pair] += edge.attributes.get('amount', 0)
        
        # Create inferred relationships for frequent transactors
        for (id_a, id_b), count in tx_counts.items():
            if count >= self.min_transactions:
                edge_id = f"inferred_tx_{id_a}_{id_b}"
                edge = NetworkEdge(
                    id=edge_id,
                    source_id=id_a,
                    target_id=id_b,
                    relationship_type=RelationshipType.TRANSACTED_WITH,
                    weight=count,
                    confidence=min(1.0, self.confidence + count * 0.02),
                    evidence=[{
                        "rule": "transaction_pattern",
                        "transaction_count": count,
                        "total_amount": tx_amounts[(id_a, id_b)]
                    }]
                )
                inferred_edges.append(edge)
        
        return inferred_edges


class NetworkGenerationEngine:
    """
    FTex Network Generation Engine.
    
    Builds knowledge graphs from resolved entities by:
    1. Creating nodes from resolved entities
    2. Extracting explicit relationships from data
    3. Inferring implicit relationships using rules
    4. Scoring and weighting relationships
    5. Propagating risk through the network
    """
    
    def __init__(self):
        self.network = Network()
        self.inference_rules: List[RelationshipInferenceRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configure default relationship inference rules."""
        # Shared address implies co-location
        self.inference_rules.append(
            SharedAttributeRule("address", RelationshipType.CO_LOCATED, 0.7)
        )
        
        # Shared phone implies connection
        self.inference_rules.append(
            SharedAttributeRule("phone", RelationshipType.SHARES_PHONE, 0.8)
        )
        
        # Shared email implies connection
        self.inference_rules.append(
            SharedAttributeRule("email", RelationshipType.SHARES_EMAIL, 0.8)
        )
        
        # Transaction patterns
        self.inference_rules.append(
            TransactionPatternRule(min_transactions=3, confidence=0.85)
        )
    
    def add_inference_rule(self, rule: RelationshipInferenceRule):
        """Add a custom inference rule."""
        self.inference_rules.append(rule)
    
    def create_node_from_entity(
        self, 
        entity_id: str,
        entity_type: str,
        name: str,
        attributes: Dict[str, Any],
        risk_score: float = 0.0,
        source_systems: List[str] = None
    ) -> NetworkNode:
        """Create a network node from an entity."""
        node = NetworkNode(
            id=entity_id,
            node_type=entity_type,
            label=name,
            attributes=attributes,
            risk_score=risk_score,
            source_systems=source_systems or []
        )
        self.network.add_node(node)
        return node
    
    def create_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        attributes: Dict[str, Any] = None,
        weight: float = 1.0,
        confidence: float = 1.0
    ) -> NetworkEdge:
        """Create an edge between two nodes."""
        edge_id = hashlib.md5(
            f"{source_id}_{target_id}_{relationship_type.value}".encode()
        ).hexdigest()[:16]
        
        edge = NetworkEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            weight=weight,
            confidence=confidence,
            attributes=attributes or {}
        )
        self.network.add_edge(edge)
        return edge
    
    def extract_relationships_from_transactions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[NetworkEdge]:
        """
        Extract relationships from transaction data.
        
        Creates SENT_TO/RECEIVED_FROM edges between entities.
        """
        edges = []
        
        for tx in transactions:
            sender_id = tx.get('sender_entity_id')
            receiver_id = tx.get('receiver_entity_id')
            
            if not sender_id or not receiver_id:
                continue
            
            # Create directed edge from sender to receiver
            edge = self.create_edge(
                source_id=sender_id,
                target_id=receiver_id,
                relationship_type=RelationshipType.SENT_TO,
                attributes={
                    'transaction_id': tx.get('id'),
                    'amount': tx.get('amount'),
                    'currency': tx.get('currency'),
                    'date': tx.get('transaction_date')
                },
                weight=tx.get('amount', 1.0)
            )
            edges.append(edge)
        
        return edges
    
    def extract_relationships_from_corporate_data(
        self,
        corporate_records: List[Dict[str, Any]]
    ) -> List[NetworkEdge]:
        """
        Extract relationships from corporate registry data.
        
        Creates ownership, directorship, and control relationships.
        """
        edges = []
        
        for record in corporate_records:
            company_id = record.get('company_id')
            
            # Directors
            for director in record.get('directors', []):
                director_id = director.get('entity_id')
                if director_id:
                    edge = self.create_edge(
                        source_id=director_id,
                        target_id=company_id,
                        relationship_type=RelationshipType.DIRECTOR_OF,
                        attributes={
                            'role': director.get('role'),
                            'appointment_date': director.get('appointment_date')
                        }
                    )
                    edges.append(edge)
            
            # Shareholders
            for shareholder in record.get('shareholders', []):
                shareholder_id = shareholder.get('entity_id')
                percentage = shareholder.get('percentage', 0)
                
                if shareholder_id:
                    rel_type = RelationshipType.CONTROLS if percentage > 50 else RelationshipType.SHAREHOLDER_OF
                    edge = self.create_edge(
                        source_id=shareholder_id,
                        target_id=company_id,
                        relationship_type=rel_type,
                        attributes={
                            'percentage': percentage,
                            'share_type': shareholder.get('share_type')
                        },
                        weight=percentage / 100.0
                    )
                    edges.append(edge)
            
            # Beneficial owners
            for bo in record.get('beneficial_owners', []):
                bo_id = bo.get('entity_id')
                if bo_id:
                    edge = self.create_edge(
                        source_id=bo_id,
                        target_id=company_id,
                        relationship_type=RelationshipType.BENEFICIAL_OWNER,
                        attributes={
                            'ownership_percentage': bo.get('percentage'),
                            'nature_of_control': bo.get('nature_of_control')
                        }
                    )
                    edges.append(edge)
        
        return edges
    
    def run_inference(self) -> List[NetworkEdge]:
        """
        Run all inference rules to discover implicit relationships.
        """
        inferred_edges = []
        
        for rule in self.inference_rules:
            new_edges = rule.apply(self.network)
            for edge in new_edges:
                # Don't add if explicit edge already exists
                if edge.id not in self.network.edges:
                    self.network.add_edge(edge)
                    inferred_edges.append(edge)
        
        return inferred_edges
    
    def propagate_risk(
        self,
        source_node_id: str,
        max_hops: int = 3,
        decay_factor: float = 0.5
    ) -> Dict[str, float]:
        """
        Propagate risk from a source node through the network.
        
        Risk decays with distance from source.
        Returns risk contributions for each affected node.
        """
        if source_node_id not in self.network.nodes:
            return {}
        
        source_risk = self.network.nodes[source_node_id].risk_score
        risk_contributions = {source_node_id: source_risk}
        
        # BFS through network
        current_level = {source_node_id}
        visited = {source_node_id}
        current_risk = source_risk
        
        for hop in range(max_hops):
            current_risk *= decay_factor
            next_level = set()
            
            for node_id in current_level:
                for edge in self.network.edges.values():
                    neighbor_id = None
                    if edge.source_id == node_id:
                        neighbor_id = edge.target_id
                    elif edge.target_id == node_id:
                        neighbor_id = edge.source_id
                    
                    if neighbor_id and neighbor_id not in visited:
                        # Weight risk by edge confidence
                        propagated_risk = current_risk * edge.confidence * edge.weight
                        risk_contributions[neighbor_id] = propagated_risk
                        next_level.add(neighbor_id)
                        visited.add(neighbor_id)
            
            current_level = next_level
            if not current_level:
                break
        
        return risk_contributions
    
    def calculate_network_metrics(self, node_id: str) -> Dict[str, float]:
        """
        Calculate network metrics for a node.
        
        - Degree centrality: number of connections
        - Risk exposure: sum of connected risk
        - Network density: clustering coefficient
        """
        if node_id not in self.network.nodes:
            return {}
        
        # Degree centrality
        in_degree = sum(1 for e in self.network.edges.values() if e.target_id == node_id)
        out_degree = sum(1 for e in self.network.edges.values() if e.source_id == node_id)
        total_degree = in_degree + out_degree
        
        # Get neighbors
        neighbors = self.network.get_neighbors(node_id, depth=1)
        
        # Risk exposure
        risk_exposure = sum(
            self.network.nodes[n].risk_score 
            for n in neighbors 
            if n in self.network.nodes
        )
        
        # Clustering coefficient (simplified)
        if len(neighbors) < 2:
            clustering = 0.0
        else:
            # Count edges between neighbors
            neighbor_edges = 0
            neighbor_list = list(neighbors)
            for i, n1 in enumerate(neighbor_list):
                for n2 in neighbor_list[i+1:]:
                    for e in self.network.edges.values():
                        if (e.source_id == n1 and e.target_id == n2) or \
                           (e.source_id == n2 and e.target_id == n1):
                            neighbor_edges += 1
                            break
            
            max_edges = len(neighbors) * (len(neighbors) - 1) / 2
            clustering = neighbor_edges / max_edges if max_edges > 0 else 0.0
        
        return {
            'in_degree': in_degree,
            'out_degree': out_degree,
            'total_degree': total_degree,
            'neighbor_count': len(neighbors),
            'risk_exposure': risk_exposure,
            'clustering_coefficient': clustering
        }
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the network."""
        return {
            'node_count': len(self.network.nodes),
            'edge_count': len(self.network.edges),
            'node_types': dict(defaultdict(int, {
                n.node_type: sum(1 for x in self.network.nodes.values() if x.node_type == n.node_type)
                for n in self.network.nodes.values()
            })),
            'relationship_types': dict(defaultdict(int, {
                e.relationship_type.value: sum(1 for x in self.network.edges.values() if x.relationship_type == e.relationship_type)
                for e in self.network.edges.values()
            })),
            'avg_risk_score': sum(n.risk_score for n in self.network.nodes.values()) / len(self.network.nodes) if self.network.nodes else 0,
            'high_risk_nodes': sum(1 for n in self.network.nodes.values() if n.risk_score >= 0.7)
        }
    
    def export_to_neo4j_format(self) -> Dict[str, List[Dict]]:
        """Export network to Neo4j-compatible format."""
        nodes = []
        for node in self.network.nodes.values():
            nodes.append({
                'id': node.id,
                'labels': [node.node_type.upper()],
                'properties': {
                    'label': node.label,
                    'risk_score': node.risk_score,
                    **node.attributes
                }
            })
        
        relationships = []
        for edge in self.network.edges.values():
            relationships.append({
                'id': edge.id,
                'type': edge.relationship_type.value,
                'startNode': edge.source_id,
                'endNode': edge.target_id,
                'properties': {
                    'weight': edge.weight,
                    'confidence': edge.confidence,
                    **edge.attributes
                }
            })
        
        return {'nodes': nodes, 'relationships': relationships}


# Demo
def demo_network_generation():
    """Demonstrate network generation capabilities."""
    
    engine = NetworkGenerationEngine()
    
    # Create nodes (entities)
    engine.create_node_from_entity(
        entity_id="E001",
        entity_type="individual",
        name="John Smith",
        attributes={"address": "123 Main St", "phone": "+65-1234-5678"},
        risk_score=0.3
    )
    
    engine.create_node_from_entity(
        entity_id="E002",
        entity_type="organization",
        name="Acme Corp",
        attributes={"address": "456 Business Rd"},
        risk_score=0.1
    )
    
    engine.create_node_from_entity(
        entity_id="E003",
        entity_type="individual",
        name="Jane Doe",
        attributes={"address": "123 Main St", "phone": "+65-1234-5678"},  # Same address and phone
        risk_score=0.8
    )
    
    # Create explicit relationships
    engine.create_edge("E001", "E002", RelationshipType.DIRECTOR_OF)
    engine.create_edge("E001", "E002", RelationshipType.SHAREHOLDER_OF, attributes={'percentage': 60})
    
    # Run inference
    inferred = engine.run_inference()
    print(f"Inferred {len(inferred)} new relationships")
    
    # Propagate risk from high-risk entity
    risk_propagation = engine.propagate_risk("E003", max_hops=2)
    print(f"Risk propagation from E003: {risk_propagation}")
    
    # Get metrics
    for node_id in ["E001", "E002", "E003"]:
        metrics = engine.calculate_network_metrics(node_id)
        print(f"Metrics for {node_id}: {metrics}")
    
    # Summary
    summary = engine.get_network_summary()
    print(f"Network summary: {summary}")


if __name__ == "__main__":
    demo_network_generation()

