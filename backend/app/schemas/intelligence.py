from pydantic import BaseModel, Field


class NLQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=8000, description="自然语言问题")


class NLQueryResponse(BaseModel):
    answer: str
    cypher: str | None = None
    records: list[dict] | None = None
    meta: dict = Field(default_factory=dict)
