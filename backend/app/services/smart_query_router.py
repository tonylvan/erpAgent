"""
GSD Smart Query Router - Unified Intelligent Query Router
Provides single entry point for all query types with automatic engine selection
Architecture: Intent Detection → Engine Selection → Query Execution → Response
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class SmartQueryRouter:
    """
    Unified intelligent query router
    Automatically selects the best engine based on query intent
    """
    
    def __init__(self):
        self.neo4j_engine = None
        self.agent_engine = None
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize query engines"""
        try:
            # Import Neo4j engine (v2)
            from app.api.v1.smart_query_v2 import Neo4jKnowledgeEngine
            self.neo4j_engine = Neo4jKnowledgeEngine()
            logger.info("[SmartQueryRouter] Neo4j engine initialized")
        except Exception as e:
            logger.warning(f"[SmartQueryRouter] Neo4j engine init failed: {e}")
        
        # Agent engine will be called directly when needed
        logger.info("[SmartQueryRouter] Router initialized successfully")
    
    def detect_intent(self, query: str) -> str:
        """
        Detect query intent and return recommended engine
        
        Returns:
            'neo4j' - Direct Neo4j query (fast, structured data)
            'agent' - OpenClaw Agent (complex analysis, reasoning)
            'llm' - DashScope LLM (general questions)
        """
        q = query.lower()
        
        # ERP Data Queries - Use Neo4j
        erp_keywords = [
            '销售', '采购', '库存', '财务', '客户', '供应商',
            '订单', '发票', '付款', '回款', '趋势', '排行',
            '销售趋势', '库存预警', '客户排行', '供应商排行',
            'sale', 'purchase', 'inventory', 'customer', 'supplier',
            'order', 'invoice', 'payment', 'top', 'trend'
        ]
        
        if any(kw in q for kw in erp_keywords):
            logger.info(f"[Intent] Detected ERP query: {query[:50]}...")
            return 'neo4j'
        
        # Complex Analysis - Use Agent
        analysis_keywords = [
            '分析', '预测', '为什么', '原因', '建议', '风险',
            '关联', '影响', '优化', '策略', '洞察',
            'analyze', 'predict', 'why', 'reason', 'suggest', 'risk'
        ]
        
        if any(kw in q for kw in analysis_keywords):
            logger.info(f"[Intent] Detected analysis query: {query[:50]}...")
            return 'agent'
        
        # Default to Neo4j for faster response
        logger.info(f"[Intent] Default to Neo4j: {query[:50]}...")
        return 'neo4j'
    
    async def query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute query using the best engine
        
        Args:
            query: User query string
            session_id: Session ID for conversation context
            
        Returns:
            Unified response with success, answer, data, follow_up
        """
        # Detect intent
        engine_type = self.detect_intent(query)
        
        logger.info(f"[SmartQueryRouter] Routing to {engine_type} engine")
        
        try:
            # Execute with selected engine
            if engine_type == 'neo4j':
                result = await self._query_neo4j(query, session_id)
            elif engine_type == 'agent':
                result = await self._query_agent(query, session_id)
            else:
                result = await self._query_llm(query)
            
            # Add metadata
            result['engine'] = engine_type
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"[SmartQueryRouter] Query failed: {e}")
            
            # Fallback to other engine
            fallback_engine = 'agent' if engine_type == 'neo4j' else 'neo4j'
            logger.info(f"[SmartQueryRouter] Fallback to {fallback_engine}")
            
            try:
                if fallback_engine == 'neo4j':
                    return await self._query_neo4j(query, session_id)
                else:
                    return await self._query_agent(query, session_id)
            except Exception as fallback_error:
                logger.error(f"[SmartQueryRouter] Fallback failed: {fallback_error}")
                return {
                    'success': False,
                    'answer': f"查询失败：{str(e)}",
                    'engine': 'error',
                    'timestamp': datetime.now().isoformat()
                }
    
    async def _query_neo4j(self, query: str, session_id: Optional[str]) -> Dict[str, Any]:
        """Query using Neo4j engine (v2)"""
        if not self.neo4j_engine:
            raise Exception("Neo4j engine not initialized")
        
        # Use Neo4j engine
        result = await self.neo4j_engine.query(query)
        
        return {
            'success': True,
            'answer': result.get('answer', ''),
            'data_type': result.get('data_type'),
            'data': result.get('data'),
            'chart_config': result.get('chart_config'),
            'follow_up': result.get('follow_up', [])
        }
    
    async def _query_agent(self, query: str, session_id: Optional[str]) -> Dict[str, Any]:
        """Query using OpenClaw Agent (v3)"""
        from app.api.v1.smart_query_v3_agent import call_openclaw_agent
        
        session_id = session_id or 'default'
        result = await call_openclaw_agent(query, session_id)
        
        return {
            'success': True,
            'answer': result.get('answer', ''),
            'data_type': result.get('data_type'),
            'data': result.get('data'),
            'chart_config': result.get('chart_config'),
            'follow_up': result.get('follow_up', []),
            'reasoning_process': result.get('reasoning_process', [])
        }
    
    async def _query_llm(self, query: str) -> Dict[str, Any]:
        """Query using DashScope LLM"""
        # Placeholder for LLM integration
        return {
            'success': True,
            'answer': f"关于'{query}'的问题，这是一个通用问题，建议使用专业查询功能。",
            'data_type': 'text',
            'follow_up': []
        }


# Global router instance
smart_query_router = SmartQueryRouter()