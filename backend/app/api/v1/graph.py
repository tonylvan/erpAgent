"""图查询 API v1。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any

from app.auth.jwt import UserInfo, get_current_user
from app.services.neo4j_ontology import fetch_ontology_graph
from app.services.neo4j_read import run_read_cypher

router = APIRouter(tags=["图查询"])


@router.get("/ontology")
def get_ontology(
    mode: str | None = Query(
        None,
        description="schema=知识图谱（默认）, instances=实例数据",
    ),
    current_user: UserInfo = Depends(get_current_user),
):
    """获取本体图谱。"""
    try:
        result = fetch_ontology_graph(mode=mode)
        return {
            "success": True,
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.post("/query")
def execute_cypher(
    cypher: str,
    parameters: dict[str, Any] | None = None,
    limit: int | None = Query(None, description="结果数量限制"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    执行只读 Cypher 查询。
    
    注意：仅允许 MATCH 查询，禁止 CREATE/DELETE 等写操作。
    """
    try:
        result = run_read_cypher(cypher, parameters=parameters, default_limit=limit)
        return {
            "success": True,
            "data": result,
            "count": len(result),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/stats")
def get_graph_stats(
    current_user: UserInfo = Depends(get_current_user),
):
    """获取图数据库统计信息。"""
    try:
        # 获取节点和关系总数
        node_count = run_read_cypher("MATCH (n) RETURN count(n) as count", fetch="one")
        rel_count = run_read_cypher("MATCH ()-[r]->() RETURN count(r) as count", fetch="one")
        
        # 获取标签分布
        labels = run_read_cypher("""
            CALL db.labels() YIELD label
            MATCH (n)
            WHERE label IN labels(n)
            RETURN label, count(n) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        
        # 获取关系类型分布
        rel_types = run_read_cypher("""
            CALL db.relationshipTypes() YIELD relationshipType
            MATCH ()-[r]->()
            WHERE type(r) = relationshipType
            RETURN relationshipType, count(r) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        
        return {
            "success": True,
            "data": {
                "node_count": node_count[0]["count"] if node_count else 0,
                "relationship_count": rel_count[0]["count"] if rel_count else 0,
                "label_distribution": labels,
                "relationship_type_distribution": rel_types,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e
