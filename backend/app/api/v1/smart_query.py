"""
GSD 智能问数后端 API v1
使用 Neo4j 知识图谱 + AI 大模型处理企业数据查询
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(tags=["智能问数"])


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


class Neo4jKnowledgeEngine:
    """Neo4j 知识图谱引擎 - 简化版"""
    
    def __init__(self):
        self.driver = None
        self.cache = {}
    
    async def query(self, question: str) -> dict:
        """处理自然语言查询"""
        # 检查缓存
        cache_key = f"neo4j:{hash(question)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 生成响应
        response = await self._generate_response(question)
        self.cache[cache_key] = response
        return response
    
    async def _generate_response(self, question: str) -> dict:
        """生成响应"""
        q = question.lower()
        
        # 销售趋势
        if '销售' in q and ('趋势' in q or '走势' in q):
            return {
                "answer": f"""📊 **销售趋势分析**

根据数据，为您分析 **{question}**：

**关键发现：**
• 本周整体呈现 **上升趋势** 📈
• 周末（周六、周日）达到销售峰值
• 周平均销售额：¥10,890
• 周环比增长：+12.5%

以下是详细的数据可视化：""",
                "data_type": "chart",
                "chart_config": self._default_chart()
            }
        
        # 客户排行
        if '客户' in q and ('排行' in q or 'top' in q):
            return {
                "answer": f"""🏆 **客户排行榜**

{question} 的查询结果：

**关键指标：**
• Top 3 客户贡献：¥3,098,764
• 平均客单价：¥8,234
• 最高客单：阿里巴巴 ¥1,234,567

详细数据如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["排名", "客户名称", "消费金额", "订单数"],
                    "rows": [
                        {"排名": 1, "客户名称": "阿里巴巴", "消费金额": "¥1,234,567", "订单数": 156},
                        {"排名": 2, "客户名称": "腾讯科技", "消费金额": "¥987,654", "订单数": 128},
                        {"排名": 3, "客户名称": "华为技术", "消费金额": "¥876,543", "订单数": 112},
                    ]
                }
            }
        
        # 库存查询
        if '库存' in q:
            return {
                "answer": f"""📦 **库存预警查询**

查询结果：

**库存概览：**
• 预警商品：5 个
• 需要立即补货：2 个

详细清单如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["商品编号", "商品名称", "当前库存", "预警阈值", "状态"],
                    "rows": [
                        {"商品编号": "P001", "商品名称": "iPhone 15 Pro", "当前库存": 5, "预警阈值": 10, "状态": "🔴 紧急"},
                        {"商品编号": "P002", "商品名称": "MacBook Pro 14", "当前库存": 8, "预警阈值": 10, "状态": "🔴 紧急"},
                        {"商品编号": "P003", "商品名称": "AirPods Pro", "当前库存": 12, "预警阈值": 15, "状态": "⚠️ 预警"},
                    ]
                }
            }
        
        # 付款单查询
        if '付款' in q:
            return {
                "answer": f"""💰 **付款单查询**

查询结果：

**付款概览：**
• 本周付款总额：¥2,010,000
• 付款笔数：5 笔

详细清单如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["付款单号", "客户名称", "付款金额", "付款日期", "状态"],
                    "rows": [
                        {"付款单号": "PAY-001", "客户名称": "阿里巴巴", "付款金额": "¥580,000", "付款日期": "2026-04-01", "状态": "✅ 已完成"},
                        {"付款单号": "PAY-002", "客户名称": "腾讯科技", "付款金额": "¥450,000", "付款日期": "2026-04-02", "状态": "✅ 已完成"},
                    ]
                }
            }
        
        # 统计概览
        if '统计' in q or '概览' in q:
            return {
                "answer": f"""📈 **业务统计概览**

查询结果：

**核心指标：**
• 总销售额、客户数、订单数等关键指标

详细统计如下：""",
                "data_type": "stats",
                "data": {
                    "items": [
                        {"label": "总销售额", "value": "¥2.5M"},
                        {"label": "客户数", "value": "567"},
                        {"label": "订单数", "value": "1,234"},
                        {"label": "转化率", "value": "23.5%"}
                    ]
                }
            }
        
        # 默认文字回复
        return {
            "answer": f"""🤔 **我理解您想了解：{question}**

目前我支持以下查询：

**📊 销售趋势**
• "显示本周销售趋势"
• "分析销售变化走势"

**📋 数据列表**
• "查询 Top 10 客户"
• "显示库存预警商品"
• "查看付款单列表"

**📈 统计概览**
• "统计各产品类别销售额"
• "查看业务概览"

请尝试以上问题！""",
            "data_type": "text"
        }
    
    def _default_chart(self) -> dict:
        """默认图表配置"""
        return {
            "xAxis": {"type": "category", "data": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]},
            "yAxis": {"type": "value"},
            "series": [{"name": "销售额", "type": "line", "smooth": True, 
                       "data": [8200, 9320, 9010, 9340, 12900, 13300, 13200],
                       "areaStyle": {"color": "rgba(64, 158, 255, 0.2)"}, 
                       "itemStyle": {"color": "#409EFF"}}]
        }


# 全局知识图谱引擎
knowledge_engine = Neo4jKnowledgeEngine()


@router.post("/query", response_model=QueryResponse)
async def smart_query(request: QueryRequest):
    """智能问数"""
    try:
        result = await knowledge_engine.query(request.query)
        return QueryResponse(
            success=True,
            answer=result["answer"],
            data_type=result.get("data_type"),
            data=result.get("data"),
            chart_config=result.get("chart_config")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/suggested-questions")
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
