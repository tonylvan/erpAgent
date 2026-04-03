# -*- coding: utf-8 -*-
"""
Clean ProblemData nodes and mark existing nodes (Option 2)
清理独立节点，改为标记现有节点
"""

from neo4j import GraphDatabase

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def clean_and_mark(driver):
    """Clean ProblemData nodes and mark existing nodes"""
    print("="*70)
    print("Step 1: Clean ProblemData nodes")
    print("="*70)
    
    with driver.session() as session:
        # Delete ProblemData nodes and their relationships
        result = session.run("""
            MATCH (n:ProblemData)
            DETACH DELETE n
            RETURN count(n) as count
        """)
        count = result.single()['count']
        print(f"  OK Deleted {count} ProblemData nodes")
        
        print("\n" + "="*70)
        print("Step 2: Mark existing nodes as problematic")
        print("="*70)
        
        # Mark problematic invoices
        result = session.run("""
            MATCH (inv:Invoice)
            WHERE inv.id >= 2001
            SET inv.isProblematic = true,
                inv.problemType = 'data_quality_issue'
            RETURN count(inv) as count
        """)
        inv_count = result.single()['count']
        print(f"  OK Marked {inv_count} problematic invoices")
        
        # Mark problematic POs
        result = session.run("""
            MATCH (po:PurchaseOrder)
            WHERE po.id >= 101
            SET po.isProblematic = true,
                po.problemType = 'data_quality_issue'
            RETURN count(po) as count
        """)
        po_count = result.single()['count']
        print(f"  OK Marked {po_count} problematic POs")
        
        # Mark noisy employees
        result = session.run("""
            MATCH (emp:Employee)
            WHERE emp.id >= 1501
            SET emp.isProblematic = true,
                emp.problemType = 'noisy_data'
            RETURN count(emp) as count
        """)
        emp_count = result.single()['count']
        print(f"  OK Marked {emp_count} noisy employees")
        
        # Mark noisy suppliers
        result = session.run("""
            MATCH (sup:Supplier)
            WHERE sup.id >= 52
            SET sup.isProblematic = true,
                sup.problemType = 'noisy_data'
            RETURN count(sup) as count
        """)
        sup_count = result.single()['count']
        print(f"  OK Marked {sup_count} noisy suppliers")
        
        # Mark noisy projects
        result = session.run("""
            MATCH (proj:Project)
            WHERE proj.id >= 51
            SET proj.isProblematic = true,
                proj.problemType = 'noisy_data'
            RETURN count(proj) as count
        """)
        proj_count = result.single()['count']
        print(f"  OK Marked {proj_count} noisy projects")
        
        # Mark noisy assets
        result = session.run("""
            MATCH (asset:FixedAsset)
            WHERE asset.id >= 101
            SET asset.isProblematic = true,
                asset.problemType = 'noisy_data'
            RETURN count(asset) as count
        """)
        asset_count = result.single()['count']
        print(f"  OK Marked {asset_count} noisy assets")
        
        print("\n" + "="*70)
        print("Step 3: Verify results")
        print("="*70)
        
        # Count marked nodes
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
        
        print(f"\n  Total Marked Nodes: {total}")
        print("="*70)
        
        # Count normal nodes
        result = session.run("""
            MATCH (n)
            WHERE n.isProblematic IS NOT true
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nNormal Nodes (for reference):")
        print("-" * 50)
        for rec in result:
            label = rec['label'] or 'Unknown'
            if label not in ['ProblemData']:
                print(f"  {label:30s}: {rec['count']}")
        
        return total

def main():
    print("="*70)
    print("Clean ProblemData and Mark Existing Nodes (Option 2)")
    print("="*70)
    
    driver = get_neo4j_driver()
    
    try:
        total = clean_and_mark(driver)
        
        print("\n" + "="*70)
        print("[OK] Option 2 migration completed!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  - Deleted: ProblemData nodes (independent)")
        print(f"  - Marked: {total} existing nodes with isProblematic=true")
        print(f"\nQuery examples:")
        print(f"  - Get problem data: MATCH (n) WHERE n.isProblematic = true RETURN n")
        print(f"  - Get normal data: MATCH (n) WHERE n.isProblematic IS NOT true RETURN n")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    main()
