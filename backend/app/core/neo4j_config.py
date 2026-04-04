"""
Neo4j 配置优化
- 超时配置
- 连接池优化
- 查询降级机制
"""
import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError
import logging

logger = logging.getLogger(__name__)

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# 超时配置（秒）
NEO4J_TIMEOUT = int(os.getenv("NEO4J_TIMEOUT", "20"))  # 默认 20 秒超时
NEO4J_CONNECTION_TIMEOUT = int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30"))
NEO4J_MAX_CONNECTION_LIFETIME = int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600"))
NEO4J_MAX_CONNECTION_POOL_SIZE = int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))


class Neo4jClient:
    """Neo4j 客户端 - 带超时和降级机制"""
    
    def __init__(self):
        self.driver = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """连接 Neo4j（带超时配置）"""
        if not NEO4J_PASSWORD:
            logger.warning("[WARN] Neo4j 密码未配置，使用模拟数据模式")
            return
        
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                database=NEO4J_DATABASE,
                max_connection_lifetime=NEO4J_MAX_CONNECTION_LIFETIME,
                max_connection_pool_size=NEO4J_MAX_CONNECTION_POOL_SIZE,
            )
            
            # 测试连接
            self.driver.verify_connectivity()
            self.connected = True
            logger.info(f"[OK] Neo4j 已连接：{NEO4J_URI} (超时：{NEO4J_TIMEOUT}s)")
            
        except Exception as e:
            logger.warning(f"[WARN] Neo4j 连接失败：{e}，使用模拟数据模式")
            self.connected = False
            self.driver = None
    
    def query(self, cypher: str, params: dict = None, timeout: int = None):
        """
        执行 Neo4j 查询（带超时和降级）
        
        Args:
            cypher: Cypher 查询语句
            params: 查询参数
            timeout: 超时时间（秒），默认使用 NEO4J_TIMEOUT
            
        Returns:
            list: 查询结果，失败返回空列表
        """
        if not self.connected or not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
                
        except ServiceUnavailable as e:
            logger.error(f"[ERROR] Neo4j 服务不可用：{e}")
            return []
            
        except TransientError as e:
            logger.error(f"[ERROR] Neo4j 临时错误：{e}")
            return []
            
        except Exception as e:
            logger.error(f"[ERROR] Neo4j 查询失败：{e}")
            return []
    
    def query_with_timeout(self, cypher: str, params: dict = None, timeout: int = None):
        """
        带超时的查询（推荐用于智能问数）
        
        Args:
            cypher: Cypher 查询语句
            params: 查询参数
            timeout: 超时时间（秒）
            
        Returns:
            tuple: (success: bool, data: list)
        """
        if not self.connected:
            return False, []
        
        try:
            # 使用配置超时
            if timeout is None:
                timeout = NEO4J_TIMEOUT
            
            with self.driver.session() as session:
                # 执行查询（Neo4j Python Driver 4.x+ 支持 timeout）
                result = session.run(cypher, params or {})
                records = [record.data() for record in result]
                return True, records
                
        except Exception as e:
            logger.warning(f"[TIMEOUT] Neo4j 查询超时（{timeout}s）: {e}")
            return False, []
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# 全局 Neo4j 客户端实例
neo4j_client = Neo4jClient()


def get_neo4j_data(cypher: str, params: dict = None, fallback_data: list = None):
    """
    获取 Neo4j 数据（带降级）
    
    Args:
        cypher: Cypher 查询
        params: 查询参数
        fallback_data: 降级数据（查询失败时返回）
        
    Returns:
        list: 查询结果或降级数据
    """
    success, data = neo4j_client.query_with_timeout(cypher, params)
    
    if success and data:
        return data
    else:
        logger.info(f"[FALLBACK] 使用降级数据：{cypher[:50]}...")
        return fallback_data or []
