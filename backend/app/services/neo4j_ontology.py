"""
从本地 Neo4j 读取本体全景：有向关系 +（可选）全库节点补全，含孤立主数据；
节点角色 object | master | subobject | event | property | relation。
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from neo4j import Driver, GraphDatabase

logger = logging.getLogger(__name__)


def _ontology_trace(msg: str) -> None:
    """终端调试：backend/.env 设置 NEO4J_ONTOLOGY_TRACE=1 时打印获取流程。"""
    logger.info("[ontology] %s", msg)
    if os.getenv("NEO4J_ONTOLOGY_TRACE", "").strip().lower() in ("1", "true", "yes"):
        print(f"[ontology] {msg}", flush=True)
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

DEFAULT_KIND_LABELS: dict[str, list[str]] = {
    "event": ["Event", "DomainEvent", "BusinessEvent", "ErpEvent", "领域事件"],
    "property": ["Property", "Attribute", "Field", "Column", "Attr", "属性"],
    "relation": [
        "Relation",
        "Constraint",
        "Rule",
        "RelationshipNode",
        "RelationNode",
        "关系",
    ],
    "subobject": [
        "SubObject",
        "SubEntity",
        "LineItem",
        "OrderLine",
        "DetailLine",
        "ChildEntity",
        "子对象",
        "子实体",
    ],
    "master": [
        "MasterData",
        "MasterDataEntity",
        "MDM",
        "PartyMaster",
        "主数据",
        "主数据实体",
    ],
    "object": ["Entity", "EntityDef", "Aggregate", "Object", "BusinessObject", "实体"],
}

_FLOW_REL = re.compile(
    r"^(TRIGGERS?|FLOWS?_?TO|LEADS?_?TO|NEXT|PREVIOUS|CAUSES|EMITS|POSTS|CREATES)$",
    re.I,
)
_ASSOC_REL = re.compile(
    r"^(RELATES?_?TO|REFERENCES?|ASSOCIATED?_?WITH|LINKS?_?TO|MAPS?_?TO)$",
    re.I,
)


def _parse_kind_labels() -> dict[str, list[str]]:
    raw = os.getenv("NEO4J_KIND_LABELS", "").strip()
    if not raw:
        return {k: list(v) for k, v in DEFAULT_KIND_LABELS.items()}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): [str(x) for x in v] for k, v in data.items()}
    except json.JSONDecodeError:
        pass
    return {k: list(v) for k, v in DEFAULT_KIND_LABELS.items()}


def _ignore_labels() -> set[str]:
    raw = os.getenv("NEO4J_IGNORE_LABELS", "__Meta__,__Internal__").strip()
    return {x.strip() for x in raw.split(",") if x.strip()}


def _node_id(n: Any) -> str:
    eid = getattr(n, "element_id", None)
    if eid is not None:
        return str(eid)
    nid = getattr(n, "id", None)
    if nid is not None:
        return str(nid)
    return str(id(n))


def _rel_id(r: Any) -> str:
    eid = getattr(r, "element_id", None)
    if eid is not None:
        return str(eid)
    rid = getattr(r, "id", None)
    if rid is not None:
        return f"rel_{rid}"
    return f"rel_{id(r)}"


def _pick_name(props: dict[str, Any], labels: list[str]) -> str:
    for k in (
        "name",
        "title",
        "label",
        "code",
        "displayName",
        "DISPLAY_NAME",
        "entity_name",
        "ENTITY_NAME",
    ):
        v = props.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()[:120]
    if labels:
        return labels[0][:120]
    return "未命名"


def _pick_sub(props: dict[str, Any], labels: list[str], role: str) -> str:
    for k in ("type", "TYPE", "kind", "ontology_type", "entity_type"):
        v = props.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()[:64]
    if len(labels) > 1:
        return labels[1][:64]
    if role == "event":
        return "Event"
    if role == "property":
        return "Attr"
    if role == "relation":
        return "Rel"
    if role == "master":
        return "主数据"
    if role == "subobject":
        return "子对象"
    return ""


def infer_kind(labels: list[str], props: dict[str, Any], kind_labels: dict[str, list[str]]) -> str:
    for key in ("ontology_kind", "node_kind", "kind", "node_type", "NODE_TYPE"):
        v = props.get(key)
        if v is None:
            continue
        s = str(v).strip().lower()
        if s in ("object", "event", "property", "relation", "master", "subobject"):
            return s
        if s in ("sub_object", "child", "line", "detail"):
            return "subobject"
        if s in ("mdm", "maindata", "主数据"):
            return "master"

    label_set = {x for x in labels}
    for role in ("event", "property", "relation", "subobject", "master", "object"):
        for cand in kind_labels.get(role, []):
            if cand in label_set:
                return role

    joined = " ".join(labels).upper()
    if "EVENT" in joined or joined.endswith("_EVT"):
        return "event"
    if any(x in joined for x in ("PROPERTY", "ATTRIBUTE", "ATTR", "FIELD", "COLUMN")):
        return "property"
    if any(x in joined for x in ("CONSTRAINT", "RULE", "RELATION_NODE")):
        return "relation"
    if any(x in joined for x in ("SUBOBJECT", "子对象", "子实体", "LINEITEM", "ORDERLINE", "DETAILLINE")):
        return "subobject"
    if any(x in joined for x in ("MASTERDATA", "MASTER_DATA", "主数据", "MDM")):
        return "master"
    return "object"


def map_edge_kind(rel_type: str) -> str:
    if _FLOW_REL.match(rel_type or ""):
        return "flow"
    if _ASSOC_REL.match(rel_type or ""):
        return "assoc"
    return "weak"


def node_to_payload(
    entity: Any,
    labels: list[str],
    props: dict[str, Any],
    kind_labels: dict[str, list[str]],
) -> dict[str, Any]:
    role = infer_kind(labels, props, kind_labels)
    nid = _node_id(entity)
    shape = "diamond" if role == "relation" else "neuron" if role == "event" else "card"
    w, h, rx = (112, 54, 12)
    if role == "property":
        w, h, rx = 96, 44, 10
    elif role == "relation":
        w, h = 40, 40
    elif role == "event":
        w, h = 52, 52
    elif role == "master":
        w, h, rx = 120, 56, 12
    elif role == "subobject":
        w, h, rx = 100, 46, 10
    return {
        "id": nid,
        "role": role,
        "shape": shape,
        "title": _pick_name(props, labels),
        "sub": _pick_sub(props, labels, role),
        "labels": labels,
        "w": w,
        "h": h,
        "rx": rx,
    }


def get_driver() -> Driver | None:
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687").strip()
    user = os.getenv("NEO4J_USER", "neo4j").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not password:
        return None
    return GraphDatabase.driver(uri, auth=(user, password))


def _session(driver: Driver):
    """
    Neo4j 5+ 多库：若未设置 NEO4J_DATABASE，则不传 database，由服务器解析默认/ home 库；
    若显式设置则连到该逻辑库（避免默认名 neo4j 在实例上不存在时报错）。
    """
    db = os.getenv("NEO4J_DATABASE", "").strip()
    if db:
        return driver.session(database=db)
    return driver.session()


def _schema_node_payload(
    label: str,
    kind_labels: dict[str, list[str]],
    instance_count: int | None = None,
) -> dict[str, Any]:
    """知识图谱模式：一个节点代表一种标签（实体类型），非数据库里的具体行。"""
    role = infer_kind([label], {}, kind_labels)
    shape = "diamond" if role == "relation" else "neuron" if role == "event" else "card"
    w, h, rx = (112, 54, 12)
    if role == "property":
        w, h, rx = 96, 44, 10
    elif role == "relation":
        w, h = 40, 40
    elif role == "event":
        w, h = 52, 52
    elif role == "master":
        w, h, rx = 120, 56, 12
    elif role == "subobject":
        w, h, rx = 100, 46, 10
    sub = ""
    if instance_count is not None and instance_count >= 0:
        sub = f"{instance_count} 实例"
    return {
        "id": f"label:{label}",
        "role": role,
        "shape": shape,
        "title": label,
        "sub": sub,
        "labels": [label],
        "w": w,
        "h": h,
        "rx": rx,
    }


def fetch_ontology_schema_graph() -> dict[str, Any]:
    """
    知识图谱 / 本体视图：按「节点标签 + 关系类型」聚合，不返回具体业务行。
    每条边表示：库中存在至少一条 (n)-[r]->(m)，且 n、m 的代表标签分别为 from_l、to_l。
    """
    _ontology_trace(
        "── schema 模式 ──\n"
        "逻辑: MATCH (n)-[r]->(m) 过滤 NEO4J_IGNORE_LABELS；"
        "端点标签取该节点「可见标签字典序最小」；"
        "按 (from_l, rel_type, to_l) 聚合 count(*) 为 instance_count；"
        "再 MATCH (n) UNWIND labels 统计各标签实例数；"
        "合并孤立标签为仅实例、无边类型节点。"
    )
    driver = get_driver()
    if driver is None:
        raise RuntimeError(
            "未配置 NEO4J_PASSWORD：请在 backend 目录下复制 .env.example 为 .env，"
            "并填写 NEO4J_PASSWORD（Neo4j 数据库密码）。"
        )

    ignore = _ignore_labels()
    kind_labels = _parse_kind_labels()
    db_name = os.getenv("NEO4J_DATABASE", "").strip() or None
    _ontology_trace(f"配置: database={db_name!r}, ignore_labels={sorted(ignore)}")

    # 端点取「可见标签里字典序最小」作为该节点的代表标签，便于稳定聚合（多标签时点仍只对应一个类型节点）
    cypher_patterns = """
    MATCH (n)-[r]->(m)
    WHERE NOT ANY(l IN labels(n) WHERE l IN $ignore)
      AND NOT ANY(l IN labels(m) WHERE l IN $ignore)
    WITH
      [x IN labels(n) WHERE NOT x IN $ignore | x] AS ns,
      type(r) AS rt,
      [x IN labels(m) WHERE NOT x IN $ignore | x] AS ms
    WHERE size(ns) > 0 AND size(ms) > 0
    WITH
      reduce(a = ns[0], b IN ns | CASE WHEN b < a THEN b ELSE a END) AS from_l,
      rt,
      reduce(a = ms[0], b IN ms | CASE WHEN b < a THEN b ELSE a END) AS to_l
    RETURN from_l, rt AS rel_type, to_l, count(*) AS instance_count
    """

    cypher_label_counts = """
    MATCH (n)
    WHERE NOT ANY(l IN labels(n) WHERE l IN $ignore)
    UNWIND labels(n) AS la
    WITH la, n
    WHERE NOT la IN $ignore
    RETURN la AS label, count(DISTINCT n) AS cnt
    """

    nodes_out: dict[str, dict[str, Any]] = {}
    edges_out: list[dict[str, Any]] = []

    diag_total = 0
    diag_visible = 0
    diag_rels = 0
    hint: str | None = None
    label_counts: dict[str, int] = {}

    try:
        with _session(driver) as session:
            row = session.run("MATCH (n) RETURN count(n) AS c").single()
            diag_total = int(row["c"]) if row else 0
            row = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            diag_rels = int(row["c"]) if row else 0
            row = session.run(
                """
                MATCH (n)
                WHERE NOT ANY(l IN labels(n) WHERE l IN $ignore)
                RETURN count(n) AS c
                """,
                ignore=list(ignore),
            ).single()
            diag_visible = int(row["c"]) if row else 0

            _ontology_trace(
                f"诊断: total_nodes={diag_total}, visible_nodes={diag_visible}, total_rels={diag_rels}"
            )

            for rec in session.run(cypher_patterns, ignore=list(ignore)):
                from_l = str(rec["from_l"])
                to_l = str(rec["to_l"])
                rt = str(rec["rel_type"])
                cnt = int(rec["instance_count"])
                sid = f"label:{from_l}"
                tid = f"label:{to_l}"
                if sid not in nodes_out:
                    nodes_out[sid] = _schema_node_payload(from_l, kind_labels, None)
                if tid not in nodes_out:
                    nodes_out[tid] = _schema_node_payload(to_l, kind_labels, None)
                eid = f"schema:{from_l}:{rt}:{to_l}"
                edges_out.append(
                    {
                        "id": eid,
                        "source": sid,
                        "target": tid,
                        "rel_type": rt,
                        "kind": map_edge_kind(rt),
                        "instance_count": cnt,
                    }
                )

            _ontology_trace(
                f"聚合边: 模式行数={len(edges_out)}（唯一 类型-关系-类型 组合），"
                f"涉及类型节点(边导出)={len(nodes_out)}"
            )

            for rec in session.run(cypher_label_counts, ignore=list(ignore)):
                la = str(rec["label"])
                label_counts[la] = int(rec["cnt"])

            for nid, payload in list(nodes_out.items()):
                lab = payload["title"]
                c = label_counts.get(lab)
                if c is not None:
                    nodes_out[nid] = {**payload, "sub": f"{c} 实例"}

            # 无出边/入边但仍存在的类型（孤立标签）
            for lab, cnt in label_counts.items():
                nid = f"label:{lab}"
                if nid not in nodes_out:
                    nodes_out[nid] = _schema_node_payload(lab, kind_labels, cnt)

            _ontology_trace(
                f"标签统计: 不同标签数={len(label_counts)}；"
                f"补全孤立类型后总节点数={len(nodes_out)}"
            )

    except (Neo4jError, ServiceUnavailable, AuthError, OSError) as e:
        msg = str(e)
        code = getattr(e, "code", "") or ""
        _ontology_trace(f"Neo4j 错误: code={code!r} msg={msg[:500]}")
        if code == "Neo.ClientError.Database.DatabaseNotFound" or "Database does not exist" in msg:
            msg = (
                f"{msg}\n"
                "请在 Neo4j Browser 执行 SHOW DATABASES 查看存在的库名，"
                "并在 backend/.env 设置 NEO4J_DATABASE=该库名。"
            )
        elif code == "Neo.ClientError.Security.Unauthorized" or "authentication failure" in msg.lower():
            msg = (
                f"{msg}\n"
                "Neo4j 认证失败：请核对 backend/.env 中的 NEO4J_USER、NEO4J_PASSWORD 是否与 "
                "Neo4j Browser / `neo4j-admin` 里该用户一致；密码含 # 等字符时请用双引号包裹。"
            )
        raise RuntimeError(msg) from e
    finally:
        driver.close()

    if not nodes_out and diag_visible > 0 and diag_rels == 0:
        hint = (
            "库中有节点但没有任何有向关系，无法推导类型之间的连接；"
            "可在 Neo4j Browser 检查是否存在 (n)-[r]->(m)。"
        )
    elif not nodes_out and diag_total == 0:
        hint = (
            "当前逻辑库中节点数为 0。请在 Neo4j Browser 执行 "
            "`MATCH (n) RETURN count(n)` 确认；并检查 NEO4J_DATABASE 是否指向存有数据的库。"
        )
    elif not nodes_out and diag_visible == 0:
        hint = (
            f"库中共有 {diag_total} 个节点，但经 NEO4J_IGNORE_LABELS 过滤后可见为 0。"
            "请缩小或清空 backend/.env 中的 NEO4J_IGNORE_LABELS。"
        )

    _ontology_trace(
        f"schema 返回: nodes={len(nodes_out)}, edges={len(edges_out)}, hint={hint!r}"
    )

    return {
        "nodes": list(nodes_out.values()),
        "edges": edges_out,
        "meta": {
            "graph_mode": "schema",
            "description": "按标签与关系类型聚合的知识图谱（非具体业务数据行）",
            "panorama": None,
            "relationship_limit": None,
            "panorama_node_limit": None,
            "node_count": len(nodes_out),
            "edge_count": len(edges_out),
            "database": db_name,
            "neo4j_total_nodes": diag_total,
            "neo4j_visible_nodes": diag_visible,
            "neo4j_total_relationships": diag_rels,
            "hint": hint,
        },
    }


def fetch_ontology_instance_graph() -> dict[str, Any]:
    """实例子图：与旧版一致，返回具体节点与关系（业务数据级）。"""
    _ontology_trace(
        "── instances 模式 ──\n"
        "逻辑: MATCH (n)-[r]->(m) RETURN n,r,m LIMIT NEO4J_GRAPH_LIMIT；"
        "可选 NEO4J_GRAPH_PANORAMA 再 MATCH (n) RETURN n LIMIT 补全孤立节点；"
        "节点为 element_id 级实例，非类型聚合。"
    )
    driver = get_driver()
    if driver is None:
        raise RuntimeError(
            "未配置 NEO4J_PASSWORD：请在 backend 目录下复制 .env.example 为 .env，"
            "并填写 NEO4J_PASSWORD（Neo4j 数据库密码）。"
        )

    rel_limit = max(1, int(os.getenv("NEO4J_GRAPH_LIMIT", "400")))
    ignore = _ignore_labels()
    kind_labels = _parse_kind_labels()
    panorama = os.getenv("NEO4J_GRAPH_PANORAMA", "true").strip().lower() in ("1", "true", "yes")
    panorama_node_limit = max(1, int(os.getenv("NEO4J_PANORAMA_NODE_LIMIT", "8000")))
    db_name = os.getenv("NEO4J_DATABASE", "").strip() or None
    _ontology_trace(
        f"配置: database={db_name!r}, rel_limit={rel_limit}, panorama={panorama}, "
        f"panorama_node_limit={panorama_node_limit}, ignore_labels={sorted(ignore)}"
    )

    cypher_rels = """
    MATCH (n)-[r]->(m)
    WHERE NOT ANY(l IN labels(n) WHERE l IN $ignore)
      AND NOT ANY(l IN labels(m) WHERE l IN $ignore)
    RETURN n, r, m
    LIMIT $limit
    """

    cypher_nodes = """
    MATCH (n)
    WHERE NOT ANY(l IN labels(n) WHERE l IN $ignore)
    RETURN n
    LIMIT $limit
    """

    nodes_out: dict[str, dict[str, Any]] = {}
    edges_out: list[dict[str, Any]] = []

    diag_total = 0
    diag_visible = 0
    diag_rels = 0
    hint: str | None = None

    try:
        with _session(driver) as session:
            row = session.run("MATCH (n) RETURN count(n) AS c").single()
            diag_total = int(row["c"]) if row else 0
            row = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            diag_rels = int(row["c"]) if row else 0
            row = session.run(
                """
                MATCH (n)
                WHERE NOT ANY(l IN labels(n) WHERE l IN $ignore)
                RETURN count(n) AS c
                """,
                ignore=list(ignore),
            ).single()
            diag_visible = int(row["c"]) if row else 0

            _ontology_trace(
                f"诊断: total_nodes={diag_total}, visible_nodes={diag_visible}, total_rels={diag_rels}"
            )

            result = session.run(cypher_rels, ignore=list(ignore), limit=rel_limit)
            for record in result:
                n = record["n"]
                r = record["r"]
                m = record["m"]
                n_labels = list(n.labels)
                m_labels = list(m.labels)
                n_props = dict(n)
                m_props = dict(m)

                sid = _node_id(n)
                tid = _node_id(m)
                if sid not in nodes_out:
                    nodes_out[sid] = node_to_payload(n, n_labels, n_props, kind_labels)
                if tid not in nodes_out:
                    nodes_out[tid] = node_to_payload(m, m_labels, m_props, kind_labels)
                rt = r.type
                edges_out.append(
                    {
                        "id": _rel_id(r),
                        "source": sid,
                        "target": tid,
                        "rel_type": rt,
                        "kind": map_edge_kind(rt),
                    }
                )

            _ontology_trace(
                f"关系扫描: 拉取边条数={len(edges_out)}（受 rel_limit≤{rel_limit}），"
                f"当前唯一节点数={len(nodes_out)}"
            )

            if panorama:
                res_nodes = session.run(cypher_nodes, ignore=list(ignore), limit=panorama_node_limit)
                added = 0
                for record in res_nodes:
                    n = record["n"]
                    nid = _node_id(n)
                    if nid in nodes_out:
                        continue
                    nodes_out[nid] = node_to_payload(n, list(n.labels), dict(n), kind_labels)
                    added += 1
                _ontology_trace(f"全景补点: 新增孤立/未在边中出现的节点约 {added} 个（上限 {panorama_node_limit}）")

            # 关闭全景或 LIMIT 曾为 0 时可能未拉到点；只要过滤后仍有可见节点则再拉一次
            if not nodes_out and diag_visible > 0:
                res_nodes = session.run(cypher_nodes, ignore=list(ignore), limit=panorama_node_limit)
                for record in res_nodes:
                    n = record["n"]
                    nid = _node_id(n)
                    if nid in nodes_out:
                        continue
                    nodes_out[nid] = node_to_payload(n, list(n.labels), dict(n), kind_labels)

    except (Neo4jError, ServiceUnavailable, AuthError, OSError) as e:
        msg = str(e)
        code = getattr(e, "code", "") or ""
        _ontology_trace(f"Neo4j 错误(instances): code={code!r} msg={msg[:500]}")
        if code == "Neo.ClientError.Database.DatabaseNotFound" or "Database does not exist" in msg:
            msg = (
                f"{msg}\n"
                "请在 Neo4j Browser 执行 SHOW DATABASES 查看存在的库名，"
                "并在 backend/.env 设置 NEO4J_DATABASE=该库名。"
            )
        elif code == "Neo.ClientError.Security.Unauthorized" or "authentication failure" in msg.lower():
            msg = (
                f"{msg}\n"
                "Neo4j 认证失败：请核对 backend/.env 中的 NEO4J_USER、NEO4J_PASSWORD 是否与 "
                "Neo4j Browser / `neo4j-admin` 里该用户一致；密码含 # 等字符时请用双引号包裹。"
            )
        raise RuntimeError(msg) from e
    finally:
        driver.close()

    if not nodes_out:
        if diag_total == 0:
            hint = (
                "当前逻辑库中节点数为 0。请在 Neo4j Browser 执行 "
                "`MATCH (n) RETURN count(n)` 确认；并检查 NEO4J_DATABASE 是否指向存有数据的库。"
            )
        elif diag_visible == 0:
            hint = (
                f"库中共有 {diag_total} 个节点，但经 NEO4J_IGNORE_LABELS 过滤后可见为 0。"
                "请缩小或清空 backend/.env 中的 NEO4J_IGNORE_LABELS。"
            )
        elif not panorama and diag_visible > 0:
            hint = (
                "库中有节点但 NEO4J_GRAPH_PANORAMA=false 且无任何有向关系，图谱为空。"
                "可将 NEO4J_GRAPH_PANORAMA 设为 true，或先在图中创建 (n)-[r]->(m) 关系。"
            )
        elif diag_rels == 0 and diag_visible > 0:
            hint = (
                "有节点但没有任何有向关系；全景已尝试加载孤立节点。"
                "若仍为空，请检查 NEO4J_PANORAMA_NODE_LIMIT 或标签过滤。"
            )
    elif nodes_out and not edges_out and diag_rels > 0:
        hint = (
            f"库中共有 {diag_rels} 条有向关系，但按 NEO4J_IGNORE_LABELS 过滤后，"
            "没有任何一条的两端节点同时可见，因此边上不会显示。"
            "请缩小忽略标签或暂时清空 NEO4J_IGNORE_LABELS。"
        )

    _ontology_trace(
        f"instances 返回: nodes={len(nodes_out)}, edges={len(edges_out)}, hint={hint!r}"
    )

    return {
        "nodes": list(nodes_out.values()),
        "edges": edges_out,
        "meta": {
            "graph_mode": "instances",
            "description": "Neo4j 中的具体节点与关系（业务数据级，受 LIMIT 与全景配置影响）",
            "panorama": panorama,
            "relationship_limit": rel_limit,
            "panorama_node_limit": panorama_node_limit if panorama else None,
            "node_count": len(nodes_out),
            "edge_count": len(edges_out),
            "database": db_name,
            "neo4j_total_nodes": diag_total,
            "neo4j_visible_nodes": diag_visible,
            "neo4j_total_relationships": diag_rels,
            "hint": hint,
        },
    }


def fetch_ontology_graph(mode: str | None = None) -> dict[str, Any]:
    """
    图谱入口。
    - schema（默认）：按标签 + 关系类型聚合的知识图谱 / 本体逻辑，不返回具体业务行。
    - instances：旧版实例子图。
    环境变量 NEO4J_GRAPH_MODE 可设 schema | instances；请求参数 ?mode= 优先。
    """
    env_mode = os.getenv("NEO4J_GRAPH_MODE", "schema")
    raw = (mode if mode is not None else env_mode).strip().lower()
    _ontology_trace(
        f"fetch_ontology_graph: 请求参数 mode={mode!r}, 环境 NEO4J_GRAPH_MODE={env_mode!r} → 使用 {raw!r}"
    )
    if raw in ("schema", "ontology", "logical", "meta"):
        return fetch_ontology_schema_graph()
    if raw in ("instances", "instance", "data", "legacy"):
        return fetch_ontology_instance_graph()
    raise ValueError(
        f"无效的图谱模式 {raw!r}：请使用 schema（知识图谱/本体，默认）或 instances（具体数据子图）。"
    )
