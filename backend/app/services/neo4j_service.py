"""
Neo4j Database Service
Handles connection and queries to Neo4j graph database
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

# Load .env file (from backend directory)
_backend_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_backend_root / ".env")

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
            
            # Debug log
            logger.info(f"[DEBUG] NEO4J_URI={uri}, NEO4J_USER={user}, Password loaded={bool(password and password != 'password')}")
            
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
                node_record = node_result.single()
                node_count = node_record["count"] if node_record else 0
                
                # Count relationships
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_record = rel_result.single()
                rel_count = rel_record["count"] if rel_record else 0
                
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
            cypher = f"MATCH (n:`{label}`) RETURN elementId(n) as id, labels(n) as labels, properties(n) as props LIMIT $limit"
        else:
            cypher = "MATCH (n) RETURN elementId(n) as id, labels(n) as labels, properties(n) as props LIMIT $limit"
        
        results = self.query(cypher, {"limit": limit})
        nodes = []
        
        for record in results:
            props = record.get("props", {})
            labels = record.get("labels", [])
            node_type = labels[0] if labels else "Entity"
            
            # Convert Neo4j DateTime to string
            clean_props = {}
            for k, v in props.items():
                if hasattr(v, 'iso_format'):  # Neo4j DateTime
                    clean_props[k] = v.iso_format()
                elif isinstance(v, (int, float, str, bool, list)):
                    clean_props[k] = v
                else:
                    clean_props[k] = str(v)
            
            nodes.append({
                "id": record.get("id", "unknown"),
                "name": clean_props.get("name") or clean_props.get("code") or clean_props.get("id") or clean_props.get("customer") or clean_props.get("price_list_name") or f"{node_type} #{len(nodes)+1}",
                "type": node_type,
                "description": clean_props.get("description", ""),
                "properties": clean_props
            })
        
        return nodes
    
    def get_edges(self, limit: int = 100) -> List[Dict]:
        """Get relationships from database"""
        # Use elementId for both nodes and relationships (Neo4j 5.x compatible)
        cypher = "MATCH (a)-[r]->(b) RETURN elementId(a) as source_id, elementId(b) as target_id, type(r) as rel_type, properties(r) as props, elementId(r) as edge_id LIMIT $limit"
        results = self.query(cypher, {"limit": limit})
        
        edges = []
        for record in results:
            props = record.get("props", {})
            
            # Convert Neo4j DateTime to string
            clean_props = {}
            for k, v in props.items():
                if hasattr(v, 'iso_format'):  # Neo4j DateTime
                    clean_props[k] = v.iso_format()
                elif isinstance(v, (int, float, str, bool, list)):
                    clean_props[k] = v
                else:
                    clean_props[k] = str(v)
            
            edges.append({
                "id": str(record.get("edge_id", 0)),
                "source": record.get("source_id", "unknown"),
                "target": record.get("target_id", "unknown"),
                "type": record.get("rel_type", "RELATED"),
                "properties": clean_props
            })
        
        return edges
    
    def get_nodes_by_ids(self, node_ids: List[str]) -> List[Dict]:
        """Get nodes by their element IDs"""
        if not node_ids:
            return []
        
        # Build Cypher with elementId matching
        ids_str = ', '.join(f'"{nid}"' for nid in node_ids)
        cypher = f"""
        MATCH (n)
        WHERE elementId(n) IN [{ids_str}]
        RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
        """
        
        results = self.query(cypher)
        nodes = []
        
        for record in results:
            props = record.get("props", {})
            labels = record.get("labels", [])
            node_type = labels[0] if labels else "Entity"
            
            # Convert Neo4j DateTime to string
            clean_props = {}
            for k, v in props.items():
                if hasattr(v, 'iso_format'):
                    clean_props[k] = v.iso_format()
                elif isinstance(v, (int, float, str, bool, list)):
                    clean_props[k] = v
                else:
                    clean_props[k] = str(v)
            
            nodes.append({
                "id": record.get("id", "unknown"),
                "name": clean_props.get("name") or clean_props.get("code") or clean_props.get("id") or clean_props.get("customer") or clean_props.get("price_list_name") or f"{node_type} #{len(nodes)+1}",
                "type": node_type,
                "description": clean_props.get("description", ""),
                "properties": clean_props
            })
        
        return nodes
    
    def create_event_node(self, event: Dict) -> bool:
        """Create an Event node from alert data"""
        if not self.connected:
            return False
        
        try:
            cypher = """
            MERGE (e:Event {alert_id: $alert_id})
            SET e.title = $title,
                e.level = $level,
                e.status = $status,
                e.business_module = $business_module,
                e.description = $description,
                e.created_at = $created_at
            RETURN e
            """
            self.query(cypher, {
                "alert_id": event.get("id"),
                "title": event.get("title"),
                "level": event.get("level"),
                "status": event.get("status"),
                "business_module": event.get("business_module"),
                "description": event.get("description"),
                "created_at": event.get("created_at")
            })
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to create event node: {e}")
            return False
    
    def sync_events(self, events: List[Dict]) -> int:
        """Sync multiple events to graph"""
        count = 0
        for event in events:
            if self.create_event_node(event):
                count += 1
        return count
    
    def link_event_to_entities(self, alert_id: int, entity_ids: List[str]) -> int:
        """Link an event to related entities"""
        if not self.connected or not entity_ids:
            return 0
        
        count = 0
        for entity_id in entity_ids:
            try:
                cypher = """
                MATCH (e:Event {alert_id: $alert_id})
                MATCH (t) WHERE elementId(t) = $entity_id OR t.id = $entity_id
                MERGE (e)-[:RELATES_TO]->(t)
                """
                self.query(cypher, {"alert_id": alert_id, "entity_id": entity_id})
                count += 1
            except Exception as e:
                logger.warning(f"Failed to link event to entity: {e}")
        return count


# Global instance
neo4j_service = Neo4jService()
