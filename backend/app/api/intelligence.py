"""智能问答 API：与 graph 路由分离；未来 replay/simulation 另建路由。"""

from fastapi import APIRouter, HTTPException

from app.intelligence.pipelines.nl_cypher import run_nl_cypher_pipeline
from app.schemas.intelligence import NLQueryRequest, NLQueryResponse

router = APIRouter()


@router.post("/query", response_model=NLQueryResponse)
def nl_query(body: NLQueryRequest) -> NLQueryResponse:
    """
    自然语言 → LLM 生成 Cypher → Neo4j 只读查询 → LLM 整理回答。
    """
    try:
        result = run_nl_cypher_pipeline(body.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return NLQueryResponse(
        answer=result.answer,
        cypher=result.cypher,
        records=result.records or None,
        meta=result.meta,
    )
