"""
加载《ERP 关系型模型到图模型的映射设计》作为 NL→Cypher 的 schema 上下文。

优先级：
1. 环境变量 ERP_MAPPING_DOC_PATH 指向的绝对/相对路径（便于引用 .openclaw 下原文）
2. 仓库内 backend/docs/erp_rdb_to_graph_mapping.md（随版本发布）
3. 内置极短回退文案
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# backend/app/services/erp_mapping_context.py → parents[2] = backend 根目录
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DOC = _BACKEND_ROOT / "docs" / "erp_rdb_to_graph_mapping.md"

_FALLBACK = (
    "图谱为 ERP 采购到付款（P2P）、应收（O2C）、总账（R2R）等领域；"
    "节点标签与关系见项目文档 docs/erp_rdb_to_graph_mapping.md。"
)


def load_erp_mapping_schema_context() -> str:
    max_chars = int(os.getenv("ERP_MAPPING_DOC_MAX_CHARS", "14000") or "14000")
    raw = os.getenv("ERP_MAPPING_DOC_PATH", "").strip()

    candidates: list[Path] = []
    if raw:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (_BACKEND_ROOT / p).resolve()
        candidates.append(p)
    candidates.append(_DEFAULT_DOC)

    for path in candidates:
        try:
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if len(text) > max_chars:
                    text = (
                        text[:max_chars]
                        + "\n\n---\n（文档已按 ERP_MAPPING_DOC_MAX_CHARS 截断；"
                        "可增大该值或精简提示词。）\n"
                    )
                logger.info("NL→Cypher schema 上下文已加载: %s (%d 字符)", path, len(text))
                return text
        except OSError as e:
            logger.warning("读取映射文档失败 %s: %s", path, e)

    logger.warning("未找到 ERP 映射文档，使用内置回退文案")
    return _FALLBACK
