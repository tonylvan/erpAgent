# -*- coding: utf-8 -*-
"""
Create Business Events - Simple Version
"""

from neo4j import GraphDatabase

NEO4J_CONFIG = {'uri': 'bolt://localhost:7687', 'auth': ('neo4j', 'Tony1985')}

def main():
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    print("="*70)
    print("创建业务事件")
    print("="*70)
    
    with driver.session() as s:
        # Invoice Events
        print("\n[1] Invoice Events...")
        r = s.run("""
            MATCH (inv:Invoice)
            CREATE (evt:Event:InvoiceEvent {
                id: 'EVT-INV-' + toString(inv.id),
                eventType: 'INVOICE_CREATED',
                entityLabel: 'Invoice',
                entityId: inv.id,
                amount: inv.amount,
                status: inv.paymentStatus,
                createdAt: datetime().epochMillis,
                source: 'AP_MODULE'
            })
            MERGE (inv)-[:GENERATED_EVENT]->(evt)
            RETURN count(evt) as cnt
        """)
        print(f"  OK Created {r.single()['cnt']} invoice events")
        
        # PO Events
        print("\n[2] PO Events...")
        r = s.run("""
            MATCH (po:PurchaseOrder)
            CREATE (evt:Event:POEvent {
                id: 'EVT-PO-' + toString(po.id),
                eventType: 'PO_CREATED',
                entityLabel: 'PurchaseOrder',
                entityId: po.id,
                amount: po.amount,
                status: po.status,
                createdAt: datetime().epochMillis,
                source: 'PO_MODULE'
            })
            MERGE (po)-[:GENERATED_EVENT]->(evt)
            RETURN count(evt) as cnt
        """)
        print(f"  OK Created {r.single()['cnt']} PO events")
        
        # Payment Events
        print("\n[3] Payment Events...")
        r = s.run("""
            MATCH (p:Payment)
            CREATE (evt:Event:PaymentEvent {
                id: 'EVT-PAY-' + toString(p.id),
                eventType: 'PAYMENT_ISSUED',
                entityLabel: 'Payment',
                entityId: p.id,
                amount: p.amount,
                checkNumber: p.checkNumber,
                createdAt: datetime().epochMillis,
                source: 'AP_MODULE'
            })
            MERGE (p)-[:GENERATED_EVENT]->(evt)
            RETURN count(evt) as cnt
        """)
        print(f"  OK Created {r.single()['cnt']} payment events")
        
        # Project Events
        print("\n[4] Project Events...")
        r = s.run("""
            MATCH (proj:Project)
            CREATE (evt:Event:ProjectEvent {
                id: 'EVT-PRJ-' + toString(proj.id),
                eventType: 'PROJECT_' + proj.statusCode,
                entityLabel: 'Project',
                entityId: proj.id,
                budgetAmount: proj.budgetAmount,
                actualCost: proj.actualCost,
                status: proj.statusCode,
                createdAt: datetime().epochMillis,
                source: 'PA_MODULE'
            })
            MERGE (proj)-[:GENERATED_EVENT]->(evt)
            RETURN count(evt) as cnt
        """)
        print(f"  OK Created {r.single()['cnt']} project events")
        
        # Asset Events
        print("\n[5] Asset Events...")
        r = s.run("""
            MATCH (asset:FixedAsset)
            CREATE (evt:Event:AssetEvent {
                id: 'EVT-AST-' + toString(asset.id),
                eventType: 'ASSET_' + asset.status,
                entityLabel: 'FixedAsset',
                entityId: asset.id,
                cost: asset.cost,
                status: asset.status,
                createdAt: datetime().epochMillis,
                source: 'FA_MODULE'
            })
            MERGE (asset)-[:GENERATED_EVENT]->(evt)
            RETURN count(evt) as cnt
        """)
        print(f"  OK Created {r.single()['cnt']} asset events")
        
        # Verify
        print("\n" + "="*70)
        print("Verification:")
        print("-"*70)
        r = s.run("""
            MATCH (evt:Event)
            RETURN labels(evt)[1] as type, count(evt) as count
            ORDER BY type
        """)
        total = 0
        print("\nEvent Types:")
        for rec in r:
            etype = rec['type'] if rec['type'] else 'Event'
            print(f"  {etype:30s}: {rec['count']}")
            total += rec['count']
        
        print(f"\n  Total Events: {total}")
        print("="*70)
        
        # Relationships
        r = s.run("""
            MATCH ()-[r:GENERATED_EVENT]->()
            RETURN count(r) as cnt
        """)
        print(f"  GENERATED_EVENT relationships: {r.single()['cnt']}")
        print("="*70)

if __name__ == '__main__':
    main()
