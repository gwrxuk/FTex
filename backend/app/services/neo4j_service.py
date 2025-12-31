"""
Neo4j service for graph-based entity resolution and analytics.
"""

from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase
from app.core.config import settings


class Neo4jService:
    """Service for interacting with Neo4j graph database."""
    
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    async def verify_connection(self):
        """Verify Neo4j connection is working."""
        async with self.driver.session() as session:
            result = await session.run("RETURN 1 as test")
            await result.single()
    
    async def close(self):
        """Close the Neo4j driver."""
        await self.driver.close()
    
    async def create_entity_node(self, entity) -> str:
        """Create an entity node in the graph."""
        async with self.driver.session() as session:
            query = """
            CREATE (e:Entity {
                id: $id,
                name: $name,
                entity_type: $entity_type,
                risk_score: $risk_score,
                is_sanctioned: $is_sanctioned,
                is_pep: $is_pep
            })
            RETURN elementId(e) as node_id
            """
            result = await session.run(
                query,
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type.value,
                risk_score=entity.risk_score,
                is_sanctioned=bool(entity.is_sanctioned),
                is_pep=bool(entity.is_pep)
            )
            record = await result.single()
            return record["node_id"] if record else None
    
    async def get_entity_relationships(self, entity_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Get relationships for an entity up to specified depth."""
        async with self.driver.session() as session:
            query = f"""
            MATCH path = (e:Entity {{id: $entity_id}})-[*1..{depth}]-(related)
            RETURN 
                related.id as related_id,
                related.name as related_name,
                related.entity_type as related_type,
                type(last(relationships(path))) as relationship_type,
                length(path) as distance
            LIMIT 100
            """
            result = await session.run(query, entity_id=entity_id)
            records = await result.data()
            return records
    
    async def get_entity_network(
        self, 
        entity_id: str, 
        depth: int = 2, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get the network graph for an entity."""
        async with self.driver.session() as session:
            query = f"""
            MATCH path = (e:Entity {{id: $entity_id}})-[*1..{depth}]-(related)
            WITH collect(path) as paths
            UNWIND paths as p
            WITH nodes(p) as ns, relationships(p) as rs
            UNWIND ns as n
            WITH collect(distinct n) as nodes, collect(distinct rs) as rels
            RETURN 
                [n in nodes | {{
                    id: n.id, 
                    label: n.name, 
                    type: n.entity_type,
                    risk_score: n.risk_score
                }}] as nodes,
                [r in rels | [rel in r | {{
                    source: startNode(rel).id,
                    target: endNode(rel).id,
                    type: type(rel)
                }}]] as edges
            LIMIT 1
            """
            result = await session.run(query, entity_id=entity_id)
            record = await result.single()
            
            if not record:
                return {"nodes": [], "edges": []}
            
            # Flatten edges list
            edges = []
            for edge_group in record["edges"]:
                edges.extend(edge_group)
            
            return {
                "nodes": record["nodes"][:limit],
                "edges": edges[:limit * 2]
            }
    
    async def find_shortest_path(
        self, 
        source_id: str, 
        target_id: str, 
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """Find shortest path between two entities."""
        async with self.driver.session() as session:
            query = f"""
            MATCH path = shortestPath(
                (source:Entity {{id: $source_id}})-[*1..{max_depth}]-(target:Entity {{id: $target_id}})
            )
            RETURN 
                [n in nodes(path) | {{id: n.id, name: n.name, type: n.entity_type}}] as nodes,
                [r in relationships(path) | {{type: type(r)}}] as relationships,
                length(path) as path_length
            """
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()
            
            if not record:
                return {"path": [], "length": -1}
            
            return {
                "nodes": record["nodes"],
                "relationships": record["relationships"],
                "length": record["path_length"]
            }
    
    async def detect_communities(self, min_size: int = 3) -> Dict[str, Any]:
        """Detect communities in the entity network using Louvain algorithm."""
        async with self.driver.session() as session:
            # This requires GDS library
            query = """
            CALL gds.louvain.stream({
                nodeProjection: 'Entity',
                relationshipProjection: {
                    RELATED: {type: '*', orientation: 'UNDIRECTED'}
                }
            })
            YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId) as node, communityId
            WITH communityId, collect({id: node.id, name: node.name}) as members
            WHERE size(members) >= $min_size
            RETURN communityId, members, size(members) as size
            ORDER BY size DESC
            LIMIT 20
            """
            try:
                result = await session.run(query, min_size=min_size)
                records = await result.data()
                return {"communities": records}
            except Exception as e:
                return {"communities": [], "error": str(e)}
    
    async def calculate_centrality(
        self, 
        algorithm: str = "pagerank", 
        limit: int = 20
    ) -> Dict[str, Any]:
        """Calculate centrality metrics for entities."""
        queries = {
            "pagerank": """
                CALL gds.pageRank.stream({
                    nodeProjection: 'Entity',
                    relationshipProjection: '*'
                })
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) as node, score
                RETURN node.id as id, node.name as name, score
                ORDER BY score DESC
                LIMIT $limit
            """,
            "betweenness": """
                CALL gds.betweenness.stream({
                    nodeProjection: 'Entity',
                    relationshipProjection: '*'
                })
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) as node, score
                RETURN node.id as id, node.name as name, score
                ORDER BY score DESC
                LIMIT $limit
            """,
            "degree": """
                MATCH (n:Entity)
                WITH n, size((n)--()) as degree
                RETURN n.id as id, n.name as name, degree as score
                ORDER BY degree DESC
                LIMIT $limit
            """
        }
        
        async with self.driver.session() as session:
            query = queries.get(algorithm, queries["degree"])
            try:
                result = await session.run(query, limit=limit)
                records = await result.data()
                return {"results": records, "algorithm": algorithm}
            except Exception as e:
                # Fallback to degree centrality if GDS not available
                if algorithm != "degree":
                    return await self.calculate_centrality("degree", limit)
                return {"results": [], "algorithm": algorithm, "error": str(e)}
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two entities."""
        async with self.driver.session() as session:
            props = properties or {}
            query = f"""
            MATCH (source:Entity {{id: $source_id}})
            MATCH (target:Entity {{id: $target_id}})
            CREATE (source)-[r:{relationship_type} $props]->(target)
            RETURN type(r) as relationship_type
            """
            result = await session.run(
                query, 
                source_id=source_id, 
                target_id=target_id,
                props=props
            )
            record = await result.single()
            return {"success": bool(record), "relationship_type": relationship_type}
    
    async def analyze_risk_propagation(
        self, 
        entity_id: str, 
        depth: int = 3
    ) -> Dict[str, Any]:
        """Analyze how risk propagates through the network."""
        async with self.driver.session() as session:
            query = f"""
            MATCH path = (source:Entity {{id: $entity_id}})-[*1..{depth}]-(affected)
            WHERE affected.id <> $entity_id
            WITH affected, 
                 length(path) as distance,
                 source.risk_score as source_risk
            RETURN 
                affected.id as id,
                affected.name as name,
                affected.entity_type as type,
                affected.risk_score as current_risk,
                distance,
                source_risk * (1.0 / distance) as propagated_risk
            ORDER BY propagated_risk DESC
            LIMIT 50
            """
            result = await session.run(query, entity_id=entity_id)
            records = await result.data()
            return {
                "source_entity": entity_id,
                "affected_entities": records
            }
    
    async def get_transaction_flow(
        self,
        entity_id: str,
        direction: str = "both",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get transaction flow for an entity."""
        async with self.driver.session() as session:
            if direction == "incoming":
                pattern = "(other)-[t:TRANSACTED]->(e:Entity {id: $entity_id})"
            elif direction == "outgoing":
                pattern = "(e:Entity {id: $entity_id})-[t:TRANSACTED]->(other)"
            else:
                pattern = "(e:Entity {id: $entity_id})-[t:TRANSACTED]-(other)"
            
            query = f"""
            MATCH {pattern}
            RETURN 
                other.id as counterparty_id,
                other.name as counterparty_name,
                t.amount as amount,
                t.currency as currency,
                t.transaction_date as date
            ORDER BY t.transaction_date DESC
            LIMIT $limit
            """
            result = await session.run(query, entity_id=entity_id, limit=limit)
            records = await result.data()
            return {
                "entity_id": entity_id,
                "direction": direction,
                "flows": records
            }

