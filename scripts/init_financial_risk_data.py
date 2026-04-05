"""
Neo4j 财务风险预警测试数据初始化脚本

用途:
1. 创建财务风险相关的节点和关系
2. 提供测试数据用于验证预警规则
3. 支持财务健康度评分计算

运行方式:
python scripts/init_financial_risk_data.py
"""

import os
import sys
from datetime import date, timedelta

from neo4j import GraphDatabase

# 配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'your_password')


def create_company_and_cashflow(tx):
    """创建公司和现金流数据"""
    
    # 创建公司节点
    query = """
    MERGE (c:Company {
        id: 'COMP-001',
        company_name: '某某科技有限公司',
        status: 'ACTIVE'
    })
    
    // 创建现金流节点
    MERGE (cf:CashFlow {
        id: 'CF-001',
        company_id: 'COMP-001',
        balance: 500000,
        minimum_threshold: 1000000,
        updated_at: datetime()
    })
    
    // 创建关系
    MERGE (c)-[:HAS_CASHFLOW]->(cf)
    
    RETURN c, cf
    """
    
    result = tx.run(query)
    record = result.single()
    print(f"✅ 创建公司和现金流：{record['c']['company_name']}, 现金流：¥{record['cf']['balance']:,.0f}")


def create_financial_ratios(tx):
    """创建财务比率数据"""
    
    query = """
    MATCH (c:Company {id: 'COMP-001'})
    
    // 创建财务比率节点
    MERGE (fr:FinancialRatio {
        id: 'FR-001',
        company_id: 'COMP-001',
        current_ratio: 0.8,
        quick_ratio: 0.6,
        debt_to_equity: 2.5,
        roe: 0.03,
        roi: 0.05,
        gross_margin: 0.12,
        net_margin: 0.08,
        updated_at: datetime()
    })
    
    // 创建关系
    MERGE (c)-[:HAS_FINANCIAL_RATIO]->(fr)
    
    RETURN fr
    """
    
    result = tx.run(query)
    record = result.single()
    fr = record['fr']
    print(f"✅ 创建财务比率:")
    print(f"   - 流动比率：{fr['current_ratio']} (标准：>1.0)")
    print(f"   - 速动比率：{fr['quick_ratio']} (标准：>0.8)")
    print(f"   - 负债权益比：{fr['debt_to_equity']} (标准：<2.0)")
    print(f"   - ROE: {fr['roe']*100:.1f}% (标准：>5%)")
    print(f"   - 毛利率：{fr['gross_margin']*100:.1f}% (标准：>15%)")


def create_budget_and_actual(tx):
    """创建预算和实际支出数据"""
    
    query = """
    // 创建部门
    MERGE (d:Department {
        id: 'DEPT-001',
        department_name: '市场部',
        status: 'ACTIVE'
    })
    
    // 创建预算节点
    MERGE (b:Budget {
        id: 'BUD-001',
        department_id: 'DEPT-001',
        amount: 1000000,
        period: '2026-Q1',
        created_at: datetime()
    })
    
    // 创建实际支出节点
    MERGE (a:Actual {
        id: 'ACT-001',
        department_id: 'DEPT-001',
        amount: 1300000,
        period: '2026-Q1',
        created_at: datetime()
    })
    
    // 创建关系
    MERGE (d)-[:HAS_BUDGET]->(b)
    MERGE (d)-[:HAS_ACTUAL]->(a)
    
    RETURN d, b, a
    """
    
    result = tx.run(query)
    record = result.single()
    variance = (record['b']['amount'] - record['a']['amount']) / record['b']['amount'] * 100
    print(f"✅ 创建部门预算:")
    print(f"   - 部门：{record['d']['department_name']}")
    print(f"   - 预算：¥{record['b']['amount']:,.0f}")
    print(f"   - 实际：¥{record['a']['amount']:,.0f}")
    print(f"   - 偏差：{variance:.1f}%")


def create_ar_transactions(tx):
    """创建应收账款交易数据"""
    
    query = """
    // 创建客户
    MERGE (c:Customer {
        id: 'CUST-001',
        customer_name: '某某贸易公司',
        status: 'ACTIVE',
        credit_limit: 500000
    })
    
    // 创建逾期应收账款
    MERGE (ar1:ARTransaction {
        id: 'AR-001',
        customer_id: 'CUST-001',
        amount: 50000,
        due_date: date() - duration({days: 60}),
        status: 'UNPAID',
        invoice_number: 'INV-2026-001'
    })
    
    MERGE (ar2:ARTransaction {
        id: 'AR-002',
        customer_id: 'CUST-001',
        amount: 40000,
        due_date: date() - duration({days: 45}),
        status: 'UNPAID',
        invoice_number: 'INV-2026-002'
    })
    
    MERGE (ar3:ARTransaction {
        id: 'AR-003',
        customer_id: 'CUST-001',
        amount: 30000,
        due_date: date() - duration({days: 30}),
        status: 'UNPAID',
        invoice_number: 'INV-2026-003'
    })
    
    MERGE (ar4:ARTransaction {
        id: 'AR-004',
        customer_id: 'CUST-001',
        amount: 20000,
        due_date: date() - duration({days: 15}),
        status: 'UNPAID',
        invoice_number: 'INV-2026-004'
    })
    
    MERGE (ar5:ARTransaction {
        id: 'AR-005',
        customer_id: 'CUST-001',
        amount: 10000,
        due_date: date() - duration({days: 7}),
        status: 'UNPAID',
        invoice_number: 'INV-2026-005'
    })
    
    MERGE (ar6:ARTransaction {
        id: 'AR-006',
        customer_id: 'CUST-001',
        amount: 5000,
        due_date: date() - duration({days: 3}),
        status: 'UNPAID',
        invoice_number: 'INV-2026-006'
    })
    
    // 创建关系
    MERGE (c)-[:OWES]->(ar1)
    MERGE (c)-[:OWES]->(ar2)
    MERGE (c)-[:OWES]->(ar3)
    MERGE (c)-[:OWES]->(ar4)
    MERGE (c)-[:OWES]->(ar5)
    MERGE (c)-[:OWES]->(ar6)
    
    RETURN c, count(ar1) as ar_count
    """
    
    result = tx.run(query)
    record = result.single()
    print(f"✅ 创建客户应收账款：{record['c']['customer_name']}, 6 笔逾期")


def create_ap_transactions(tx):
    """创建应付账款交易数据"""
    
    query = """
    // 创建供应商
    MERGE (s:Supplier {
        id: 'SUP-001',
        vendor_name: '某某供应商',
        status: 'ACTIVE',
        payment_terms: 'NET30'
    })
    
    // 创建 7 天内到期的应付账款
    MERGE (ap1:APTransaction {
        id: 'AP-001',
        supplier_id: 'SUP-001',
        amount: 50000,
        due_date: date() + duration({days: 2}),
        status: 'UNPAID',
        invoice_number: 'AP-2026-001'
    })
    
    MERGE (ap2:APTransaction {
        id: 'AP-002',
        supplier_id: 'SUP-001',
        amount: 40000,
        due_date: date() + duration({days: 5}),
        status: 'UNPAID',
        invoice_number: 'AP-2026-002'
    })
    
    MERGE (ap3:APTransaction {
        id: 'AP-003',
        supplier_id: 'SUP-001',
        amount: 30000,
        due_date: date() + duration({days: 7}),
        status: 'UNPAID',
        invoice_number: 'AP-2026-003'
    })
    
    // 创建关系
    MERGE (s)<-[:OWED_BY]-(ap1)
    MERGE (s)<-[:OWED_BY]-(ap2)
    MERGE (s)<-[:OWED_BY]-(ap3)
    
    RETURN s, count(ap1) as ap_count
    """
    
    result = tx.run(query)
    record = result.single()
    print(f"✅ 创建供应商应付账款：{record['s']['vendor_name']}, 3 笔 7 天内到期")


def verify_data(tx):
    """验证创建的数据"""
    
    queries = {
        '公司': "MATCH (c:Company) RETURN count(c) as count",
        '现金流': "MATCH (cf:CashFlow) RETURN count(cf) as count",
        '财务比率': "MATCH (fr:FinancialRatio) RETURN count(fr) as count",
        '部门': "MATCH (d:Department) RETURN count(d) as count",
        '预算': "MATCH (b:Budget) RETURN count(b) as count",
        '实际支出': "MATCH (a:Actual) RETURN count(a) as count",
        '客户': "MATCH (c:Customer) RETURN count(c) as count",
        '应收账款': "MATCH (ar:ARTransaction) RETURN count(ar) as count",
        '供应商': "MATCH (s:Supplier) RETURN count(s) as count",
        '应付账款': "MATCH (ap:APTransaction) RETURN count(ap) as count",
    }
    
    print("\n📊 数据验证:")
    for name, query in queries.items():
        result = tx.run(query)
        record = result.single()
        count = record['count'] if record else 0
        print(f"   - {name}: {count}")


def main():
    """主函数"""
    print("🚀 Neo4j 财务风险预警测试数据初始化")
    print("=" * 60)
    
    # 创建驱动
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # 执行创建
            print("\n📝 创建测试数据...")
            session.execute_write(create_company_and_cashflow)
            session.execute_write(create_financial_ratios)
            session.execute_write(create_budget_and_actual)
            session.execute_write(create_ar_transactions)
            session.execute_write(create_ap_transactions)
            
            # 验证数据
            session.execute_read(verify_data)
        
        print("\n✅ 财务风险测试数据初始化完成!")
        print("\n💡 提示:")
        print("   - 运行预警规则测试：pytest tests/test_alert_rules.py -v")
        print("   - 测试财务风险 API: curl http://localhost:8005/api/v1/alerts/financial")
        print("   - 查看预警看板：http://localhost:5177 (AlertCenter 组件)")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        print("\n请检查:")
        print("   1. Neo4j 是否运行")
        print("   2. 数据库连接配置是否正确")
        print("   3. 是否有足够的权限创建节点")
        sys.exit(1)
    finally:
        driver.close()


if __name__ == '__main__':
    main()
