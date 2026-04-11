# -*- coding: utf-8 -*-
"""
Sync PostgreSQL application data (alerts, tickets) to Neo4j
PostgreSQL only has 3 tables: alerts, query_history, tickets
This script syncs alerts and tickets to Neo4j as Event nodes
"""

import psycopg2
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# PostgreSQL config
PG_HOST = os.getenv('DB_HOST', 'localhost')
PG_PORT = os.getenv('DB_PORT', '5432')
PG_DB = os.getenv('DB_NAME', 'erpagent')
PG_USER = os.getenv('DB_USER', 'postgres')
PG_PASSWORD = os.getenv('DB_PASSWORD', 'Tony1985')

# Neo4j config
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Tony1985')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')


class PgAppDataSync:
    def __init__(self):
        print("=" * 60)
        print("PostgreSQL Application Data to Neo4j Sync")
        print("=" * 60)
        print(f"PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DB}")
        print(f"Neo4j: {NEO4J_URI}")
        print("=" * 60)
        
        self.pg_conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DB,
            user=PG_USER, password=PG_PASSWORD
        )
        self.pg_cursor = self.pg_conn.cursor()
        self.neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print("[OK] PostgreSQL connected")
        print("[OK] Neo4j connected")
        print("=" * 60)
    
    def close(self):
        self.pg_cursor.close()
        self.pg_conn.close()
        self.neo4j_driver.close()
        print("[OK] Connections closed")
    
    def run_neo4j_query(self, query, params=None):
        with self.neo4j_driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params or {})
            return [record for record in result]
    
    def sync_alerts(self):
        """Sync alerts table to Neo4j as Event nodes"""
        print("[INFO] Syncing alerts...")
        
        self.pg_cursor.execute("""
            SELECT id, title, level, status, business_module, description, 
                   created_at, updated_at, acknowledged_by, acknowledged_at 
            FROM alerts 
            ORDER BY created_at DESC
        """)
        alerts = self.pg_cursor.fetchall()
        
        synced = 0
        for alert in alerts:
            alert_id = str(alert[0])
            self.run_neo4j_query("""
                MERGE (a:Alert {id: $id})
                SET a.title = $title,
                    a.level = $level,
                    a.status = $status,
                    a.businessModule = $businessModule,
                    a.description = $description,
                    a.createdAt = $createdAt,
                    a.updatedAt = $updatedAt,
                    a.acknowledgedBy = $acknowledgedBy,
                    a.acknowledgedAt = $acknowledgedAt
            """, {
                'id': alert_id,
                'title': alert[1],
                'level': alert[2],
                'status': alert[3],
                'businessModule': alert[4],
                'description': alert[5],
                'createdAt': str(alert[6]) if alert[6] else None,
                'updatedAt': str(alert[7]) if alert[7] else None,
                'acknowledgedBy': alert[8] if alert[8] else None,
                'acknowledgedAt': str(alert[9]) if alert[9] else None
            })
            synced += 1
        
        print(f"[OK] Synced {synced} alerts to Neo4j")
        return synced
    
    def sync_tickets(self):
        """Sync tickets table to Neo4j as Event nodes"""
        print("[INFO] Syncing tickets...")
        
        self.pg_cursor.execute("""
            SELECT id, title, status, priority, description, category,
                   created_by, assigned_to, created_at, updated_at, 
                   resolved_at, resolved_by, solution
            FROM tickets 
            ORDER BY created_at DESC
        """)
        tickets = self.pg_cursor.fetchall()
        
        synced = 0
        for ticket in tickets:
            ticket_id = str(ticket[0])
            self.run_neo4j_query("""
                MERGE (t:Ticket {id: $id})
                SET t.title = $title,
                    t.status = $status,
                    t.priority = $priority,
                    t.description = $description,
                    t.category = $category,
                    t.createdBy = $createdBy,
                    t.assignedTo = $assignedTo,
                    t.createdAt = $createdAt,
                    t.updatedAt = $updatedAt,
                    t.resolvedAt = $resolvedAt,
                    t.resolvedBy = $resolvedBy,
                    t.solution = $solution
            """, {
                'id': ticket_id,
                'title': ticket[1],
                'status': ticket[2],
                'priority': ticket[3],
                'description': ticket[4],
                'category': ticket[5],
                'createdBy': str(ticket[6]) if ticket[6] else None,
                'assignedTo': str(ticket[7]) if ticket[7] else None,
                'createdAt': str(ticket[8]) if ticket[8] else None,
                'updatedAt': str(ticket[9]) if ticket[9] else None,
                'resolvedAt': str(ticket[10]) if ticket[10] else None,
                'resolvedBy': str(ticket[11]) if ticket[11] else None,
                'solution': ticket[12] if ticket[12] else None
            })
            synced += 1
        
        print(f"[OK] Synced {synced} tickets to Neo4j")
        return synced
    
    def create_relationships(self):
        """Create relationships between alerts and tickets"""
        print("[INFO] Creating relationships...")
        
        # Link alerts and tickets with same source or related content
        self.run_neo4j_query("""
            MATCH (a:Alert), (t:Ticket)
            WHERE a.source = t.createdBy OR a.source = t.assignedTo
            MERGE (a)-[:RELATED_TO]->(t)
        """)
        
        print("[OK] Relationships created")
    
    def get_stats(self):
        """Get sync statistics"""
        print("\n[INFO] Getting statistics...")
        
        result = self.run_neo4j_query("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        
        print("\nNeo4j Node Statistics:")
        print("-" * 40)
        for record in result:
            print(f"  {record['label']}: {record['count']}")
        
        result = self.run_neo4j_query("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        
        print("\nNeo4j Relationship Statistics:")
        print("-" * 40)
        for record in result:
            print(f"  {record['type']}: {record['count']}")
    
    def run(self):
        """Run full sync"""
        try:
            self.sync_alerts()
            self.sync_tickets()
            self.create_relationships()
            self.get_stats()
            
            print("\n" + "=" * 60)
            print("[OK] Sync completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[ERROR] Sync failed: {e}")
            raise
        finally:
            self.close()


if __name__ == '__main__':
    sync = PgAppDataSync()
    sync.run()
