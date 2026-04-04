"""
数据库连接管理
"""

import psycopg2
from psycopg2 import pool
from app.core.config import postgres_config
import logging

logger = logging.getLogger(__name__)

# 数据库连接池
db_pool = None


def get_db_pool():
    """获取数据库连接池"""
    global db_pool
    if db_pool is None:
        try:
            db_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # minconn
                20,  # maxconn
                host=postgres_config.host,
                port=postgres_config.port,
                database=postgres_config.database,
                user=postgres_config.user,
                password=postgres_config.password
            )
            logger.info("数据库连接池创建成功")
        except Exception as e:
            logger.error(f"创建数据库连接池失败：{e}")
            raise
    return db_pool


def get_db():
    """获取数据库连接（用于 FastAPI Depends）"""
    db = None
    try:
        pool = get_db_pool()
        db = pool.getconn()
        yield db
    finally:
        if db:
            pool.putconn(db)


def close_db_pool():
    """关闭数据库连接池"""
    global db_pool
    if db_pool:
        db_pool.closeall()
        logger.info("数据库连接池已关闭")


# 简单的连接测试
def test_connection():
    """测试数据库连接"""
    try:
        conn = psycopg2.connect(
            host=postgres_config.host,
            port=postgres_config.port,
            database=postgres_config.database,
            user=postgres_config.user,
            password=postgres_config.password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logger.info(f"PostgreSQL 连接成功：{version}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL 连接失败：{e}")
        return False


if __name__ == "__main__":
    # 测试连接
    success = test_connection()
    if success:
        print("✅ 数据库连接测试通过")
    else:
        print("❌ 数据库连接测试失败")
