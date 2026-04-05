# -*- coding: utf-8 -*-
"""
Neo4j Database Connection Module
"""
from neo4j import GraphDatabase
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jClient:
    """Neo4j Database Client"""
    
    _instance: Optional['Neo4jClient'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.driver = None
        return cls._instance
    
    def connect(self):
        """Connect to Neo4j database"""
        uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "Tony1985")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
            print(f"[OK] Neo4j connected: {uri}")
            return True
        except Exception as e:
            print(f"[ERROR] Neo4j connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect"""
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")
    
    def query(self, cypher: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query"""
        if not self.driver:
            self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"Neo4j query error: {e}")
            return []
    
    def write(self, cypher: str, params: Optional[Dict] = None) -> bool:
        """Execute write operation"""
        if not self.driver:
            self.connect()
        
        try:
            with self.driver.session() as session:
                session.run(cypher, params or {})
            return True
        except Exception as e:
            print(f"Neo4j write error: {e}")
            return False


# Global client instance
neo4j_client = Neo4jClient()


def get_neo4j() -> Neo4jClient:
    """Get Neo4j client instance"""
    return neo4j_client


def init_neo4j():
    """Initialize Neo4j connection"""
    return neo4j_client.connect()
