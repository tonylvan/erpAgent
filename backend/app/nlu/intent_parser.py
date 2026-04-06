# -*- coding: utf-8 -*-
# NLU 引擎 - 自然语言理解模块
# 基于 DashScope LLM 实现意图识别和实体抽取
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re


class IntentType(str, Enum):
    """意图类型枚举"""
    QUERY_SALES = "QUERY_SALES"  # 销售查询
    QUERY_PURCHASE = "QUERY_PURCHASE"  # 采购查询
    QUERY_INVENTORY = "QUERY_INVENTORY"  # 库存查询
    QUERY_CUSTOMER = "QUERY_CUSTOMER"  # 客户查询
    QUERY_SUPPLIER = "QUERY_SUPPLIER"  # 供应商查询
    QUERY_FINANCE = "QUERY_FINANCE"  # 财务查询
    QUERY_RANKING = "QUERY_RANKING"  # 排名查询
    QUERY_TREND = "QUERY_TREND"  # 趋势分析
    QUERY_COMPARISON = "QUERY_COMPARISON"  # 对比分析
    QUERY_STATISTICS = "QUERY_STATISTICS"  # 统计查询
    UNKNOWN = "UNKNOWN"  # 未知意图


@dataclass
class Entity:
    """实体数据结构"""
    entity_type: str  # 实体类型 (时间/地区/产品/客户等)
    value: str  # 实体值
    original_text: str  # 原始文本
    confidence: float = 1.0  # 置信度


@dataclass
class QueryIntent:
    """查询意图结构"""
    intent_type: IntentType  # 意图类型
    entities: Dict[str, Any] = field(default_factory=dict)  # 实体字典
    time_range: Optional[Dict[str, str]] = None  # 时间范围
    region: Optional[str] = None  # 地区
    product: Optional[str] = None  # 产品
    customer: Optional[str] = None  # 客户
    supplier: Optional[str] = None  # 供应商
    metric: Optional[str] = None  # 指标 (销售额/数量等)
    dimension: Optional[str] = None  # 维度 (按日/月/年等)
    operation: Optional[str] = None  # 操作 (排名/汇总/平均等)
    limit: int = 100  # 返回数量限制
    raw_query: str = ""  # 原始查询


class NLUEngine:
    """NLU 引擎核心类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 NLU 引擎
        
        Args:
            api_key: DashScope API Key，如不提供则使用环境变量
        """
        self.api_key = api_key
        self._init_llm()
        
    def _init_llm(self):
        """初始化 LLM 模型"""
        try:
            import dashscope
            dashscope.api_key = self.api_key
            self.llm = dashscope.Generation()
            print("[+] DashScope LLM 初始化成功")
        except ImportError:
            print("⚠️ DashScope 未安装，使用规则匹配降级方案")
            self.llm = None
        except Exception as e:
            print(f"⚠️ DashScope 初始化失败：{e}，使用降级方案")
            self.llm = None
    
    def parse(self, query: str) -> QueryIntent:
        """
        解析用户查询
        
        Args:
            query: 用户输入的查询文本
            
        Returns:
            QueryIntent: 结构化查询意图
        """
        # 1. 使用 LLM 解析（如果可用）
        if self.llm:
            return self._parse_with_llm(query)
        
        # 2. 降级方案：规则匹配
        return self._parse_with_rules(query)
    
    def _parse_with_llm(self, query: str) -> QueryIntent:
        """使用 LLM 解析查询"""
        prompt = self._build_llm_prompt(query)
        
        try:
            response = self.llm.call(
                model='qwen-turbo',
                prompt=prompt,
                temperature=0.1,
                max_tokens=500
            )
            
            if response.status_code == 200:
                result_text = response.output.text
                return self._parse_llm_result(result_text, query)
            else:
                print(f"⚠️ LLM 调用失败：{response.code}")
                return self._parse_with_rules(query)
                
        except Exception as e:
            print(f"⚠️ LLM 解析异常：{e}，使用降级方案")
            return self._parse_with_rules(query)
    
    def _build_llm_prompt(self, query: str) -> str:
        """构建 LLM 提示词"""
        return f"""
你是一个 ERP 智能问数系统的 NLU 引擎。请分析用户查询并提取结构化信息。
用户查询：{query}

请提取以下信息并以 JSON 格式返回：{{
    "intent_type": "查询类型 (QUERY_SALES/QUERY_PURCHASE/QUERY_INVENTORY/QUERY_CUSTOMER/QUERY_SUPPLIER/QUERY_FINANCE/QUERY_RANKING/QUERY_TREND/QUERY_COMPARISON/QUERY_STATISTICS)",
    "time_range": {{"start": "开始时间", "end": "结束时间"}},
    "region": "地区",
    "product": "产品",
    "customer": "客户",
    "supplier": "供应商",
    "metric": "指标 (销售额/数量/利润等)",
    "dimension": "维度 (按日/月/年/地区/产品等)",
    "operation": "操作 (排名/汇总/平均/计数等)",
    "limit": 返回数量限制 (默认 100)
}}

时间表达转换规则：
- "本月" -> start: "2026-04-01", end: "2026-04-30"
- "上月" -> start: "2026-03-01", end: "2026-03-31"
- "本周" -> 本周一到周日
- "上周" -> 上周一到上周日
- "今年" -> start: "2026-01-01", end: "2026-12-31"
- "最近 7 天" -> 从今天往前推 7 天

只返回 JSON，不要其他内容。
"""
    
    def _parse_llm_result(self, result_text: str, raw_query: str) -> QueryIntent:
        """解析 LLM 返回结果"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group()
            
            data = json.loads(result_text)
            
            intent = QueryIntent(
                intent_type=IntentType(data.get('intent_type', 'UNKNOWN')),
                entities=data,
                time_range=data.get('time_range'),
                region=data.get('region'),
                product=data.get('product'),
                customer=data.get('customer'),
                supplier=data.get('supplier'),
                metric=data.get('metric'),
                dimension=data.get('dimension'),
                operation=data.get('operation'),
                limit=data.get('limit', 100),
                raw_query=raw_query
            )
            
            return intent
            
        except Exception as e:
            print(f"⚠️ 解析 LLM 结果失败：{e}")
            return self._parse_with_rules(raw_query)
    
    def _parse_with_rules(self, query: str) -> QueryIntent:
        """使用规则匹配解析查询（降级方案）"""
        query_lower = query.lower()
        
        # 1. 意图识别
        intent_type = self._match_intent(query_lower)
        
        # 2. 实体抽取
        entities = self._extract_entities(query)
        
        # 3. 构建意图
        intent = QueryIntent(
            intent_type=intent_type,
            entities=entities,
            time_range=entities.get('time_range'),
            region=entities.get('region'),
            product=entities.get('product'),
            customer=entities.get('customer'),
            supplier=entities.get('supplier'),
            metric=entities.get('metric'),
            dimension=entities.get('dimension'),
            operation=entities.get('operation'),
            limit=100,
            raw_query=query
        )
        
        return intent
    
    def _match_intent(self, query: str) -> IntentType:
        """匹配意图类型"""
        # 采购查询优先匹配（避免"采购订单"被误判为销售）
        if any(word in query for word in ['采购', '供应商', '进货']):
            return IntentType.QUERY_PURCHASE
        
        elif any(word in query for word in ['销售', '订单', '成交']):
            if any(word in query for word in ['排名', 'top', '最']):
                return IntentType.QUERY_RANKING
            elif any(word in query for word in ['趋势', '走势']):
                return IntentType.QUERY_TREND
            else:
                return IntentType.QUERY_SALES
        
        elif any(word in query for word in ['库存', '存货', '仓库']):
            return IntentType.QUERY_INVENTORY
        
        elif any(word in query for word in ['客户', '顾客']):
            return IntentType.QUERY_CUSTOMER
        
        elif any(word in query for word in ['财务', '付款', '应收', '应付']):
            return IntentType.QUERY_FINANCE
        
        elif any(word in query for word in ['对比', '比较']):
            return IntentType.QUERY_COMPARISON
        
        elif any(word in query for word in ['统计', '汇总', '总计']):
            return IntentType.QUERY_STATISTICS
        
        return IntentType.UNKNOWN
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """抽取实体"""
        entities = {}
        
        # 时间实体
        time_range = self._extract_time(query)
        if time_range:
            entities['time_range'] = time_range
        
        # 地区实体
        regions = ['华东', '华南', '华北', '华西', '东北', '西南', '西北']
        for region in regions:
            if region in query:
                entities['region'] = region
                break
        
        # 指标实体
        metrics = ['销售额', '销售金额', '金额', '数量', '利润', '成本']
        for metric in metrics:
            if metric in query:
                entities['metric'] = metric
                break
        
        # 操作实体
        operations = ['排名', 'top', '汇总', '统计', '平均', '计数']
        for op in operations:
            if op in query:
                entities['operation'] = op
                break
        
        return entities
    
    def _extract_time(self, query: str) -> Optional[Dict[str, str]]:
        """抽取时间范围"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        if '本月' in query:
            start = now.replace(day=1)
            if now.month == 12:
                end = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end = now.replace(month=now.month+1, day=1) - timedelta(days=1)
            return {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}
        
        elif '上月' in query:
            if now.month == 1:
                start = now.replace(year=now.year-1, month=12, day=1)
            else:
                start = now.replace(month=now.month-1, day=1)
            end = start.replace(day=1) + timedelta(days=31)
            end = end.replace(day=1) - timedelta(days=1)
            return {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}
        
        elif '本周' in query:
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(days=6)
            return {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}
        
        elif '上周' in query:
            start = now - timedelta(days=now.weekday() + 7)
            end = start + timedelta(days=6)
            return {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}
        
        elif '今年' in query:
            start = now.replace(month=1, day=1)
            end = now.replace(month=12, day=31)
            return {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}
        
        elif '最近' in query and '天' in query:
            match = re.search(r'最近 (\d+) 天', query)
            if match:
                days = int(match.group(1))
                end = now
                start = now - timedelta(days=days)
                return {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}
        
        return None


# 测试函数
def test_nlu():
    """测试 NLU 引擎"""
    print("=" * 60)
    print("NLU 引擎测试")
    print("=" * 60)
    
    engine = NLUEngine()
    
    test_cases = [
        "查询本月销售趋势",
        "显示 Top 10 客户排行",
        "华东区上月销售额统计",
        "库存预警商品有哪些",
        "对比各产品类别销售额",
        "最近 7 天采购订单汇总",
    ]
    
    for query in test_cases:
        print(f"\n查询：{query}")
        intent = engine.parse(query)
        print(f"意图：{intent.intent_type.value}")
        print(f"地区：{intent.region}")
        print(f"指标：{intent.metric}")
        print(f"操作：{intent.operation}")
        print(f"时间：{intent.time_range}")


if __name__ == '__main__':
    test_nlu()
