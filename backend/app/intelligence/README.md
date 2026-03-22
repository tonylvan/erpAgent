# 智能编排（Intelligence）

## 分层

| 目录 | 职责 |
|------|------|
| `pipelines/` | 可运行流水线。当前：`nl_cypher`（自然语言 → Cypher → Neo4j → LLM 整理） |
| `graph_memory/` | **端口** `GraphMemoryPort`，供未来 Graphiti / 向量记忆等接入，**不**与 NL 查询混写 |
| `replay/` | 事件回放（占位，独立演进） |
| `simulation/` | 推演 / What-if（占位，独立演进） |

## 依赖方向

- `pipelines/nl_cypher` → `app/llm`、`app/prompts`、`app/services/neo4j_read`
- 不依赖 `replay` / `simulation` / `graph_memory` 的具体实现

## Prompt

文本在 `app/prompts/packs/<pack>/*.md`，注册名在 `app/prompts/registry.py`。新增场景时复制 pack 或加文件。

## ERP 映射上下文（NL→Cypher）

- **默认**：`app/prompts/packs/nl_cypher/schema_erp_graph.md`（标签/关系/链路与索引要点）+ `cypher_constraints.md`（只读与安全规则）。与《ERP 关系型模型到图模型的映射设计》对齐，便于独立改版 Prompt。
- **可选附录**：`ERP_MAPPING_DOC_APPEND=1` 时追加 `erp_mapping_context.load_erp_mapping_schema_context()`（仓库内 `backend/docs/erp_rdb_to_graph_mapping.md` 或 `ERP_MAPPING_DOC_PATH`）。

## LLM

抽象：`app/llm/protocols.LLMProvider`，工厂：`app/llm/factory.get_llm_provider()`。新增厂商时增加 `providers/` 实现并在工厂分支注册。
