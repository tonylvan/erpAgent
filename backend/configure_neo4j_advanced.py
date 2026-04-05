# -*- coding: utf-8 -*-
"""
Neo4j 高级配置脚本
- 内存参数配置
- 慢查询日志启用
- 索引维护计划
"""

from neo4j import GraphDatabase
import os
import json
from datetime import datetime

uri = 'bolt://localhost:7687'
auth = ('neo4j', 'Tony1985')

print('='*70)
print('Neo4j 高级配置')
print('='*70)

driver = GraphDatabase.driver(uri, auth=auth)

with driver.session() as session:
    
    # 1. 检查当前配置
    print('\n[1/4] 检查当前配置...')
    
    try:
        # 获取数据库信息
        db_info = session.run("CALL dbms.components()").single()
        print(f'  Neo4j 版本：{db_info[0]}')
        print(f'  版本详情：{db_info[1]}')
    except Exception as e:
        print(f'  [WARN] 无法获取版本信息：{str(e)[:50]}')
    
    # 2. 尝试配置内存参数
    print('\n[2/4] 配置内存参数...')
    
    memory_configs = [
        ("dbms.memory.heap.initial_size", "512M", "堆内存初始大小"),
        ("dbms.memory.heap.max_size", "2G", "堆内存最大值"),
        ("dbms.memory.pagecache.size", "1G", "页面缓存大小"),
    ]
    
    config_success = 0
    for key, value, desc in memory_configs:
        try:
            session.run(f"CALL dbms.setConfigValue('{key}', '{value}')")
            print(f'  [OK] {desc}: {value}')
            config_success += 1
        except Exception as e:
            error_msg = str(e)
            if 'permissions' in error_msg.lower() or 'privilege' in error_msg.lower():
                print(f'  [WARN] {desc}: 需要管理员权限')
            else:
                print(f'  [WARN] {desc}: {error_msg[:40]}')
    
    if config_success == 0:
        print('\n  [INFO] 需要 Neo4j 管理员权限才能修改配置')
        print('  手动配置方法:')
        print('  1. 编辑 neo4j/conf/neo4j.conf')
        print('  2. 添加以下配置:')
        for key, value, desc in memory_configs:
            print(f'     {key}={value}')
        print('  3. 重启 Neo4j 服务')
    
    # 3. 启用慢查询日志
    print('\n[3/4] 配置慢查询日志...')
    
    query_logging_configs = [
        ("dbms.logs.query.enabled", "true", "查询日志启用"),
        ("dbms.logs.query.threshold", "1000", "慢查询阈值 (ms)"),
        ("dbms.logs.query.max_characters", "10000", "最大字符数"),
    ]
    
    log_success = 0
    for key, value, desc in query_logging_configs:
        try:
            session.run(f"CALL dbms.setConfigValue('{key}', '{value}')")
            print(f'  [OK] {desc}: {value}')
            log_success += 1
        except Exception as e:
            print(f'  [WARN] {desc}: 需要配置文件修改')
    
    if log_success == 0:
        print('\n  [INFO] 需要在 neo4j.conf 中手动配置查询日志')
    
    # 4. 创建索引维护脚本
    print('\n[4/4] 创建索引维护计划...')
    
    # 检查所有索引状态
    indexes = session.run("SHOW INDEXES")
    index_list = []
    for idx in indexes:
        index_list.append({
            'name': idx[1],
            'type': idx[0],
            'state': idx[3] if len(idx) > 3 else 'ONLINE'
        })
    
    print(f'  当前索引数：{len(index_list)}')
    
    # 生成索引健康检查报告
    online_count = sum(1 for idx in index_list if idx['state'] == 'ONLINE')
    print(f'  在线索引：{online_count}/{len(index_list)}')
    
    # 创建维护脚本
    maintenance_script = '''# Neo4j 索引维护脚本
# 建议每月执行一次

from neo4j import GraphDatabase

uri = 'bolt://localhost:7687'
auth = ('neo4j', 'Tony1985')

driver = GraphDatabase.driver(uri, auth=auth)

with driver.session() as session:
    # 1. 更新统计信息
    print("更新统计信息...")
    session.run("CALL db.stats.update()")
    
    # 2. 检查索引健康状态
    print("检查索引状态...")
    indexes = session.run("SHOW INDEXES")
    for idx in indexes:
        print(f"  {idx[1]}: {idx[3] if len(idx) > 3 else 'ONLINE'}")
    
    # 3. 清理废弃索引
    print("清理废弃索引...")
    # 注意：生产环境谨慎使用
    # session.run("DROP INDEX index_name")
    
    # 4. 性能测试
    print("性能测试...")
    import time
    
    test_queries = [
        "MATCH (n) RETURN count(n)",
        "MATCH ()-[r]->() RETURN count(r)",
        "MATCH (i:Invoice) WHERE i.payment_status = 'PENDING' RETURN i LIMIT 100"
    ]
    
    for query in test_queries:
        start = time.time()
        result = session.run(query)
        _ = list(result)
        elapsed = (time.time() - start) * 1000
        print(f"  {query[:50]}: {elapsed:.1f}ms")

driver.close()
print("维护完成！")
'''
    
    # 保存维护脚本
    script_path = 'neo4j_monthly_maintenance.py'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(maintenance_script)
    
    print(f'  [OK] 维护脚本已保存：{script_path}')
    
    # 5. 创建配置报告
    print('\n[5/5] 生成配置报告...')
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'neo4j_uri': uri,
        'indexes': {
            'total': len(index_list),
            'online': online_count,
            'details': index_list
        },
        'memory_config': {
            'attempted': config_success > 0,
            'success_count': config_success
        },
        'query_logging': {
            'attempted': log_success > 0,
            'success_count': log_success
        }
    }
    
    report_path = 'neo4j_config_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f'  [OK] 配置报告已保存：{report_path}')

print('\n' + '='*70)
print('Neo4j 高级配置完成！')
print('='*70)

driver.close()

# 打印后续步骤
print('\n[INFO] 后续步骤:')
print('1. 重启 Neo4j 服务使内存配置生效')
print('2. 查看日志文件：neo4j/logs/query.log')
print('3. 每月执行一次维护脚本：python neo4j_monthly_maintenance.py')
print('\n[FILES] 生成的文件:')
print('  - neo4j_monthly_maintenance.py (月度维护脚本)')
print('  - neo4j_config_report.json (配置报告)')
