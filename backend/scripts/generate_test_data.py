"""
Neo4j 测试数据生成器
每 5 分钟生成今日数据并同步到 Neo4j
"""
from neo4j import GraphDatabase
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# 今日日期
TODAY = datetime.now()
TODAY_STR = TODAY.strftime('%Y-%m-%d')
WEEK = TODAY.isocalendar()[1]
MONTH = TODAY.month
YEAR = TODAY.year

# 客户列表
CUSTOMERS = [
    "阿里巴巴", "腾讯科技", "华为技术", "字节跳动", "美团",
    "京东", "拼多多", "百度", "小米", "OPPO"
]

# 产品列表
PRODUCTS = [
    {"code": "P001", "name": "iPhone 15 Pro", "category": "electronics", "price": 7999},
    {"code": "P002", "name": "MacBook Pro 14", "category": "electronics", "price": 14999},
    {"code": "P003", "name": "AirPods Pro", "category": "electronics", "price": 1899},
    {"code": "P004", "name": "iPad Air", "category": "electronics", "price": 4799},
    {"code": "P005", "name": "Apple Watch", "category": "electronics", "price": 2999},
    {"code": "P006", "name": "智能沙发", "category": "home", "price": 5999},
    {"code": "P007", "name": "智能台灯", "category": "home", "price": 299},
    {"code": "P008", "name": "智能音箱", "category": "home", "price": 799},
]

# 星期映射
WEEKDAY_MAP = {
    0: '周一', 1: '周二', 2: '周三', 3: '周四',
    4: '周五', 5: '周六', 6: '周日'
}


def get_neo4j_driver():
    """获取 Neo4j 连接"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def generate_time_nodes(session):
    """生成今日时间节点"""
    print("\n[1/5] 生成时间维度节点...")
    
    # 获取今日是周几
    weekday = WEEKDAY_MAP[TODAY.weekday()]
    
    # 检查是否已存在
    result = session.run("""
    MATCH (t:Time {day: $day, week: $week, month: $month, year: $year})
    RETURN count(t) as count
    """, day=weekday, week=WEEK, month=MONTH, year=YEAR)
    
    count = result.single()["count"]
    if count > 0:
        print(f"  [SKIP] 时间节点已存在")
        return
    
    session.run("""
    CREATE (t:Time {
        day: $day,
        week: $week,
        month: $month,
        year: $year,
        quarter: ceil($month / 3.0),
        date: $date
    })
    """, day=weekday, week=WEEK, month=MONTH, year=YEAR, date=TODAY_STR)
    
    print(f"  [OK] 创建时间节点：{weekday}")


def generate_sales_data(session):
    """生成销售数据"""
    print("\n[2/5] 生成销售数据...")
    
    weekday = WEEKDAY_MAP[TODAY.weekday()]
    
    # 生成 12 条销售记录（每 2 小时一笔）
    for hour in range(8, 20, 2):
        amount = random.randint(5000, 15000)
        
        session.run("""
        MATCH (t:Time {day: $day, week: $week, month: $month, year: $year})
        CREATE (s:Sale {
            amount: $amount,
            hour: $hour,
            timestamp: datetime($date)
        })
        CREATE (s)-[:HAS_TIME]->(t)
        """, day=weekday, week=WEEK, month=MONTH, year=YEAR, amount=amount, hour=hour, date=f"{TODAY_STR}T{hour:02d}:00:00")
    
    print(f"  [OK] 创建 6 条销售记录")


def generate_customer_orders(session):
    """生成客户订单"""
    print("\n[3/5] 生成客户订单...")
    
    # 随机选 5 个客户生成订单
    selected_customers = random.sample(CUSTOMERS, 5)
    
    for customer in selected_customers:
        # 检查客户是否存在
        result = session.run("""
        MATCH (c:Customer {name: $name})
        RETURN c
        """, name=customer)
        
        if not result.single():
            # 创建客户
            session.run("""
            CREATE (c:Customer {
                name: $name,
                industry: '科技',
                region: '华东',
                level: '核心'
            })
            """, name=customer)
        
        # 创建订单
        amount = random.randint(500000, 1500000)
        session.run("""
        MATCH (c:Customer {name: $name})
        CREATE (o:Order {
            amount: $amount,
            date: $date,
            status: 'completed'
        })
        CREATE (c)-[:PURCHASED]->(o)
        """, name=customer, amount=amount, date=TODAY_STR)
    
    print(f"  [OK] 创建 5 个客户订单")


def generate_inventory_data(session):
    """生成库存数据"""
    print("\n[4/5] 生成库存数据...")
    
    for product in PRODUCTS:
        # 检查产品是否存在
        result = session.run("""
        MATCH (p:Product {code: $code})
        RETURN p
        """, code=product["code"])
        
        if result.single():
            # 更新库存
            stock = random.randint(3, 30)
            threshold = random.randint(10, 25)
            session.run("""
            MATCH (p:Product {code: $code})
            SET p.stock = $stock, p.threshold = $threshold
            """, code=product["code"], stock=stock, threshold=threshold)
        else:
            # 创建产品
            stock = random.randint(3, 30)
            threshold = random.randint(10, 25)
            session.run("""
            CREATE (p:Product {
                code: $code,
                name: $name,
                category: $category,
                price: $price,
                stock: $stock,
                threshold: $threshold
            })
            """, code=product["code"], name=product["name"], 
                category=product["category"], price=product["price"],
                stock=stock, threshold=threshold)
    
    print(f"  [OK] 创建/更新 8 个产品库存")


def generate_payment_data(session):
    """生成付款数据"""
    print("\n[5/5] 生成付款数据...")
    
    # 生成 5 条付款记录
    payment_methods = ['银行转账', '电汇', '支付宝', '微信支付']
    statuses = ['已完成', '已完成', '已完成', '处理中']
    
    for i in range(5):
        customer = random.choice(CUSTOMERS)
        amount = random.randint(200000, 600000)
        method = random.choice(payment_methods)
        status = random.choice(statuses)
        payment_id = f"PAY-{TODAY.strftime('%Y%m%d')}-{i+1:03d}"
        
        # 使用 MERGE 避免重复
        session.run("""
        MERGE (pay:Payment {id: $id})
        SET pay.customer = $customer,
            pay.amount = $amount,
            pay.date = $date,
            pay.method = $method,
            pay.status = $status
        """, id=payment_id, customer=customer, amount=amount, 
            date=TODAY_STR, method=method, status=status)
    
    print(f"  [OK] 创建/更新 5 条付款记录")


def generate_all_data():
    """生成所有测试数据"""
    print("=" * 60)
    print(f"Neo4j 测试数据生成器 - {TODAY_STR}")
    print("=" * 60)
    
    try:
        driver = get_neo4j_driver()
        print(f"[OK] 已连接 Neo4j: {NEO4J_URI}")
    except Exception as e:
        print(f"[错误] 连接失败：{e}")
        return
    
    try:
        with driver.session() as session:
            generate_time_nodes(session)
            generate_sales_data(session)
            generate_customer_orders(session)
            generate_inventory_data(session)
            generate_payment_data(session)
            
            # 统计结果
            result = session.run("MATCH (n) RETURN count(n) as total")
            total = result.single()["total"]
            
            print("\n" + "=" * 60)
            print(f"[SUCCESS] 数据生成完成！")
            print(f"总节点数：{total}")
            print(f"日期：{TODAY_STR}")
            print("=" * 60)
            
    except Exception as e:
        print(f"[错误] 生成失败：{e}")
    finally:
        driver.close()


if __name__ == "__main__":
    generate_all_data()
