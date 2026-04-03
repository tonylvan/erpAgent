"""数据查询 API。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any

from app.auth.jwt import UserInfo, get_current_user
from app.services.postgres_service import (
    get_table_list,
    get_table_columns,
    get_table_data,
    search_tables,
    get_statistics,
)

router = APIRouter(prefix="/data", tags=["数据查询"])


@router.get("/tables")
def list_tables(
    schema: str = Query("public", description="Schema 名称"),
    current_user: UserInfo = Depends(get_current_user),
):
    """获取所有表列表。"""
    try:
        tables = get_table_list(schema)
        return {
            "success": True,
            "data": tables,
            "count": len(tables),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/tables/search")
def search_tables_api(
    keyword: str = Query(..., min_length=1, description="搜索关键字"),
    current_user: UserInfo = Depends(get_current_user),
):
    """搜索表名。"""
    try:
        tables = search_tables(keyword)
        return {
            "success": True,
            "data": tables,
            "count": len(tables),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败：{e}") from e


@router.get("/tables/{table_name}/columns")
def get_columns(
    table_name: str,
    schema: str = Query("public", description="Schema 名称"),
    current_user: UserInfo = Depends(get_current_user),
):
    """获取表的列信息。"""
    try:
        columns = get_table_columns(table_name, schema)
        return {
            "success": True,
            "data": columns,
            "count": len(columns),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/tables/{table_name}/data")
def get_data(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    where: str = Query("", description="WHERE 子句（不含 WHERE 关键字）"),
    order_by: str = Query("", description="ORDER BY 子句（不含 ORDER BY 关键字）"),
    schema: str = Query("public", description="Schema 名称"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    获取表数据（分页）。
    
    注意：where 参数存在 SQL 注入风险，生产环境应使用参数化查询或白名单验证。
    """
    try:
        # 简单的 SQL 注入防护
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
        where_upper = where.upper()
        for kw in dangerous_keywords:
            if kw in where_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"WHERE 子句包含禁止的关键字：{kw}",
                )
        
        # 构建 WHERE 子句
        where_clause = f"WHERE {where}" if where.strip() else ""
        
        # 构建 ORDER BY 子句
        order_clause = f"ORDER BY {order_by}" if order_by.strip() else ""
        
        result = get_table_data(
            table_name=table_name,
            limit=limit,
            offset=offset,
            where_clause=where_clause,
            where_params=(),
            order_by=order_clause,
        )
        
        return {
            "success": True,
            "data": result["data"],
            "pagination": {
                "total": result["total"],
                "limit": result["limit"],
                "offset": result["offset"],
                "has_more": result["offset"] + result["limit"] < result["total"],
            },
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/statistics")
def get_db_statistics(
    current_user: UserInfo = Depends(get_current_user),
):
    """获取数据库统计信息。"""
    try:
        stats = get_statistics()
        return {
            "success": True,
            "data": stats,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e
