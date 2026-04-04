"""
GSD 智能问数后端 API v2.5 - 模拟数据版
- 使用模拟数据返回 ERP 查询结果
- 保留 Redis 缓存和降级机制
- 后续可集成 OpenClaw Gateway HTTP API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import sys
import re
import hashlib
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.redis_cache import cache

router = APIRouter(tags=["智能问数 v2.5"])


class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    answer: str
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None


class SmartQueryEngine:
    """智能问数引擎 - 模拟数据版"""
    
    def __init__(self):
        self.cache = cache
        self.memory_cache = {}
    
    async def query(self, question: str) -> dict:
        """处理查询 - 使用模拟数据"""
        cache_key = f"gsd:query:{hashlib.md5(question.encode()).hexdigest()}"
        
        cached = self.cache.get(cache_key)
        if cached:
            print(f"[CACHE] Redis 命中：{question}")
            return cached
        
        if cache_key in self.memory_cache:
            print(f"[CACHE] 内存命中：{question}")
            return self.memory_cache[cache_key]
        
        print(f"[Engine] 查询：{question}")
        response = self._generate_response(question)
        
        if self.cache.enabled:
            self.cache.set(cache_key, response, expire=3600)
        else:
            self.memory_cache[cache_key] = response
        
        if len(self.memory_cache) > 1000:
            self.memory_cache.pop(next(iter(self.memory_cache)))
        
        return response
    
    def _generate_response(self, question: str) -> dict:
        """生成模拟响应 - 基于关键词匹配"""
        q = question.lower()
        
        # 库存查询
        if '库存' in q or '预警' in q:
            return {
                "answer": f"""【库存状态分析】

为您查询到当前库存情况（数据日期：2026-04-04）：

【库存概览】
- 总 SKU 数：1,234 个
- 库存充足：892 个 (72.3%)
- 库存预警：89 个 (7.2%)
- 库存短缺：23 个 (1.9%)

【需要关注的品类】
1. 电子产品 - 3 款商品库存紧张
2. 家居用品 - 2 款商品需要补货

详细清单如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["商品编号", "商品名称", "当前库存", "预警阈值", "状态"],
                    "rows": [
                        {"商品编号": "P001", "商品名称": "iPhone 15 Pro", "当前库存": 5, "预警阈值": 10, "状态": "紧急"},
                        {"商品编号": "P002", "商品名称": "MacBook Pro 14", "当前库存": 8, "预警阈值": 10, "状态": "紧急"},
                        {"商品编号": "P003", "商品名称": "AirPods Pro", "当前库存": 12, "预警阈值": 15, "状态": "预警"},
                        {"商品编号": "P004", "商品名称": "iPad Air", "当前库存": 18, "预警阈值": 20, "状态": "预警"},
                        {"商品编号": "P005", "商品名称": "Apple Watch", "当前库存": 25, "预警阈值": 30, "状态": "预警"},
                    ]
                },
                "follow_up": ["生成补货订单", "查看历史库存趋势", "优化库存周转率"]
            }
        
        # 付款单查询
        if '付款' in q or '付款单' in q:
            return {
                "answer": f"""【付款单查询结果】

为您查询到最近 7 天的付款记录（数据日期：2026-04-04）：

【付款概览】
- 总付款金额：¥1,890,000
- 已完成：5 笔
- 处理中：1 笔
- 已取消：0 笔

详细记录如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["付款单号", "客户名称", "付款金额", "付款日期", "状态"],
                    "rows": [
                        {"付款单号": "PAY-2026040401", "客户名称": "阿里巴巴", "付款金额": "¥580,000", "付款日期": "2026-04-04", "状态": "已完成"},
                        {"付款单号": "PAY-2026040301", "客户名称": "腾讯科技", "付款金额": "¥450,000", "付款日期": "2026-04-03", "状态": "已完成"},
                        {"付款单号": "PAY-2026040201", "客户名称": "华为技术", "付款金额": "¥380,000", "付款日期": "2026-04-02", "状态": "已完成"},
                        {"付款单号": "PAY-2026040101", "客户名称": "小米科技", "付款金额": "¥290,000", "付款日期": "2026-04-01", "状态": "已完成"},
                        {"付款单号": "PAY-2026033101", "客户名称": "字节跳动", "付款金额": "¥190,000", "付款日期": "2026-03-31", "状态": "处理中"},
                    ]
                },
                "follow_up": ["查看未完成付款单", "分析付款趋势", "导出付款报表"]
            }
        
        # 客户排行
        if any(kw in q for kw in ['排行', 'top', '排名', '客户列表']):
            limit_match = re.search(r'top\s*(\d+)|(\d+) 强', q)
            limit = int(limit_match.group(1) or limit_match.group(2) or 10)
            
            return {
                "answer": f"""【客户价值排行榜 Top {limit}】

为您查询到客户消费排行（数据日期：2026-04-04）：

【排行概览】
- 总客户数：156 家
- 活跃客户：89 家
- 本月新增：12 家

详细排行如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["排名", "客户名称", "消费金额", "订单数", "平均客单价"],
                    "rows": [
                        {"排名": 1, "客户名称": "阿里巴巴", "消费金额": "¥2,580,000", "订单数": 45, "平均客单价": "¥57,333"},
                        {"排名": 2, "客户名称": "腾讯科技", "消费金额": "¥2,150,000", "订单数": 38, "平均客单价": "¥56,579"},
                        {"排名": 3, "客户名称": "华为技术", "消费金额": "¥1,890,000", "订单数": 32, "平均客单价": "¥59,063"},
                        {"排名": 4, "客户名称": "小米科技", "消费金额": "¥1,650,000", "订单数": 29, "平均客单价": "¥56,897"},
                        {"排名": 5, "客户名称": "字节跳动", "消费金额": "¥1,420,000", "订单数": 25, "平均客单价": "¥56,800"},
                        {"排名": 6, "客户名称": "百度在线", "消费金额": "¥1,280,000", "订单数": 22, "平均客单价": "¥58,182"},
                        {"排名": 7, "客户名称": "京东世纪", "消费金额": "¥1,150,000", "订单数": 20, "平均客单价": "¥57,500"},
                        {"排名": 8, "客户名称": "美团点评", "消费金额": "¥980,000", "订单数": 18, "平均客单价": "¥54,444"},
                        {"排名": 9, "客户名称": "滴滴出行", "消费金额": "¥850,000", "订单数": 15, "平均客单价": "¥56,667"},
                        {"排名": 10, "客户名称": "拼多多", "消费金额": "¥720,000", "订单数": 13, "平均客单价": "¥55,385"},
                    ][:limit]
                },
                "follow_up": ["查看客户详情", "分析客户行业分布", "导出客户报表"]
            }
        
        # 销售趋势
        if '销售' in q and ('趋势' in q or '走势' in q):
            return {
                "answer": f"""【本周销售趋势分析】

为您查询到本周（2026-03-29 至 2026-04-04）的销售数据：

【趋势概览】
- 本周总销售额：¥8,950,000
- 环比上周：+12.5% ↑
- 日均销售额：¥1,278,571

【趋势分析】
本周销售呈现上升趋势，周三和周五达到峰值。""",
                "data_type": "chart",
                "chart_config": {
                    "type": "line",
                    "title": "本周销售趋势",
                    "xAxis": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                    "yAxis": [980000, 1150000, 1580000, 1250000, 1680000, 1320000, 990000],
                    "xName": "日期",
                    "yName": "销售额 (元)"
                },
                "follow_up": ["查看月度销售趋势", "分析销售品类占比", "导出销售报表"]
            }
        
        # 财务概览
        if any(kw in q for kw in ['财务', '指标', '概览', '统计']):
            return {
                "answer": f"""【财务关键指标概览】

为您查询到当前财务数据（数据日期：2026-04-04）：

【核心指标】
- 本月营收：¥28,500,000
- 本月支出：¥19,200,000
- 净利润：¥9,300,000
- 净利率：32.6%

【现金流】
- 现金余额：¥45,800,000
- 应收账款：¥12,300,000
- 应付账款：¥8,900,000""",
                "data_type": "stats",
                "data": {
                    "items": [
                        {"label": "本月营收", "value": "¥28,500,000", "trend": "+8.5%"},
                        {"label": "本月支出", "value": "¥19,200,000", "trend": "+3.2%"},
                        {"label": "净利润", "value": "¥9,300,000", "trend": "+21.5%"},
                        {"label": "净利率", "value": "32.6%", "trend": "+3.8%"},
                        {"label": "现金余额", "value": "¥45,800,000", "trend": "+5.2%"},
                        {"label": "应收账款", "value": "¥12,300,000", "trend": "-2.1%"},
                    ]
                },
                "follow_up": ["查看财务明细", "分析成本结构", "导出财务报表"]
            }
        
        # 员工查询
        if any(kw in q for kw in ['员工', '职员', '人力', 'hr', '人数']):
            return {
                "answer": f"""【ERP 员工统计】

为您查询到当前员工数据（数据日期：2026-04-04）：

【员工概览】
- 总员工数：1,256 人
- 正式员工：1,089 人 (86.7%)
- 试用期：98 人 (7.8%)
- 实习生：69 人 (5.5%)

【部门分布】
- 研发部：456 人 (36.3%)
- 销售部：312 人 (24.8%)
- 市场部：178 人 (14.2%)
- 财务部：89 人 (7.1%)
- 人力资源部：67 人 (5.3%)
- 其他：154 人 (12.3%)

详细清单如下：""",
                "data_type": "table",
                "data": {
                    "columns": ["部门", "正式员工", "试用期", "实习生", "合计"],
                    "rows": [
                        {"部门": "研发部", "正式员工": 398, "试用期": 38, "实习生": 20, "合计": 456},
                        {"部门": "销售部", "正式员工": 275, "试用期": 25, "实习生": 12, "合计": 312},
                        {"部门": "市场部", "正式员工": 156, "试用期": 15, "实习生": 7, "合计": 178},
                        {"部门": "财务部", "正式员工": 78, "试用期": 8, "实习生": 3, "合计": 89},
                        {"部门": "人力资源部", "正式员工": 59, "试用期": 5, "实习生": 3, "合计": 67},
                        {"部门": "运营部", "正式员工": 123, "试用期": 7, "实习生": 24, "合计": 154},
                    ]
                },
                "follow_up": ["查看部门详情", "分析员工流动率", "导出员工报表"]
            }
        
        # 默认响应
        return {
            "answer": f"""【智能问数助手】

我理解您想了解：{question}

目前我支持以下查询类型：

【销售分析】
- "显示本周销售趋势"
- "分析销售变化走势"

【客户洞察】
- "查询 Top 10 客户"
- "分析客户行业分布"

【库存管理】
- "显示库存预警商品"
- "生成补货建议"

【财务数据】
- "查看本周付款单"
- "统计月度收款"

请尝试以上问题！""",
            "data_type": "text",
            "follow_up": ["显示本周销售趋势", "查询 Top 10 客户", "显示库存预警商品"]
        }


# 全局引擎
query_engine = SmartQueryEngine()


@router.post("/query", response_model=QueryResponse)
async def smart_query(request: QueryRequest):
    """智能问数 v2.5"""
    try:
        result = await query_engine.query(request.query)
        return QueryResponse(
            success=True,
            answer=result["answer"],
            data_type=result.get("data_type"),
            data=result.get("data"),
            chart_config=result.get("chart_config"),
            follow_up=result.get("follow_up")
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


@router.get("/cache-stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    stats = cache.stats()
    return {
        "cache_enabled": stats.get("enabled", False),
        "redis_connected": stats.get("connected", False),
        "db_size": stats.get("db_size", 0),
        "total_commands": stats.get("total_commands_processed", 0),
        "cache_hits": stats.get("keyspace_hits", 0),
        "cache_misses": stats.get("keyspace_misses", 0),
        "hit_rate": f"{(stats.get('keyspace_hits', 0) / max(stats.get('keyspace_hits', 0) + stats.get('keyspace_misses', 1), 1)) * 100:.1f}%"
    }
