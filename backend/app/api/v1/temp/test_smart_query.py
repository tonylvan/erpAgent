"""
GSD 智能问数后端单元测试
使用 pytest 测试框架
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.v1.smart_query import OpenClawSessionManager


# ============  fixtures  ============
@pytest.fixture
async def client():
    """创建异步测试客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def session_manager():
    """创建会话管理器实例"""
    return OpenClawSessionManager()


# ============  关键词匹配测试  ============
class TestKeywordDetection:
    """测试查询意图识别"""
    
    @pytest.mark.asyncio
    async def test_sales_trend_keywords(self, session_manager):
        """测试销售趋势关键词匹配"""
        queries = [
            "显示本周销售趋势",
            "销售变化趋势",
            "本周销售走势",
            "分析一下销售趋势"
        ]
        for query in queries:
            result = await session_manager._smart_response(query)
            assert result["data_type"] == "chart", f"Failed for: {query}"
    
    @pytest.mark.asyncio
    async def test_inventory_keywords(self, session_manager):
        """测试库存关键词匹配"""
        queries = [
            "查询库存状态",
            "库存预警商品",
            "库存列表",
            "显示库存预警"
        ]
        for query in queries:
            result = await session_manager._smart_response(query)
            assert result["data_type"] == "table", f"Failed for: {query}"
    
    @pytest.mark.asyncio
    async def test_customer_ranking_keywords(self, session_manager):
        """测试客户排行关键词匹配"""
        queries = [
            "查询 Top 10 客户",
            "客户排行榜",
            "Top 客户消费排名",
            "客户列表"
        ]
        for query in queries:
            result = await session_manager._smart_response(query)
            assert result["data_type"] == "table", f"Failed for: {query}"
    
    @pytest.mark.asyncio
    async def test_stats_keywords(self, session_manager):
        """测试统计关键词匹配"""
        queries = [
            "统计各产品销售额",
            "业务概览",
            "核心指标分析",
            "统计数据"
        ]
        for query in queries:
            result = await session_manager._smart_response(query)
            assert result["data_type"] == "stats", f"Failed for: {query}"
    
    @pytest.mark.asyncio
    async def test_payment_keywords(self, session_manager):
        """测试付款单关键词匹配"""
        queries = [
            "本周 最高金额的付款单",
            "查询付款单",
            "付款单列表",
            "最大金额的付款"
        ]
        for query in queries:
            result = await session_manager._smart_response(query)
            assert result["data_type"] == "table", f"Failed for: {query}"
    
    @pytest.mark.asyncio
    async def test_unknown_query(self, session_manager):
        """测试未知查询的降级处理"""
        result = await session_manager._smart_response("今天天气怎么样")
        assert result["data_type"] == "text"
        assert "请尝试以下问题" in result["answer"]


# ============  API 端点测试  ============
class TestAPIEndpoints:
    """测试 API 端点"""
    
    @pytest.mark.asyncio
    async def test_query_sales_trend(self, client):
        """测试销售趋势查询 API"""
        response = await client.post("/api/v1/smart-query/query", json={
            "query": "显示本周销售趋势",
            "context": {}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "chart"
        assert "chart_config" in data
    
    @pytest.mark.asyncio
    async def test_query_inventory(self, client):
        """测试库存查询 API"""
        response = await client.post("/api/v1/smart-query/query", json={
            "query": "查询库存状态",
            "context": {}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
        assert "data" in data
        assert "columns" in data["data"]
        assert "rows" in data["data"]
    
    @pytest.mark.asyncio
    async def test_query_stats(self, client):
        """测试统计查询 API"""
        response = await client.post("/api/v1/smart-query/query", json={
            "query": "统计各产品销售额",
            "context": {}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "stats"
        assert "data" in data
        assert "items" in data["data"]
    
    @pytest.mark.asyncio
    async def test_query_payment(self, client):
        """测试付款单查询 API"""
        response = await client.post("/api/v1/smart-query/query", json={
            "query": "本周 最高金额的付款单",
            "context": {}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
    
    @pytest.mark.asyncio
    async def test_get_suggested_questions(self, client):
        """测试获取推荐问题 API"""
        response = await client.get("/api/v1/smart-query/suggested-questions")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) > 0


# ============  性能测试  ============
class TestPerformance:
    """测试性能"""
    
    @pytest.mark.asyncio
    async def test_response_time(self, client):
        """测试响应时间"""
        import time
        
        start = time.time()
        response = await client.post("/api/v1/smart-query/query", json={
            "query": "显示本周销售趋势",
            "context": {}
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Response time {elapsed}s exceeds 2s limit"
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, client):
        """测试并发查询"""
        import asyncio
        
        queries = [
            "显示本周销售趋势",
            "查询库存状态",
            "统计各产品销售额",
            "查询 Top 10 客户",
            "本周 最高金额的付款单"
        ]
        
        tasks = [
            client.post("/api/v1/smart-query/query", json={
                "query": q,
                "context": {}
            })
            for q in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        for response in results:
            assert response.status_code == 200
            assert response.json()["success"] is True


# ============  缓存测试  ============
class TestCache:
    """测试缓存功能"""
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, session_manager):
        """测试缓存命中"""
        query = "显示本周销售趋势"
        
        # 第一次查询
        result1 = await session_manager.send_query(query)
        
        # 第二次查询（应该命中缓存）
        result2 = await session_manager.send_query(query)
        
        # 验证结果相同
        assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_cache_different_queries(self, session_manager):
        """测试不同查询不共享缓存"""
        query1 = "显示本周销售趋势"
        query2 = "查询库存状态"
        
        result1 = await session_manager.send_query(query1)
        result2 = await session_manager.send_query(query2)
        
        assert result1["data_type"] == "chart"
        assert result2["data_type"] == "table"


# ============  数据生成测试  ============
class TestDataGeneration:
    """测试数据生成"""
    
    @pytest.mark.asyncio
    async def test_chart_data_structure(self, session_manager):
        """测试图表数据结构"""
        result = await session_manager._smart_response("显示本周销售趋势")
        
        assert "chart_config" in result
        chart = result["chart_config"]
        
        # 验证 ECharts 配置结构
        assert "xAxis" in chart
        assert "yAxis" in chart
        assert "series" in chart
        assert len(chart["series"]) > 0
    
    @pytest.mark.asyncio
    async def test_table_data_structure(self, session_manager):
        """测试表格数据结构"""
        result = await session_manager._smart_response("查询库存状态")
        
        assert "data" in result
        data = result["data"]
        
        # 验证表格结构
        assert "columns" in data
        assert "rows" in data
        assert isinstance(data["columns"], list)
        assert isinstance(data["rows"], list)
        assert len(data["rows"]) > 0
    
    @pytest.mark.asyncio
    async def test_stats_data_structure(self, session_manager):
        """测试统计数据结构"""
        result = await session_manager._smart_response("统计各产品销售额")
        
        assert "data" in result
        data = result["data"]
        
        # 验证统计结构
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
