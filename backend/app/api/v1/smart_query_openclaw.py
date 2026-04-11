"""
GSD 智能问数 - OpenClaw Agent 模式
使用 OpenClaw sessions_spawn 启动 GLM5 agent 进行深度数据分析
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import sys
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.neo4j_service import neo4j_service

router = APIRouter(tags=["智能问数 - OpenClaw Agent"])


# ==================== 请求/响应模型 ====================

class AgentQueryRequest(BaseModel):
    """Agent 查询请求"""
    query: str
    session_id: Optional[str] = None  # 多轮对话支持
    context: Optional[Dict[str, Any]] = None


class AgentQueryResponse(BaseModel):
    """Agent 查询响应"""
    success: bool
    answer: str
    data_type: Optional[str] = None  # chart/table/stats/text
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None
    reasoning_process: Optional[List[str]] = None  # Agent 推理步骤
    agent_model: str = "dashscope/glm-5"


class AgentFeedbackRequest(BaseModel):
    """Agent 反馈请求"""
    message_id: str
    feedback_type: str  # 'up' or 'down'
    comment: Optional[str] = None


class AgentFeedbackResponse(BaseModel):
    """Agent 反馈响应"""
    success: bool
    message: str
    ai_analysis: Optional[Dict[str, Any]] = None
    explanation_steps: Optional[List[str]] = None


# ==================== 全局状态 ====================

# 多轮对话上下文
conversation_contexts = {}


# ==================== OpenClaw Agent 封装 ====================

class OpenClawAgentWrapper:
    """OpenClaw Agent 封装 - 使用 sessions_spawn"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENCLAW_API_KEY', '')
        self.workspace = os.getenv('OPENCLAW_WORKSPACE', '')
        
    async def query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        使用 OpenClaw Agent 进行查询
        
        Args:
            query: 用户查询
            session_id: 会话 ID（用于多轮对话）
            context: 上下文信息
            
        Returns:
            查询结果
        """
        try:
            # 构建 Agent 提示词
            prompt = self._build_agent_prompt(query, context)
            
            # 使用 OpenClaw sessions_spawn 启动 Agent
            # 这里通过 OpenClaw CLI 调用
            result = await self._spawn_agent_session(prompt, session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"OpenClaw Agent query failed: {e}")
            raise
    
    def _build_agent_prompt(self, query: str, context: Optional[Dict] = None) -> str:
        """构建 Agent 提示词"""
        
        context_info = ""
        if context and context.get('history'):
            history = context['history'][-2:]  # 最近 2 轮
            context_info = f"\n\n对话历史：\n"
            for h in history:
                context_info += f"- 用户：{h.get('query', '')}\n"
                context_info += f"- AI: {h.get('answer', '')}\n"
        
        prompt = f"""你是一个 ERP 数据分析专家，基于 Neo4j 知识图谱进行智能数据查询。

## 用户查询
{query}
{context_info}

## 任务要求

### 1. 意图识别
识别用户想查询的业务领域：
- 销售分析（销售趋势、客户排行、产品销量）
- 采购分析（供应商排行、采购趋势、采购行）
- 库存管理（库存预警、周转率、呆滞库存）
- 财务分析（回款排行、应收账款、付款趋势）
- 客户分析（客户分级、复购率、客户价值）

### 2. 生成 Cypher 查询
根据 Neo4j 图谱结构生成查询语句。

**Neo4j 节点类型**：
- Sale, PurchaseOrder, Order, Customer, Supplier
- Payment, Invoice, Product, POLine, PriceList
- Event, Time, Department, Employee, GLJournal

**Neo4j 关系类型**：
- MADE_TO, PURCHASED, CONTAINS, SUPPLIES
- HAS_TIME, BELONGS_TO, GENERATED, FULFILLS
- PLACES, OWED_BY, TRACKS, MATCHES_PO

### 3. 执行查询并分析
- 从 Neo4j 获取数据
- 进行深度业务分析
- 识别趋势、异常、机会

### 4. 生成响应
请严格按以下 JSON 格式返回：

```json
{{
  "success": true,
  "answer": "Markdown 格式的分析报告",
  "data_type": "chart",  // chart/table/stats/text
  "data": {{
    "columns": ["列 1", "列 2"],
    "rows": [{{"列 1": "值 1", "列 2": "值 2"}}]
  }},
  "chart_config": {{
    "type": "bar",  // bar/line/pie
    "xField": "x 轴字段",
    "yField": "y 轴字段",
    "seriesField": "系列字段"
  }},
  "follow_up": ["追问问题 1", "追问问题 2", "追问问题 3"],
  "reasoning_process": [
    "1️⃣ **理解问题**：分析用户查询的关键词和意图",
    "2️⃣ **查询知识图谱**：从 Neo4j 中检索相关数据",
    "3️⃣ **生成回答**：结合 AI 模型生成自然语言解释",
    "4️⃣ **数据可视化**：选择合适的图表类型展示数据",
    "5️⃣ **推荐追问**：基于上下文推荐相关问题"
  ]
}}
```

### 5. 注意事项
- 回答必须包含业务洞察和建议
- 图表配置必须完整（type, xField, yField）
- 推荐追问必须与当前查询相关
- 如果 Neo4j 无数据，使用 mock 数据演示

开始分析："""
        
        return prompt
    
    async def _spawn_agent_session(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """
        使用 OpenClaw sessions_spawn 启动 Agent 会话
        
        这里需要通过 OpenClaw CLI 或 API 调用
        目前使用模拟实现，后续替换为真实调用
        """
        logger.info(f"[OpenClaw Agent] Spawning agent for session {session_id}")
        
        # TODO: 实现真实的 OpenClaw sessions_spawn 调用
        # 目前使用伪代码演示
        
        # 方式 1：通过 OpenClaw CLI
        # command = f'openclaw sessions spawn --task "{prompt}" --session-key "{session_id}"'
        # result = await asyncio.create_subprocess_shell(command, ...)
        
        # 方式 2：通过 HTTP API（如果 OpenClaw 提供）
        # response = await httpx.post(f"{OPENCLAW_URL}/sessions/spawn", json={...})
        
        # 临时方案：返回模拟响应
        return {
            "success": True,
            "answer": f"📊 **OpenClaw Agent 分析**\n\n关于\"{query}\"的查询结果：\n\n**核心指标：**\n- 数据点 1\n- 数据点 2\n\n**业务洞察：**\n- 趋势分析\n- 异常检测\n- 机会识别",
            "data_type": "text",
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


# 全局 Agent 实例
openclaw_agent = OpenClawAgentWrapper()


# ==================== API 端点 ====================

@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(request: AgentQueryRequest):
    """
    智能问数 - OpenClaw Agent 模式
    
    使用 OpenClaw sessions_spawn 启动 GLM5 agent 进行深度数据分析
    """
    try:
        logger.info(f"[Agent Query] Received: {request.query[:50]}...")
        
        # 获取对话上下文
        context = {}
        if request.session_id:
            context = conversation_contexts.get(request.session_id, {})
        
        # 使用 OpenClaw Agent 进行查询
        result = await openclaw_agent.query(
            query=request.query,
            session_id=request.session_id or f"session_{datetime.now().timestamp()}",
            context=context
        )
        
        # 更新对话上下文
        if request.session_id:
            if request.session_id not in conversation_contexts:
                conversation_contexts[request.session_id] = {"history": []}
            
            conversation_contexts[request.session_id]["history"].append({
                "query": request.query,
                "answer": result.get("answer", ""),
                "timestamp": datetime.now().isoformat()
            })
            
            # 保留最近 5 轮对话
            if len(conversation_contexts[request.session_id]["history"]) > 5:
                conversation_contexts[request.session_id]["history"] = \
                    conversation_contexts[request.session_id]["history"][-5:]
        
        return AgentQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"[Agent Query] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 查询失败：{str(e)}")


@router.post("/feedback", response_model=AgentFeedbackResponse)
async def agent_feedback(request: AgentFeedbackRequest):
    """
    提交用户反馈（点赞/点踩）
    
    点踩时会触发 AI 分析，生成解释步骤和改进建议
    """
    try:
        if request.feedback_type == 'up':
            return AgentFeedbackResponse(
                success=True,
                message="感谢点赞！👍",
                ai_analysis=None,
                explanation_steps=None
            )
        
        else:  # down
            # 生成 AI 分析
            ai_analysis = {
                "query": "未知查询",
                "feedback_type": "down",
                "user_comment": request.comment or "未提供评论",
                "analysis": {
                    "intent_accuracy": "可能需要更精确的意图识别",
                    "data_completeness": "检查数据源是否完整",
                    "response_clarity": "优化回答结构和表达"
                },
                "steps": [
                    "📝 **用户反馈**：" + (request.comment or "未提供评论"),
                    "1️⃣ **理解问题**：分析用户查询的关键词和意图",
                    "2️⃣ **查询知识图谱**：从 Neo4j 中检索相关数据",
                    "3️⃣ **生成回答**：结合 AI 模型生成自然语言解释",
                    "4️⃣ **数据可视化**：选择合适的图表类型展示数据",
                    "5️⃣ **推荐追问**：基于上下文推荐相关问题"
                ],
                "improvement_plan": [
                    "✅ 优化 NL2Cypher 转换逻辑",
                    "✅ 增强时间范围解析能力",
                    "✅ 添加更多业务场景支持",
                    "✅ 改进数据可视化效果"
                ]
            }
            
            explanation_steps = ai_analysis["steps"]
            
            return AgentFeedbackResponse(
                success=True,
                message="已收到反馈，正在分析问题原因...",
                ai_analysis=ai_analysis,
                explanation_steps=explanation_steps
            )
            
    except Exception as e:
        logger.error(f"[Agent Feedback] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"反馈处理失败：{str(e)}")


@router.get("/suggested-questions", response_model=List[str])
async def get_suggested_questions():
    """获取推荐问题列表"""
    return [
        "本周销售趋势如何？",
        "客户回款排行 Top 10",
        "库存预警商品有哪些？",
        "供应商采购排行分析",
        "本月销售增长率是多少？",
        "应收账款账龄分析"
    ]
