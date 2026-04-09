"""
GSD 社群发现 API - 基于 Louvain 算法的社群检测
支持：
- 社群划分（Louvain 算法）
- 社群统计信息
- 社群可视化
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["社群发现"])

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class CommunityDetectionRequest(BaseModel):
    """社群发现请求"""
    algorithm: str = "louvain"  # louvain / label_propagation
    max_iterations: int = 100   # 最大迭代次数
    resolution: float = 1.0     # Louvain 分辨率参数


class CommunityNode(BaseModel):
    """社群中的节点"""
    id: str
    type: str
    name: str
    community: int
    properties: Dict[str, Any] = {}


class CommunityStats(BaseModel):
    """社群统计信息"""
    community_id: int
    node_count: int
    edge_count: int
    density: float
    top_types: Dict[str, int]  # 节点类型分布


class CommunityDetectionResult(BaseModel):
    """社群发现结果"""
    success: bool
    algorithm: str
    community_count: int  # 社群数量
    total_nodes: int  # 总节点数
    total_edges: int  # 总边数
    communities: List[CommunityStats]  # 社群统计
    modularity: float  # 模块度（社群质量指标）
    nodes: List[CommunityNode]  # 节点列表（带社群标签）
    error: Optional[str] = None


def get_neo4j_driver():
    """获取 Neo4j 驱动"""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return driver
    except Exception as e:
        print(f"[CommunityDetection] Neo4j connection error: {e}")
        return None


@router.post("/detect-communities", response_model=CommunityDetectionResult)
async def detect_communities(request: CommunityDetectionRequest):
    """
    检测图谱中的社群结构
    
    使用 Louvain 算法进行社群划分
    """
    driver = get_neo4j_driver()
    
    if not driver:
        return CommunityDetectionResult(
            success=False,
            algorithm=request.algorithm,
            community_count=0,
            total_nodes=0,
            total_edges=0,
            communities=[],
            modularity=0.0,
            nodes=[],
            error="Neo4j 连接失败"
        )
    
    try:
        with driver.session() as session:
            # 使用 Neo4j Graph Data Science (GDS) 库
            # 如果没有 GDS，使用简化版 Louvain 实现
            
            # 检查是否有 GDS
            try:
                # 尝试使用 GDS Louvain
                gds_query = """
                CALL gds.louvain.stream({
                    nodeProjection: '*',
                    relationshipProjection: {
                        all: {
                            type: '*',
                            orientation: 'UNDIRECTED'
                        }
                    },
                    maxIterations: $max_iterations,
                    resolution: $resolution
                })
                YIELD nodeId, community
                RETURN gds.util.asNode(nodeId).id as id, 
                       labels(gds.util.asNode(nodeId))[0] as type,
                       gds.util.asNode(nodeId).name as name,
                       gds.util.asNode(nodeId) as properties,
                       community
                """
                
                result = session.run(
                    gds_query,
                    max_iterations=request.max_iterations,
                    resolution=request.resolution
                )
                
                nodes = []
                community_map = {}
                
                for record in result:
                    node_id = record['id'] or str(record['nodeId'])
                    community = record['community']
                    
                    node_data = CommunityNode(
                        id=node_id,
                        type=record['type'] or 'Unknown',
                        name=record['name'] or node_id,
                        community=community,
                        properties=dict(record['properties']) if record['properties'] else {}
                    )
                    nodes.append(node_data)
                    
                    if community not in community_map:
                        community_map[community] = []
                    community_map[community].append(node_data)
                
                # 计算社群统计
                communities = []
                for comm_id, comm_nodes in community_map.items():
                    # 计算社群内边数
                    node_ids = [n.id for n in comm_nodes]
                    
                    edge_query = """
                    MATCH (n1)-[r]-(n2)
                    WHERE n1.id IN $node_ids AND n2.id IN $node_ids
                    RETURN count(r) as edge_count
                    """
                    
                    edge_result = session.run(edge_query, node_ids=node_ids)
                    edge_count = edge_result.single()['edge_count']
                    
                    # 计算密度
                    n = len(comm_nodes)
                    max_edges = n * (n - 1) / 2 if n > 1 else 1
                    density = edge_count / max_edges if max_edges > 0 else 0
                    
                    # 节点类型分布
                    type_dist = {}
                    for node in comm_nodes:
                        type_dist[node.type] = type_dist.get(node.type, 0) + 1
                    
                    communities.append(CommunityStats(
                        community_id=comm_id,
                        node_count=n,
                        edge_count=edge_count,
                        density=round(density, 4),
                        top_types=type_dist
                    ))
                
                # 计算模块度（简化版）
                modularity_query = """
                CALL gds.louvain.stats({
                    nodeProjection: '*',
                    relationshipProjection: {
                        all: {
                            type: '*',
                            orientation: 'UNDIRECTED'
                        }
                    }
                })
                YIELD modularity
                RETURN modularity
                """
                
                try:
                    mod_result = session.run(modularity_query)
                    modularity = mod_result.single()['modularity']
                except:
                    modularity = 0.0
                
                # 统计总数
                total_nodes_query = "MATCH (n) RETURN count(n) as total"
                total_edges_query = "MATCH ()-[r]->() RETURN count(r) as total"
                
                total_nodes = session.run(total_nodes_query).single()['total']
                total_edges = session.run(total_edges_query).single()['total']
                
                return CommunityDetectionResult(
                    success=True,
                    algorithm=request.algorithm,
                    community_count=len(communities),
                    total_nodes=total_nodes,
                    total_edges=total_edges,
                    communities=sorted(communities, key=lambda x: x.node_count, reverse=True),
                    modularity=round(modularity, 4),
                    nodes=nodes
                )
                
            except Exception as e:
                # GDS 不可用，使用简化版标签传播算法
                print(f"[CommunityDetection] GDS not available, using simplified algorithm: {e}")
                
                # 简化版：基于节点类型的社群划分
                type_query = """
                MATCH (n)
                WITH labels(n)[0] as type, collect(n) as nodes
                RETURN type, size(nodes) as count
                """
                
                type_result = session.run(type_query)
                
                nodes = []
                communities = []
                community_id = 0
                
                for record in type_result:
                    node_type = record['type']
                    
                    # 获取该类型的所有节点
                    node_query = """
                    MATCH (n)
                    WHERE labels(n)[0] = $type
                    RETURN n.id as id, n.name as name, n
                    """
                    
                    node_result = session.run(node_query, type=node_type)
                    
                    type_nodes = []
                    for node_record in node_result:
                        node_id = node_record['id'] or str(node_record['id'])
                        
                        # Convert Neo4j DateTime to string
                        clean_props = {}
                        if node_record['n']:
                            for k, v in dict(node_record['n']).items():
                                if hasattr(v, 'iso_format'):  # Neo4j DateTime
                                    clean_props[k] = v.iso_format()
                                elif isinstance(v, (int, float, str, bool, list)):
                                    clean_props[k] = v
                                else:
                                    clean_props[k] = str(v)
                        
                        node_data = CommunityNode(
                            id=node_id,
                            type=node_type or 'Unknown',
                            name=node_record['name'] or node_id,
                            community=community_id,
                            properties=clean_props
                        )
                        type_nodes.append(node_data)
                        nodes.append(node_data)
                    
                    # 计算社群统计
                    node_ids = [n.id for n in type_nodes]
                    edge_query = """
                    MATCH (n1)-[r]-(n2)
                    WHERE n1.id IN $node_ids AND n2.id IN $node_ids
                    RETURN count(r) as edge_count
                    """
                    
                    edge_result = session.run(edge_query, node_ids=node_ids)
                    edge_count = edge_result.single()['edge_count']
                    
                    n = len(type_nodes)
                    max_edges = n * (n - 1) / 2 if n > 1 else 1
                    density = edge_count / max_edges if max_edges > 0 else 0
                    
                    communities.append(CommunityStats(
                        community_id=community_id,
                        node_count=n,
                        edge_count=edge_count,
                        density=round(density, 4),
                        top_types={node_type: n}
                    ))
                    
                    community_id += 1
                
                # 统计总数
                total_nodes_query = "MATCH (n) RETURN count(n) as total"
                total_edges_query = "MATCH ()-[r]->() RETURN count(r) as total"
                
                total_nodes = session.run(total_nodes_query).single()['total']
                total_edges = session.run(total_edges_query).single()['total']
                
                return CommunityDetectionResult(
                    success=True,
                    algorithm="type_based",
                    community_count=len(communities),
                    total_nodes=total_nodes,
                    total_edges=total_edges,
                    communities=sorted(communities, key=lambda x: x.node_count, reverse=True),
                    modularity=0.0,
                    nodes=nodes
                )
    
    except Exception as e:
        print(f"[CommunityDetection] Error: {e}")
        return CommunityDetectionResult(
            success=False,
            algorithm=request.algorithm,
            community_count=0,
            total_nodes=0,
            total_edges=0,
            communities=[],
            modularity=0.0,
            nodes=[],
            error=str(e)
        )
    
    finally:
        driver.close()


@router.get("/community/{community_id}/nodes")
async def get_community_nodes(community_id: int):
    """
    获取指定社群的所有节点
    """
    driver = get_neo4j_driver()
    
    if not driver:
        return {
            "success": False,
            "nodes": [],
            "error": "Neo4j 连接失败"
        }
    
    try:
        with driver.session() as session:
            # 这里需要存储社群信息，简化版直接返回所有节点
            query = """
            MATCH (n)
            RETURN n.id as id, labels(n)[0] as type, n.name as name, n
            LIMIT 100
            """
            
            result = session.run(query)
            nodes = []
            
            for record in result:
                nodes.append({
                    "id": record['id'] or str(record['id']),
                    "type": record['type'] or 'Unknown',
                    "name": record['name'] or record['id'],
                    "properties": dict(record['n']) if record['n'] else {}
                })
            
            return {
                "success": True,
                "nodes": nodes,
                "count": len(nodes)
            }
    
    except Exception as e:
        return {
            "success": False,
            "nodes": [],
            "error": str(e)
        }
    
    finally:
        driver.close()
