# -*- coding: utf-8 -*-
"""
Create Business Events from Existing Data
根据现有业务数据创建事件
"""

from neo4j import GraphDatabase
from datetime import datetime, timedelta
import random

NEO4J_CONFIG = {'uri': 'bolt://localhost:7687', 'auth': ('neo4j', 'Tony1985')}

def get_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def create_events(driver):
    print("="*70)
    print("创建业务事件")
    print("="*70)
    
    with driver.session() as s:
        # 1. 从 Invoice 创建事件
        print("\n[1] 从 Invoice 创建事件...")
        r = s.run("""
            MATCH (inv:Invoice)
            WHERE NOT (inv)-[:GENERATED_EVENT]->()
            WITH inv LIMIT 50
            CALL {
                WITH inv
                CREATE (evt:Event:InvoiceEvent {
                    id: 'EVT-INV-' + toString(inv.id),
                    eventType: 'INVOICE_' + inv.paymentStatus,
                    entityLabel: 'Invoice',
                    entityId: inv.id,
                    eventDate: inv.invoiceDate,
                    amount: inv.amount,
                    status: inv.paymentStatus,
                    createdAt: datetime().epochMillis,
                    source: 'AP_MODULE'
                })
                MERGE (inv)-[:GENERATED_EVENT]->(evt)
                RETURN count(evt) as cnt
            }
            RETURN sum(cnt) as total
        """)
        inv_cnt = r.single()['total']
        print(f"  OK 创建 {inv_cnt} 个发票事件")
        
        # 2. 从 PO 创建事件
        print("\n[2] 从 PurchaseOrder 创建事件...")
        r = s.run("""
            MATCH (po:PurchaseOrder)
            WHERE NOT (po)-[:GENERATED_EVENT]->()
            WITH po LIMIT 50
            CALL {
                WITH po
                CREATE (evt:Event:POEvent {
                    id: 'EVT-PO-' + toString(po.id),
                    eventType: 'PO_' + po.status,
                    entityLabel: 'PurchaseOrder',
                    entityId: po.id,
                    eventDate: po.creationDate,
                    amount: po.amount,
                    status: po.status,
                    createdAt: datetime().epochMillis,
                    source: 'PO_MODULE'
                })
                MERGE (po)-[:GENERATED_EVENT]->(evt)
                RETURN count(evt) as cnt
            }
            RETURN sum(cnt) as total
        """)
        po_cnt = r.single()['total']
        print(f"  OK 创建 {po_cnt} 个采购订单事件")
        
        # 3. 从 Payment 创建事件
        print("\n[3] 从 Payment 创建事件...")
        r = s.run("""
            MATCH (p:Payment)
            WHERE NOT (p)-[:GENERATED_EVENT]->()
            WITH p LIMIT 50
            CALL {
                WITH p
                CREATE (evt:Event:PaymentEvent {
                    id: 'EVT-PAY-' + toString(p.id),
                    eventType: 'PAYMENT_ISSUED',
                    entityLabel: 'Payment',
                    entityId: p.id,
                    eventDate: p.paymentDate,
                    amount: p.amount,
                    checkNumber: p.checkNumber,
                    status: 'COMPLETED',
                    createdAt: datetime().epochMillis,
                    source: 'AP_MODULE'
                })
                MERGE (p)-[:GENERATED_EVENT]->(evt)
                RETURN count(evt) as cnt
            }
            RETURN sum(cnt) as total
        """)
        pay_cnt = r.single()['total']
        print(f"  OK 创建 {pay_cnt} 个付款事件")
        
        # 4. 从 Project 创建事件
        print("\n[4] 从 Project 创建事件...")
        r = s.run("""
            MATCH (proj:Project)
            WHERE NOT (proj)-[:GENERATED_EVENT]->()
            WITH proj LIMIT 50
            CALL {
                WITH proj
                CREATE (evt:Event:ProjectEvent {
                    id: 'EVT-PRJ-' + toString(proj.id),
                    eventType: 'PROJECT_' + proj.statusCode,
                    entityLabel: 'Project',
                    entityId: proj.id,
                    eventDate: proj.startDate,
                    budgetAmount: proj.budgetAmount,
                    actualCost: proj.actualCost,
                    status: proj.statusCode,
                    createdAt: datetime().epochMillis,
                    source: 'PA_MODULE'
                })
                MERGE (proj)-[:GENERATED_EVENT]->(evt)
                RETURN count(evt) as cnt
            }
            RETURN sum(cnt) as total
        """)
        prj_cnt = r.single()['total']
        print(f"  OK 创建 {prj_cnt} 个项目事件")
        
        # 5. 从 FixedAsset 创建事件
        print("\n[5] 从 FixedAsset 创建事件...")
        r = s.run("""
            MATCH (asset:FixedAsset)
            WHERE NOT (asset)-[:GENERATED_EVENT]->()
            WITH asset LIMIT 50
            CALL {
                WITH asset
                CREATE (evt:Event:AssetEvent {
                    id: 'EVT-AST-' + toString(asset.id),
                    eventType: 'ASSET_' + asset.status,
                    entityLabel: 'FixedAsset',
                    entityId: asset.id,
                    eventDate: date().toString(),
                    cost: asset.cost,
                    status: asset.status,
                    createdAt: datetime().epochMillis,
                    source: 'FA_MODULE'
                })
                MERGE (asset)-[:GENERATED_EVENT]->(evt)
                RETURN count(evt) as cnt
            }
            RETURN sum(cnt) as total
        """)
        asset_cnt = r.single()['total']
        print(f"  OK 创建 {asset_cnt} 个资产事件")
        
        # 6. 创建系统事件
        print("\n[6] 创建系统事件...")
        r = s.run("""
            CREATE (evt:Event:SystemEvent {
                id: 'EVT-SYS-001',
                eventType: 'SYSTEM_STARTUP',
                entityLabel: 'System',
                entityId: 'ERP-SYSTEM',
                eventDate: datetime().date().toString(),
                message: 'ERP System initialized',
                status: 'SUCCESS',
                createdAt: datetime().epochMillis,
                source: 'SYSTEM'
            })
            RETURN count(evt) as total
        """)
        sys_cnt = r.single()['total']
        print(f"  OK 创建 {sys_cnt} 个系统事件")
        
        # 验证
        print("\n" + "="*70)
        print("验证事件创建:")
        print("-"*70)
        r = s.run("""
            MATCH (evt:Event)
            RETURN labels(evt)[1] as type, count(evt) as count
            ORDER BY type
        """)
        print("\n事件类型统计:")
        total = 0
        for rec in r:
            etype = rec['type'] if rec['type'] else 'Event'
            print(f"  {etype:30s}: {rec['count']}")
            total += rec['count']
        
        print(f"\n  总计：{total}")
        print("="*70)
        
        return total

def main():
    driver = get_driver()
    try:
        total = create_events(driver)
        print(f"\n[OK] 创建了 {total} 个业务事件！")
        print("\n查询示例:")
        print("  MATCH (evt:Event) RETURN evt LIMIT 10")
        print("  MATCH (inv:Invoice)-[:GENERATED_EVENT]->(evt:Event) RETURN inv, evt LIMIT 5")
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    main()
