"""
GSD 智能问数全链路集成测试
覆盖：前后端集成、API 工作流、数据一致性、错误恢复
总计 15 个测试用例
"""
import pytest
import asyncio
import aiohttp
import time
from typing import List, Dict, Any


# 配置
BASE_URL = "http://localhost:8005"
FRONTEND_URL = "http://localhost:5176"


class TestFullWorkflow:
    """全链路工作流测试"""
    
    @pytest.fixture
    async def session(self):
        """创建 HTTP 会话"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    # ==================== 端到端工作流测试 (5 个) ====================
    
    @pytest.mark.asyncio
    async def test_complete_query_workflow(self, session):
        """测试完整查询工作流"""
        # 1. 获取推荐问题
        async with session.get(f"{BASE_URL}/api/v1/suggested-questions") as resp:
            assert resp.status == 200
            suggested = await resp.json()
            assert "questions" in suggested
        
        # 2. 执行查询
        query = suggested["questions"][0]
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": query}
        ) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert result["success"] is True
            assert "answer" in result
            assert "data_type" in result
        
        # 3. 验证响应时间
        start = time.time()
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": "测试"}
        ) as resp:
            await resp.json()
            elapsed = time.time() - start
            assert elapsed < 2.0  # 响应时间 < 2 秒
    
    @pytest.mark.asyncio
    async def test_multiple_query_types_workflow(self, session):
        """测试多种查询类型工作流"""
        test_cases = [
            ("销售趋势", ["chart", "text"]),
            ("客户排行", ["table", "text"]),
            ("库存预警", ["table", "text"]),
            ("统计概览", ["stats", "text"]),
        ]
        
        for query, expected_types in test_cases:
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": query}
            ) as resp:
                assert resp.status == 200
                result = await resp.json()
                assert result["success"] is True
                # 验证返回类型在预期范围内
                assert result["data_type"] in expected_types
    
    @pytest.mark.asyncio
    async def test_concurrent_users_workflow(self, session):
        """测试多用户并发工作流"""
        queries = ["销售趋势"] * 10
        
        async def make_query(q):
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": q}
            ) as resp:
                return await resp.json()
        
        # 并发执行 10 个查询
        tasks = [make_query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        assert all(r["success"] for r in results)
    
    @pytest.mark.asyncio
    async def test_session_continuity_workflow(self, session):
        """测试会话连续性工作流"""
        conversation = [
            "销售趋势",
            "再详细一点",
            "对比上个月",
            "显示图表"
        ]
        
        responses = []
        for query in conversation:
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": query}
            ) as resp:
                result = await resp.json()
                responses.append(result)
                assert result["success"] is True
        
        # 验证所有响应都有效
        assert len(responses) == len(conversation)
        assert all(r["success"] for r in responses)
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, session):
        """测试错误恢复工作流"""
        # 1. 发送无效查询
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": ""}
        ) as resp:
            assert resp.status in [200, 422]
        
        # 2. 发送有效查询恢复
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": "销售趋势"}
        ) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert result["success"] is True
    
    # ==================== 数据一致性测试 (3 个) ====================
    
    @pytest.mark.asyncio
    async def test_response_structure_consistency(self, session):
        """测试响应结构一致性"""
        queries = ["销售趋势", "客户排行", "库存预警"]
        
        responses = []
        for query in queries:
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": query}
            ) as resp:
                result = await resp.json()
                responses.append(result)
        
        # 验证所有响应都有相同的必需字段
        for resp in responses:
            assert "success" in resp
            assert "answer" in resp
            assert "data_type" in resp
    
    @pytest.mark.asyncio
    async def test_cache_consistency(self, session):
        """测试缓存一致性"""
        query = "缓存一致性测试"
        
        # 执行 3 次相同查询
        results = []
        for _ in range(3):
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": query}
            ) as resp:
                result = await resp.json()
                results.append(result["answer"])
        
        # 验证所有响应相同（缓存命中）
        assert results[0] == results[1] == results[2]
    
    @pytest.mark.asyncio
    async def test_data_format_consistency(self, session):
        """测试数据格式一致性"""
        # 测试图表数据格式
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": "销售趋势"}
        ) as resp:
            result = await resp.json()
            if result["data_type"] == "chart":
                assert "chart_config" in result
                chart = result["chart_config"]
                assert "xAxis" in chart
                assert "yAxis" in chart
                assert "series" in chart
        
        # 测试表格数据格式
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": "客户排行"}
        ) as resp:
            result = await resp.json()
            if result["data_type"] == "table":
                assert "data" in result
                table_data = result["data"]
                assert "columns" in table_data
                assert "rows" in table_data
    
    # ==================== 性能集成测试 (4 个) ====================
    
    @pytest.mark.asyncio
    async def test_response_time_p50(self, session):
        """测试 P50 响应时间"""
        times = []
        
        for _ in range(20):
            start = time.time()
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": "性能测试"}
            ) as resp:
                await resp.json()
                times.append(time.time() - start)
        
        # 计算 P50
        times.sort()
        p50 = times[len(times) // 2]
        assert p50 < 0.5  # P50 < 500ms
    
    @pytest.mark.asyncio
    async def test_response_time_p99(self, session):
        """测试 P99 响应时间"""
        times = []
        
        for _ in range(100):
            start = time.time()
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": "性能测试"}
            ) as resp:
                await resp.json()
                times.append(time.time() - start)
        
        # 计算 P99
        times.sort()
        p99_index = int(len(times) * 0.99)
        p99 = times[p99_index] if p99_index < len(times) else times[-1]
        assert p99 < 0.5  # P99 < 500ms
    
    @pytest.mark.asyncio
    async def test_qps_throughput(self, session):
        """测试 QPS 吞吐量"""
        start = time.time()
        tasks = []
        
        # 发送 100 个并发请求
        for _ in range(100):
            task = session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": "吞吐量测试"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*[session.request("POST", f"{BASE_URL}/api/v1/query", json={"query": "测试"}) for _ in range(100)])
        elapsed = time.time() - start
        
        qps = 100 / elapsed
        assert qps > 10  # QPS > 10（测试环境）
    
    @pytest.mark.asyncio
    async def test_error_rate_under_load(self, session):
        """测试负载下的错误率"""
        total_requests = 50
        failed_requests = 0
        
        tasks = []
        for _ in range(total_requests):
            task = session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": "负载测试"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for resp in responses:
            if isinstance(resp, Exception):
                failed_requests += 1
        
        error_rate = failed_requests / total_requests
        assert error_rate < 0.01  # 错误率 < 1%
    
    # ==================== 边界条件测试 (3 个) ====================
    
    @pytest.mark.asyncio
    async def test_long_conversation(self, session):
        """测试长对话场景"""
        # 模拟 20 轮对话
        for i in range(20):
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": f"第{i + 1}轮测试"}
            ) as resp:
                assert resp.status == 200
                result = await resp.json()
                assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_special_characters(self, session):
        """测试特殊字符处理"""
        test_queries = [
            "销售趋势！！！###",
            "客户排行 $$$%^&*",
            "库存预警 ()[]{}",
            "统计概览 <>?:\"",
        ]
        
        for query in test_queries:
            async with session.post(
                f"{BASE_URL}/api/v1/query",
                json={"query": query}
            ) as resp:
                assert resp.status == 200
    
    @pytest.mark.asyncio
    async def test_unicode_support(self, session):
        """测试 Unicode 支持"""
        query = "销售趋势 📊💰📈 分析！！！"
        
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={"query": query}
        ) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert result["success"] is True


# ==================== 前端集成测试 ====================

class TestFrontendIntegration:
    """前端集成测试"""
    
    @pytest.fixture
    async def session(self):
        """创建 HTTP 会话"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.mark.asyncio
    async def test_frontend_loads(self, session):
        """测试前端页面加载"""
        async with session.get(FRONTEND_URL) as resp:
            assert resp.status == 200
    
    @pytest.mark.asyncio
    async def test_frontend_api_integration(self, session):
        """测试前端 API 集成"""
        # 验证前后端连接
        async with session.get(f"{BASE_URL}/api/v1/suggested-questions") as resp:
            assert resp.status == 200


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
