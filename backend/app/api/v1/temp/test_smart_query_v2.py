"""
GSD 智能问数 v2 自动化测试
测试 Neo4j 知识图谱 + AI 大模型集成
"""
import asyncio
import time
import httpx
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 测试配置
BASE_URL = "http://localhost:8005"
QUERY_ENDPOINT = "/api/v1/smart-query-v2/query"
SUGGESTED_ENDPOINT = "/api/v1/smart-query/suggested-questions"

# 测试用例
TEST_CASES = [
    # 销售趋势查询
    {
        "name": "销售趋势查询",
        "query": "显示本周销售趋势",
        "expected_type": "chart",
        "expected_keywords": ["上升", "销售", "趋势"]
    },
    # 客户排行查询
    {
        "name": "客户排行查询",
        "query": "查询 Top 10 客户",
        "expected_type": "table",
        "expected_keywords": ["客户", "排行", "贡献"]
    },
    # 库存查询
    {
        "name": "库存预警查询",
        "query": "显示库存预警商品",
        "expected_type": "table",
        "expected_keywords": ["库存", "预警", "补货"]
    },
    # 付款单查询
    {
        "name": "付款单查询",
        "query": "查看本周付款单",
        "expected_type": "table",
        "expected_keywords": ["付款", "金额", "状态"]
    },
    # 统计概览
    {
        "name": "统计概览",
        "query": "统计各产品类别销售额",
        "expected_type": "stats",
        "expected_keywords": ["统计", "指标", "销售额"]
    },
    # 时间范围解析
    {
        "name": "时间范围解析 - 本月",
        "query": "显示本月销售趋势",
        "expected_type": "chart",
        "expected_keywords": ["销售", "本月"]
    },
    # Top N 提取
    {
        "name": "Top N 提取 - Top 5",
        "query": "查询 Top 5 客户",
        "expected_type": "table",
        "expected_keywords": ["客户", "排行"]
    },
    # 未知查询降级
    {
        "name": "未知查询降级",
        "query": "今天天气怎么样",
        "expected_type": "text",
        "expected_keywords": ["支持", "查询"]
    }
]


async def test_query(client: httpx.AsyncClient, test_case: dict) -> dict:
    """执行单个查询测试"""
    start_time = time.time()
    
    try:
        response = await client.post(
            QUERY_ENDPOINT,
            json={"query": test_case["query"], "context": {}}
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            return {
                "name": test_case["name"],
                "success": False,
                "error": f"HTTP {response.status_code}",
                "elapsed": elapsed
            }
        
        data = response.json()
        
        # 验证返回类型
        actual_type = data.get("data_type", "unknown")
        type_match = actual_type == test_case["expected_type"]
        
        # 验证关键词
        answer = data.get("answer", "")
        keywords_found = [kw for kw in test_case["expected_keywords"] if kw in answer]
        keywords_match = len(keywords_found) >= len(test_case["expected_keywords"]) * 0.5
        
        # 验证数据结构
        structure_valid = True
        if test_case["expected_type"] == "chart":
            structure_valid = "chart_config" in data and data["chart_config"]
        elif test_case["expected_type"] == "table":
            structure_valid = "data" in data and data["data"] and "columns" in data["data"]
        elif test_case["expected_type"] == "stats":
            structure_valid = "data" in data and data["data"] and "items" in data["data"]
        
        # 验证追问建议
        has_follow_up = "follow_up" in data and len(data.get("follow_up", [])) > 0
        
        success = type_match and keywords_match and structure_valid
        
        return {
            "name": test_case["name"],
            "success": success,
            "type_match": type_match,
            "keywords_match": keywords_match,
            "structure_valid": structure_valid,
            "has_follow_up": has_follow_up,
            "elapsed": elapsed,
            "actual_type": actual_type,
            "expected_type": test_case["expected_type"]
        }
    
    except Exception as e:
        return {
            "name": test_case["name"],
            "success": False,
            "error": str(e),
            "elapsed": time.time() - start_time
        }


async def test_suggested_questions(client: httpx.AsyncClient) -> dict:
    """测试推荐问题 API"""
    try:
        response = await client.get(SUGGESTED_ENDPOINT)
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        questions = data.get("questions", [])
        
        return {
            "success": True,
            "count": len(questions),
            "questions": questions
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_performance(client: httpx.AsyncClient, concurrent_users: int = 5) -> dict:
    """测试并发性能"""
    queries = [case["query"] for case in TEST_CASES[:3]]  # 使用前 3 个查询
    
    async def make_query(query: str):
        start = time.time()
        response = await client.post(QUERY_ENDPOINT, json={"query": query})
        return time.time() - start, response.status_code
    
    start_time = time.time()
    tasks = [make_query(q) for q in queries * (concurrent_users // len(queries) + 1)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    latencies = [r[0] for r in results]
    status_codes = [r[1] for r in results]
    
    return {
        "concurrent_users": concurrent_users,
        "total_queries": len(results),
        "total_time": total_time,
        "avg_latency": sum(latencies) / len(latencies),
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "qps": len(results) / total_time,
        "success_rate": sum(1 for code in status_codes if code == 200) / len(status_codes) * 100
    }


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("[TEST] GSD 智能问数 v2 自动化测试")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. 测试推荐问题 API
        print("\n[1/4] 测试推荐问题 API...")
        suggested_result = await test_suggested_questions(client)
        if suggested_result["success"]:
            print(f"[OK] 推荐问题 API 正常 ({suggested_result['count']} 个问题)")
            for q in suggested_result["questions"]:
                print(f"   - {q}")
        else:
            print(f"[FAIL] 推荐问题 API 失败：{suggested_result.get('error')}")
        
        # 2. 运行功能测试
        print("\n[2/4] 运行功能测试...")
        results = []
        for test_case in TEST_CASES:
            result = await test_query(client, test_case)
            results.append(result)
            
            status = "[OK]" if result["success"] else "[FAIL]"
            elapsed_ms = f"{result['elapsed']*1000:.0f}ms"
            
            if result["success"]:
                print(f"{status} {result['name']} - {elapsed_ms}")
            else:
                print(f"{status} {result['name']} - 失败：{result.get('error', '未知错误')}")
                if "actual_type" in result:
                    print(f"   期望：{result['expected_type']}, 实际：{result['actual_type']}")
        
        # 3. 性能测试
        print("\n[3/4] 运行性能测试...")
        perf_result = await test_performance(client, concurrent_users=5)
        print(f"并发用户数：{perf_result['concurrent_users']}")
        print(f"总查询数：{perf_result['total_queries']}")
        print(f"总耗时：{perf_result['total_time']:.2f}s")
        print(f"平均延迟：{perf_result['avg_latency']*1000:.0f}ms")
        print(f"最小延迟：{perf_result['min_latency']*1000:.0f}ms")
        print(f"最大延迟：{perf_result['max_latency']*1000:.0f}ms")
        print(f"QPS: {perf_result['qps']:.1f}")
        print(f"成功率：{perf_result['success_rate']:.1f}%")
        
        # 4. 汇总结果
        print("\n[4/4] 汇总结果")
        print("=" * 60)
        
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        pass_rate = passed / total * 100 if total > 0 else 0
        
        print(f"\n功能测试：{passed}/{total} 通过 ({pass_rate:.1f}%)")
        
        # 性能指标评估
        print("\n性能指标评估:")
        perf_targets = {
            "avg_latency": 2000,  # ms
            "qps": 50,
            "success_rate": 99
        }
        
        latency_ok = perf_result["avg_latency"] * 1000 < perf_targets["avg_latency"]
        qps_ok = perf_result["qps"] >= perf_targets["qps"]
        success_ok = perf_result["success_rate"] >= perf_targets["success_rate"]
        
        print(f"  平均延迟：{perf_result['avg_latency']*1000:.0f}ms {'[OK]' if latency_ok else '[FAIL]'} (目标 <{perf_targets['avg_latency']}ms)")
        print(f"  QPS: {perf_result['qps']:.1f} {'[OK]' if qps_ok else '[FAIL]'} (目标 >={perf_targets['qps']})")
        print(f"  成功率：{perf_result['success_rate']:.1f}% {'[OK]' if success_ok else '[FAIL]'} (目标 >={perf_targets['success_rate']}%)")
        
        overall_pass = passed == total and latency_ok and qps_ok and success_ok
        
        print("\n" + "=" * 60)
        if overall_pass:
            print("[SUCCESS] 所有测试通过！GSD 智能问数 v2 功能正常！")
        else:
            print("[WARNING] 部分测试未通过，请检查日志")
        print("=" * 60)
        
        return overall_pass


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)
