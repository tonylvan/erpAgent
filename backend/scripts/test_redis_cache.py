"""
Redis 缓存测试脚本
测试 Redis 缓存集成和性能提升
"""
import requests
import time

BASE_URL = "http://localhost:8005"

def test_cache_performance():
    """测试缓存性能"""
    print("=" * 60)
    print("Redis 缓存性能测试")
    print("=" * 60)
    
    test_query = "显示本周销售趋势"
    
    # 第一次查询（未缓存）
    print("\n[1/3] 第一次查询（未缓存）...")
    start = time.time()
    r1 = requests.post(f"{BASE_URL}/api/v1/smart-query-v25/query", json={"query": test_query})
    t1 = (time.time() - start) * 1000
    print(f"  耗时：{t1:.0f}ms")
    
    # 第二次查询（缓存命中）
    print("\n[2/3] 第二次查询（缓存命中）...")
    start = time.time()
    r2 = requests.post(f"{BASE_URL}/api/v1/smart-query-v25/query", json={"query": test_query})
    t2 = (time.time() - start) * 1000
    print(f"  耗时：{t2:.0f}ms")
    
    # 第三次查询（缓存命中）
    print("\n[3/3] 第三次查询（缓存命中）...")
    start = time.time()
    r3 = requests.post(f"{BASE_URL}/api/v1/smart-query-v25/query", json={"query": test_query})
    t3 = (time.time() - start) * 1000
    print(f"  耗时：{t3:.0f}ms")
    
    # 计算性能提升
    avg_cached = (t2 + t3) / 2
    improvement = ((t1 - avg_cached) / t1) * 100 if t1 > 0 else 0
    
    print("\n" + "=" * 60)
    print("性能对比:")
    print(f"  未缓存平均：{t1:.0f}ms")
    print(f"  缓存命中平均：{avg_cached:.0f}ms")
    print(f"  性能提升：{improvement:.1f}%")
    print("=" * 60)
    
    # 获取缓存统计
    print("\n获取缓存统计...")
    r_stats = requests.get(f"{BASE_URL}/api/v1/smart-query-v25/cache-stats")
    stats = r_stats.json()
    
    print(f"  缓存启用：{'是' if stats.get('cache_enabled') else '否'}")
    print(f"  Redis 连接：{'是' if stats.get('redis_connected') else '否'}")
    print(f"  数据库大小：{stats.get('db_size', 0)} keys")
    print(f"  缓存命中：{stats.get('cache_hits', 0)}")
    print(f"  缓存未命中：{stats.get('cache_misses', 0)}")
    print(f"  命中率：{stats.get('hit_rate', '0%')}")
    
    print("\n[OK] 测试完成！")


if __name__ == "__main__":
    test_cache_performance()
