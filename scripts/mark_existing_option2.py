# -*- coding: utf-8 -*-
"""
Mark Problematic Data in Neo4j (Option 2)
标记现有节点 - 数据已在 Neo4j 中
"""

from neo4j import GraphDatabase

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def mark_by_id_range(driver, label, id_prop, min_id, problem_type):
    """Mark nodes by ID range"""
    with driver.session() as session:
        # First check if nodes exist with this label
        check = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
        total = check.single()['count']
        
        # Mark problematic ones
        result = session.run(f"""
            MATCH (n:{label})
            WHERE n.{id_prop} >= $min_id
            SET n.isProblematic = true,
                n.problemType = $problem_type
            RETURN count(n) as count
        """, min_id=min_id, problem_type=problem_type)
        
        marked = result.single()['count']
        return total, marked

def main():
    print("="*70)
    print("Option 2: Mark Existing Nodes as Problematic")
    print("="*70)
    
    driver = get_neo4j_driver()
    
    try:
        configs = [
            ('Invoice', 'id', 2001, 'data_quality_issue'),
            ('PurchaseOrder', 'id', 101, 'data_quality_issue'),
            ('Employee', 'id', 1501, 'noisy_data'),
            ('Supplier', 'id', 52, 'noisy_data'),
            ('Project', 'id', 51, 'noisy_data'),
            ('FixedAsset', 'id', 101, 'noisy_data'),
        ]
        
        total_marked = 0
        
        for label, id_prop, min_id, problem_type in configs:
            total, marked = mark_by_id_range(driver, label, id_prop, min_id, problem_type)
            print(f"  {label:20s}: {marked}/{total} marked")
            total_marked += marked
        
        print("\n" + "="*70)
        print("Verification:")
        print("="*70)
        
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.isProblematic = true
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY label
            """)
            
            print("\nMarked Problem Nodes:")
            print("-" * 50)
            total = 0
            for rec in result:
                label = rec['label'] or 'Unknown'
                print(f"  {label:30s}: {rec['count']}")
                total += rec['count']
            
            print(f"\n  Total Marked: {total}")
            print("="*70)
        
        print("\n[OK] Option 2 completed!")
        print(f"\nQuery: MATCH (n) WHERE n.isProblematic = true RETURN n")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    main()
