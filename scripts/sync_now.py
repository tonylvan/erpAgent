# -*- coding: utf-8 -*-
"""Quick sync script for PG to Neo4j"""
import psycopg2
from neo4j import GraphDatabase

# Connection settings
PG_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'erpagent',
    'user': 'postgres',
    'password': 'Tony1985'
}

NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

def main():
    print('[INFO] Connecting to databases...')
    
    # Connect PostgreSQL
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cur = pg_conn.cursor()
    print('[OK] PostgreSQL connected')
    
    # Connect Neo4j
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    print('[OK] Neo4j connected')
    
    # Get PostgreSQL tables
    pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    all_tables = [r[0] for r in pg_cur.fetchall()]
    print(f'\n[INFO] PostgreSQL tables ({len(all_tables)}): {all_tables[:20]}...')
    
    # Get Neo4j node counts
    print('\n[INFO] Neo4j data:')
    with neo4j_driver.session() as session:
        # Total nodes
        result = session.run('MATCH (n) RETURN count(n) as count')
        total = result.single()['count']
        print(f'  - Total nodes: {total}')
        
        # Total relationships
        result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
        rels = result.single()['count']
        print(f'  - Total relationships: {rels}')
        
        # By label
        result = session.run('MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC LIMIT 10')
        print('  - Top 10 labels:')
        for record in result:
            print(f'      {record["label"]}: {record["count"]}')
    
    # Show Neo4j stats
    print('\n[INFO] Neo4j stats:')
    with neo4j_driver.session() as session:
        result = session.run('MATCH (n) RETURN count(n) as count')
        total = result.single()['count']
        print(f'  - Total nodes: {total}')
        
        result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
        rels = result.single()['count']
        print(f'  - Total relationships: {rels}')
        
        result = session.run('MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC LIMIT 10')
        print('  - Top labels:')
        for record in result:
            print(f'      {record["label"]}: {record["count"]}')
    
    print('\n[OK] Status check complete!')
    
    # Cleanup
    pg_cur.close()
    pg_conn.close()
    neo4j_driver.close()

if __name__ == '__main__':
    main()