"""
GSD 路径分析 API - 查询两个节点之间的关联路径
支持：
- 最短路径查询
- 所有路径查询（限制深度）
- 路径可视化
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["路径分析"])

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class PathAnalysisRequest(BaseModel):
    """路径分析请求"""
    source_node_id: str  # 起始节点 ID
    target_node_id: str  # 目标节点 ID
    max_depth: int = 5   # 最大深度（默认 5 层）
    relationship_types: Optional[List[str]] = None  # 限制关系类型


class PathResult(BaseModel):
    """路径分析结果"""
    success: bool
    paths: List[List[Dict[str, Any]]]  # 路径列表
    path_count: int  # 找到的路径数量
    min_depth: int  # 最短路径深度
    max_depth: int  # 最长路径深度
    error: Optional[str] = None


def get_neo4j_driver():
    """获取 Neo4j 驱动"""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return driver
    except Exception as e:
        print(f"[PathAnalysis] Neo4j connection error: {e}")
        return None


@router.post("/analyze-path", response_model=PathResult)
async def analyze_path(request: PathAnalysisRequest):
    """
    分析两个节点之间的关联路径
    """
    driver = get_neo4j_driver()
    
    if not driver:
        return PathResult(
            success=False,
            paths=[],
            path_count=0,
            min_depth=0,
            max_depth=0,
            error="Neo4j 连接失败"
        )
    
    try:
        with driver.session() as session:
            # 构建 Cypher 查询
            rel_pattern = f"-[r*..{request.max_depth}]->"
            
            cypher = f"""
                MATCH (source), (target)
                WHERE source.id = $source_id AND target.id = $target_id
                MATCH path = (source){rel_pattern}(target)
                RETURN path
                LIMIT 10
            """
            
            result = session.run(
                cypher,
                source_id=request.source_node_id,
                target_id=request.target_node_id
            )
            
            paths = []
            min_depth = float('inf')
            max_depth = 0
            
            for record in result:
                path = record['path']
                path_nodes = []
                
                nodes = list(path.nodes)
                relationships = list(path.relationships)
                
                depth = len(relationships)
                min_depth = min(min_depth, depth)
                max_depth = max(max_depth, depth)
                
                for i, node in enumerate(nodes):
                    path_nodes.append({
                        "type": "node",
                        "id": node.get('id', str(node.id)),
                        "node_type": list(node.labels)[0] if node.labels else "Unknown",
                        "name": node.get('name', node.get('id', str(node.id))),
                        "properties": dict(node)
                    })
                    
                    if i < len(relationships):
                        rel = relationships[i]
                        path_nodes.append({
                            "type": "relationship",
                            "type_name": rel.type,
                            "source": rel.start_node.get('id', str(rel.start_node.id)),
                            "target": rel.end_node.get('id', str(rel.end_node.id)),
                            "properties": dict(rel)
                        })
                
                paths.append(path_nodes)
            
            if min_depth == float('inf'):
                min_depth = 0
            
            return PathResult(
                success=True,
                paths=paths,
                path_count=len(paths),
                min_depth=min_depth,
                max_depth=max_depth
            )
    
    except Exception as e:
        print(f"[PathAnalysis] Error: {e}")
        return PathResult(
            success=False,
            paths=[],
            path_count=0,
            min_depth=0,
            max_depth=0,
            error=str(e)
        )
    
    finally:
        driver.close()


@router.get("/node/{node_id}/neighbors")
async def get_node_neighbors(node_id: str, depth: int = 1):
    """
    获取节点的邻居节点（指定深度）
    """
    driver = get_neo4j_driver()
    
    if not driver:
        return {
            "success": False,
            "nodes": [],
            "edges": [],
            "error": "Neo4j 连接失败"
        }
    
    try:
        with driver.session() as session:
            cypher = f"""
                MATCH (center)
                WHERE center.id = $node_id
                OPTIONAL MATCH (center)-[r*..{depth}]-(neighbor)
                RETURN center, collect(DISTINCT neighbor) as neighbors, collect(DISTINCT r) as relationships
            """
            
            result = session.run(cypher, node_id=node_id)
            record = result.single()
            
            if not record:
                return {
                    "success": False,
                    "nodes": [],
                    "edges": [],
                    "error": "未找到中心节点"
                }
            
            nodes = []
            node_ids = set()
            
            center = record['center']
            center_id = center.get('id', str(center.id))
            nodes.append({
                "id": center_id,
                "type": list(center.labels)[0] if center.labels else "Unknown",
                "name": center.get('name', center_id),
                "properties": dict(center),
                "isCenter": True
            })
            node_ids.add(center_id)
            
            for neighbor in record['neighbors']:
                if neighbor:
                    neighbor_id = neighbor.get('id', str(neighbor.id))
                    if neighbor_id not in node_ids:
                        nodes.append({
                            "id": neighbor_id,
                            "type": list(neighbor.labels)[0] if neighbor.labels else "Unknown",
                            "name": neighbor.get('name', neighbor_id),
                            "properties": dict(neighbor),
                            "isCenter": False
                        })
                        node_ids.add(neighbor_id)
            
            edges = []
            for rel_list in record['relationships']:
                if rel_list:
                    for rel in rel_list:
                        if rel:
                            edges.append({
                                "source": rel.start_node.get('id', str(rel.start_node.id)),
                                "target": rel.end_node.get('id', str(rel.end_node.id)),
                                "type": rel.type,
                                "properties": dict(rel)
                            })
            
            return {
                "success": True,
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "depth": depth
                }
            }
    
    except Exception as e:
        print(f"[PathAnalysis] Error: {e}")
        return {
            "success": False,
            "nodes": [],
            "edges": [],
            "error": str(e)
        }
    
    finally:
        driver.close()
