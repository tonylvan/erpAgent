#!/usr/bin/env python
"""Neo4j 知识图谱架构导出脚本"""
from neo4j import GraphDatabase
import json

uri = 'bolt://127.0.0.1:7687'
auth = ('neo4j', 'Tony1985')
driver = GraphDatabase.driver(uri, auth=auth)
session = driver.session()

print('=' * 80)
print('ERP 知识图谱架构文档')
print('=' * 80)

# 核心业务模块
modules = {
    'PTP (采购到付款)': {
        'nodes': ['Supplier', 'PurchaseOrder', 'POLine', 'Invoice', 'Payment'],
        'description': '供应商 → 采购订单 → 发票 → 付款全流程'
    },
    'OTC (订单到收款)': {
        'nodes': ['Customer', 'Order', 'Sale', 'Product'],
        'description': '客户 → 订单 → 销售 → 产品全流程'
    },
    '财务核算': {
        'nodes': ['GLAccount', 'GLJournal', 'GLBalance', 'AccountingEntry'],
        'description': '总账科目 → 日记账 → 余额 → 会计分录'
    },
    '时间维度': {
        'nodes': ['Time'],
        'description': '时间维度表，支持按年/月/日分析'
    }
}

for module_name, module_info in modules.items():
    print(f'\n{"="*80}')
    print(f'模块：{module_name}')
    print(f'说明：{module_info["description"]}')
    print(f'{"="*80}')
    
    for label in module_info['nodes']:
        try:
            # 查询节点属性和示例
            result = session.run(f'''
                MATCH (n:{label})
                WITH n, keys(n) as propertyKeys
                RETURN propertyKeys, count(n) as count
                LIMIT 1
            ''')
            record = result.single()
            if record:
                props = record['propertyKeys']
                count = record['count']
                
                # 查询示例数据
                sample = session.run(f'MATCH (n:{label}) RETURN n LIMIT 1')
                sample_record = sample.single()
                
                print(f'\n【{label}】节点 (共{count}个)')
                print(f'属性：{", ".join(props) if props else "无属性"}')
                
                if sample_record:
                    node = sample_record['n']
                    print('示例数据:')
                    for key in list(node.keys())[:5]:  # 只显示前 5 个属性
                        print(f'  - {key}: {node[key]}')
        except Exception as e:
            print(f'\n【{label}】节点 - 查询失败：{e}')

# 关系模式
print(f'\n\n{"="*80}')
print('关系模式 (Relationship Patterns)')
print(f'{"="*80}')

result = session.run('''
    MATCH (a)-[r]->(b)
    WITH labels(a)[0] as from, type(r) as rel, labels(b)[0] as to, count(r) as count
    RETURN from, rel, to, count
    ORDER BY count DESC
    LIMIT 30
''')

print('\n关系模式 | 数量')
print('-' * 80)
for record in result:
    print(f"{record['from']}-[:{record['rel']}]->{record['to']} | {record['count']} 条")

session.close()

print(f'\n\n{"="*80}')
print('架构导出完成！')
print(f'{"="*80}')
