"""
NL→Cypher 的 Schema 上下文拼装：结构化 Prompt + 可选附录完整映射文档。

默认仅注入 prompts 包内的 schema_erp_graph + cypher_constraints（体量可控）。
设置 ERP_MAPPING_DOC_APPEND=1 时追加截断后的《ERP 关系型模型到图模型的映射设计》全文。
"""

from __future__ import annotations

import logging
import os

from app.prompts.loader import load_prompt_cached
from app.prompts.registry import NL_CYPHER_CONSTRAINTS, NL_SCHEMA_ERP_GRAPH
from app.services.erp_mapping_context import load_erp_mapping_schema_context

logger = logging.getLogger(__name__)


def build_nl_cypher_schema_context() -> str:
    core = load_prompt_cached(*NL_SCHEMA_ERP_GRAPH)
    constraints = load_prompt_cached(*NL_CYPHER_CONSTRAINTS)
    parts: list[str] = [core, constraints]

    append = os.getenv("ERP_MAPPING_DOC_APPEND", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "full",
    )
    if append:
        extra = load_erp_mapping_schema_context()
        parts.append(
            "## 附录：完整映射设计（截断）\n\n"
            + extra
        )
        logger.info("NL→Cypher 已追加完整映射文档附录")

    text = "\n\n---\n\n".join(parts)
    logger.debug("NL→Cypher schema 上下文总长度: %d", len(text))
    return text
