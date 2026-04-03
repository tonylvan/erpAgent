"""PostgreSQL 数据服务：提供关系型数据查询接口。"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# 连接池全局变量
_connection_pool: pool.SimpleConnectionPool | None = None


def get_connection_pool() -> pool.SimpleConnectionPool | None:
    """获取 PostgreSQL 连接池。"""
    global _connection_pool
    
    if _connection_pool is not None:
        return _connection_pool
    
    # 从环境变量读取配置
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "erpagent")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    
    if not password:
        logger.warning("未配置 POSTGRES_PASSWORD，PostgreSQL 服务不可用")
        return None
    
    try:
        minconn = int(os.getenv("POSTGRES_POOL_MIN", "1"))
        maxconn = int(os.getenv("POSTGRES_POOL_MAX", "10"))
        
        _connection_pool = pool.SimpleConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        logger.info(f"PostgreSQL 连接池创建成功 (min={minconn}, max={maxconn})")
        return _connection_pool
    except Exception as e:
        logger.error(f"PostgreSQL 连接池创建失败：{e}")
        return None


@contextmanager
def get_connection() -> Generator[Any, None, None]:
    """获取数据库连接（上下文管理器）。"""
    pool_instance = get_connection_pool()
    if pool_instance is None:
        raise RuntimeError("PostgreSQL 未配置")
    
    conn = None
    try:
        conn = pool_instance.getconn()
        yield conn
    finally:
        if conn:
            pool_instance.putconn(conn)


def execute_query(
    query: str,
    params: tuple | dict | None = None,
    fetch: str = "all",
    timeout: int = 30,
) -> list[dict] | dict | int:
    """
    执行 SQL 查询。
    
    Args:
        query: SQL 查询语句
        params: 查询参数
        fetch: 返回模式 ("all", "one", "count")
        timeout: 查询超时时间（秒）
    
    Returns:
        查询结果
    """
    conn = None
    try:
        with get_connection() as conn:
            conn.set_session(readonly=True, autocommit=False)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SET statement_timeout = {timeout * 1000}")
                cur.execute(query, params)
                
                if fetch == "count":
                    return cur.rowcount
                elif fetch == "one":
                    result = cur.fetchone()
                    return dict(result) if result else None
                else:  # "all"
                    results = cur.fetchall()
                    return [dict(row) for row in results]
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL 查询错误：{e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.commit()


def execute_write(
    query: str,
    params: tuple | dict | None = None,
    return_id: bool = False,
) -> int | dict | None:
    """
    执行写操作（INSERT/UPDATE/DELETE）。
    
    Args:
        query: SQL 语句
        params: 参数
        return_id: 是否返回自增 ID
    
    Returns:
        影响的行数或插入的 ID
    """
    conn = None
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if return_id:
                    query = query.rstrip(";") + " RETURNING id"
                    cur.execute(query, params)
                    result = cur.fetchone()
                    conn.commit()
                    return dict(result) if result else None
                else:
                    cur.execute(query, params)
                    conn.commit()
                    return cur.rowcount
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL 写操作错误：{e}")
        if conn:
            conn.rollback()
        raise


# ============ 业务查询方法 ============

def get_table_list(schema: str = "public") -> list[dict]:
    """获取所有表信息。"""
    query = """
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        ORDER BY table_name
    """
    return execute_query(query, (schema,))


def get_table_columns(table_name: str, schema: str = "public") -> list[dict]:
    """获取表的列信息。"""
    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """
    return execute_query(query, (schema, table_name))


def get_table_data(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    where_clause: str = "",
    where_params: tuple = (),
    order_by: str = "",
) -> dict:
    """
    获取表数据（分页）。
    
    Returns:
        {
            "data": [...],
            "total": 123,
            "limit": 100,
            "offset": 0
        }
    """
    schema = "public"
    
    # 计数查询
    count_query = f"""
        SELECT COUNT(*) as total
        FROM {schema}.{table_name}
        {where_clause}
    """
    total_result = execute_query(count_query, where_params, fetch="one")
    total = total_result["total"] if total_result else 0
    
    # 数据查询
    data_query = f"""
        SELECT *
        FROM {schema}.{table_name}
        {where_clause}
        {order_by}
        LIMIT %s OFFSET %s
    """
    data_params = where_params + (limit, offset)
    data = execute_query(data_query, data_params)
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def search_tables(keyword: str) -> list[dict]:
    """搜索表名包含关键字的表。"""
    query = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name ILIKE %s
        ORDER BY table_name
        LIMIT 50
    """
    return execute_query(query, (f"%{keyword}%",))


def get_statistics() -> dict:
    """获取数据库统计信息。"""
    stats = {
        "table_count": 0,
        "total_rows": 0,
        "top_tables": [],
    }
    
    # 表数量
    result = execute_query(
        "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = 'public'",
        fetch="one",
    )
    stats["table_count"] = result["count"] if result else 0
    
    # 前 10 个大表
    result = execute_query("""
        SELECT 
            schemaname || '.' || tablename as table_name,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes
        FROM pg_stat_user_tables
        ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
        LIMIT 10
    """)
    stats["top_tables"] = result or []
    
    return stats
