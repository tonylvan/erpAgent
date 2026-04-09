#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Neo4j data statistics"""

from neo4j import GraphDatabase

def check_data():
    driver = GraphDatabase.driver(
        'bolt://127.0.0.1:7687',
        auth=('neo4j', 'Tony1985')
    )
    
    with driver.session() as session:
        # Count nodes by label
        result = session.run('''
            MATCH (n)
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY count DESC
        ''')
        
        print("=" * 50)
        print("Neo4j Node Statistics")
        print("=" * 50)
        total_nodes = 0
        for record in result:
            print(f"{record['label']}: {record['count']}")
            total_nodes += record['count']
        
        # Count relationships
        rel_result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
        rel_count = rel_result.single()['count']
        
        print("=" * 50)
        print(f"Total Nodes: {total_nodes}")
        print(f"Total Relationships: {rel_count}")
        print("=" * 50)
        
        # Check GL/XLA specific data
        gl_check = session.run('''
            MATCH (n)
            WHERE n:GLLedger OR n:GLPeriod OR n:GLAccount OR n:GLBatch OR n:GLJournal
                 OR n:XLAEvent OR n:AccountingEntry
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY label
        ''')
        
        print("\nGL/XLA Data:")
        gl_total = 0
        for record in gl_check:
            print(f"  {record['label']}: {record['count']}")
            gl_total += record['count']
        
        if gl_total == 0:
            print("  ⚠️ No GL/XLA data found!")
        
    driver.close()

if __name__ == '__main__':
    check_data()