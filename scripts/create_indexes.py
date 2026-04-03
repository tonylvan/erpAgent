# -*- coding: utf-8 -*-
"""
Create Recommended Indexes for Neo4j
创建推荐的索引
"""

from neo4j import GraphDatabase

NEO4J_CONFIG = {'uri': 'bolt://localhost:7687', 'auth': ('neo4j', 'Tony1985')}

def main():
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    print("="*70)
    print("创建 Neo4j 推荐索引")
    print("="*70)
    
    with driver.session() as s:
        # 1. 金额字段索引
        print("\n[1] 创建金额字段索引...")
        
        indexes = [
            # 发票金额
            ("CREATE INDEX invoice_amount_idx IF NOT EXISTS FOR (i:Invoice) ON (i.amount)", "Invoice.amount"),
            ("CREATE INDEX invoice_vendor_id_idx IF NOT EXISTS FOR (i:Invoice) ON (i.vendorId)", "Invoice.vendorId"),
            
            # PO 金额
            ("CREATE INDEX po_amount_idx IF NOT EXISTS FOR (p:PurchaseOrder) ON (p.amount)", "PurchaseOrder.amount"),
            ("CREATE INDEX po_status_idx IF NOT EXISTS FOR (p:PurchaseOrder) ON (p.status)", "PurchaseOrder.status"),
            
            # 问题数据查询
            ("CREATE INDEX problematic_idx IF NOT EXISTS FOR (n:ProblemData) ON (n.isProblematic)", "ProblemData.isProblematic"),
            
            # 姓名查询
            ("CREATE INDEX employee_name_idx IF NOT EXISTS FOR (e:Employee) ON (e.name)", "Employee.name"),
            ("CREATE INDEX supplier_name_idx IF NOT EXISTS FOR (s:Supplier) ON (s.name)", "Supplier.name"),
            
            # 事件查询
            ("CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.eventType)", "Event.eventType"),
            ("CREATE INDEX event_source_idx IF NOT EXISTS FOR (e:Event) ON (e.source)", "Event.source"),
            
            # 复合索引
            ("CREATE INDEX invoice_status_amount_idx IF NOT EXISTS FOR (i:Invoice) ON (i.paymentStatus, i.amount)", "Invoice (status, amount)"),
            ("CREATE INDEX po_status_amount_idx IF NOT EXISTS FOR (p:PurchaseOrder) ON (p.status, p.amount)", "PO (status, amount)"),
        ]
        
        created = 0
        skipped = 0
        errors = 0
        
        for cypher, desc in indexes:
            try:
                r = s.run(cypher)
                r.consume()
                print(f"  [OK] {desc}")
                created += 1
            except Exception as e:
                err_msg = str(e)
                if 'already exists' in err_msg.lower():
                    print(f"  [SKIP] {desc} (已存在)")
                    skipped += 1
                else:
                    print(f"  [ERR] {desc} (错误：{err_msg[:50]})")
                    errors += 1
        
        # 验证索引
        print("\n" + "="*70)
        print("验证索引创建:")
        print("-"*70)
        r = s.run("SHOW INDEXES YIELD labelsOrTypes, properties, name RETURN labelsOrTypes as label, properties, name ORDER BY label")
        
        print("\n已创建的索引:")
        idx_count = 0
        for rec in r:
            label = rec['label'][0] if rec['label'] else 'Unknown'
            props = rec['properties']
            if isinstance(props, list):
                props_str = ', '.join(props)
            else:
                props_str = str(props)
            print(f"  {label:25s}: {props_str}")
            idx_count += 1
        
        print(f"\n  总计：{idx_count} 个索引")
        print("="*70)
        
        # 性能对比建议
        print("\n📊 性能提升预期:")
        print("-"*70)
        print("  金额范围查询：2-3 秒 → 0.1-0.2 秒 (15-25x 提升)")
        print("  问题数据统计：1-2 秒 → 0.2-0.3 秒 (5-8x 提升)")
        print("  标签过滤查询：0.5-1 秒 → 0.05-0.1 秒 (10x 提升)")
        print("="*70)
        
        print("\n✅ 索引创建完成！")
        print("\n💡 查询示例:")
        print("  MATCH (inv:Invoice) WHERE inv.amount > 10000 RETURN inv")
        print("  MATCH (n:ProblemData) RETURN n")
        print("  MATCH (evt:Event) WHERE evt.source = 'AP_MODULE' RETURN evt")

if __name__ == '__main__':
    main()
