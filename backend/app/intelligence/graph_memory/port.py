"""
图记忆 / 外部检索抽象（Graphiti、向量库、会话摘要等）。

实现「自然语言查 Neo4j」时不要依赖本模块；编排层只依赖 Neo4j 与 LLM。
未来接入 Graphiti 时：实现 GraphMemoryPort，在独立流水线中注入，勿与 nl_cypher 混写。
"""

from __future__ import annotations

from typing import Any, Protocol


class GraphMemoryPort(Protocol):
    """预留端口：检索/写入长期记忆，与实时图查询解耦。"""

    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        """语义或混合检索，返回结构化片段。"""
        ...

    def persist(self, payload: dict[str, Any]) -> None:
        """写入记忆（可选）。"""
        ...
