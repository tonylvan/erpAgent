"""
Neo4j 知识图谱初始化脚本
创建 GSD 智能问数所需的节点和关系
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# 检查配置
if not NEO4J_PASSWORD:
    print("[错误] Neo4j 密码未配置！")
    print("请在 D:\\erpAgent\\backend\\.env 文件中配置：")
    print("NEO4J_PASSWORD=你的密码")
    exit(1)


def init_neo4j():
    """初始化 Neo4j 知识图谱"""
    print("=" * 60)
    print("Neo4j 知识图谱初始化")
    print("=" * 60)
    
    try:
        # 连接 Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print(f"[OK] 已连接 Neo4j: {NEO4J_URI}")
    except Exception as e:
        print(f"[错误] 连接失败：{e}")
        return
    
    try:
        with driver.session() as session:
            # 1. 清理旧数据（可选）
            print("\n[1/6] 清理旧数据...")
            session.run("MATCH (n) DETACH DELETE n")
            print("[OK] 清理完成")
            
            # 2. 创建时间维度节点
            print("\n[2/6] 创建时间维度节点...")
            time_query = """
            CREATE (t1:Time {day: '周一', week: 14, month: 4, year: 2026, quarter: 2})
            CREATE (t2:Time {day: '周二', week: 14, month: 4, year: 2026, quarter: 2})
            CREATE (t3:Time {day: '周三', week: 14, month: 4, year: 2026, quarter: 2})
            CREATE (t4:Time {day: '周四', week: 14, month: 4, year: 2026, quarter: 2})
            CREATE (t5:Time {day: '周五', week: 14, month: 4, year: 2026, quarter: 2})
            CREATE (t6:Time {day: '周六', week: 14, month: 4, year: 2026, quarter: 2})
            CREATE (t7:Time {day: '周日', week: 14, month: 4, year: 2026, quarter: 2})
            """
            session.run(time_query)
            print("[OK] 创建 7 个时间节点")
            
            # 3. 创建客户节点
            print("\n[3/6] 创建客户节点...")
            customer_query = """
            CREATE (c1:Customer {name: '阿里巴巴', industry: '科技', region: '华东', level: '战略'})
            CREATE (c2:Customer {name: '腾讯科技', industry: '科技', region: '华南', level: '战略'})
            CREATE (c3:Customer {name: '华为技术', industry: '科技', region: '华南', level: '核心'})
            CREATE (c4:Customer {name: '字节跳动', industry: '科技', region: '华北', level: '核心'})
            CREATE (c5:Customer {name: '美团', industry: '互联网', region: '华北', level: '成长'})
            CREATE (c6:Customer {name: '京东', industry: '电商', region: '华北', level: '战略'})
            CREATE (c7:Customer {name: '拼多多', industry: '电商', region: '华东', level: '核心'})
            CREATE (c8:Customer {name: '百度', industry: '科技', region: '华北', level: '核心'})
            CREATE (c9:Customer {name: '小米', industry: '科技', region: '华北', level: '成长'})
            CREATE (c10:Customer {name: 'OPPO', industry: '科技', region: '华南', level: '成长'})
            """
            session.run(customer_query)
            print("[OK] 创建 10 个客户节点")
            
            # 4. 创建销售数据
            print("\n[4/6] 创建销售数据...")
            sale_query = """
            MATCH (t1:Time {day: '周一'})
            MATCH (t2:Time {day: '周二'})
            MATCH (t3:Time {day: '周三'})
            MATCH (t4:Time {day: '周四'})
            MATCH (t5:Time {day: '周五'})
            MATCH (t6:Time {day: '周六'})
            MATCH (t7:Time {day: '周日'})
            
            CREATE (s1:Sale {amount: 8200, date: '2026-04-01'})-[:HAS_TIME]->(t1)
            CREATE (s2:Sale {amount: 9320, date: '2026-04-02'})-[:HAS_TIME]->(t2)
            CREATE (s3:Sale {amount: 9010, date: '2026-04-03'})-[:HAS_TIME]->(t3)
            CREATE (s4:Sale {amount: 9340, date: '2026-04-04'})-[:HAS_TIME]->(t4)
            CREATE (s5:Sale {amount: 12900, date: '2026-04-05'})-[:HAS_TIME]->(t5)
            CREATE (s6:Sale {amount: 13300, date: '2026-04-06'})-[:HAS_TIME]->(t6)
            CREATE (s7:Sale {amount: 13200, date: '2026-04-07'})-[:HAS_TIME]->(t7)
            """
            session.run(sale_query)
            print("[OK] 创建 7 条销售记录")
            
            # 5. 创建订单和客户关系
            print("\n[5/6] 创建订单数据...")
            order_query = """
            MATCH (c1:Customer {name: '阿里巴巴'})
            MATCH (c2:Customer {name: '腾讯科技'})
            MATCH (c3:Customer {name: '华为技术'})
            MATCH (c4:Customer {name: '字节跳动'})
            MATCH (c5:Customer {name: '美团'})
            
            CREATE (o1:Order {amount: 1234567, date: '2026-04-01', status: 'completed'})
            CREATE (o2:Order {amount: 987654, date: '2026-04-02', status: 'completed'})
            CREATE (o3:Order {amount: 876543, date: '2026-04-03', status: 'completed'})
            CREATE (o4:Order {amount: 765432, date: '2026-04-04', status: 'processing'})
            CREATE (o5:Order {amount: 654321, date: '2026-04-05', status: 'processing'})
            
            CREATE (c1)-[:PURCHASED]->(o1)
            CREATE (c2)-[:PURCHASED]->(o2)
            CREATE (c3)-[:PURCHASED]->(o3)
            CREATE (c4)-[:PURCHASED]->(o4)
            CREATE (c5)-[:PURCHASED]->(o5)
            """
            session.run(order_query)
            print("[OK] 创建 5 条订单记录")
            
            # 6. 创建产品库存数据
            print("\n[6/6] 创建产品库存数据...")
            product_query = """
            CREATE (p1:Product {code: 'P001', name: 'iPhone 15 Pro', stock: 5, threshold: 10, category: 'electronics', price: 7999})
            CREATE (p2:Product {code: 'P002', name: 'MacBook Pro 14', stock: 8, threshold: 10, category: 'electronics', price: 14999})
            CREATE (p3:Product {code: 'P003', name: 'AirPods Pro', stock: 12, threshold: 15, category: 'electronics', price: 1899})
            CREATE (p4:Product {code: 'P004', name: 'iPad Air', stock: 18, threshold: 20, category: 'electronics', price: 4799})
            CREATE (p5:Product {code: 'P005', name: 'Apple Watch', stock: 22, threshold: 25, category: 'electronics', price: 2999})
            CREATE (p6:Product {code: 'P006', name: '智能沙发', stock: 3, threshold: 8, category: 'home', price: 5999})
            CREATE (p7:Product {code: 'P007', name: '智能台灯', stock: 15, threshold: 20, category: 'home', price: 299})
            CREATE (p8:Product {code: 'P008', name: '智能音箱', stock: 30, threshold: 25, category: 'home', price: 799})
            """
            session.run(product_query)
            print("[OK] 创建 8 个产品节点")
            
            # 7. 创建付款数据
            print("\n[7/7] 创建付款数据...")
            payment_query = """
            CREATE (pay1:Payment {id: 'PAY-001', customer: '阿里巴巴', amount: 580000, date: '2026-04-01', method: '银行转账', status: '已完成'})
            CREATE (pay2:Payment {id: 'PAY-002', customer: '腾讯科技', amount: 450000, date: '2026-04-02', method: '电汇', status: '已完成'})
            CREATE (pay3:Payment {id: 'PAY-003', customer: '华为技术', amount: 380000, date: '2026-04-01', method: '银行转账', status: '已完成'})
            CREATE (pay4:Payment {id: 'PAY-004', customer: '字节跳动', amount: 320000, date: '2026-04-03', method: '支付宝', status: '处理中'})
            CREATE (pay5:Payment {id: 'PAY-005', customer: '美团', amount: 280000, date: '2026-04-03', method: '银行转账', status: '处理中'})
            """
            session.run(payment_query)
            print("[OK] 创建 5 条付款记录")
            
            # 统计结果
            print("\n" + "=" * 60)
            print("初始化完成！统计信息：")
            print("=" * 60)
            
            result = session.run("MATCH (n) RETURN count(n) as total")
            total = result.single()["total"]
            print(f"总节点数：{total}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            total_rel = result.single()["total"]
            print(f"总关系数：{total_rel}")
            
            print("\n[OK] Neo4j 知识图谱初始化完成！")
            print("=" * 60)
            
    except Exception as e:
        print(f"[错误] 初始化失败：{e}")
    finally:
        driver.close()


if __name__ == "__main__":
    init_neo4j()
