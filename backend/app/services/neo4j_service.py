# Neo4j 服务模块 - 提供统一的 Neo4j 连接管理

from typing import Optional, Generator
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j 服务类"""
    
    def __init__(self, uri: str = "bolt://127.0.0.1:7687", 
                 user: str = "neo4j", 
                 password: str = "Tony1985"):
        """
        初始化 Neo4j 服务
        
        Args:
            uri: Neo4j URI
            user: 用户名
            password: 密码
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def connect(self):
        """连接到 Neo4j"""
        try:
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info(f"✅ Neo4j 连接成功：{self.uri}")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 连接失败：{e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 连接已关闭")
    
    @contextmanager
    def get_session(self) -> Generator:
        """
        获取 Neo4j 会话（上下文管理器）
        
        Yields:
            Neo4j Session
        """
        if not self.driver:
            self.connect()
        
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(self, cypher: str, parameters: Optional[dict] = None) -> list:
        """
        执行 Cypher 查询
        
        Args:
            cypher: Cypher 查询语句
            parameters: 查询参数
            
        Returns:
            list: 查询结果
        """
        try:
            with self.get_session() as session:
                result = session.run(cypher, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"查询执行失败：{e}")
            return []
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            result = self.execute_query("RETURN 1 as health")
            return len(result) > 0 and result[0].get('health') == 1
        except:
            return False


# 全局服务实例
_neo4j_service: Optional[Neo4jService] = None


def get_neo4j_service() -> Neo4jService:
    """获取 Neo4j 服务实例"""
    global _neo4j_service
    
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    
    return _neo4j_service


def get_neo4j_session():
    """获取 Neo4j 会话（用于依赖注入）"""
    service = get_neo4j_service()
    return service.get_session()


def execute_neo4j_query(cypher: str, parameters: Optional[dict] = None) -> list:
    """执行 Neo4j 查询（便捷函数）"""
    service = get_neo4j_service()
    return service.execute_query(cypher, parameters)


def neo4j_health_check() -> bool:
    """Neo4j 健康检查"""
    service = get_neo4j_service()
    return service.health_check()
