"""
Prompt 逻辑名 → 文件映射。新增 pack 或改名时只改此处。
"""

from __future__ import annotations

# nl_cypher 流水线
NL_CYPHER_SYSTEM = ("nl_cypher", "cypher_system")
NL_CYPHER_USER = ("nl_cypher", "cypher_user")
NL_CYPHER_SUMMARIZE = ("nl_cypher", "summarize_system")
# 结构化 schema / 硬约束（由映射设计文档提炼，可独立维护）
NL_SCHEMA_ERP_GRAPH = ("nl_cypher", "schema_erp_graph")
NL_CYPHER_CONSTRAINTS = ("nl_cypher", "cypher_constraints")
