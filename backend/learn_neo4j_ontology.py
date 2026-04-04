"""
Neo4j 本体学习脚本
"""
from neo4j import GraphDatabase
import os

# 连接配置
uri = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'Tony1985')

print('=' * 60)
print('Neo4j 本体学习')
print('=' * 60)
print(f'连接：{uri}')
print(f'用户：{user}')
print()

driver = GraphDatabase.driver(uri, auth=(user, password))

# 1. 查询所有节点标签
print('[1] 节点标签 (Labels)')
print('-' * 60)
with driver.session() as session:
    result = session.run('CALL db.labels()')
    labels = [r['label'] for r in result]
    for i, label in enumerate(labels, 1):
        print(f'  {i:2d}. {label}')
    print(f'\n总计：{len(labels)} 个标签')

# 2. 查询所有关系类型
print('\n[2] 关系类型 (Relationship Types)')
print('-' * 60)
with driver.session() as session:
    result = session.run('CALL db.relationshipTypes()')
    rels = [r['relationshipType'] for r in result]
    for i, rel in enumerate(rels, 1):
        print(f'  {i:2d}. {rel}')
    print(f'\n总计：{len(rels)} 个关系类型')

# 3. 查询节点统计
print('\n[3] 节点统计')
print('-' * 60)
with driver.session() as session:
    result = session.run('MATCH (n) RETURN count(n) as total')
    total = result.single()['total']
    print(f'  总节点数：{total}')

# 4. 查询各标签节点数量
print('\n[4] 各标签节点数量 (Top 20)')
print('-' * 60)
with driver.session() as session:
    result = session.run('''
        MATCH (n)
        UNWIND labels(n) as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        LIMIT 20
    ''')
    for r in result:
        print(f'  {str(r["label"]):30s}: {r["count"]:5d} 个')

# 5. 查询关系统计
print('\n[5] 关系统计')
print('-' * 60)
with driver.session() as session:
    result = session.run('MATCH ()-[r]->() RETURN count(r) as total')
    total = result.single()['total']
    print(f'  总关系数：{total}')

# 6. 查询各关系类型数量
print('\n[6] 各关系类型数量')
print('-' * 60)
with driver.session() as session:
    result = session.run('''
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
        LIMIT 20
    ''')
    for r in result:
        print(f'  {str(r["type"]):30s}: {r["count"]:5d} 个')

# 7. 查询示例节点属性
print('\n[7] 示例节点属性')
print('-' * 60)
with driver.session() as session:
    for label in ['Sale', 'Customer', 'Product', 'Payment', 'Order', 'Time']:
        try:
            result = session.run(f'MATCH (n:{label}) RETURN properties(n) as props LIMIT 1')
            record = result.single()
            if record:
                props = record['props']
                print(f'  {label}: {list(props.keys())}')
        except Exception as e:
            print(f'  {label}: 未找到')

driver.close()
print('\n' + '=' * 60)
print('学习完成！')
print('=' * 60)
