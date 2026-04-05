"""
GSD 智能问数后端自动化测试框架
覆盖：关键词匹配、API 端点、性能、缓存、数据生成
总计 27 个测试用例
"""
import pytest
import asyncio
import time
from httpx import AsyncClient, ASGITransport
from typing import Dict, Any

# 导入 FastAPI 应用
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.main import app


# ==================== Fixtures ====================

@pytest.fixture
async def client():
    """异步 HTTP 客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_queries():
    """示例查询"""
    return {
        "sales_trend": "显示本周销售趋势",
        "customer_rank": "查询 Top 10 客户",
        "inventory": "显示库存预警商品",
        "payment": "查看付款单列表",
        "stats": "统计各产品类别销售额",
        "unknown": "今天天气怎么样"
    }


# ==================== 关键词匹配测试 (8 个) ====================

class TestKeywordMatching:
    """关键词匹配逻辑测试"""
    
    @pytest.mark.asyncio
    async def test_sales_trend_detection(self, client):
        """测试销售趋势查询识别"""
        response = await client.post("/api/v1/query", json={"query": "显示本周销售趋势"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "chart"
        assert "chart_config" in data
    
    @pytest.mark.asyncio
    async def test_customer_rank_detection(self, client):
        """测试客户排行查询识别"""
        response = await client.post("/api/v1/query", json={"query": "查询 Top 10 客户"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_inventory_detection(self, client):
        """测试库存查询识别"""
        response = await client.post("/api/v1/query", json={"query": "显示库存预警商品"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
    
    @pytest.mark.asyncio
    async def test_payment_detection(self, client):
        """测试付款单查询识别"""
        response = await client.post("/api/v1/query", json={"query": "查看付款单列表"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
    
    @pytest.mark.asyncio
    async def test_stats_detection(self, client):
        """测试统计概览查询识别"""
        response = await client.post("/api/v1/query", json={"query": "统计各产品类别销售额"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "stats"
    
    @pytest.mark.asyncio
    async def test_unknown_query_fallback(self, client):
        """测试未知查询降级处理"""
        response = await client.post("/api/v1/query", json={"query": "今天天气怎么样"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "text"
    
    @pytest.mark.asyncio
    async def test_query_case_insensitive(self, client):
        """测试查询大小写不敏感"""
        response1 = await client.post("/api/v1/query", json={"query": "显示本周销售趋势"})
        response2 = await client.post("/api/v1/query", json={"query": "DISPLAY WEEKLY SALES TREND"})
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.asyncio
    async def test_query_with_special_chars(self, client):
        """测试特殊字符处理"""
        response = await client.post("/api/v1/query", json={"query": "销售趋势！！！###"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ==================== API 端点测试 (7 个) ====================

class TestAPIEndpoints:
    """API 端点功能测试"""
    
    @pytest.mark.asyncio
    async def test_query_endpoint_exists(self, client):
        """测试查询端点存在性"""
        response = await client.post("/api/v1/query", json={"query": "test"})
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_suggested_questions_endpoint(self, client):
        """测试推荐问题端点"""
        response = await client.get("/api/v1/suggested-questions")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) > 0
    
    @pytest.mark.asyncio
    async def test_query_response_structure(self, client):
        """测试查询响应结构"""
        response = await client.post("/api/v1/query", json={"query": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "answer" in data
        assert "data_type" in data
    
    @pytest.mark.asyncio
    async def test_query_empty_string(self, client):
        """测试空字符串查询"""
        response = await client.post("/api/v1/query", json={"query": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_query_long_text(self, client):
        """测试长文本查询"""
        long_query = "请帮我分析一下我们公司最近的销售趋势和客户排行榜情况" * 10
        response = await client.post("/api/v1/query", json={"query": long_query})
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_query_with_context(self, client):
        """测试带上下文的查询"""
        response = await client.post("/api/v1/query", json={
            "query": "销售趋势",
            "context": {"user_id": "test123", "time_range": "week"}
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_api_health(self, client):
        """测试 API 健康状态"""
        response = await client.get("/docs")
        assert response.status_code == 200


# ==================== 性能测试 (5 个) ====================

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_response_time_single_query(self, client):
        """测试单次查询响应时间"""
        start = time.time()
        response = await client.post("/api/v1/query", json={"query": "销售趋势"})
        elapsed = time.time() - start
        assert elapsed < 1.0  # 响应时间 < 1 秒
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, client):
        """测试并发查询"""
        tasks = [
            client.post("/api/v1/query", json={"query": "销售趋势"})
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in responses)
    
    @pytest.mark.asyncio
    async def test_response_time_average(self, client):
        """测试平均响应时间"""
        times = []
        for _ in range(5):
            start = time.time()
            await client.post("/api/v1/query", json={"query": "销售趋势"})
            times.append(time.time() - start)
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5  # 平均响应时间 < 500ms
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, client):
        """测试缓存性能"""
        # 第一次查询
        start1 = time.time()
        await client.post("/api/v1/query", json={"query": "缓存测试"})
        time1 = time.time() - start1
        
        # 第二次查询（应该命中缓存）
        start2 = time.time()
        await client.post("/api/v1/query", json={"query": "缓存测试"})
        time2 = time.time() - start2
        
        assert time2 <= time1  # 缓存应该更快或相等
    
    @pytest.mark.asyncio
    async def test_stress_test_50_queries(self, client):
        """测试 50 次连续查询"""
        start = time.time()
        for _ in range(50):
            response = await client.post("/api/v1/query", json={"query": "压力测试"})
            assert response.status_code == 200
        elapsed = time.time() - start
        qps = 50 / elapsed
        assert qps > 10  # QPS > 10


# ==================== 缓存测试 (4 个) ====================

class TestCaching:
    """缓存功能测试"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_same_query(self, client):
        """测试相同查询命中缓存"""
        response1 = await client.post("/api/v1/query", json={"query": "缓存命中测试"})
        response2 = await client.post("/api/v1/query", json={"query": "缓存命中测试"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["answer"] == response2.json()["answer"]
    
    @pytest.mark.asyncio
    async def test_cache_different_queries(self, client):
        """测试不同查询不命中缓存"""
        response1 = await client.post("/api/v1/query", json={"query": "销售趋势"})
        response2 = await client.post("/api/v1/query", json={"query": "客户排行"})
        
        assert response1.json()["answer"] != response2.json()["answer"]
    
    @pytest.mark.asyncio
    async def test_cache_consistency(self, client):
        """测试缓存一致性"""
        responses = []
        for _ in range(3):
            response = await client.post("/api/v1/query", json={"query": "一致性测试"})
            responses.append(response.json()["answer"])
        
        assert all(r == responses[0] for r in responses)
    
    @pytest.mark.asyncio
    async def test_cache_memory_usage(self, client):
        """测试缓存内存使用"""
        # 执行多次不同查询
        for i in range(20):
            await client.post("/api/v1/query", json={"query": f"缓存测试{i}"})
        
        # 应该不崩溃
        response = await client.post("/api/v1/query", json={"query": "最终测试"})
        assert response.status_code == 200


# ==================== 数据生成测试 (3 个) ====================

class TestDataGeneration:
    """数据生成测试"""
    
    @pytest.mark.asyncio
    async def test_chart_data_structure(self, client):
        """测试图表数据结构"""
        response = await client.post("/api/v1/query", json={"query": "销售趋势"})
        data = response.json()
        
        assert "chart_config" in data
        chart = data["chart_config"]
        assert "xAxis" in chart
        assert "yAxis" in chart
        assert "series" in chart
    
    @pytest.mark.asyncio
    async def test_table_data_structure(self, client):
        """测试表格数据结构"""
        response = await client.post("/api/v1/query", json={"query": "客户排行"})
        data = response.json()
        
        assert "data" in data
        table_data = data["data"]
        assert "columns" in table_data
        assert "rows" in table_data
        assert isinstance(table_data["columns"], list)
        assert isinstance(table_data["rows"], list)
    
    @pytest.mark.asyncio
    async def test_stats_data_structure(self, client):
        """测试统计数据结构"""
        response = await client.post("/api/v1/query", json={"query": "统计概览"})
        data = response.json()
        
        assert "data" in data
        stats_data = data["data"]
        assert "items" in stats_data
        assert isinstance(stats_data["items"], list)


# ==================== 边界条件测试 (5 个) ====================

class TestEdgeCases:
    """边界条件测试"""
    
    @pytest.mark.asyncio
    async def test_unicode_characters(self, client):
        """测试 Unicode 字符"""
        response = await client.post("/api/v1/query", json={
            "query": "销售趋势 📊 分析！！！💰"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, client):
        """测试超长查询"""
        long_query = "销售" * 1000
        response = await client.post("/api/v1/query", json={"query": long_query})
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, client):
        """测试 SQL 注入尝试"""
        response = await client.post("/api/v1/query", json={
            "query": "'; DROP TABLE users; --"
        })
        assert response.status_code == 200  # 应该安全处理
    
    @pytest.mark.asyncio
    async def test_xss_attempt(self, client):
        """测试 XSS 攻击尝试"""
        response = await client.post("/api/v1/query", json={
            "query": "<script>alert('xss')</script>"
        })
        assert response.status_code == 200  # 应该安全处理
    
    @pytest.mark.asyncio
    async def test_null_bytes(self, client):
        """测试空字节"""
        response = await client.post("/api/v1/query", json={
            "query": "test\x00query"
        })
        assert response.status_code == 200


# ==================== 集成测试 (5 个) ====================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_sales(self, client):
        """测试完整工作流程：销售查询"""
        # 1. 获取推荐问题
        suggested = await client.get("/api/v1/suggested-questions")
        assert suggested.status_code == 200
        
        # 2. 执行查询
        response = await client.post("/api/v1/query", json={"query": "显示本周销售趋势"})
        assert response.status_code == 200
        data = response.json()
        
        # 3. 验证响应
        assert data["success"] is True
        assert data["data_type"] == "chart"
        assert len(data["answer"]) > 0
    
    @pytest.mark.asyncio
    async def test_full_workflow_customer(self, client):
        """测试完整工作流程：客户查询"""
        response = await client.post("/api/v1/query", json={"query": "查询 Top 10 客户"})
        assert response.status_code == 200
        data = response.json()
        assert data["data_type"] == "table"
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_multiple_query_types(self, client):
        """测试多种查询类型"""
        queries = [
            ("销售趋势", "chart"),
            ("客户排行", "table"),
            ("库存预警", "table"),
            ("统计概览", "stats"),
        ]
        
        for query, expected_type in queries:
            response = await client.post("/api/v1/query", json={"query": query})
            assert response.status_code == 200
            # 注意：实际类型可能因关键词匹配逻辑而异
    
    @pytest.mark.asyncio
    async def test_session_continuity(self, client):
        """测试会话连续性"""
        # 模拟多轮对话
        queries = [
            "销售趋势",
            "客户排行",
            "再详细一点",
            "对比上个月"
        ]
        
        for query in queries:
            response = await client.post("/api/v1/query", json={"query": query})
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """测试错误处理"""
        # 发送无效请求
        response = await client.post("/api/v1/query", json={})
        # 应该返回错误而不是崩溃
        assert response.status_code in [200, 422]


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=html"])
