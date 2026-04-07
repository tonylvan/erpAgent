"""
Neo4j Database Service
Handles connection and queries to Neo4j graph database
"""
import os
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


class Neo4jService:
    def __init__(self):
        self.driver = None
        self.connected = False
        self.connect()
    
    def connect(self):
        """Connect to Neo4j database"""
        try:
            uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
                record = result.single()
                if record:
                    self.connected = True
                    logger.info(f"[OK] Neo4j connected: {uri}")
                else:
                    self.connected = True
                    logger.info(f"[OK] Neo4j connected (empty database): {uri}")
                    
        except ServiceUnavailable as e:
            self.connected = False
            logger.error(f"[ERROR] Neo4j connection failed: {e}")
        except Exception as e:
            self.connected = False
            logger.error(f"[ERROR] Neo4j error: {e}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.connected = False
    
    def query(self, cypher: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute Cypher query and return results"""
        if not self.connected or not self.driver:
            logger.warning("Neo4j not connected, returning empty results")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"[ERROR] Neo4j query failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.connected:
            return {"nodes": 0, "relationships": 0, "labels": [], "relationship_types": []}
        
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()["count"] if node_result.single() else 0
                
                # Count relationships
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()["count"] if rel_result.single() else 0
                
                # Get labels
                label_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in label_result]
                
                # Get relationship types
                rel_type_result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in rel_type_result]
                
                return {
                    "nodes": node_count,
                    "relationships": rel_count,
                    "labels": labels,
                    "relationship_types": rel_types
                }
        except Exception as e:
            logger.error(f"[ERROR] Neo4j stats failed: {e}")
            return {"nodes": 0, "relationships": 0, "labels": [], "relationship_types": []}
    
    def get_nodes(self, label: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get nodes from database"""
        if label:
            cypher = f"MATCH (n:`{label}`) RETURN n LIMIT $limit"
        else:
            cypher = "MATCH (n) RETURN n LIMIT $limit"
        
        results = self.query(cypher, {"limit": limit})
        nodes = []
        
        for record in results:
            node = record.get("n", {})
            if hasattr(node, "items"):
                node_data = dict(node.items())
                nodes.append({
                    "id": str(node.get("id", hash(str(node)))),
                    "name": node.get("name", "Unknown"),
                    "type": label or list(node.keys())[0] if node else "Unknown",
                    "properties": node_data
                })
        
        return nodes
    
    def get_edges(self, limit: int = 100) -> List[Dict]:
        """Get relationships from database"""
        cypher = "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT $limit"
        results = self.query(cypher, {"limit": limit})
        
        edges = []
        for record in results:
            rel = record.get("r", {})
            start = record.get("a", {})
            end = record.get("b", {})
            
            if rel and hasattr(rel, "items"):
                edges.append({
                    "id": str(hash(str(rel))),
                    "source": str(start.get("id", hash(str(start)))),
                    "target": str(end.get("id", hash(str(end)))),
                    "type": rel.type if hasattr(rel, "type") else "RELATED",
                    "properties": dict(rel.items()) if hasattr(rel, "items") else {}
                })
        
        return edges


# Global instance
neo4j_service = Neo4jService()
