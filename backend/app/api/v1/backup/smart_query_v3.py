"""
GSD Smart Query Backend API v3 - OpenClaw Integration
Calls OpenClaw agent for intelligent routing (ERP -> Neo4j, General -> LLM)

Windows Note: Uses full PowerShell script path for reliability
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import subprocess
import json
import os
import sys
from datetime import datetime

router = APIRouter(tags=["Smart Query v3 - OpenClaw Integration"])


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


class OpenClawCaller:
    """OpenClaw Agent Caller - Windows Compatible (Full Path)"""
    
    # npm global script path on Windows
    OPENCLAW_PS1 = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.ps1"
    
    @staticmethod
    def call(query: str, user_id: str = "admin") -> Dict[str, Any]:
        """
        Call OpenClaw CLI using PowerShell script full path.
        
        Windows 根因分析：
        1. npm 全局安装的命令实际是 .ps1 PowerShell 脚本
        2. subprocess.run() 默认只搜索 PATHEXT 中的扩展名（.exe,.bat,.cmd 等）
        3. .ps1 不在 PATHEXT 中，所以直接调用 "openclaw" 会失败
        4. 解决方案：
           - 方案 A: shell=True（依赖 shell 解析）
           - 方案 B: 直接调用 .ps1 脚本完整路径（更可靠）
        
        参考：
        - https://docs.python.org/3/library/subprocess.html#windows-popen-constructor
        - https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/pathext
        """
        try:
            # Verify script exists
            if not os.path.exists(OpenClawCaller.OPENCLAW_PS1):
                return {
                    "success": False,
                    "route": "error",
                    "answer": f"OpenClaw script not found at {OpenClawCaller.OPENCLAW_PS1}",
                    "data_type": "text"
                }
            
            # Escape quotes in query
            safe_query = query.replace('"', '`"')
            
            # Call PowerShell script directly with full path
            cmd = [
                "powershell",
                "-ExecutionPolicy", "Bypass",
                "-File", OpenClawCaller.OPENCLAW_PS1,
                "agent",
                "--message", safe_query,
                "--thinking"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace',
                # Hide console window on Windows
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "route": "error",
                    "answer": f"OpenClaw call failed (exit {result.returncode}): {result.stderr}",
                    "data_type": "text"
                }
            
            response_text = result.stdout.strip()
            
            # Return the response
            return {
                "success": True,
                "route": "llm",
                "answer": response_text,
                "data_type": "text"
            }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "route": "error",
                "answer": "OpenClaw call timeout (60s)",
                "data_type": "text"
            }
        except Exception as e:
            return {
                "success": False,
                "route": "error",
                "answer": f"OpenClaw call error: {str(e)}",
                "data_type": "text"
            }


@router.post("/query", response_model=QueryResponse)
async def smart_query_v3(request: QueryRequest):
    """
    Smart Query v3 - OpenClaw Integration
    
    Routes queries intelligently:
    - ERP queries (payment, purchase, inventory, etc.) -> Neo4j
    - General questions -> LLM direct answer
    """
    try:
        result = OpenClawCaller.call(request.query, request.user_id)
        
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
        "version": "v3",
        "integration": "OpenClaw Agent",
        "windows_powershell": True,
        "script_path": OpenClawCaller.OPENCLAW_PS1,
        "timestamp": datetime.now().isoformat()
    }
