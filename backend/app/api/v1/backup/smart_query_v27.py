"""
GSD Smart Query Backend API v2.7 - DashScope Direct LLM
Uses DashScope SDK for general questions, Neo4j for ERP queries
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
import dashscope
from dashscope import Generation

router = APIRouter(tags=["Smart Query v2.7 - DashScope Direct"])

# Configure API Key
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-sp-4d5fceda0a674836b4c9a6e70e329330')


class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "admin"
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    answer: str
    route: Optional[str] = None
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None


class DashScopeCaller:
    """DashScope LLM Caller - Direct API Call"""
    
    @staticmethod
    def call(query: str) -> Dict[str, Any]:
        """Call DashScope Qwen model directly"""
        try:
            response = Generation.call(
                model='qwen-plus',
                messages=[
                    {'role': 'system', 'content': '你是 GSD 智能问数助手，擅长回答 ERP 数据查询问题和一般性问题。'},
                    {'role': 'user', 'content': query}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "route": "llm",
                    "answer": response.output.choices[0].message.content,
                    "data_type": "text"
                }
            else:
                return {
                    "success": False,
                    "route": "error",
                    "answer": f"DashScope API error: {response.code} - {response.message}",
                    "data_type": "text"
                }
                
        except Exception as e:
            return {
                "success": False,
                "route": "error",
                "answer": f"DashScope call error: {str(e)}",
                "data_type": "text"
            }


@router.post("/query", response_model=QueryResponse)
async def smart_query_v27(request: QueryRequest):
    """
    Smart Query v2.7 - DashScope Direct LLM
    
    Uses DashScope SDK for general questions
    """
    try:
        result = DashScopeCaller.call(request.query)
        
        return QueryResponse(
            success=result.get("success", False),
            answer=result.get("answer", "No response"),
            route=result.get("route"),
            data_type=result.get("data_type"),
            data=result.get("data"),
            chart_config=result.get("chart_config"),
            follow_up=result.get("follow_up", [])
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            answer=f"Query failed: {str(e)}",
            route="error",
            data_type="text"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "v2.7",
        "integration": "DashScope Direct SDK",
        "model": "qwen-plus",
        "timestamp": datetime.now().isoformat()
    }
