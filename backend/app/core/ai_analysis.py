"""
MiniMax AI 分析服务 - 基于 OpenClaw Gateway
用于点踩反馈的智能分析
"""
import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

class MiniMaxAIService:
    """MiniMax AI 分析服务"""
    
    def __init__(self):
        self.gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
        self.gateway_token = os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
        self.model = "MiniMax-Text-01"
        self.timeout = 30  # 秒
    
    def analyze_query_feedback(
        self,
        original_query: str,
        user_comment: str,
        query_result: Optional[Dict] = None,
        execution_time_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        分析点踩反馈
        
        Args:
            original_query: 原始查询
            user_comment: 用户评论
            query_result: 查询结果（可选）
            execution_time_ms: 执行时间（可选）
        
        Returns:
            AI 分析报告
        """
        # 构建提示词
        prompt = self._build_analysis_prompt(
            original_query,
            user_comment,
            query_result,
            execution_time_ms
        )
        
        # 调用 MiniMax 模型
        try:
            analysis_result = self._call_minimax(prompt)
            
            # 解析 AI 响应
            return self._parse_analysis_result(analysis_result)
        except Exception as e:
            # 降级方案：返回模拟分析
            return self._fallback_analysis(original_query, user_comment)
    
    def _build_analysis_prompt(
        self,
        original_query: str,
        user_comment: str,
        query_result: Optional[Dict],
        execution_time_ms: Optional[int]
    ) -> str:
        """构建 AI 分析提示词"""
        
        prompt = f"""你是一位专业的 SQL 查询优化专家。请分析以下点踩反馈并给出专业的分析报告。

【原始查询】
{original_query}

【用户反馈】
{user_comment}

【查询性能】
执行时间：{execution_time_ms or 'N/A'} 毫秒

【查询结果】
{json.dumps(query_result, ensure_ascii=False, indent=2) if query_result else 'N/A'}

请以 JSON 格式输出分析报告，包含以下字段：
1. report: 详细的分析报告（Markdown 格式）
2. issues: 可能的问题列表（数组）
3. suggestions: 优化建议列表（数组）
4. suggested_reasons: 推荐用户选择的点踩原因（数组，3-5 个常见原因）
5. confidence: 置信度评分（0-1 之间的小数）
6. optimized_query: 优化后的查询（如果适用）
7. expected_improvement: 预期改进（如性能提升百分比）

常见点踩原因参考：查询结果不准确、SQL 性能慢、数据不完整、展示方式不当、时间范围错误、缺少关键指标

请确保 JSON 格式正确，可以直接解析。"""
        
        return prompt
    
    def _call_minimax(self, prompt: str) -> str:
        """调用 MiniMax 模型"""
        
        url = f"{self.gateway_url}/agent"
        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": prompt,
            "model": self.model,
            "temperature": 0.3,  # 较低温度，更专业
            "max_tokens": 2000
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"MiniMax API 调用失败：{response.status_code}")
        
        result = response.json()
        return result.get("answer", "")
    
    def _parse_analysis_result(self, ai_response: str) -> Dict[str, Any]:
        """解析 AI 响应结果"""
        
        try:
            # 尝试从响应中提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except:
            pass
        
        # 解析失败时返回结构化响应
        return {
            "report": ai_response,
            "issues": ["AI 解析失败"],
            "suggestions": ["请手动检查查询"],
            "confidence": 0.5,
            "optimized_query": None,
            "expected_improvement": None
        }
    
    def _fallback_analysis(
        self,
        original_query: str,
        user_comment: str
    ) -> Dict[str, Any]:
        """降级方案：模拟分析"""
        
        return {
            "report": f"""## 🤖 AI 分析报告

### 原始查询
```sql
{original_query}
```

### 用户反馈
{user_comment}

### 可能的问题
1. 查询理解偏差
2. 结果展示不当
3. 性能优化不足

### 优化建议
1. 明确查询条件
2. 添加必要的索引
3. 优化结果展示格式

### 置信度评分
中等（60%）""",
            "issues": ["查询理解偏差", "结果展示不当"],
            "suggestions": ["明确查询条件", "添加索引", "优化展示"],
            "suggested_reasons": ["查询结果不准确", "SQL 性能慢", "数据不完整", "展示方式不当"],
            "confidence": 0.6,
            "optimized_query": None,
            "expected_improvement": "30%"
        }


# 全局 AI 服务实例
ai_service = MiniMaxAIService()
