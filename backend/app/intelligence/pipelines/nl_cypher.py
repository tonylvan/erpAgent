"""
自然语言 → Cypher → Neo4j → 再经 LLM 整理答案。

仅负责本流水线；不导入 replay / simulation / graph_memory 实现。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm import get_llm_provider
from app.llm.types import ChatMessage
from app.prompts.loader import load_prompt_cached, render
from app.prompts.registry import NL_CYPHER_SUMMARIZE, NL_CYPHER_SYSTEM, NL_CYPHER_USER
from app.services.nl_cypher_context import build_nl_cypher_schema_context
from app.services.neo4j_read import records_preview_json, run_read_cypher

logger = logging.getLogger(__name__)


def _extract_cypher(llm_text: str) -> str:
    t = (llm_text or "").strip()
    m = re.search(r"```(?:cypher)?\s*([\s\S]*?)```", t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t


@dataclass
class NLQueryResult:
    answer: str
    cypher: str | None = None
    records: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


def default_schema_context() -> str:
    """结构化 Schema + 约束；可选附录完整映射文档。见 app/services/nl_cypher_context.py。"""
    return build_nl_cypher_schema_context()


def run_nl_cypher_pipeline(
    question: str,
    *,
    schema_context: str | None = None,
) -> NLQueryResult:
    llm = get_llm_provider()
    if llm is None:
        return NLQueryResult(
            answer="服务未配置 LLM：请在 .env 设置 LLM_API_BASE、LLM_MODEL（及需要的 LLM_API_KEY）。",
            meta={"error": "llm_not_configured"},
        )

    ctx = schema_context if schema_context is not None else default_schema_context()
    pack_s, name_s = NL_CYPHER_SYSTEM
    pack_u, name_u = NL_CYPHER_USER
    sys_prompt = render(load_prompt_cached(pack_s, name_s), schema_context=ctx)
    user_prompt = render(load_prompt_cached(pack_u, name_u), question=question.strip())

    gen = llm.complete(
        [
            ChatMessage(role="system", content=sys_prompt),
            ChatMessage(role="user", content=user_prompt),
        ],
        temperature=0.1,
    )
    raw_text = gen.get("text") or ""
    cypher = _extract_cypher(raw_text)
    meta: dict[str, Any] = {
        "usage": gen.get("usage"),
        "model": gen.get("usage", {}).get("model"),
        "schema_context_chars": len(ctx),
    }

    records: list[dict[str, Any]] = []
    err: str | None = None
    try:
        records = run_read_cypher(cypher)
    except Exception as e:
        err = str(e)
        logger.warning("Cypher 执行失败: %s", err)
        meta["neo4j_error"] = err

    pack_sum, name_sum = NL_CYPHER_SUMMARIZE
    sum_sys = load_prompt_cached(pack_sum, name_sum)
    payload = (
        f"用户问题：\n{question}\n\n"
        f"执行的 Cypher：\n{cypher}\n\n"
        f"Neo4j 返回（JSON）：\n{records_preview_json(records)}\n"
    )
    if err:
        payload += f"\n执行错误：{err}\n"

    final = llm.complete(
        [
            ChatMessage(role="system", content=sum_sys),
            ChatMessage(role="user", content=payload),
        ],
        temperature=0.3,
    )
    answer = (final.get("text") or "").strip() or "（模型未返回内容）"
    meta["summarize_usage"] = final.get("usage")

    return NLQueryResult(
        answer=answer,
        cypher=cypher,
        records=records,
        meta=meta,
    )
