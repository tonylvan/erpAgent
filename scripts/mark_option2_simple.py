# -*- coding: utf-8 -*-
"""
Mark Existing Nodes as Problematic (Option 2)
只标记现有节点，不同步数据
"""

from neo4j import GraphDatabase

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def mark_all(driver):
    """Mark problematic nodes by ID ranges"""
    print("="*70)
    print("Option 2: Mark Existing Nodes as Problematic")
    print("="*70)
    
    with driver.session() as session:
        # Mark problematic invoices (ID >= 2001)
        result = session.run("""
            MATCH (inv:Invoice)
            WHERE inv.id >= 2001
            SET inv.isProblematic = true,
                inv.problemType = 'data_quality_issue'
            RETURN count(inv) as count
        """)
        inv_count = result.single()['count']
        print(f"\n  OK Marked {inv_count} problematic invoices")
        
        # Mark problematic POs (ID >= 101)
        result = session.run("""
            MATCH (po:PurchaseOrder)
            WHERE po.id >= 101
            SET po.isProblematic = true,
                po.problemType = 'data_quality_issue'
            RETURN count(po) as count
        """)
        po_count = result.single()['count']
        print(f"  OK Marked {po_count} problematic POs")
        
        # Mark noisy employees (ID >= 1501)
        result = session.run("""
            MATCH (emp:Employee)
            WHERE emp.id >= 1501
            SET emp.isProblematic = true,
                emp.problemType = 'noisy_data'
            RETURN count(emp) as count
        """)
        emp_count = result.single()['count']
        print(f"  OK Marked {emp_count} noisy employees")
        
        # Mark noisy suppliers (ID >= 52)
        result = session.run("""
            MATCH (sup:Supplier)
            WHERE sup.id >= 52
            SET sup.isProblematic = true,
                sup.problemType = 'noisy_data'
            RETURN count(sup) as count
        """)
        sup_count = result.single()['count']
        print(f"  OK Marked {sup_count} noisy suppliers")
        
        # Mark noisy projects (ID >= 51)
        result = session.run("""
            MATCH (proj:Project)
            WHERE proj.id >= 51
            SET proj.isProblematic = true,
                proj.problemType = 'noisy_data'
            RETURN count(proj) as count
        """)
        proj_count = result.single()['count']
        print(f"  OK Marked {proj_count} noisy projects")
        
        # Mark noisy assets (ID >= 101)
        result = session.run("""
            MATCH (asset:FixedAsset)
            WHERE asset.id >= 101
            SET asset.isProblematic = true,
                asset.problemType = 'noisy_data'
            RETURN count(asset) as count
        """)
        asset_count = result.single()['count']
        print(f"  OK Marked {asset_count} noisy assets")
        
        # Verify
        print("\n" + "="*70)
        print("Verification:")
        print("="*70)
        
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
        
        return total

def main():
    driver = get_neo4j_driver()
    
    try:
        total = mark_all(driver)
        
        print("\n" + "="*70)
        print("[OK] Option 2 completed!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  - Marked nodes: {total}")
        print(f"  - Property: isProblematic = true")
        print(f"\nQuery examples:")
        print(f"  - Get problem: MATCH (n) WHERE n.isProblematic = true RETURN n")
        print(f"  - Get normal: MATCH (n) WHERE n.isProblematic IS NULL RETURN n")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    main()
