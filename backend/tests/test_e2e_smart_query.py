"""
GSD 智能问数系统 - 端到端自动化测试
验证完整流程：Neo4j → API → 缓存 → 响应
"""
import requests
import time
import json
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8005"
TIMEOUT = 30

# 测试用例
TEST_CASES = [
    {
        "name": "销售趋势查询",
        "query": "显示本周销售趋势",
        "expected_type": "chart",
        "expected_keywords": ["销售", "趋势", "上升"]
    },
    {
        "name": "客户排行查询",
        "query": "查询 Top 10 客户",
        "expected_type": "table",
        "expected_keywords": ["客户", "排行", "贡献"]
    },
    {
        "name": "库存预警查询",
        "query": "显示库存预警商品",
        "expected_type": "table",
        "expected_keywords": ["库存", "预警", "补货"]
    },
    {
        "name": "付款单查询",
        "query": "查看本周付款单",
        "expected_type": "table",
        "expected_keywords": ["付款", "金额", "状态"]
    },
    {
        "name": "统计概览查询",
        "query": "统计各产品类别销售额",
        "expected_type": "stats",
        "expected_keywords": ["统计", "指标", "销售额"]
    },
    {
        "name": "未知查询降级",
        "query": "今天天气怎么样",
        "expected_type": "text",
        "expected_keywords": ["支持", "查询"]
    }
]


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f" {text} ")
    print("=" * 70)


def print_result(name, success, message=""):
    """打印测试结果"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {name}")
    if message:
        print(f"     {message}")


def test_health_check():
    """测试 1: 健康检查"""
    print_header("测试 1: 健康检查")
    
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            print_result("后端服务", True, f"状态：{data.get('status')}")
            return True
        else:
            print_result("后端服务", False, f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print_result("后端服务", False, str(e))
        return False


def test_neo4j_connection():
    """测试 2: Neo4j 连接"""
    print_header("测试 2: Neo4j 连接")
    
    try:
        # 通过查询测试 Neo4j 连接
        r = requests.post(
            f"{BASE_URL}/api/v1/smart-query-v25/query",
            json={"query": "测试连接"},
            timeout=TIMEOUT
        )
        
        if r.status_code == 200:
            print_result("Neo4j 连接", True, "查询正常")
            return True
        else:
            print_result("Neo4j 连接", False, f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print_result("Neo4j 连接", False, str(e))
        return False


def test_query_api():
    """测试 3: 查询 API 功能"""
    print_header("测试 3: 查询 API 功能测试")
    
    passed = 0
    failed = 0
    
    for case in TEST_CASES:
        try:
            start = time.time()
            r = requests.post(
                f"{BASE_URL}/api/v1/smart-query-v25/query",
                json={"query": case["query"]},
                timeout=TIMEOUT
            )
            elapsed = (time.time() - start) * 1000
            
            if r.status_code != 200:
                print_result(case["name"], False, f"HTTP {r.status_code}")
                failed += 1
                continue
            
            data = r.json()
            actual_type = data.get("data_type")
            
            # 验证返回类型
            if actual_type != case["expected_type"]:
                print_result(
                    case["name"], 
                    False, 
                    f"类型不匹配：期望 {case['expected_type']}, 实际 {actual_type}"
                )
                failed += 1
                continue
            
            # 验证关键词
            answer = data.get("answer", "")
            keywords_found = sum(1 for kw in case["expected_keywords"] if kw in answer)
            
            if keywords_found < len(case["expected_keywords"]) * 0.5:
                print_result(
                    case["name"],
                    False,
                    f"关键词匹配不足：{keywords_found}/{len(case['expected_keywords'])}"
                )
                failed += 1
                continue
            
            # 验证响应时间
            if elapsed > 2000:
                print_result(
                    case["name"],
                    False,
                    f"响应时间过长：{elapsed:.0f}ms (>2000ms)"
                )
                failed += 1
                continue
            
            print_result(case["name"], True, f"{elapsed:.0f}ms - {actual_type}")
            passed += 1
            
        except Exception as e:
            print_result(case["name"], False, str(e))
            failed += 1
    
    print(f"\n总计：{passed} 通过，{failed} 失败")
    return failed == 0


def test_cache_performance():
    """测试 4: 缓存性能"""
    print_header("测试 4: 缓存性能测试")
    
    query = "显示本周销售趋势"
    
    try:
        # 第一次查询（未缓存）
        start = time.time()
        r1 = requests.post(
            f"{BASE_URL}/api/v1/smart-query-v25/query",
            json={"query": query},
            timeout=TIMEOUT
        )
        t1 = (time.time() - start) * 1000
        
        # 第二次查询（缓存命中）
        start = time.time()
        r2 = requests.post(
            f"{BASE_URL}/api/v1/smart-query-v25/query",
            json={"query": query},
            timeout=TIMEOUT
        )
        t2 = (time.time() - start) * 1000
        
        # 第三次查询（缓存命中）
        start = time.time()
        r3 = requests.post(
            f"{BASE_URL}/api/v1/smart-query-v25/query",
            json={"query": query},
            timeout=TIMEOUT
        )
        t3 = (time.time() - start) * 1000
        
        avg_cached = (t2 + t3) / 2
        improvement = ((t1 - avg_cached) / max(t1, 0.001)) * 100
        
        print(f"  未缓存平均：{t1:.0f}ms")
        print(f"  缓存命中平均：{avg_cached:.0f}ms")
        print(f"  性能提升：{improvement:.1f}%")
        
        if improvement > 50:
            print_result("缓存性能", True, f"提升 {improvement:.1f}%")
            return True
        else:
            print_result("缓存性能", False, f"提升不足：{improvement:.1f}%")
            return False
            
    except Exception as e:
        print_result("缓存性能", False, str(e))
        return False


def test_cache_stats():
    """测试 5: 缓存统计 API"""
    print_header("测试 5: 缓存统计 API")
    
    try:
        r = requests.get(
            f"{BASE_URL}/api/v1/smart-query-v25/cache-stats",
            timeout=TIMEOUT
        )
        
        if r.status_code != 200:
            print_result("缓存统计", False, f"HTTP {r.status_code}")
            return False
        
        data = r.json()
        
        # 验证必要字段
        required_fields = ["cache_enabled", "cache_hits", "cache_misses"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print_result("缓存统计", False, f"缺少字段：{missing}")
            return False
        
        print_result("缓存统计", True, f"命中：{data.get('cache_hits')}, 未命中：{data.get('cache_misses')}")
        return True
        
    except Exception as e:
        print_result("缓存统计", False, str(e))
        return False


def test_suggested_questions():
    """测试 6: 推荐问题 API"""
    print_header("测试 6: 推荐问题 API")
    
    try:
        r = requests.get(
            f"{BASE_URL}/api/v1/smart-query/suggested-questions",
            timeout=TIMEOUT
        )
        
        if r.status_code != 200:
            print_result("推荐问题", False, f"HTTP {r.status_code}")
            return False
        
        data = r.json()
        questions = data.get("questions", [])
        
        if len(questions) < 5:
            print_result("推荐问题", False, f"问题数量不足：{len(questions)}")
            return False
        
        print_result("推荐问题", True, f"{len(questions)} 个问题")
        return True
        
    except Exception as e:
        print_result("推荐问题", False, str(e))
        return False


def test_api_docs():
    """测试 7: API 文档"""
    print_header("测试 7: API 文档")
    
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        
        if r.status_code == 200:
            print_result("API 文档", True, "Swagger UI 可访问")
            return True
        else:
            print_result("API 文档", False, f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print_result("API 文档", False, str(e))
        return False


def run_all_tests():
    """运行所有测试"""
    print_header("GSD 智能问数系统 - 端到端自动化测试")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址：{BASE_URL}")
    
    start_time = time.time()
    
    results = []
    
    # 执行测试
    results.append(("健康检查", test_health_check()))
    results.append(("Neo4j 连接", test_neo4j_connection()))
    results.append(("查询 API", test_query_api()))
    results.append(("缓存性能", test_cache_performance()))
    results.append(("缓存统计", test_cache_stats()))
    results.append(("推荐问题", test_suggested_questions()))
    results.append(("API 文档", test_api_docs()))
    
    total_time = time.time() - start_time
    
    # 汇总结果
    print_header("测试结果汇总")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    for name, result in results:
        status = "[OK]" if result else "[ERROR]"
        print(f"{status} {name}")
    
    print(f"\n总计：{passed}/{total} 通过 ({success_rate:.1f}%)")
    print(f"总耗时：{total_time:.2f}秒")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 判断是否全部通过
    if passed == total:
        print_header("[SUCCESS] 所有测试通过！GSD 智能问数系统运行正常！")
        return True
    else:
        print_header("[WARNING] 部分测试未通过，请检查日志")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
