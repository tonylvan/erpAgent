from fastapi import APIRouter, HTTPException, Query

from app.services.neo4j_ontology import fetch_ontology_graph

router = APIRouter()


@router.get("/ontology")
def get_ontology_graph(
    mode: str | None = Query(
        None,
        description="schema=按标签与关系类型聚合的知识图谱（默认）；instances=具体节点与关系子图",
    ),
):
    """拉取 Neo4j 图谱：默认可视化本体/逻辑关系；可选 instances 查看实例数据。"""
    try:
        return fetch_ontology_graph(mode=mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
