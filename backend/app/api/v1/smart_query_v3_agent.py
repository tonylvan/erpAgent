"""
GSD Smart Query v3 - OpenClaw Agent Integration
Uses OpenClaw sessions_spawn to start a new agent for answering queries
Returns both reasoning process and final result for frontend display
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import sys
import subprocess
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(tags=["智能问数 v3 - Agent"])


# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # For multi-turn conversation
    with_reasoning: bool = True  # Include reasoning process in response


class ReasoningStep(BaseModel):
    """Single reasoning step"""
    step: int
    action: str
    description: str
    result: Optional[str] = None


class AgentQueryResponse(BaseModel):
    """Response from agent-powered query"""
    success: bool
    answer: str
    reasoning_process: List[ReasoningStep] = []  # Reasoning steps
    data_type: Optional[str] = None  # chart/table/stats/text
    data: Optional[Dict[str, Any]] = None  # Structured data
    chart_config: Optional[Dict[str, Any]] = None  # ECharts config
    follow_up: Optional[List[str]] = None  # Suggested follow-up questions
    session_id: str  # Session ID for conversation continuity
    timestamp: datetime = None


class OpenClawSessionManager:
    """Manager for OpenClaw agent sessions"""
    
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_session(self, session_id: str) -> str:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            # Create new session with GLM-5 model
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "model": "dashscope/glm-5",
                "message_count": 0
            }
        return session_id
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session_id,
                "created_at": session["created_at"].isoformat(),
                "model": session["model"],
                "message_count": session["message_count"]
            }
        return None
    
    def increment_message_count(self, session_id: str):
        """Increment message count for session"""
        if session_id in self.sessions:
            self.sessions[session_id]["message_count"] += 1


# Session manager instance
session_manager = OpenClawSessionManager()


def build_agent_prompt(query: str, context: Optional[Dict] = None) -> str:
    """Build prompt for agent with reasoning instructions"""
    
    system_prompt = """You are an ERP data analysis expert. Your task is to:
1. Analyze the user's query step by step
2. Show your reasoning process clearly
3. Provide structured data when applicable
4. Suggest follow-up questions

Format your response as JSON:
{
    "reasoning_steps": [
        {"step": 1, "action": "analyze", "description": "...", "result": "..."},
        {"step": 2, "action": "query", "description": "...", "result": "..."}
    ],
    "answer": "Final answer in markdown format",
    "data_type": "chart|table|stats|text",
    "data": {...},  // Optional structured data
    "chart_config": {...},  // Optional ECharts config
    "follow_up": ["Question 1?", "Question 2?"]
}"""
    
    context_str = ""
    if context:
        context_str = f"\nContext: {json.dumps(context, ensure_ascii=False)}"
    
    user_prompt = f"""Analyze this ERP data query:

Query: {query}{context_str}

Think step by step and provide your complete reasoning process."""
    
    return system_prompt, user_prompt


async def call_openclaw_agent(query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Call OpenClaw agent via sessions_send
    Returns structured response with reasoning process
    """
    try:
        logger.info(f"[OpenClaw] Calling sessions_send for query: {query[:50]}...")
        
        # Build message with context
        context_str = f"\nContext: {json.dumps(context, ensure_ascii=False)}" if context else ""
        message = f"""Analyze this ERP data query and provide structured response:

Query: {query}{context_str}

Format your response as:
1. Key findings
2. Data analysis  
3. Recommendations
"""
        
        # Call OpenClaw CLI sessions_send
        result = subprocess.run(
            ['openclaw', 'sessions_send',
             '--label', 'smart-query-agent',
             '--message', message,
             '--timeout-seconds', '30'],
            capture_output=True,
            text=True,
            timeout=35
        )
        
        if result.returncode == 0:
            # Parse response
            response_text = result.stdout.strip()
            
            logger.info(f"[OpenClaw] Response received: {len(response_text)} chars")
            
            return {
                "success": True,
                "answer": response_text,
                "data_type": "text",
                "reasoning_process": [{
                    "step": 1,
                    "action": "openclaw_agent",
                    "description": "使用 OpenClaw Agent 分析查询",
                    "result": f"响应长度：{len(response_text)} 字符"
                }],
                "follow_up": [
                    "查看详细数据",
                    "导出报告",
                    "与上月对比"
                ]
            }
        else:
            logger.warning(f"[OpenClaw] sessions_send failed: {result.stderr}")
            raise Exception(result.stderr)
            
    except Exception as e:
        logger.warning(f"[OpenClaw] Failed, falling back to v2: {e}")
        # Fallback to v2 NL2Cypher
        from app.api.v1.smart_query_v2 import get_knowledge_engine
        engine = get_knowledge_engine()
        v2_response = await engine.query(query)
        
        return {
            "reasoning_steps": [{
                "step": 1,
                "action": "fallback",
                "description": "OpenClaw 调用失败，使用 Neo4j 直接查询",
                "result": "使用 v2 NL2Cypher 引擎"
            }],
            "answer": v2_response.get("answer", "查询完成"),
            "data_type": v2_response.get("data_type", "text"),
            "data": v2_response.get("data"),
            "chart_config": v2_response.get("chart_config"),
            "follow_up": v2_response.get("follow_up", [])
        }


@router.post("/query", response_model=AgentQueryResponse)
async def smart_query_agent(request: QueryRequest):
    """
    Smart Query v3 - Agent-powered query with reasoning
    
    Uses OpenClaw sessions_spawn to start a new agent for each query.
    Returns both reasoning process and final result for frontend display.
    """
    try:
        # Get or create session
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        session_manager.get_or_create_session(session_id)
        
        # Get conversation context (for multi-turn)
        context = None  # TODO: Load from session history
        
        # Call agent
        agent_response = await call_openclaw_agent(
            query=request.query,
            session_id=session_id,
            context=context
        )
        
        # Convert reasoning steps to model
        reasoning_steps = [
            ReasoningStep(**step) for step in agent_response.get("reasoning_steps", [])
        ]
        
        return AgentQueryResponse(
            success=True,
            answer=agent_response["answer"],
            reasoning_process=reasoning_steps,
            data_type=agent_response.get("data_type"),
            data=agent_response.get("data"),
            chart_config=agent_response.get("chart_config"),
            follow_up=agent_response.get("follow_up"),
            session_id=session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    info = session_manager.get_session_info(session_id)
    if info:
        return {"success": True, "session": info}
    raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id in session_manager.sessions:
        del session_manager.sessions[session_id]
        return {"success": True, "message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")
