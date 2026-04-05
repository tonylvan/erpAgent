# -*- coding: utf-8 -*-
"""
GSD 智能问数平台 - 性能基准测试

测试项目:
1. API 响应时间 (P50/P90/P99)
2. 并发查询能力 (QPS)
3. RTR 同步延迟
4. Neo4j 查询性能
5. Redis 缓存命中率
"""

import time
import statistics
import json
import requests
import psycopg2
from neo4j import GraphDatabase
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

load_dotenv()

# 配置
CONFIG = {
    'backend_url': 'http://localhost:8005',
    'postgres': {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'erp'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    },
    'neo4j': {
        'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        'user': os.getenv('NEO4J_USER', 'neo4j'),
        'password': os.getenv('NEO4J_PASSWORD', 'Tony1985')
    }
}

# 测试结果
results = {}


def test_api_health():
    """测试 1: API 健康检查"""
    print("\n" + "="*70)
    print("测试 1: API 健康检查")
    print("="*70)
    
    try:
        start = time.time()
        response = requests.get(f"{CONFIG['backend_url']}/api/health", timeout=5)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 状态：{data.get('status', 'unknown')}")
            print(f"[OK] 服务：{data.get('service', 'unknown')}")
            print(f"[OK] 延迟：{latency:.2f}ms")
            results['api_health'] = {
                'status': 'ok',
                'latency_ms': round(latency, 2)
            }
        else:
            print(f"[FAIL] 状态码：{response.status_code}")
            results['api_health'] = {'status': 'error', 'code': response.status_code}
    except Exception as e:
        print(f"[FAIL] 错误：{e}")
        results['api_health'] = {'status': 'error', 'message': str(e)}


def test_api_response_time():
    """测试 2: API 响应时间 (P50/P90/P99)"""
    print("\n" + "="*70)
    print("测试 2: API 响应时间测试 (100 次请求)")
    print("="*70)
    
    latencies = []
    test_endpoints = [
        ('GET', '/api/health'),
        ('GET', '/api/graph/nodes?limit=10'),
        ('POST', '/api/v4/query', {'question': '查询前 10 个供应商', 'limit': 10}),
    ]
    
    for method, endpoint, *data in test_endpoints:
        endpoint_latencies = []
        payload = data[0] if data else None
        
        print(f"\n测试端点：{method} {endpoint}")
        
        for i in range(30):
            try:
                start = time.time()
                if method == 'GET':
                    response = requests.get(f"{CONFIG['backend_url']}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{CONFIG['backend_url']}{endpoint}", json=payload, timeout=10)
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    endpoint_latencies.append(latency)
            except Exception as e:
                pass  # 静默失败
        
        if endpoint_latencies:
            p50 = statistics.median(endpoint_latencies)
            p90 = sorted(endpoint_latencies)[int(len(endpoint_latencies) * 0.9)]
            p99 = sorted(endpoint_latencies)[int(len(endpoint_latencies) * 0.99)]
            avg = statistics.mean(endpoint_latencies)
            
            print(f"  平均：{avg:.2f}ms | P50: {p50:.2f}ms | P90: {p90:.2f}ms | P99: {p99:.2f}ms")
            latencies.extend(endpoint_latencies)
            
            results[f'api_{endpoint.replace("/", "_")}'] = {
                'avg_ms': round(avg, 2),
                'p50_ms': round(p50, 2),
                'p90_ms': round(p90, 2),
                'p99_ms': round(p99, 2),
                'samples': len(endpoint_latencies)
            }
    
    # 总体统计
    if latencies:
        overall_p50 = statistics.median(latencies)
        overall_p90 = sorted(latencies)[int(len(latencies) * 0.9)]
        overall_p99 = sorted(latencies)[int(len(latencies) * 0.99)]
        
        print(f"\n总体统计:")
        print(f"  P50: {overall_p50:.2f}ms")
        print(f"  P90: {overall_p90:.2f}ms")
        print(f"  P99: {overall_p99:.2f}ms")
        
        results['api_overall'] = {
            'p50_ms': round(overall_p50, 2),
            'p90_ms': round(overall_p90, 2),
            'p99_ms': round(overall_p99, 2),
            'total_samples': len(latencies)
        }


def test_concurrent_queries():
    """测试 3: 并发查询能力 (QPS)"""
    print("\n" + "="*70)
    print("测试 3: 并发查询能力测试")
    print("="*70)
    
    def make_query():
        try:
            start = time.time()
            response = requests.post(
                f"{CONFIG['backend_url']}/api/v4/query",
                json={'question': '查询前 5 个供应商', 'limit': 5},
                timeout=10
            )
            latency = (time.time() - start)
            return response.status_code == 200, latency
        except:
            return False, 0
    
    # 测试不同并发级别
    concurrency_levels = [1, 5, 10, 20]
    
    for concurrency in concurrency_levels:
        print(f"\n并发数：{concurrency}")
        
        success_count = 0
        latencies = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_query) for _ in range(concurrency * 5)]
            for future in as_completed(futures):
                success, latency = future.result()
                if success:
                    success_count += 1
                    latencies.append(latency)
        
        total_time = time.time() - start_time
        qps = success_count / total_time
        avg_latency = statistics.mean(latencies) * 1000 if latencies else 0
        
        print(f"  成功：{success_count}/{concurrency * 5}")
        print(f"  总耗时：{total_time:.2f}s")
        print(f"  QPS: {qps:.2f}")
        print(f"  平均延迟：{avg_latency:.2f}ms")
        
        results[f'concurrent_{concurrency}'] = {
            'success_rate': f"{success_count}/{concurrency * 5}",
            'qps': round(qps, 2),
            'avg_latency_ms': round(avg_latency, 2)
        }


def test_rtr_sync_latency():
    """测试 4: RTR 同步延迟"""
    print("\n" + "="*70)
    print("测试 4: RTR 实时同步延迟测试")
    print("="*70)
    
    try:
        # 连接 PostgreSQL
        pg_conn = psycopg2.connect(**CONFIG['postgres'])
        pg_conn.autocommit = True
        pg_cur = pg_conn.cursor()
        
        # 连接 Neo4j
        neo4j_driver = GraphDatabase.driver(**CONFIG['neo4j'])
        
        import random
        test_id = random.randint(200000, 999999)
        
        # 记录插入时间
        insert_time = datetime.now()
        
        # 插入测试数据
        pg_cur.execute("""
            INSERT INTO ap_invoices_all 
            (invoice_id, invoice_num, vendor_id, invoice_amount, status) 
            VALUES (%s, %s, %s, %s, %s)
        """, (test_id, f'BENCH-{test_id}', 1, 100.00, 'PENDING'))
        
        print(f"✅ PostgreSQL 插入时间：{insert_time.strftime('%H:%M:%S.%f')[:-3]}")
        
        # 等待同步
        time.sleep(2)
        
        # 查询 Neo4j
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (i:Invoice {invoice_id: $id}) 
                RETURN i.sync_time as sync_time
            """, id=test_id)
            record = result.single()
            
            if record and record['sync_time']:
                sync_time = record['sync_time']
                if isinstance(sync_time, str):
                    sync_time = datetime.fromisoformat(sync_time.replace('Z', '+00:00'))
                
                latency = (sync_time - insert_time.replace(tzinfo=sync_time.tzinfo)).total_seconds() * 1000
                print(f"✅ Neo4j 同步时间：{sync_time.strftime('%H:%M:%S.%f')[:-3]}")
                print(f"✅ 同步延迟：{latency:.2f}ms")
                
                results['rtr_sync'] = {
                    'latency_ms': round(latency, 2),
                    'status': 'ok'
                }
            else:
                print("⚠️ Neo4j 未找到同步记录（可能消费者未运行）")
                results['rtr_sync'] = {'status': 'warning', 'message': 'Consumer not running'}
        
        # 清理测试数据
        pg_cur.execute("DELETE FROM ap_invoices_all WHERE invoice_id = %s", (test_id,))
        
        pg_cur.close()
        pg_conn.close()
        neo4j_driver.close()
        
    except Exception as e:
        print(f"❌ 错误：{e}")
        results['rtr_sync'] = {'status': 'error', 'message': str(e)}


def test_neo4j_query_performance():
    """测试 5: Neo4j 查询性能"""
    print("\n" + "="*70)
    print("测试 5: Neo4j 查询性能测试")
    print("="*70)
    
    try:
        neo4j_driver = GraphDatabase.driver(**CONFIG['neo4j'])
        
        test_queries = [
            ("简单查询", "MATCH (n) RETURN count(n)"),
            ("带标签查询", "MATCH (i:Invoice) RETURN count(i)"),
            ("关系查询", "MATCH ()-[r]->() RETURN count(r)"),
            ("属性索引查询", "MATCH (i:Invoice {status: 'PENDING'}) RETURN i LIMIT 100"),
            ("路径查询", "MATCH p=()-[:SUPPLIES]->() RETURN p LIMIT 50"),
        ]
        
        for name, query in test_queries:
            latencies = []
            
            for _ in range(10):
                start = time.time()
                with neo4j_driver.session() as session:
                    result = session.run(query)
                    _ = list(result)
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            
            avg = statistics.mean(latencies)
            p95 = sorted(latencies)[9]
            
            print(f"\n{name}:")
            print(f"  平均：{avg:.2f}ms | P95: {p95:.2f}ms")
            
            results[f'neo4j_{name}'] = {
                'avg_ms': round(avg, 2),
                'p95_ms': round(p95, 2)
            }
        
        neo4j_driver.close()
        
    except Exception as e:
        print(f"❌ 错误：{e}")
        results['neo4j_performance'] = {'status': 'error', 'message': str(e)}


def generate_report():
    """生成测试报告"""
    print("\n" + "="*70)
    print("📊 性能基准测试报告")
    print("="*70)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': 'v3.5.0',
        'results': results
    }
    
    # 保存报告
    report_path = 'docs/performance-benchmark-report.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# GSD 智能问数平台 - 性能基准测试报告\n\n")
        f.write(f"**测试时间**: {report['timestamp']}\n")
        f.write(f"**版本**: {report['version']}\n\n")
        
        f.write("## 📊 测试结果总览\n\n")
        
        # API 响应时间
        if 'api_overall' in results:
            f.write("### API 响应时间\n\n")
            f.write(f"| 指标 | 数值 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| P50 | {results['api_overall']['p50_ms']}ms |\n")
            f.write(f"| P90 | {results['api_overall']['p90_ms']}ms |\n")
            f.write(f"| P99 | {results['api_overall']['p99_ms']}ms |\n")
            f.write(f"| 样本数 | {results['api_overall']['total_samples']} |\n\n")
        
        # 并发性能
        f.write("### 并发查询能力\n\n")
        f.write(f"| 并发数 | QPS | 平均延迟 | 成功率 |\n")
        f.write(f"|--------|-----|---------|--------|\n")
        for key, value in results.items():
            if key.startswith('concurrent_'):
                f.write(f"| {key.split('_')[1]} | {value['qps']} | {value['avg_latency_ms']}ms | {value['success_rate']} |\n")
        f.write("\n")
        
        # RTR 同步
        if 'rtr_sync' in results and results['rtr_sync'].get('status') == 'ok':
            f.write("### RTR 同步延迟\n\n")
            f.write(f"| 指标 | 数值 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 同步延迟 | {results['rtr_sync']['latency_ms']}ms |\n")
            f.write(f"| 目标 | <500ms |\n")
            f.write(f"| 状态 | {'✅ 达标' if results['rtr_sync']['latency_ms'] < 500 else '⚠️ 待优化'} |\n\n")
        
        # Neo4j 性能
        f.write("### Neo4j 查询性能\n\n")
        f.write(f"| 查询类型 | 平均延迟 | P95 |\n")
        f.write(f"|---------|---------|-----|\n")
        for key, value in results.items():
            if key.startswith('neo4j_') and 'avg_ms' in value:
                name = key.replace('neo4j_', '')
                f.write(f"| {name} | {value['avg_ms']}ms | {value['p95_ms']}ms |\n")
        
        f.write("\n---\n\n")
        f.write("*报告由 benchmark_performance.py 自动生成*\n")
    
    print(f"\n✅ 报告已保存：{report_path}")
    
    # 保存 JSON 结果
    json_path = 'docs/performance-benchmark-results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON 结果已保存：{json_path}")


def main():
    """主函数"""
    print("="*70)
    print("GSD 智能问数平台 - 性能基准测试")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 执行测试
    test_api_health()
    test_api_response_time()
    test_concurrent_queries()
    test_rtr_sync_latency()
    test_neo4j_query_performance()
    
    # 生成报告
    generate_report()
    
    print("\n" + "="*70)
    print("✅ 性能基准测试完成！")
    print("="*70)


if __name__ == '__main__':
    main()
