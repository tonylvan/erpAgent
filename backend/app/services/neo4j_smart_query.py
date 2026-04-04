"""
Neo4j 智能查询引擎
基于学习到的本体结构，提供自然语言到 Cypher 的转换
"""
import os
from neo4j import GraphDatabase

class Neo4jQueryEngine:
    """Neo4j 智能查询引擎"""
    
    def __init__(self):
        uri = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'Tony1985')
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.timeout = int(os.getenv('NEO4J_QUERY_TIMEOUT', '5') or '5')
        
        # 查询模板库
        self.query_templates = {
            'sale_trend': """
                MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
                RETURN t.day as day, sum(s.amount) as amount
                ORDER BY t.day
            """,
            'customer_rank': """
                MATCH (c:Customer)-[:PURCHASED]->(o:Order)
                RETURN c.name as customer, count(o) as orders, sum(o.amount) as total
                ORDER BY total DESC
                LIMIT 10
            """,
            'inventory_warning': """
                MATCH (p:Product)
                WHERE p.stock < p.threshold
                RETURN p.code as code, p.name as name, p.stock as stock, p.threshold as threshold
                ORDER BY p.stock
            """,
            'payment_stats': """
                MATCH (p:Payment)
                RETURN p.status as status, count(p) as count, sum(p.amount) as total
                GROUP BY p.status
            """,
            'employee_count': """
                MATCH (e:Employee)
                RETURN count(e) as total
            """,
        }
    
    def execute(self, question: str) -> dict:
        """执行自然语言查询"""
        q = question.lower()
        
        # 销售趋势
        if '销售' in q and ('趋势' in q or '走势' in q):
            return self._execute_cypher(self.query_templates['sale_trend'], 'chart')
        
        # 客户排行
        if '客户' in q and ('排行' in q or '排名' in q or 'top' in q):
            return self._execute_cypher(self.query_templates['customer_rank'], 'table')
        
        # 库存查询
        if '库存' in q or '预警' in q:
            return self._execute_cypher(self.query_templates['inventory_warning'], 'table')
        
        # 付款统计
        if '付款' in q:
            return self._execute_cypher(self.query_templates['payment_stats'], 'stats')
        
        # 员工查询
        if '员工' in q or '职员' in q or '人力' in q:
            return self._execute_cypher(self.query_templates['employee_count'], 'stats')
        
        # 默认返回
        return {
            'success': False,
            'answer': '暂不支持该查询',
            'data_type': 'text'
        }
    
    def _execute_cypher(self, cypher: str, data_type: str) -> dict:
        """执行 Cypher 查询"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher, timeout=self.timeout)
                records = [r.data() for r in result]
                
                if not records:
                    return {
                        'success': True,
                        'answer': '未查询到数据',
                        'data_type': 'text'
                    }
                
                # 根据数据类型构建响应
                if data_type == 'chart':
                    return self._build_chart_response(records)
                elif data_type == 'table':
                    return self._build_table_response(records)
                elif data_type == 'stats':
                    return self._build_stats_response(records)
                else:
                    return {
                        'success': True,
                        'answer': str(records),
                        'data_type': 'text'
                    }
        except Exception as e:
            return {
                'success': False,
                'answer': f'查询失败：{str(e)}',
                'data_type': 'text'
            }
    
    def _build_chart_response(self, records: list) -> dict:
        """构建图表响应"""
        if not records:
            return {'success': False, 'answer': '无数据', 'data_type': 'text'}
        
        first = records[0]
        x_key = list(first.keys())[0]
        y_key = list(first.keys())[1] if len(first.keys()) > 1 else list(first.keys())[0]
        
        return {
            'success': True,
            'answer': f'查询到 {len(records)} 条趋势数据',
            'data_type': 'chart',
            'chart_config': {
                'type': 'line',
                'title': '趋势分析',
                'xAxis': [str(r[x_key]) for r in records],
                'yAxis': [float(r[y_key]) if isinstance(r[y_key], (int, float)) else 0 for r in records],
                'xName': x_key,
                'yName': y_key
            }
        }
    
    def _build_table_response(self, records: list) -> dict:
        """构建表格响应"""
        if not records:
            return {'success': False, 'answer': '无数据', 'data_type': 'text'}
        
        columns = list(records[0].keys())
        rows = []
        for r in records:
            row = {}
            for k, v in r.items():
                row[k] = f'¥{v:,.0f}' if isinstance(v, (int, float)) and v > 1000 else v
            rows.append(row)
        
        return {
            'success': True,
            'answer': f'查询到 {len(records)} 条记录',
            'data_type': 'table',
            'data': {
                'columns': columns,
                'rows': rows
            }
        }
    
    def _build_stats_response(self, records: list) -> dict:
        """构建统计响应"""
        if not records:
            return {'success': False, 'answer': '无数据', 'data_type': 'text'}
        
        items = []
        for r in records:
            label = list(r.values())[0]
            value = list(r.values())[1] if len(r) > 1 else list(r.values())[0]
            items.append({
                'label': str(label),
                'value': f'{value:,.0f}' if isinstance(value, (int, float)) else str(value)
            })
        
        return {
            'success': True,
            'answer': f'查询到 {len(records)} 条统计',
            'data_type': 'stats',
            'data': {
                'items': items
            }
        }
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# 测试
if __name__ == '__main__':
    engine = Neo4jQueryEngine()
    
    test_queries = [
        '销售趋势',
        '客户排行',
        '库存预警',
        '付款统计',
        '员工数量'
    ]
    
    print('=' * 60)
    print('Neo4j 智能查询测试')
    print('=' * 60)
    
    for q in test_queries:
        print(f'\n查询：{q}')
        print('-' * 60)
        result = engine.execute(q)
        print(f'类型：{result.get("data_type")}')
        print(f'回答：{result.get("answer", "")[:200]}')
        if result.get('data'):
            print(f'数据：{result.get("data")}')
    
    engine.close()
    print('\n' + '=' * 60)
    print('测试完成！')
    print('=' * 60)
