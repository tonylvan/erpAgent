"""
生成 OTC/P2P/RTR 业务流程示例数据并导入 Neo4j
OTC = Order-to-Cash (订单到收款)
P2P = Procure-to-Pay (采购到付款)
RTR = Record-to-Report (记录到报告)
"""

from neo4j import GraphDatabase
from datetime import datetime, timedelta
import random

# Neo4j 连接配置
URI = "bolt://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "Tony1985"

# 今天日期
TODAY = datetime.now().strftime("%Y-%m-%d")

# 示例数据
CUSTOMERS = ["阿里巴巴", "腾讯科技", "华为技术", "小米科技", "京东集团", "拼多多", "网易公司", "字节跳动", "美团", "OPPO"]
SUPPLIERS = ["供应商 A", "供应商 B", "供应商 C", "供应商 D", "供应商 E", "供应商 F", "供应商 G", "供应商 H"]
PRODUCTS = [
    {"code": "P001", "name": "iPhone 15 Pro", "category": "electronics", "price": 8999},
    {"code": "P002", "name": "MacBook Pro 14", "category": "electronics", "price": 14999},
    {"code": "P003", "name": "AirPods Pro", "category": "electronics", "price": 1899},
    {"code": "P004", "name": "智能沙发", "category": "home", "price": 5999},
    {"code": "P005", "name": "智能台灯", "category": "home", "price": 299},
    {"code": "P006", "name": "办公椅", "category": "home", "price": 1299},
    {"code": "P007", "name": "显示器 27 寸", "category": "electronics", "price": 2499},
    {"code": "P008", "name": "键盘鼠标套装", "category": "electronics", "price": 599},
]

def create_sample_data():
    """创建 OTC/P2P/RTR 示例数据"""
    
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    with driver.session() as session:
        print("📊 开始生成 OTC/P2P/RTR 数据...")
        
        # 清除旧数据（可选）
        # session.run("MATCH (n) DETACH DELETE n")
        
        # 创建 10 条 OTC (Order-to-Cash) 流程数据
        print("\n🔄 创建 OTC (订单到收款) 流程数据...")
        for i in range(1, 6):  # 5 条 OTC 数据
            customer = CUSTOMERS[i-1]
            product = PRODUCTS[i % len(PRODUCTS)]
            order_amount = random.randint(10000, 100000)
            order_date = TODAY
            payment_date = TODAY
            payment_amount = order_amount * random.uniform(0.9, 1.0)
            
            # 创建 OTC 流程节点和关系
            session.run("""
            // 创建客户
            MERGE (c:Customer {name: $customer})
            
            // 创建订单
            CREATE (o:Order {
                id: 'OTC-ORDER-' + $i,
                amount: $order_amount,
                date: date($order_date),
                status: 'completed'
            })
            
            // 创建销售记录
            CREATE (s:Sale {
                id: 'OTC-SALE-' + $i,
                amount: $order_amount,
                date: date($order_date)
            })
            
            // 创建付款记录
            CREATE (p:Payment {
                id: 'OTC-PAY-' + $i,
                customer: $customer,
                amount: $payment_amount,
                date: date($payment_date),
                status: 'completed',
                method: 'bank_transfer'
            })
            
            // 创建关系
            CREATE (c)-[:PLACED]->(o)
            CREATE (o)-[:GENERATES]->(s)
            CREATE (s)-[:MADE_TO]->(c)
            CREATE (c)-[:MADE_PAYMENT]->(p)
            """, {
                "customer": customer,
                "i": str(i),
                "order_amount": order_amount,
                "order_date": order_date,
                "payment_amount": payment_amount,
                "payment_date": payment_date
            })
            
            print(f"  ✅ OTC-{i}: {customer} - 订单¥{order_amount:,} - 付款¥{payment_amount:,.0f}")
        
        # 创建 5 条 P2P (Procure-to-Pay) 流程数据
        print("\n📋 创建 P2P (采购到付款) 流程数据...")
        for i in range(1, 6):
            supplier = SUPPLIERS[i-1]
            product = PRODUCTS[i % len(PRODUCTS)]
            po_amount = random.randint(50000, 200000)
            po_date = TODAY
            payment_date = TODAY
            
            # 创建 P2P 流程节点和关系
            session.run("""
            // 创建供应商
            MERGE (s:Supplier {name: $supplier})
            
            // 创建采购单
            CREATE (po:PurchaseOrder {
                id: 'P2P-PO-' + $i,
                amount: $po_amount,
                date: date($po_date),
                status: 'completed',
                supplier: $supplier
            })
            
            // 创建付款记录
            CREATE (p:Payment {
                id: 'P2P-PAY-' + $i,
                supplier: $supplier,
                amount: $po_amount,
                date: date($payment_date),
                status: 'completed',
                method: 'bank_transfer'
            })
            
            // 创建关系
            CREATE (s)-[:SUPPLIES]->(po)
            CREATE (s)-[:RECEIVED_PAYMENT]->(p)
            """, {
                "supplier": supplier,
                "i": str(i),
                "po_amount": po_amount,
                "po_date": po_date,
                "payment_date": payment_date
            })
            
            print(f"  ✅ P2P-{i}: {supplier} - 采购¥{po_amount:,}")
        
        # 创建 RTR (Record-to-Report) 相关数据
        print("\n📈 创建 RTR (记录到报告) 流程数据...")
        for i in range(1, 6):
            # 创建总账条目
            session.run("""
            CREATE (gl:GeneralLedger {
                id: 'RTR-GL-' + $i,
                account: $account,
                amount: $amount,
                date: date($date),
                type: $type,
                status: 'posted'
            })
            """, {
                "i": str(i),
                "account": f"科目 {6000 + i}",
                "amount": random.randint(10000, 500000),
                "date": TODAY,
                "type": random.choice(["收入", "成本", "费用", "资产"])
            })
            
            print(f"  ✅ RTR-{i}: 总账条目 - 科目{6000+i}")
        
        # 统计结果
        result = session.run("""
        MATCH (n) 
        RETURN 
            count(DISTINCT n) as total_nodes,
            count(DISTINCT CASE WHEN 'Customer' IN labels(n) THEN n END) as customers,
            count(DISTINCT CASE WHEN 'Supplier' IN labels(n) THEN n END) as suppliers,
            count(DISTINCT CASE WHEN 'Order' IN labels(n) THEN n END) as orders,
            count(DISTINCT CASE WHEN 'PurchaseOrder' IN labels(n) THEN n END) as purchase_orders,
            count(DISTINCT CASE WHEN 'Sale' IN labels(n) THEN n END) as sales,
            count(DISTINCT CASE WHEN 'Payment' IN labels(n) THEN n END) as payments,
            count(DISTINCT CASE WHEN 'GeneralLedger' IN labels(n) THEN n END) as gl_entries
        """)
        
        record = result.single()
        
        print("\n" + "="*60)
        print("📊 数据生成完成！")
        print("="*60)
        print(f"总节点数：{record['total_nodes']}")
        print(f"  • 客户：{record['customers']}")
        print(f"  • 供应商：{record['suppliers']}")
        print(f"  • 订单：{record['orders']}")
        print(f"  • 采购单：{record['purchase_orders']}")
        print(f"  • 销售：{record['sales']}")
        print(f"  • 付款：{record['payments']}")
        print(f"  • 总账：{record['gl_entries']}")
        print("="*60)
        
        # 查询关系统计
        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = rel_result.single()["count"]
        print(f"总关系数：{rel_count}")
        print("="*60)
    
    driver.close()
    print("\n✅ Neo4j 连接已关闭")


if __name__ == "__main__":
    create_sample_data()
