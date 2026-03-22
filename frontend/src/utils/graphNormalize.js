const VALID_ROLES = ["object", "event", "relation", "property", "master", "subobject"];

/**
 * 统一 Neo4j 返回的节点字段，避免 role/shape 与模板不一致时整块不渲染。
 */
export function normalizeGraphNode(n) {
  let role = String(n.role ?? "object").toLowerCase().trim();
  if (!VALID_ROLES.includes(role)) role = "object";

  // 与后端 node_to_payload 一致，避免 API 里 shape/role 矛盾导致模板无分支
  const shape =
    role === "relation" ? "diamond" : role === "event" ? "neuron" : "card";

  const w = Number(n.w) > 0 ? Number(n.w) : 112;
  const h = Number(n.h) > 0 ? Number(n.h) : 54;
  const rx = n.rx != null && !Number.isNaN(Number(n.rx)) ? Number(n.rx) : 12;

  return {
    ...n,
    id: String(n.id ?? ""),
    role,
    shape,
    w,
    h,
    rx,
    title: n.title != null ? String(n.title) : "未命名",
    sub: n.sub != null ? String(n.sub) : "",
    labels: Array.isArray(n.labels) ? n.labels : [],
  };
}
