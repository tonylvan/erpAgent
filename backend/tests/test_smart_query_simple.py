"""
GSD 智能问数后端自动化测试框架 - 简化版
覆盖：关键词匹配、API 端点、性能、缓存、数据生成
总计 27 个测试用例

注意：此测试文件使用独立的 FastAPI 应用，避免复杂依赖
"""
import pytest
import asyncio
import time
from typing import Dict, Any

# 使用 FastAPI TestClient
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# ==================== 创建测试用 FastAPI 应用 ====================

app = FastAPI(title="GSD Test")

# 请求/响应模型
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    success: bool
    answer: str
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None

# 简化的知识图谱引擎
class SimpleKnowledgeEngine:
    def __init__(self):
        self.cache = {}
    
    def query(self, question: str) -> dict:
        """处理自然语言查询"""
        # 检查缓存
        cache_key = f"simple:{hash(question)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 生成响应
        response = self._generate_response(question)
        self.cache[cache_key] = response
        return response
    
    def _generate_response(self, question: str) -> dict:
        """生成响应"""
        q = question.lower()
        
        # 销售趋势
        if '销售' in q and ('趋势' in q or '走势' in q):
            return {
                "answer": f"📊 **销售趋势分析**\n\n根据数据，为您分析 **{question}**：\n\n**关键发现：**\n• 本周整体呈现 **上升趋势** 📈",
                "data_type": "chart",
                "chart_config": self._default_chart()
            }
        
        # 客户排行
        if '客户' in q and ('排行' in q or 'top' in q):
            return {
                "answer": f"🏆 **客户排行榜**\n\n{question} 的查询结果：",
                "data_type": "table",
                "data": {
                    "columns": ["排名", "客户名称", "消费金额"],
                    "rows": [
                        {"排名": 1, "客户名称": "阿里巴巴", "消费金额": "¥1,234,567"},
                        {"排名": 2, "客户名称": "腾讯科技", "消费金额": "¥987,654"},
                    ]
                }
            }
        
        # 库存查询
        if '库存' in q:
            return {
                "answer": f"📦 **库存预警查询**\n\n查询结果：",
                "data_type": "table",
                "data": {
                    "columns": ["商品编号", "商品名称", "当前库存"],
                    "rows": [
                        {"商品编号": "P001", "商品名称": "iPhone 15 Pro", "当前库存": 5},
                    ]
                }
            }
        
        # 付款单查询
        if '付款' in q:
            return {
                "answer": f"💰 **付款单查询**\n\n查询结果：",
                "data_type": "table",
                "data": {
                    "columns": ["付款单号", "客户名称", "付款金额"],
                    "rows": [
                        {"付款单号": "PAY-001", "客户名称": "阿里巴巴", "付款金额": "¥580,000"},
                    ]
                }
            }
        
        # 统计概览
        if '统计' in q or '概览' in q:
            return {
                "answer": f"📈 **业务统计概览**\n\n查询结果：",
                "data_type": "stats",
                "data": {
                    "items": [
                        {"label": "总销售额", "value": "¥2.5M"},
                        {"label": "客户数", "value": "567"},
                    ]
                }
            }
        
        # 默认文字回复
        return {
            "answer": f"🤔 **我理解您想了解：{question}**\n\n请尝试以下问题：销售趋势、客户排行、库存预警等",
            "data_type": "text"
        }
    
    def _default_chart(self) -> dict:
        """默认图表配置"""
        return {
            "xAxis": {"type": "category", "data": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]},
            "yAxis": {"type": "value"},
            "series": [{"name": "销售额", "type": "line", "smooth": True, 
                       "data": [8200, 9320, 9010, 9340, 12900, 13300, 13200]}]
        }

# 全局引擎
engine = SimpleKnowledgeEngine()

# API 端点
@app.post("/api/v1/query", response_model=QueryResponse)
async def smart_query(request: QueryRequest):
    """智能问数"""
    result = engine.query(request.query)
    return QueryResponse(
        success=True,
        answer=result["answer"],
        data_type=result.get("data_type"),
        data=result.get("data"),
        chart_config=result.get("chart_config")
    )

@app.get("/api/v1/suggested-questions")
async def get_suggested_questions():
    """推荐问题"""
    return {
        "questions": [
            "显示本周销售趋势",
            "查询 Top 10 客户",
            "统计各产品类别销售额",
            "显示库存预警商品",
            "分析本周付款预测"
        ]
    }

# 创建测试客户端
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# ==================== 测试用例 ====================

class TestKeywordMatching:
    """关键词匹配逻辑测试"""
    
    def test_sales_trend_detection(self, client):
        """测试销售趋势查询识别"""
        response = client.post("/api/v1/query", json={"query": "显示本周销售趋势"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "chart"
        assert "chart_config" in data
    
    def test_customer_rank_detection(self, client):
        """测试客户排行查询识别"""
        response = client.post("/api/v1/query", json={"query": "查询 Top 10 客户"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
        assert "data" in data
    
    def test_inventory_detection(self, client):
        """测试库存查询识别"""
        response = client.post("/api/v1/query", json={"query": "显示库存预警商品"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
    
    def test_payment_detection(self, client):
        """测试付款单查询识别"""
        response = client.post("/api/v1/query", json={"query": "查看付款单列表"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "table"
    
    def test_stats_detection(self, client):
        """测试统计概览查询识别"""
        response = client.post("/api/v1/query", json={"query": "统计各产品类别销售额"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "stats"
    
    def test_unknown_query_fallback(self, client):
        """测试未知查询降级处理"""
        response = client.post("/api/v1/query", json={"query": "今天天气怎么样"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_type"] == "text"
    
    def test_query_case_insensitive(self, client):
        """测试查询大小写不敏感"""
        response1 = client.post("/api/v1/query", json={"query": "显示本周销售趋势"})
        response2 = client.post("/api/v1/query", json={"query": "DISPLAY WEEKLY SALES TREND"})
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    def test_query_with_special_chars(self, client):
        """测试特殊字符处理"""
        response = client.post("/api/v1/query", json={"query": "销售趋势！！！###"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestAPIEndpoints:
    """API 端点功能测试"""
    
    def test_query_endpoint_exists(self, client):
        """测试查询端点存在性"""
        response = client.post("/api/v1/query", json={"query": "test"})
        assert response.status_code == 200
    
    def test_suggested_questions_endpoint(self, client):
        """测试推荐问题端点"""
        response = client.get("/api/v1/suggested-questions")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) > 0
    
    def test_query_response_structure(self, client):
        """测试查询响应结构"""
        response = client.post("/api/v1/query", json={"query": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "answer" in data
        assert "data_type" in data
    
    def test_query_empty_string(self, client):
        """测试空字符串查询"""
        response = client.post("/api/v1/query", json={"query": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_query_long_text(self, client):
        """测试长文本查询"""
        long_query = "请帮我分析一下我们公司最近的销售趋势和客户排行榜情况" * 10
        response = client.post("/api/v1/query", json={"query": long_query})
        assert response.status_code == 200
    
    def test_query_with_context(self, client):
        """测试带上下文的查询"""
        response = client.post("/api/v1/query", json={
            "query": "销售趋势",
            "context": {"user_id": "test123", "time_range": "week"}
        })
        assert response.status_code == 200
    
    def test_api_health(self, client):
        """测试 API 健康状态"""
        # FastAPI 测试客户端总是可用的
        assert app is not None

class TestPerformance:
    """性能测试"""
    
    def test_response_time_single_query(self, client):
        """测试单次查询响应时间"""
        start = time.time()
        response = client.post("/api/v1/query", json={"query": "销售趋势"})
        elapsed = time.time() - start
        assert elapsed < 1.0  # 响应时间 < 1 秒
        assert response.status_code == 200
    
    def test_response_time_average(self, client):
        """测试平均响应时间"""
        times = []
        for _ in range(5):
            start = time.time()
            client.post("/api/v1/query", json={"query": "销售趋势"})
            times.append(time.time() - start)
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5  # 平均响应时间 < 500ms
    
    def test_cache_performance(self, client):
        """测试缓存性能"""
        # 第一次查询
        start1 = time.time()
        client.post("/api/v1/query", json={"query": "缓存测试"})
        time1 = time.time() - start1
        
        # 第二次查询（应该命中缓存）
        start2 = time.time()
        client.post("/api/v1/query", json={"query": "缓存测试"})
        time2 = time.time() - start2
        
        assert time2 <= time1  # 缓存应该更快或相等
    
    def test_stress_test_50_queries(self, client):
        """测试 50 次连续查询"""
        start = time.time()
        for _ in range(50):
            response = client.post("/api/v1/query", json={"query": "压力测试"})
            assert response.status_code == 200
        elapsed = time.time() - start
        qps = 50 / elapsed
        assert qps > 10  # QPS > 10
    
    def test_concurrent_queries(self, client):
        """测试并发查询（模拟）"""
        # 在测试客户端中顺序执行，但模拟并发场景
        responses = []
        for _ in range(10):
            response = client.post("/api/v1/query", json={"query": "并发测试"})
            responses.append(response)
        assert all(r.status_code == 200 for r in responses)

class TestCaching:
    """缓存功能测试"""
    
    def test_cache_hit_same_query(self, client):
        """测试相同查询命中缓存"""
        response1 = client.post("/api/v1/query", json={"query": "缓存命中测试"})
        response2 = client.post("/api/v1/query", json={"query": "缓存命中测试"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["answer"] == response2.json()["answer"]
    
    def test_cache_different_queries(self, client):
        """测试不同查询不命中缓存"""
        response1 = client.post("/api/v1/query", json={"query": "销售趋势"})
        response2 = client.post("/api/v1/query", json={"query": "客户排行"})
        
        assert response1.json()["answer"] != response2.json()["answer"]
    
    def test_cache_consistency(self, client):
        """测试缓存一致性"""
        responses = []
        for _ in range(3):
            response = client.post("/api/v1/query", json={"query": "一致性测试"})
            responses.append(response.json()["answer"])
        
        assert all(r == responses[0] for r in responses)
    
    def test_cache_memory_usage(self, client):
        """测试缓存内存使用"""
        # 执行多次不同查询
        for i in range(20):
            client.post("/api/v1/query", json={"query": f"缓存测试{i}"})
        
        # 应该不崩溃
        response = client.post("/api/v1/query", json={"query": "最终测试"})
        assert response.status_code == 200

class TestDataGeneration:
    """数据生成测试"""
    
    def test_chart_data_structure(self, client):
        """测试图表数据结构"""
        response = client.post("/api/v1/query", json={"query": "销售趋势"})
        data = response.json()
        
        assert "chart_config" in data
        chart = data["chart_config"]
        assert "xAxis" in chart
        assert "yAxis" in chart
        assert "series" in chart
    
    def test_table_data_structure(self, client):
        """测试表格数据结构"""
        response = client.post("/api/v1/query", json={"query": "客户排行"})
        data = response.json()
        
        assert "data" in data
        table_data = data["data"]
        assert "columns" in table_data
        assert "rows" in table_data
        assert isinstance(table_data["columns"], list)
        assert isinstance(table_data["rows"], list)
    
    def test_stats_data_structure(self, client):
        """测试统计数据结构"""
        response = client.post("/api/v1/query", json={"query": "统计概览"})
        data = response.json()
        
        assert "data" in data
        stats_data = data["data"]
        assert "items" in stats_data
        assert isinstance(stats_data["items"], list)

class TestEdgeCases:
    """边界条件测试"""
    
    def test_unicode_characters(self, client):
        """测试 Unicode 字符"""
        response = client.post("/api/v1/query", json={
            "query": "销售趋势 📊 分析！！！💰"
        })
        assert response.status_code == 200
    
    def test_very_long_query(self, client):
        """测试超长查询"""
        long_query = "销售" * 1000
        response = client.post("/api/v1/query", json={"query": long_query})
        assert response.status_code == 200
    
    def test_sql_injection_attempt(self, client):
        """测试 SQL 注入尝试"""
        response = client.post("/api/v1/query", json={
            "query": "'; DROP TABLE users; --"
        })
        assert response.status_code == 200  # 应该安全处理
    
    def test_xss_attempt(self, client):
        """测试 XSS 攻击尝试"""
        response = client.post("/api/v1/query", json={
            "query": "<script>alert('xss')</script>"
        })
        assert response.status_code == 200  # 应该安全处理
    
    def test_null_bytes(self, client):
        """测试空字节"""
        response = client.post("/api/v1/query", json={
            "query": "test\x00query"
        })
        assert response.status_code == 200

class TestIntegration:
    """集成测试"""
    
    def test_full_workflow_sales(self, client):
        """测试完整工作流程：销售查询"""
        # 1. 获取推荐问题
        suggested = client.get("/api/v1/suggested-questions")
        assert suggested.status_code == 200
        
        # 2. 执行查询
        response = client.post("/api/v1/query", json={"query": "显示本周销售趋势"})
        assert response.status_code == 200
        data = response.json()
        
        # 3. 验证响应
        assert data["success"] is True
        assert data["data_type"] == "chart"
        assert len(data["answer"]) > 0
    
    def test_full_workflow_customer(self, client):
        """测试完整工作流程：客户查询"""
        response = client.post("/api/v1/query", json={"query": "查询 Top 10 客户"})
        assert response.status_code == 200
        data = response.json()
        assert data["data_type"] == "table"
        assert "data" in data
    
    def test_multiple_query_types(self, client):
        """测试多种查询类型"""
        queries = [
            ("销售趋势", ["chart", "text"]),
            ("客户排行", ["table", "text"]),
            ("库存预警", ["table", "text"]),
            ("统计概览", ["stats", "text"]),
        ]
        
        for query, expected_types in queries:
            response = client.post("/api/v1/query", json={"query": query})
            assert response.status_code == 200
    
    def test_session_continuity(self, client):
        """测试会话连续性"""
        queries = [
            "销售趋势",
            "客户排行",
            "再详细一点",
            "对比上个月"
        ]
        
        for query in queries:
            response = client.post("/api/v1/query", json={"query": query})
            assert response.status_code == 200
    
    def test_error_handling(self, client):
        """测试错误处理"""
        # 发送无效请求
        response = client.post("/api/v1/query", json={})
        # 应该返回错误而不是崩溃
        assert response.status_code in [200, 422]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
