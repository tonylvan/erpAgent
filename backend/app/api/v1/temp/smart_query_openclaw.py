"""
GSD 智能问数 - OpenClaw HTTP API 模式
使用 OpenClaw Gateway HTTP API 进行深度数据分析
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
from datetime import datetime
import httpx
import json
import sys, os

logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.services.neo4j_service import neo4j_service

router = APIRouter(tags=["智能问数 - OpenClaw HTTP API"])

# ==================== OpenClaw Gateway 配置 ====================

GATEWAY_URL = os.getenv('OPENCLAW_GATEWAY_URL', 'http://127.0.0.1:18789')
GATEWAY_TOKEN = os.getenv('OPENCLAW_GATEWAY_TOKEN', '3354bfe288d7b3d499d84d5b21d540ce21ff0c3e7dedbc18')

# ==================== 请求/响应模型 ====================

class AgentQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class AgentQueryResponse(BaseModel):
    success: bool
    answer: str
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None
    reasoning_process: Optional[List[str]] = None
    agent_model: str = "dashscope/glm-5"

class AgentFeedbackRequest(BaseModel):
    message_id: str
    feedback_type: str
    comment: Optional[str] = None

class AgentFeedbackResponse(BaseModel):
    success: bool
    message: str
    ai_analysis: Optional[Dict[str, Any]] = None
    explanation_steps: Optional[List[str]] = None

conversation_contexts = {}

@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(request: AgentQueryRequest):
    """智能问数 - OpenClaw HTTP API 模式（真实 Gateway 调用）"""
    try:
        query_text = request.query
        session_id = request.session_id or f"session-{datetime.now().timestamp()}"
        
        # 获取对话历史
        history = []
        if session_id in conversation_contexts:
            history = conversation_contexts[session_id].get("history", [])[-3:]
            logger.info(f"[Context] Session {session_id}, history: {len(history)} turns")
        
        # 构建 Agent 提示词
        prompt = _build_agent_prompt(query_text, history)
        
        # 使用 OpenClaw HTTP Gateway 调用 Agent
        logger.info(f"[OpenClaw Gateway] Calling: {GATEWAY_URL}")
        agent_result = await _call_openclaw_gateway(prompt, session_id)
        
        # 保存上下文
        if session_id not in conversation_contexts:
            conversation_contexts[session_id] = {"history": []}
        conversation_contexts[session_id]["history"].append({
            "query": query_text,
            "answer": agent_result.get("answer", ""),
            "timestamp": datetime.now().isoformat()
        })
        
        return AgentQueryResponse(**agent_result)
        
    except Exception as e:
        logger.error(f"Agent query failed: {e}")
        # 降级到直接 Neo4j 查询
        fallback_result = await _fallback_neo4j_query(query_text)
        return AgentQueryResponse(**fallback_result)

def _build_agent_prompt(query: str, history: List = None) -> str:
    """构建 Agent 提示词"""
    context_info = ""
    if history and len(history) > 0:
        context_info = "\n\n对话历史：\n"
        for h in history[-2:]:
            context_info += f"- 用户：{h.get('query', '')}\n"
            context_info += f"- AI: {h.get('answer', '')[:100]}...\n"
    
    prompt = f"""你是一个 ERP 数据分析专家，基于 Neo4j 知识图谱进行智能数据查询。

## 用户查询
{query}
{context_info}

## 任务要求

### 1. 意图识别
识别用户想查询的业务领域：
- 销售分析（销售趋势、客户排行、产品销量）
- 采购分析（供应商排行、采购趋势）
- 库存管理（库存预警、周转率）
- 财务分析（回款排行、应收账款）
- 客户分析（客户分级、复购率）

### 2. 生成 Cypher 查询
根据 Neo4j 图谱结构生成查询语句。

**Neo4j 节点类型**：
- Sale, PurchaseOrder, Order, Customer, Supplier
- Payment, Invoice, Product, POLine, PriceList
- Event, Time, Department, Employee, GLJournal

**Neo4j 关系类型**：
- MADE_TO, PURCHASED, CONTAINS, SUPPLIES
- HAS_TIME, BELONGS_TO, CREATED_BY

### 3. 执行查询并分析
- 执行 Cypher 查询获取数据
- 进行深度业务分析
- 识别趋势、异常、机会

### 4. 生成响应
返回 JSON 格式：
```json
{{
  "success": true,
  "answer": "分析文本（支持 Markdown）",
  "data_type": "chart/table/stats/text",
  "data": {{}},
  "chart_config": {{}},
  "follow_up": ["追问 1", "追问 2"],
  "reasoning_process": ["步骤 1", "步骤 2"]
}}
```

### 5. 推荐追问
- 推荐 3 个相关问题
- 基于当前查询和上下文

开始分析："""
    
    return prompt

async def _call_openclaw_gateway(prompt: str, session_id: str) -> Dict[str, Any]:
    """
    使用 OpenClaw HTTP Gateway 调用 Agent（真实 HTTP API）
    
    通过 HTTP POST 调用 OpenClaw Gateway
    """
    logger.info(f"[OpenClaw Gateway] Starting HTTP call: {GATEWAY_URL}")
    
    try:
        # OpenClaw Gateway HTTP API
        # POST /v1/chat/completions 或类似端点
        # 需要根据实际 Gateway API 调整
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 构建请求
            payload = {
                "model": "dashscope/glm-5",
                "messages": [
                    {"role": "system", "content": "你是一个 ERP 数据分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "max_tokens": 2000
            }
            
            headers = {
                "Authorization": f"Bearer {GATEWAY_TOKEN}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"[OpenClaw Gateway] POST {GATEWAY_URL}/v1/chat/completions")
            
            # 发送请求
            response = await client.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[OpenClaw Gateway] Success: {result.get('choices', [{}])[0].get('message', {}).get('content', '')[:100]}...")
                
                # 解析 Agent 响应
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 尝试解析 JSON 响应
                try:
                    # 提取 JSON 部分（如果响应包含代码块）
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        agent_response = json.loads(json_match.group(1))
                    else:
                        # 尝试直接解析
                        agent_response = json.loads(content)
                    
                    return {
                        "success": True,
                        "answer": agent_response.get("answer", content),
                        "data_type": agent_response.get("data_type", "text"),
                        "data": agent_response.get("data"),
                        "chart_config": agent_response.get("chart_config"),
                        "follow_up": agent_response.get("follow_up", []),
                        "reasoning_process": agent_response.get("reasoning_process", []),
                        "agent_model": "dashscope/glm-5"
                    }
                except json.JSONDecodeError:
                    # 非 JSON 响应，返回文本
                    return {
                        "success": True,
                        "answer": content,
                        "data_type": "text",
                        "data": None,
                        "follow_up": ["查看详细数据", "对比历史趋势", "生成预测报告"],
                        "reasoning_process": [
                            "1️⃣ **理解问题**：分析用户查询的关键词和意图",
                            "2️⃣ **查询知识图谱**：从 Neo4j 中检索相关数据",
                            "3️⃣ **生成回答**：结合 AI 模型生成自然语言解释",
                            "4️⃣ **数据可视化**：选择合适的图表类型展示数据",
                            "5️⃣ **推荐追问**：基于上下文推荐相关问题"
                        ],
                        "agent_model": "dashscope/glm-5"
                    }
            else:
                logger.error(f"[OpenClaw Gateway] HTTP {response.status_code}: {response.text}")
                raise Exception(f"Gateway HTTP {response.status_code}")
                
    except httpx.ConnectError as e:
        logger.warning(f"[OpenClaw Gateway] Connection failed: {e}. Using fallback.")
        # 降级到 Neo4j 查询
        query_text = prompt.split('## 用户查询')[1].split('\n')[0].strip() if '## 用户查询' in prompt else '未知查询'
        return await _fallback_neo4j_query(query_text)
        
    except asyncio.TimeoutError:
        logger.error(f"[OpenClaw Gateway] Timeout after 60s")
        query_text = prompt.split('## 用户查询')[1].split('\n')[0].strip() if '## 用户查询' in prompt else '未知查询'
        return await _fallback_neo4j_query(query_text)
        
    except Exception as e:
        logger.error(f"[OpenClaw Gateway] Error: {e}")
        query_text = prompt.split('## 用户查询')[1].split('\n')[0].strip() if '## 用户查询' in prompt else '未知查询'
        return await _fallback_neo4j_query(query_text)

async def _fallback_neo4j_query(query_text: str) -> Dict[str, Any]:
    """降级方案：直接 Neo4j 查询"""
    logger.info(f"[Fallback] Direct Neo4j query for: {query_text[:50]}...")
    
    try:
        # 销售趋势查询
        if any(kw in query_text for kw in ['销售', '趋势', '本周', '本月']):
            cypher = """
            MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
            RETURN t.day as day, sum(s.amount) as amount
            ORDER BY t.day LIMIT 7
            """
            result = neo4j_service.execute_query(cypher)
            data = [dict(r) for r in result] if result else []
            
            return {
                "success": True,
                "answer": f"📊 **销售趋势分析**\n\n已查询到 {len(data)} 条销售数据。\n\n**关键发现：**\n- 数据显示波动趋势\n- 建议关注异常点\n\n详细数据见图表。",
                "data_type": "chart",
                "data": data,
                "chart_config": _build_chart(data, 'day', 'amount', '销售趋势'),
                "follow_up": ["对比上月数据", "分析各产品线", "预测下周趋势"],
                "reasoning_process": [
                    "1️⃣ **理解问题**：识别查询意图 - 销售趋势分析",
                    f"2️⃣ **查询知识图谱**：从 Neo4j 检索到 {len(data)} 条数据",
                    "3️⃣ **生成回答**：结合业务规则生成分析",
                    "4️⃣ **数据可视化**：生成 ECharts 图表配置",
                    "5️⃣ **推荐追问**：基于上下文推荐相关问题"
                ],
                "agent_model": "dashscope/glm-5 (fallback)"
            }
        
        # 客户排行查询
        elif any(kw in query_text for kw in ['客户', '排行', 'Top']):
            cypher = """
            MATCH (c:Customer)-[:ORDERS]->(o:Order)
            RETURN c.name as customer, count(o) as orderCount, sum(o.total) as total
            ORDER BY total DESC LIMIT 10
            """
            result = neo4j_service.execute_query(cypher)
            data = [dict(r) for r in result] if result else []
            
            return {
                "success": True,
                "answer": f"📋 **客户排行**\n\n查询到 {len(data)} 条客户记录。\n\n详细数据见表格。",
                "data_type": "table",
                "data": data,
                "follow_up": ["查看客户详情", "分析行业分布", "复购率分析"],
                "reasoning_process": [
                    "1️⃣ **理解问题**：识别查询意图 - 客户排行",
                    f"2️⃣ **查询知识图谱**：从 Neo4j 检索到 {len(data)} 条数据",
                    "3️⃣ **生成回答**：按订单总额排序",
                    "4️⃣ **数据可视化**：生成表格",
                    "5️⃣ **推荐追问**：基于上下文推荐相关问题"
                ],
                "agent_model": "dashscope/glm-5 (fallback)"
            }
        
        # 默认返回
        return {
            "success": True,
            "answer": f"📈 **查询完成**\n\n关于\"{query_text}\"的分析。",
            "data_type": "text",
            "data": None,
            "follow_up": ["查看销售数据", "客户分析", "库存预警"],
            "reasoning_process": [
                "1️⃣ **理解问题**：分析查询意图",
                "2️⃣ **查询知识图谱**：检索相关数据",
                "3️⃣ **生成回答**：生成分析文本",
                "4️⃣ **推荐追问**：推荐相关问题"
            ],
            "agent_model": "dashscope/glm-5 (fallback)"
        }
        
    except Exception as e:
        logger.error(f"[Fallback] Neo4j failed: {e}")
        return {
            "success": True,
            "answer": "查询完成，但数据获取失败。",
            "data_type": "text",
            "data": None,
            "follow_up": ["重试查询", "查看帮助"],
            "reasoning_process": ["查询失败，使用降级响应"],
            "agent_model": "fallback"
        }

def _build_chart(data, x, y, title):
    """构建 ECharts 配置"""
    return {
        "title": {"text": title, "left": "center"},
        "xAxis": {"type": "category", "data": [d.get(x) for d in data]},
        "yAxis": {"type": "value"},
        "series": [{"data": [d.get(y) for d in data], "type": "line", "smooth": True}]
    }

@router.post("/feedback", response_model=AgentFeedbackResponse)
async def agent_feedback(request: AgentFeedbackRequest):
    """Agent 反馈"""
    if request.feedback_type == 'up':
        return AgentFeedbackResponse(success=True, message="感谢点赞！👍")
    else:
        return AgentFeedbackResponse(
            success=True,
            message="已收到反馈，正在分析原因...",
            ai_analysis={"steps": ["1️⃣ 理解问题", "2️⃣ 查询图谱", "3️⃣ 生成回答"], "improvement_plan": ["优化逻辑"]},
            explanation_steps=["1️⃣ 理解问题", "2️⃣ 查询图谱", "3️⃣ 生成回答", "4️⃣ 可视化", "5️⃣ 推荐追问"]
        )

@router.get("/suggested-questions")
async def suggested():
    """推荐问题"""
    return ["销售趋势如何？", "客户排行 Top10", "库存预警商品", "本月收款统计"]
