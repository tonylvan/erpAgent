"""
GSD 智能问数 - Agent 深度分析模块
使用 OpenClaw sessions_spawn 启动 GLM5 agent 进行复杂查询分析
"""
import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class SmartQueryAgent:
    """智能问数 Agent 封装 - 使用 OpenClaw sessions_spawn"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENCLAW_API_KEY', '')
        self.base_url = os.getenv('OPENCLAW_BASE_URL', 'http://localhost:8080')
        
    async def analyze_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        使用 OpenClaw Agent 进行深度分析
        
        Args:
            query: 用户查询
            context: 上下文信息（历史对话、业务背景等）
            
        Returns:
            分析结果：包含回答、数据类型、图表配置、追问建议
        """
        try:
            # 构建 agent 任务提示
            prompt = self._build_prompt(query, context)
            
            # 使用 OpenClaw sessions_spawn 启动 agent
            # 注意：这里需要通过 OpenClaw CLI 或 API 调用
            result = await self._spawn_agent(prompt)
            
            # 解析 agent 响应
            return self._parse_result(result, query)
            
        except Exception as e:
            logger.error(f"Agent analysis failed: {e}")
            return {
                "success": False,
                "error": f"深度分析失败：{str(e)}",
                "fallback": True  # 标记需要降级到 NL2Cypher
            }
    
    def _build_prompt(self, query: str, context: Optional[Dict] = None) -> str:
        """构建 agent 提示词"""
        
        context_info = ""
        if context:
            if context.get('history'):
                context_info += f"\n历史对话：{json.dumps(context['history'], ensure_ascii=False)}"
            if context.get('business_context'):
                context_info += f"\n业务背景：{context['business_context']}"
        
        prompt = f"""你是一个 ERP 数据分析专家，基于 Neo4j 知识图谱进行智能查询。

## 用户查询
{query}
{context_info}

## 任务要求
1. **理解意图** - 识别用户想查询的业务领域（销售/采购/库存/财务/客户）
2. **生成 Cypher** - 根据 Neo4j 图谱结构生成查询语句
3. **深度分析** - 不仅返回数据，还要提供：
   - 业务洞察（趋势、异常、机会）
   - 风险预警（潜在问题）
   - 行动建议（具体可执行的建议）
4. **推荐追问** - 基于当前查询推荐 3 个相关问题

## Neo4j 图谱结构
- 节点类型：Company, Customer, Product, SalesOrder, PurchaseOrder, Inventory, Invoice, Payment
- 关系类型：PURCHASED_FROM, SOLD_TO, CONTAINS, SUPPLIES, OWES, PAID

## 输出格式
请严格按以下 JSON 格式返回：
```json
{{
  "intent": "销售分析",
  "cypher": "MATCH (c:Customer)-[:PURCHASED_FROM]->(o:SalesOrder)...",
  "analysis": "深度业务分析文本（支持 Markdown）",
  "data_type": "chart|table|stats|text",
  "chart_config": {{ "type": "bar", "xField": "customer", "yField": "amount" }},
  "follow_up": ["问题 1", "问题 2", "问题 3"]
}}
```

开始分析："""
        
        return prompt
    
    async def _spawn_agent(self, prompt: str) -> str:
        """
        使用 OpenClaw sessions_spawn 启动 agent
        
        实际实现需要通过 OpenClaw CLI:
        openclaw sessions_spawn --task="{prompt}" --model="dashscope/glm-5"
        
        或使用 Python SDK（如果有）
        """
        # TODO: 实现 OpenClaw sessions_spawn 调用
        # 这里提供两种方案：
        
        # 方案 1: 使用 subprocess 调用 OpenClaw CLI
        # import subprocess
        # result = subprocess.run(
        #     ['openclaw', 'sessions_spawn', '--task', prompt, '--model', 'dashscope/glm-5'],
        #     capture_output=True,
        #     text=True,
        #     timeout=30
        # )
        # return result.stdout
        
        # 方案 2: 使用 HTTP API（如果 OpenClaw 提供）
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         f'{self.base_url}/sessions_spawn',
        #         json={'task': prompt, 'model': 'dashscope/glm-5'}
        #     ) as resp:
        #         return await resp.text()
        
        # 临时降级方案：返回提示
        return json.dumps({
            "status": "pending",
            "message": "OpenClaw sessions_spawn 待集成",
            "prompt": prompt
        }, ensure_ascii=False)
    
    def _parse_result(self, result: str, original_query: str) -> Dict[str, Any]:
        """解析 agent 响应"""
        try:
            data = json.loads(result)
            
            return {
                "success": True,
                "answer": data.get('analysis', '分析完成'),
                "data_type": data.get('data_type', 'text'),
                "chart_config": data.get('chart_config'),
                "cypher": data.get('cypher', ''),
                "follow_up": data.get('follow_up', []),
                "intent": data.get('intent', 'general'),
                "source": 'agent'  # 标记来自 agent
            }
        except json.JSONDecodeError:
            # 如果不是 JSON，当作纯文本处理
            return {
                "success": True,
                "answer": result,
                "data_type": 'text',
                "source": 'agent'
            }


# 查询分类器
def classify_query(query: str) -> tuple:
    """
    分类查询：决定使用 NL2Cypher 还是 Agent
    
    Returns:
        (query_type, confidence)
        - "simple": 简单查询，用 NL2Cypher
        - "complex": 复杂分析，用 Agent
    """
    
    # 简单查询关键词
    simple_keywords = [
        '多少', '几个', '哪些', '列表', '排行', 'top',
        '统计', '汇总', '合计', '总数', '平均'
    ]
    
    # 复杂分析关键词
    complex_keywords = [
        '分析', '为什么', '原因', '趋势', '预测',
        '建议', '如何', '策略', '影响', '评估',
        '对比', '差异', '异常', '风险', '机会'
    ]
    
    query_lower = query.lower()
    
    # 计算匹配度
    simple_score = sum(1 for kw in simple_keywords if kw in query_lower)
    complex_score = sum(1 for kw in complex_keywords if kw in query_lower)
    
    if complex_score > simple_score and complex_score >= 2:
        return "complex", 0.8
    elif simple_score > complex_score:
        return "simple", 0.9
    else:
        # 默认使用 NL2Cypher（快速通道）
        return "simple", 0.6


# 全局实例
agent_instance = SmartQueryAgent()


# 统一的智能问数接口
async def smart_query(query: str, context: Optional[Dict] = None, use_agent: bool = False) -> Dict[str, Any]:
    """
    智能问数统一接口
    
    Args:
        query: 用户查询
        context: 上下文
        use_agent: 是否强制使用 Agent
        
    Returns:
        查询结果
    """
    
    if use_agent:
        # 强制使用 Agent
        return await agent_instance.analyze_query(query, context)
    
    # 自动分类
    query_type, confidence = classify_query(query)
    
    if query_type == "complex":
        # 复杂查询使用 Agent
        logger.info(f"Complex query detected: {query[:50]}...")
        return await agent_instance.analyze_query(query, context)
    else:
        # 简单查询使用 NL2Cypher（快速通道）
        logger.info(f"Simple query detected: {query[:50]}...")
        # TODO: 调用现有的 NL2Cypher 逻辑
        # from app.api.v1.smart_query_v2 import nl2cypher_query
        # return await nl2cypher_query(query, context)
        
        # 临时返回
        return {
            "success": True,
            "answer": f"[NL2Cypher 快速响应] {query}",
            "data_type": "text",
            "source": "nl2cypher"
        }
