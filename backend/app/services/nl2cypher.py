# NL2Cypher 引擎 - 自然语言转 Cypher 查询
# 基于 NLU 意图生成 Neo4j Cypher 查询

from typing import Dict, Any, Optional
from app.nlu.intent_parser import QueryIntent, IntentType


class NL2CypherEngine:
    """NL2Cypher 引擎核心类"""
    
    def __init__(self):
        """初始化 NL2Cypher 引擎"""
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """加载 Neo4j Schema"""
        return {
            'node_labels': [
                'Supplier', 'PurchaseOrder', 'POLine', 'Invoice', 'Payment',
                'Customer', 'Order', 'Sale', 'Product', 'Time',
                'GLAccount', 'GLJournal', 'PriceList'
            ],
            'relationship_types': [
                'SUPPLIES', 'HAS_LINE', 'MATCHES_PO', 'PAYS_TO',
                'ORDERS', 'CONTAINS', 'BUYS', 'OCCURS_ON',
                'HAS_TIME', 'GENERATES', 'SOLD_IN'
            ],
            'properties': {
                'Sale': ['amount', 'timestamp', 'hour'],
                'Order': ['amount', 'status', 'date'],
                'Customer': ['customer_name', 'customer_number', 'status'],
                'Product': ['name', 'code', 'category', 'price', 'stock'],
                'Supplier': ['vendor_name', 'vendor_type'],
                'PurchaseOrder': ['status'],
                'Invoice': ['amount', 'status', 'invoice_num'],
                'Payment': ['amount', 'status', 'date'],
                'Time': ['year', 'month', 'day', 'week', 'quarter']
            }
        }
    
    def generate(self, intent: QueryIntent) -> str:
        """
        根据查询意图生成 Cypher 查询
        
        Args:
            intent: 结构化查询意图
            
        Returns:
            str: Cypher 查询语句
        """
        # 根据意图类型选择生成策略
        if intent.intent_type == IntentType.QUERY_SALES:
            return self._generate_sales_query(intent)
        
        elif intent.intent_type == IntentType.QUERY_RANKING:
            return self._generate_ranking_query(intent)
        
        elif intent.intent_type == IntentType.QUERY_TREND:
            return self._generate_trend_query(intent)
        
        elif intent.intent_type == IntentType.QUERY_STATISTICS:
            return self._generate_statistics_query(intent)
        
        elif intent.intent_type == IntentType.QUERY_INVENTORY:
            return self._generate_inventory_query(intent)
        
        elif intent.intent_type == IntentType.QUERY_PURCHASE:
            return self._generate_purchase_query(intent)
        
        elif intent.intent_type == IntentType.QUERY_CUSTOMER:
            return self._generate_customer_query(intent)
        
        else:
            return self._generate_fallback_query(intent)
    
    def _generate_sales_query(self, intent: QueryIntent) -> str:
        """生成销售查询 Cypher"""
        cypher_parts = []
        
        # MATCH 子句
        if intent.operation == '排名':
            cypher_parts.append("MATCH (c:Customer)-[:GENERATES]->(s:Sale)")
        elif intent.dimension == '产品':
            cypher_parts.append("MATCH (s:Sale)-[:SOLD_IN]->(p:Product)")
        else:
            cypher_parts.append("MATCH (s:Sale)")
        
        # WHERE 子句（时间过滤）
        where_clauses = []
        if intent.time_range:
            where_clauses.append(
                f"s.timestamp >= '{intent.time_range['start']}' "
                f"AND s.timestamp <= '{intent.time_range['end']}'"
            )
        
        if intent.region:
            where_clauses.append(f"s.region = '{intent.region}'")
        
        if where_clauses:
            cypher_parts.append("WHERE " + " AND ".join(where_clauses))
        
        # RETURN 子句
        if intent.operation == '排名':
            cypher_parts.append("RETURN c.customer_name, sum(s.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        elif intent.dimension == '产品':
            cypher_parts.append("RETURN p.name, sum(s.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        else:
            cypher_parts.append("RETURN sum(s.amount) as total, count(s) as count")
        
        return "\n".join(cypher_parts)
    
    def _generate_ranking_query(self, intent: QueryIntent) -> str:
        """生成排名查询 Cypher"""
        cypher_parts = []
        
        # 根据排名维度选择
        if '客户' in intent.raw_query or intent.dimension == '客户':
            cypher_parts.append("MATCH (c:Customer)-[:GENERATES]->(s:Sale)")
            if intent.time_range:
                cypher_parts.append(
                    f"WHERE s.timestamp >= '{intent.time_range['start']}' "
                    f"AND s.timestamp <= '{intent.time_range['end']}'"
                )
            cypher_parts.append("RETURN c.customer_name, sum(s.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        elif '产品' in intent.raw_query or intent.dimension == '产品':
            cypher_parts.append("MATCH (p:Product)<-[:SOLD_IN]-(s:Sale)")
            if intent.time_range:
                cypher_parts.append(
                    f"WHERE s.timestamp >= '{intent.time_range['start']}' "
                    f"AND s.timestamp <= '{intent.time_range['end']}'"
                )
            cypher_parts.append("RETURN p.name, sum(s.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        elif '供应商' in intent.raw_query:
            cypher_parts.append("MATCH (s:Supplier)-[:SUPPLIES]->(i:Invoice)")
            cypher_parts.append("RETURN s.vendor_name, sum(i.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        else:
            # 默认客户排名
            cypher_parts.append("MATCH (c:Customer)-[:GENERATES]->(s:Sale)")
            cypher_parts.append("RETURN c.customer_name, sum(s.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(cypher_parts)
    
    def _generate_trend_query(self, intent: QueryIntent) -> str:
        """生成趋势分析 Cypher"""
        cypher_parts = []
        
        cypher_parts.append("MATCH (s:Sale)-[:HAS_TIME]->(t:Time)")
        
        where_clauses = []
        if intent.time_range:
            where_clauses.append(
                f"s.timestamp >= '{intent.time_range['start']}' "
                f"AND s.timestamp <= '{intent.time_range['end']}'"
            )
        
        if intent.region:
            where_clauses.append(f"s.region = '{intent.region}'")
        
        if where_clauses:
            cypher_parts.append("WHERE " + " AND ".join(where_clauses))
        
        # 按时间维度分组
        if intent.dimension == '月':
            cypher_parts.append("RETURN t.year, t.month, sum(s.amount) as total")
            cypher_parts.append("ORDER BY t.year, t.month")
        elif intent.dimension == '周':
            cypher_parts.append("RETURN t.year, t.week, sum(s.amount) as total")
            cypher_parts.append("ORDER BY t.year, t.week")
        else:
            # 默认按天
            cypher_parts.append("RETURN t.year, t.month, t.day, sum(s.amount) as total")
            cypher_parts.append("ORDER BY t.year, t.month, t.day")
        
        cypher_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(cypher_parts)
    
    def _generate_statistics_query(self, intent: QueryIntent) -> str:
        """生成统计查询 Cypher"""
        cypher_parts = []
        
        if '销售' in intent.raw_query:
            cypher_parts.append("MATCH (s:Sale)")
            if intent.time_range:
                cypher_parts.append(
                    f"WHERE s.timestamp >= '{intent.time_range['start']}' "
                    f"AND s.timestamp <= '{intent.time_range['end']}'"
                )
            cypher_parts.append("RETURN sum(s.amount) as total_sales, avg(s.amount) as avg_sales, count(s) as count")
        
        elif '采购' in intent.raw_query:
            cypher_parts.append("MATCH (i:Invoice)")
            if intent.time_range:
                cypher_parts.append(
                    f"WHERE i.date >= '{intent.time_range['start']}' "
                    f"AND i.date <= '{intent.time_range['end']}'"
                )
            cypher_parts.append("RETURN sum(i.amount) as total_purchase, count(i) as count")
        
        elif '库存' in intent.raw_query:
            cypher_parts.append("MATCH (p:Product)")
            cypher_parts.append("RETURN sum(p.stock) as total_stock, avg(p.stock) as avg_stock")
        
        else:
            cypher_parts.append("MATCH (s:Sale)")
            cypher_parts.append("RETURN count(s) as total, sum(s.amount) as total_amount")
        
        return "\n".join(cypher_parts)
    
    def _generate_inventory_query(self, intent: QueryIntent) -> str:
        """生成库存查询 Cypher"""
        cypher_parts = []
        
        cypher_parts.append("MATCH (p:Product)")
        
        where_clauses = []
        
        # 库存预警
        if '预警' in intent.raw_query or '不足' in intent.raw_query:
            where_clauses.append("p.stock < p.threshold")
        
        if intent.product:
            where_clauses.append(f"p.name = '{intent.product}'")
        
        if where_clauses:
            cypher_parts.append("WHERE " + " AND ".join(where_clauses))
        
        cypher_parts.append("RETURN p.code, p.name, p.category, p.stock, p.threshold")
        cypher_parts.append("ORDER BY p.stock ASC")
        cypher_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(cypher_parts)
    
    def _generate_purchase_query(self, intent: QueryIntent) -> str:
        """生成采购查询 Cypher"""
        cypher_parts = []
        
        if '供应商' in intent.raw_query:
            cypher_parts.append("MATCH (s:Supplier)-[:SUPPLIES]->(i:Invoice)")
            if intent.time_range:
                cypher_parts.append(
                    f"WHERE i.date >= '{intent.time_range['start']}' "
                    f"AND i.date <= '{intent.time_range['end']}'"
                )
            cypher_parts.append("RETURN s.vendor_name, sum(i.amount) as total")
            cypher_parts.append("ORDER BY total DESC")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        elif '订单' in intent.raw_query:
            cypher_parts.append("MATCH (po:PurchaseOrder)")
            if intent.time_range:
                cypher_parts.append(
                    f"WHERE po.date >= '{intent.time_range['start']}' "
                    f"AND po.date <= '{intent.time_range['end']}'"
                )
            cypher_parts.append("RETURN po.segment1, po.status, po.amount")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        else:
            cypher_parts.append("MATCH (i:Invoice)")
            cypher_parts.append("RETURN i.invoice_num, i.amount, i.status")
            cypher_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(cypher_parts)
    
    def _generate_customer_query(self, intent: QueryIntent) -> str:
        """生成客户查询 Cypher"""
        cypher_parts = []
        
        if '排行' in intent.raw_query or '排名' in intent.raw_query:
            return self._generate_ranking_query(intent)
        
        cypher_parts.append("MATCH (c:Customer)")
        
        if intent.customer:
            cypher_parts.append(f"WHERE c.customer_name = '{intent.customer}'")
        
        cypher_parts.append("RETURN c.customer_name, c.customer_number, c.status")
        cypher_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(cypher_parts)
    
    def _generate_fallback_query(self, intent: QueryIntent) -> str:
        """生成兜底查询 Cypher"""
        # 通用查询：返回最近的銷售記錄
        cypher_parts = []
        
        cypher_parts.append("MATCH (s:Sale)")
        
        if intent.time_range:
            cypher_parts.append(
                f"WHERE s.timestamp >= '{intent.time_range['start']}' "
                f"AND s.timestamp <= '{intent.time_range['end']}'"
            )
        
        cypher_parts.append("RETURN s.amount, s.timestamp")
        cypher_parts.append("ORDER BY s.timestamp DESC")
        cypher_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(cypher_parts)
    
    def validate(self, cypher: str) -> bool:
        """
        验证 Cypher 查询安全性
        
        Args:
            cypher: Cypher 查询语句
            
        Returns:
            bool: 是否安全
        """
        # 禁止 DROP/DELETE/DETACH 等危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'DETACH', 'REMOVE', 'SET', 'MERGE']
        
        cypher_upper = cypher.upper()
        for keyword in dangerous_keywords:
            if keyword in cypher_upper and 'MATCH' not in cypher_upper:
                return False
        
        return True
    
    def sanitize(self, cypher: str) -> str:
        """
        清理 Cypher 查询（防止注入）
        
        Args:
            cypher: Cypher 查询语句
            
        Returns:
            str: 清理后的查询
        """
        # 移除危险字符
        cypher = cypher.replace(';', '')
        cypher = cypher.replace('//', '')
        cypher = cypher.replace('/*', '')
        cypher = cypher.replace('*/', '')
        
        # 添加 LIMIT 保护
        if 'LIMIT' not in cypher.upper():
            cypher = cypher.rstrip() + '\nLIMIT 100'
        
        return cypher


# 测试函数
def test_nl2cypher():
    """测试 NL2Cypher 引擎"""
    print("=" * 60)
    print("NL2Cypher 引擎测试")
    print("=" * 60)
    
    from app.nlu.intent_parser import NLUEngine
    
    nlu = NLUEngine()
    nl2cypher = NL2CypherEngine()
    
    test_cases = [
        "查询本月销售趋势",
        "显示 Top 10 客户排行",
        "华东区上月销售额统计",
        "库存预警商品有哪些",
    ]
    
    for query in test_cases:
        print(f"\n查询：{query}")
        intent = nlu.parse(query)
        print(f"意图：{intent.intent_type.value}")
        
        cypher = nl2cypher.generate(intent)
        print(f"Cypher:\n{cypher}\n")


if __name__ == '__main__':
    test_nl2cypher()
