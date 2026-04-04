"""
AI 分析服务 - 使用 MiniMax 模型

功能:
- 调用 MiniMax API 进行智能分析
- 生成查询优化建议
- 提供置信度评分
"""

import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# MiniMax API 配置
MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-Text-01"

# 注意：实际使用时需要从环境变量或配置读取 API Key
# 这里使用 OpenClaw 内部调用方式
class MiniMaxAIService:
    """MiniMax AI 分析服务"""
    
    def __init__(self):
        self.api_url = MINIMAX_API_URL
        self.model = MINIMAX_MODEL
    
    def analyze_query_feedback(
        self,
        query_text: str,
        sql_query: Optional[str],
        result_type: str,
        execution_time_ms: int,
        user_comment: Optional[str] = None
    ) -> Dict:
        """
        分析用户点踩的查询，生成优化建议
        
        参数:
            query_text: 用户原始查询
            sql_query: 生成的 SQL
            result_type: 结果类型
            execution_time_ms: 执行时间
            user_comment: 用户反馈意见
        
        返回:
            {
                "analysis": str,  # AI 分析报告
                "suggested_optimizations": List[str],  # 优化建议列表
                "confidence_score": float,  # 置信度 0-1
                "requires_user_confirmation": bool
            }
        """
        
        # 构建提示词
        prompt = self._build_analysis_prompt(
            query_text, sql_query, result_type, execution_time_ms, user_comment
        )
        
        # 调用 MiniMax API
        try:
            ai_response = self._call_minimax(prompt)
            
            # 解析 AI 响应
            analysis_report = ai_response.get("reply", "")
            optimizations = self._extract_optimizations(analysis_report)
            confidence = ai_response.get("confidence", 0.75)
            
            return {
                "analysis": analysis_report,
                "suggested_optimizations": optimizations,
                "confidence_score": confidence,
                "requires_user_confirmation": True
            }
        
        except Exception as e:
            logger.error(f"MiniMax AI 分析失败：{e}")
            # 降级返回模拟分析
            return self._get_fallback_analysis(
                query_text, sql_query, result_type, execution_time_ms
            )
    
    def _build_analysis_prompt(
        self,
        query_text: str,
        sql_query: Optional[str],
        result_type: str,
        execution_time_ms: int,
        user_comment: Optional[str]
    ) -> str:
        """构建 AI 分析提示词"""
        
        prompt = f"""你是一位专业的数据查询优化专家。用户对以下查询结果不满意（点踩），请分析可能的问题并提供优化建议。

## 查询信息
- **用户问题**: {query_text}
- **生成 SQL**: {sql_query if sql_query else 'N/A'}
- **结果类型**: {result_type}
- **执行时间**: {execution_time_ms}ms
- **用户反馈**: {user_comment if user_comment else '未提供具体意见'}

## 分析要求

请从以下维度分析可能的问题：

1. **查询理解偏差**
   - AI 是否误解了用户的某些关键词？
   - 业务术语是否准确匹配？
   - 时间范围/筛选条件是否正确？

2. **SQL 优化不足**
   - 是否存在性能问题（缺少索引、全表扫描）？
   - JOIN 逻辑是否正确？
   - 聚合函数使用是否恰当？

3. **结果展示不当**
   - 选择的图表类型是否适合数据特征？
   - 是否需要分组/排序/分页？
   - 数据粒度是否合适？

4. **数据覆盖不全**
   - 是否遗漏了相关表或字段？
   - 是否需要关联其他业务表？
   - 是否需要考虑权限/数据隔离？

## 输出格式

请严格按照以下 Markdown 格式输出：

```markdown
## 🤖 AI 分析报告

### 原始查询
**用户问题**: {{query_text}}
**生成 SQL**: {{sql_query}}
**结果类型**: {{result_type}}
**执行时间**: {{execution_time}}ms

### 可能的问题
1. **问题类别** - 具体说明（置信度：高/中/低）
2. ...

### 优化建议
1. {{具体建议 1}}
2. {{具体建议 2}}
3. ...

### 置信度评分
**{{score}}%** - {{评分依据}}

---
**请确认以上分析是否准确，确认后我将执行优化。**
```

请开始分析："""
        
        return prompt
    
    def _call_minimax(self, prompt: str) -> Dict:
        """调用 MiniMax API"""
        
        # 使用 OpenClaw 内部调用方式
        # 注意：实际部署时需要替换为真实的 API Key 调用
        headers = {
            "Authorization": "Bearer YOUR_MINIMAX_API_KEY",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 注意：这里使用 OpenClaw 的 sessions_spawn 调用 AI
        # 实际部署时应该使用真实的 HTTP 请求
        # response = requests.post(self.api_url, json=payload, headers=headers)
        # response.raise_for_status()
        # data = response.json()
        
        # 临时使用模拟响应（等待真实集成）
        return {
            "reply": self._generate_mock_analysis(prompt),
            "confidence": 0.85
        }
    
    def _generate_mock_analysis(self, prompt: str) -> str:
        """生成模拟分析（临时使用）"""
        return """## 🤖 AI 分析报告

### 原始查询
**用户问题**: 查询上月销售收入
**生成 SQL**: SELECT SUM(amount) FROM sales...
**结果类型**: stats
**执行时间**: 150ms

### 可能的问题
1. **查询理解偏差** - "上月"的定义可能需要明确（自然月 vs 滚动 30 天）
2. **SQL 优化不足** - 未使用日期索引，可能导致全表扫描
3. **结果展示不当** - 仅返回总额，缺少趋势分析
4. **数据覆盖不全** - 可能遗漏退货数据、折扣数据

### 优化建议
1. 明确时间范围：使用 DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
2. 添加日期索引：CREATE INDEX idx_sales_date ON sales(created_at)
3. 按日展示趋势：GROUP BY DATE(created_at)
4. 包含退货数据：LEFT JOIN sales_returns
5. 使用折线图展示每日趋势

### 置信度评分
**85%** - 基于常见查询优化模式匹配

---
**请确认以上分析是否准确，确认后我将执行优化。**
"""
    
    def _extract_optimizations(self, analysis_report: str) -> List[str]:
        """从分析报告中提取优化建议"""
        optimizations = []
        
        try:
            # 简单解析 Markdown 格式
            lines = analysis_report.split('\n')
            in_optimizations = False
            
            for line in lines:
                if '### 优化建议' in line:
                    in_optimizations = True
                    continue
                
                if in_optimizations:
                    if line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                        # 提取建议内容
                        opt = line.split('. ', 1)[1] if '. ' in line else line
                        optimizations.append(opt.strip())
                    elif line.startswith('###'):
                        break
        except Exception as e:
            logger.error(f"提取优化建议失败：{e}")
        
        return optimizations if optimizations else ["请手动优化查询"]
    
    def _get_fallback_analysis(
        self,
        query_text: str,
        sql_query: Optional[str],
        result_type: str,
        execution_time_ms: int
    ) -> Dict:
        """降级分析（AI 调用失败时使用）"""
        
        return {
            "analysis": f"""## 🤖 AI 分析报告（降级模式）

### 原始查询
**用户问题**: {query_text}
**生成 SQL**: {sql_query[:200] if sql_query else 'N/A'}
**结果类型**: {result_type}
**执行时间**: {execution_time_ms}ms

### 可能的问题
1. **查询理解偏差** - 需要更多上下文
2. **SQL 优化不足** - 建议检查执行计划
3. **结果展示不当** - 尝试其他可视化方式
4. **数据覆盖不全** - 确认数据源完整性

### 优化建议
1. 使用更具体的业务术语
2. 明确时间范围和筛选条件
3. 指定期望的展示方式
4. 提供示例数据

### 置信度评分
**60%** - AI 服务暂时不可用

---
**请确认以上分析是否准确。**
""",
            "suggested_optimizations": [
                "使用更具体的业务术语",
                "明确时间范围",
                "检查数据源"
            ],
            "confidence_score": 0.6,
            "requires_user_confirmation": True
        }


# 全局实例
ai_service = MiniMaxAIService()
