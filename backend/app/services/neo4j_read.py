"""只读 Cypher 执行：供 NL 查询等场景使用，与 ontology 聚合逻辑分离。"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from neo4j.graph import Node, Path, Relationship

from app.services.neo4j_ontology import _session, get_driver

logger = logging.getLogger(__name__)

# 禁止写操作与高危调用（可按环境放宽）
_FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH\s+DELETE|SET|REMOVE|DROP|LOAD\s+CSV|"
    r"CREATE\s+INDEX|CREATE\s+CONSTRAINT|FOREACH)\b",
    re.IGNORECASE | re.MULTILINE,
)


def _serialize_value(v: Any) -> Any:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, Node):
        return {"_type": "node", "labels": list(v.labels), "properties": dict(v)}
    if isinstance(v, Relationship):
        return {"_type": "relationship", "type": v.type, "properties": dict(v)}
    if isinstance(v, Path):
        return {
            "_type": "path",
            "nodes": [_serialize_value(n) for n in v.nodes],
            "relationships": [_serialize_value(r) for r in v.relationships],
        }
    if isinstance(v, list):
        return [_serialize_value(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _serialize_value(x) for k, x in v.items()}
    return str(v)


def validate_read_only_cypher(cypher: str) -> None:
    if not cypher or not cypher.strip():
        raise ValueError("Cypher 为空")
    if _FORBIDDEN.search(cypher):
        raise ValueError("仅允许只读查询：检测到禁止的关键字")
    raw = (os.getenv("NEO4J_NL_ALLOW_CALL", "") or "").strip().lower() in ("1", "true", "yes")
    if not raw and re.search(r"\bCALL\b", cypher, re.IGNORECASE):
        raise ValueError("默认禁止 CALL；若需 CALL db.labels() 等，设置 NEO4J_NL_ALLOW_CALL=1")


def run_read_cypher(
    cypher: str,
    *,
    parameters: dict[str, Any] | None = None,
    default_limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    执行只读 Cypher，返回可 JSON 序列化的行列表。
    default_limit：若语句中不含 LIMIT，则追加 LIMIT（简单拼接，复杂查询请在 Prompt 中要求模型写 LIMIT）。
    """
    validate_read_only_cypher(cypher)
    q = cypher.strip().rstrip(";")
    lim = default_limit if default_limit is not None else int(os.getenv("NEO4J_NL_DEFAULT_LIMIT", "200") or "200")
    if lim > 0 and not re.search(r"\bLIMIT\b", q, re.IGNORECASE):
        q = f"{q} LIMIT {lim}"

    driver = get_driver()
    if driver is None:
        raise RuntimeError("Neo4j 未配置（NEO4J_PASSWORD）")

    params = dict(parameters or {})
    out: list[dict[str, Any]] = []
    try:
        with _session(driver) as session:
            result = session.run(q, params)
            for record in result:
                row: dict[str, Any] = {}
                for k in record.keys():
                    row[str(k)] = _serialize_value(record[k])
                out.append(row)
    finally:
        driver.close()

    return out


def records_preview_json(records: list[dict[str, Any]], max_chars: int = 12000) -> str:
    s = json.dumps(records, ensure_ascii=False, indent=2)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 20] + "\n…(截断)"
