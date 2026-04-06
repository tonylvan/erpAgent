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
        description="schema=知识图谱(默认), instances=实例数据",
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
        raise HTTPException(status_code=500, detail=f"查询失败:{e}") from e


@router.post("/query")
def execute_cypher(
    cypher: str,
    parameters: dict[str, Any] | None = None,
    limit: int | None = Query(None, description="结果数量限制"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    执行只读 Cypher 查询。

    注意:仅允许 MATCH 查询,禁止 CREATE/DELETE 等写操作。
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
        raise HTTPException(status_code=500, detail=f"查询失败:{e}") from e


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


@router.get("/entity/{entity_id}")
def get_entity_detail(
    entity_id: str,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    获取实体详情。
    
    返回指定 ID 的实体及其所有属性。
    """
    try:
        cypher = """
        MATCH (n)
        WHERE id(n) = $entity_id OR n.id = $entity_id OR n.entity_id = $entity_id
        RETURN n
        LIMIT 1
        """
        result = run_read_cypher(
            cypher,
            parameters={"entity_id": int(entity_id) if entity_id.isdigit() else entity_id},
            fetch="one"
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # Extract node properties
        node = result.get("n", {})
        properties = dict(node) if hasattr(node, 'keys') else node
        
        return {
            "success": True,
            "data": {
                "id": entity_id,
                "properties": properties,
                "labels": list(node.keys()) if hasattr(node, 'keys') else []
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/entity/{entity_id}/relationships")
def get_entity_relationships(
    entity_id: str,
    depth: int = Query(1, ge=1, le=3, description="关系深度 (1-3 跳)"),
    rel_type: str | None = Query(None, description="关系类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="结果数量限制"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    获取实体的关系网络。
    
    支持 1-3 跳关系探索，可选关系类型过滤。
    """
    try:
        entity_id_value = int(entity_id) if entity_id.isdigit() else entity_id
        
        if rel_type:
            cypher = f"""
            MATCH (n)-[r:{rel_type}*1..{depth}]-(m)
            WHERE id(n) = $entity_id OR n.id = $entity_id OR n.entity_id = $entity_id
            RETURN n, r, m
            LIMIT $limit
            """
        else:
            cypher = f"""
            MATCH path=(n)-[*1..{depth}]-(m)
            WHERE id(n) = $entity_id OR n.id = $entity_id OR n.entity_id = $entity_id
            WITH n, relationships(path) as rels, nodes(path) as nodes
            UNWIND rels as r
            RETURN n, r, m
            LIMIT $limit
            """
        
        result = run_read_cypher(
            cypher,
            parameters={"entity_id": entity_id_value, "limit": limit}
        )
        
        # Process results
        nodes = {}
        relationships = []
        
        for row in result:
            if 'n' in row:
                n_data = dict(row['n']) if hasattr(row['n'], 'keys') else row['n']
                n_id = getattr(row['n'], 'id', hash(str(n_data)))
                nodes[str(n_id)] = n_data
            if 'm' in row:
                m_data = dict(row['m']) if hasattr(row['m'], 'keys') else row['m']
                m_id = getattr(row['m'], 'id', hash(str(m_data)))
                nodes[str(m_id)] = m_data
            if 'r' in row:
                r_type = type(row['r']).__name__ if hasattr(row['r'], '__class__') else str(row['r'])
                r_props = dict(row['r']) if hasattr(row['r'], 'keys') else {}
                relationships.append({"type": r_type, "properties": r_props})
        
        return {
            "success": True,
            "data": {
                "entity_id": entity_id,
                "depth": depth,
                "nodes": list(nodes.values()),
                "relationships": relationships,
                "count": len(nodes)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/entity/{from_id}/path/to/{to_id}")
def find_entity_path(
    from_id: str,
    to_id: str,
    max_depth: int = Query(5, ge=1, le=10, description="最大搜索深度"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    查找两个实体之间的路径。
    
    使用最短路径算法查找连接。
    """
    try:
        from_id_value = int(from_id) if from_id.isdigit() else from_id
        to_id_value = int(to_id) if to_id.isdigit() else to_id
        
        cypher = """
        MATCH (n), (m)
        WHERE (id(n) = $from_id OR n.id = $from_id OR n.entity_id = $from_id)
          AND (id(m) = $to_id OR m.id = $to_id OR m.entity_id = $to_id)
        MATCH path = shortestPath((n)-[*1..$max_depth]-(m))
        RETURN path
        LIMIT 1
        """
        
        result = run_read_cypher(
            cypher,
            parameters={"from_id": from_id_value, "to_id": to_id_value, "max_depth": max_depth},
            fetch="one"
        )
        
        if not result or not result.get("path"):
            return {
                "success": True,
                "data": {
                    "from_id": from_id,
                    "to_id": to_id,
                    "path": None,
                    "message": "未找到连接路径"
                }
            }
        
        path = result["path"]
        nodes = [dict(n) for n in path.nodes] if hasattr(path, 'nodes') else []
        rels = [type(r).__name__ for r in path.relationships] if hasattr(path, 'relationships') else []
        
        return {
            "success": True,
            "data": {
                "from_id": from_id,
                "to_id": to_id,
                "path": {
                    "nodes": nodes,
                    "relationships": rels,
                    "length": len(nodes)
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e


@router.get("/entities/search")
def search_entities(
    keyword: str | None = Query(None, description="搜索关键词"),
    label: str | None = Query(None, description="实体类型/标签"),
    limit: int = Query(50, ge=1, le=500, description="结果数量限制"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    搜索实体。
    
    支持关键词和标签过滤。
    """
    try:
        conditions = []
        params = {"limit": limit}
        
        if keyword:
            conditions.append("toString(id(n)) CONTAINS $keyword OR ANY(k IN keys(n) WHERE toString(n[k]) CONTAINS $keyword)")
            params["keyword"] = keyword
        
        if label:
            conditions.append("$label IN labels(n)")
            params["label"] = label
        
        where_clause = " AND ".join(conditions) if conditions else "true"
        
        cypher = f"""
        MATCH (n)
        WHERE {where_clause}
        RETURN n
        LIMIT $limit
        """
        
        result = run_read_cypher(cypher, parameters=params)
        
        entities = []
        for row in result:
            node = row.get("n", {})
            entities.append({
                "id": str(getattr(node, 'id', hash(str(node)))),
                "properties": dict(node) if hasattr(node, 'keys') else node,
                "labels": list(node.keys()) if hasattr(node, 'keys') else []
            })
        
        return {
            "success": True,
            "data": entities,
            "count": len(entities)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{e}") from e
