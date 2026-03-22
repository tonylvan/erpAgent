# Cypher 生成约束（必须遵守）

## 只读与安全

- **仅允许**读：`MATCH`、`OPTIONAL MATCH`、`WHERE`、`WITH`、`RETURN`、`ORDER BY`、`SKIP`、`LIMIT`、`UNWIND`、`COLLECT`、`COUNT`、`DISTINCT` 等。
- **禁止**任何写：`CREATE`、`MERGE`、`DELETE`、`DETACH DELETE`、`SET`、`REMOVE`、`DROP`、`LOAD CSV`、管理类 `CALL`（如 `apoc.*` 写操作）。
- 若环境未开放 `CALL`，默认禁止 `CALL`；需要 `db.labels` 等探查时由运维配置放开。

## 结果规模

- **必须**带 `LIMIT`（或 `WITH` 子句后再 `LIMIT` 的可证明有界写法）；若用户未指定，使用合理默认如 **200**。
- 避免全图 `MATCH (n)` 无过滤；探查时用 `MATCH (n:Label) RETURN n LIMIT 20`。

## 与 Schema 一致

- 节点标签、关系类型、属性名使用 **英文驼峰**（与 Neo4j 存储及映射文档一致），如 `:Supplier`、`[:HAS_LINE]`、`invoiceNum`。
- 不确定标签时：先 `CALL db.labels()` 或 `MATCH (n) RETURN labels(n) LIMIT 1` 类探查（仅当允许 CALL）。

## 参数化

- 优先使用 `$param` 参数占位（若驱动支持）；字符串拼接时注意转义。

## 输出格式

- 只输出 **一条** 可执行 Cypher；可附 `//` 单行注释。
- 需要多步时，用 **一条** 语句内的 `WITH` 链式完成，或只返回最关键的一条查询。
