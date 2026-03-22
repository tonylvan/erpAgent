import { apiUrl } from "./baseUrl.js";

/**
 * 自然语言 → Cypher → Neo4j → LLM 整理
 * @param {string} question
 * @returns {Promise<{ answer: string, cypher: string | null, records: array | null, meta: object }>}
 */
export async function postIntelligenceQuery(question) {
  const res = await fetch(apiUrl("/api/intelligence/query"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    /* ignore */
  }
  if (!res.ok) {
    const d = data?.detail;
    const msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x.msg ?? JSON.stringify(x)).join("; ")
          : JSON.stringify(data) || res.statusText;
    throw new Error(msg || `请求失败 HTTP ${res.status}`);
  }
  return data;
}
