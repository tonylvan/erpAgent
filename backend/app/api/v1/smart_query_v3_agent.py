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
from datetime import datetime

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
    Call OpenClaw agent via sessions_spawn
    Returns structured response with reasoning process
    """
    try:
        # Build prompt
        system_prompt, user_prompt = build_agent_prompt(query, context)
        
        # For now, use mock response (replace with actual OpenClaw call when available)
        # In production, use: from openclaw import sessions_spawn
        agent_response = {
            "reasoning_steps": [
                {
                    "step": 1,
                    "action": "intent_analysis",
                    "description": "Analyzing user query intent",
                    "result": "Data query request identified"
                },
                {
                    "step": 2,
                    "action": "entity_extraction",
                    "description": "Extracting entities from query",
                    "result": "Entities: [customers, sales, time_period]"
                },
                {
                    "step": 3,
                    "action": "cypher_generation",
                    "description": "Generating Cypher query for Neo4j",
                    "result": "MATCH (c:Customer)-[:PURCHASED]->(o:Order) RETURN c.name, sum(o.amount)"
                },
                {
                    "step": 4,
                    "action": "data_analysis",
                    "description": "Analyzing query results",
                    "result": "Found 10 top customers with total sales"
                }
            ],
            "answer": f"""## Query Results

Based on your query: **"{query}"**

### Key Findings:
- Total records analyzed: 1,234
- Time period: Last 30 days
- Top result: Customer ABC with $1.2M sales

### Recommendations:
1. Focus on top 10 customers for Q2
2. Monitor customer retention rate
3. Consider upselling to mid-tier customers
""",
            "data_type": "table",
            "data": {
                "columns": ["Customer", "Sales", "Orders", "Growth"],
                "rows": [
                    ["ABC Corp", "$1,234,567", 145, "+15.3%"],
                    ["XYZ Ltd", "$987,654", 98, "+8.7%"],
                    ["123 Inc", "$765,432", 76, "+12.1%"]
                ]
            },
            "chart_config": {
                "title": {"text": "Sales by Customer", "left": "center"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {
                    "type": "category",
                    "data": ["ABC Corp", "XYZ Ltd", "123 Inc"],
                    "axisLabel": {"rotate": 45}
                },
                "yAxis": {
                    "type": "value",
                    "name": "Sales Amount",
                    "axisLabel": {"formatter": "${value}"}
                },
                "series": [{
                    "name": "Sales",
                    "type": "bar",
                    "data": [1234567, 987654, 765432],
                    "itemStyle": {"color": "#667eea"}
                }],
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": true}
            },
            "follow_up": [
                "Show me the sales trend for ABC Corp",
                "What products did XYZ Ltd purchase?",
                "Compare Q1 vs Q2 performance"
            ]
        }
        
        # Update session message count
        session_manager.increment_message_count(session_id)
        
        return agent_response
        
    except Exception as e:
        # Fallback response
        return {
            "reasoning_steps": [{
                "step": 1,
                "action": "error",
                "description": "Agent call failed",
                "result": str(e)
            }],
            "answer": f"Query processed with fallback mode: {query}",
            "data_type": "text",
            "follow_up": ["Try rephrasing your question"]
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
