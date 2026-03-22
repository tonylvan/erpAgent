/**
 * 按有向边分层（左→右沿路径），层内 barycenter 减少交叉；边用正交折线 + 车道错开，避免贝塞尔交织。
 * 分层优先采用「采购到付款」语义序，避免纯最长路导致左右两大块割裂。
 */

const PAD_X = 40;
const PAD_Y = 36;
/** 列间距（与节点宽度匹配，本体图多为 card ~120） */
export const LAYER_GAP_X = 168;
const NODE_Y_GAP = 18;

const VIEW_MARGIN = 48;
const MIN_VIEW_W = 920;
const MIN_VIEW_H = 360;

/**
 * 在固定 viewBox 内将节点群（含底部回绕区 extraBottom）水平、垂直居中。
 * 会原地修改节点的 x/y。
 */
export function centerGraphInViewport(nodes, extraBottom = 0) {
  if (!nodes.length) {
    return { viewW: MIN_VIEW_W, viewH: MIN_VIEW_H };
  }
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const n of nodes) {
    const w = Number(n.w) > 0 ? Number(n.w) : 112;
    const h = Number(n.h) > 0 ? Number(n.h) : 54;
    minX = Math.min(minX, n.x);
    minY = Math.min(minY, n.y);
    maxX = Math.max(maxX, n.x + w);
    maxY = Math.max(maxY, n.y + h);
  }
  const contentW = maxX - minX;
  const contentH = maxY - minY + extraBottom;
  const viewW = Math.max(MIN_VIEW_W, contentW + 2 * VIEW_MARGIN);
  const viewH = Math.max(MIN_VIEW_H, contentH + 2 * VIEW_MARGIN);
  const dx = (viewW - contentW) / 2 - minX;
  const dy = (viewH - contentH) / 2 - minY;
  for (const n of nodes) {
    n.x += dx;
    n.y += dy;
  }
  return { viewW, viewH };
}

/** Neo4j 标签 / 本体类型：采购→应付→付款→总账 大致阶段（数值越大越靠右） */
const P2P_LABEL_RANK = {
  Supplier: 5,
  SupplierSite: 8,
  SupplierContact: 8,
  BankAccount: 12,
  PurchaseOrder: 20,
  POLine: 24,
  PODistribution: 26,
  POShipment: 28,
  Invoice: 36,
  InvoiceLine: 38,
  InvoiceDistribution: 38,
  PaymentSchedule: 42,
  InvoicePayment: 44,
  Payment: 48,
  Customer: 52,
  CustomerSite: 54,
  ARTransaction: 56,
  ARTransactionLine: 58,
  ARApplication: 58,
  XLATransactionEntity: 62,
  XLAEvent: 64,
  XLAEventTrace: 66,
  AccountingEntry: 70,
  AccountingLine: 72,
  DistributionLink: 72,
  GLLedger: 78,
  GLPeriod: 80,
  GLBatch: 82,
  GLJournal: 84,
  GLJournalLine: 86,
  GLAccount: 88,
  GLBalance: 90,
  AuditEvent: 96,
};

/** 演示图中文标题 → 与 P2P 阶段对齐 */
const P2P_TITLE_RANK = {
  供应商: 5,
  采购订单: 20,
  接收: 28,
  应付发票: 36,
  PO创建: 18,
  收货: 30,
  三单匹配: 40,
  触发: 34,
  约束: 38,
  过账: 44,
  付款: 48,
  付款执行: 50,
  "日记账 / 总账": 78,
};

function primaryLabelKey(node) {
  if (node.labels && node.labels.length) return String(node.labels[0]);
  const sid = String(node.id ?? "");
  const m = sid.match(/^label:(.+)$/);
  if (m) return m[1];
  return String(node.title ?? "").trim();
}

function semanticRank(node) {
  const key = primaryLabelKey(node);
  if (key && Object.prototype.hasOwnProperty.call(P2P_LABEL_RANK, key)) {
    return P2P_LABEL_RANK[key];
  }
  if (key && Object.prototype.hasOwnProperty.call(P2P_TITLE_RANK, key)) {
    return P2P_TITLE_RANK[key];
  }
  const t = String(node.title ?? "").trim();
  if (t && Object.prototype.hasOwnProperty.call(P2P_TITLE_RANK, t)) {
    return P2P_TITLE_RANK[t];
  }
  return 50;
}

/** 将非连续层号压成 0..k-1，去掉「中间空几列」造成的视觉割裂 */
function compressLayers(ids, layer) {
  const uniq = [...new Set([...ids].map((id) => layer[id] ?? 0))].sort((a, b) => a - b);
  const remap = new Map();
  uniq.forEach((v, i) => remap.set(v, i));
  for (const id of ids) {
    layer[id] = remap.get(layer[id] ?? 0) ?? 0;
  }
}

/**
 * @param {Array<{ id: string, w?: number, h?: number }>} nodes
 * @param {Array<{ from: string, to: string }>} edges
 */
export function layoutOntology(nodes, edges = []) {
  if (!nodes.length) {
    return { viewW: 920, viewH: 360 };
  }

  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const ids = new Set(nodes.map((n) => n.id));

  /** 初值：采购到付款语义阶段；再沿边 longest-path 松弛，保证依赖向右 */
  const layer = {};
  for (const id of ids) {
    layer[id] = semanticRank(nodeMap[id]);
  }

  const validEdges = edges.filter((e) => e.from && e.to && nodeMap[e.from] && nodeMap[e.to]);
  const maxIter = Math.min(120, ids.size * 4 + 20);
  for (let iter = 0; iter < maxIter; iter++) {
    let changed = false;
    for (const e of validEdges) {
      const nu = layer[e.from] + 1;
      if (nu > layer[e.to]) {
        layer[e.to] = nu;
        changed = true;
      }
    }
    if (!changed) break;
  }

  compressLayers(ids, layer);

  const maxLayer = Math.max(0, ...[...ids].map((id) => layer[id] ?? 0));

  /** 按层分桶 */
  const buckets = Array.from({ length: maxLayer + 1 }, () => []);
  for (const id of ids) {
    const L = Math.max(0, layer[id] ?? 0);
    buckets[L].push(id);
  }

  /** 无边连接的节点：移到第 0 列末尾，避免单独占一列 */
  const touched = new Set();
  for (const e of validEdges) {
    touched.add(e.from);
    touched.add(e.to);
  }
  const isolated = [...ids].filter((id) => !touched.has(id));
  for (const id of isolated) {
    const L = layer[id] ?? 0;
    const b = buckets[L];
    const idx = b.indexOf(id);
    if (idx >= 0) b.splice(idx, 1);
  }
  if (buckets[0]) buckets[0].push(...isolated);

  /** 层内 barycenter 排序，减少边交叉 */
  const posInLayer = (id, L) => {
    const arr = buckets[L];
    const i = arr.indexOf(id);
    return i < 0 ? 0 : i;
  };

  const medianPred = (id, L, incoming) => {
    const preds = incoming.get(id) ?? [];
    const fromPrev = preds.filter((p) => (layer[p] ?? 0) === L - 1);
    if (!fromPrev.length) return 0;
    const xs = fromPrev.map((p) => posInLayer(p, L - 1)).sort((a, b) => a - b);
    const m = Math.floor(xs.length / 2);
    return xs.length % 2 ? xs[m] : (xs[m - 1] + xs[m]) / 2;
  };

  const medianSucc = (id, L, outgoing) => {
    const succs = outgoing.get(id) ?? [];
    const toNext = succs.filter((s) => (layer[s] ?? 0) === L + 1);
    if (!toNext.length) return 0;
    const xs = toNext.map((s) => posInLayer(s, L + 1)).sort((a, b) => a - b);
    const m = Math.floor(xs.length / 2);
    return xs.length % 2 ? xs[m] : (xs[m - 1] + xs[m]) / 2;
  };

  const incoming = new Map();
  const outgoing = new Map();
  for (const id of ids) {
    incoming.set(id, []);
    outgoing.set(id, []);
  }
  for (const e of validEdges) {
    outgoing.get(e.from).push(e.to);
    incoming.get(e.to).push(e.from);
  }

  const tie = (a, b) => {
    const ra = semanticRank(nodeMap[a]);
    const rb = semanticRank(nodeMap[b]);
    if (ra !== rb) return ra - rb;
    return String(a).localeCompare(String(b));
  };

  for (let pass = 0; pass < 10; pass++) {
    for (let L = 1; L < buckets.length; L++) {
      buckets[L].sort((a, b) => {
        const d = medianPred(a, L, incoming) - medianPred(b, L, incoming);
        if (Math.abs(d) > 1e-6) return d;
        return tie(a, b);
      });
    }
    for (let L = buckets.length - 2; L >= 0; L--) {
      buckets[L].sort((a, b) => {
        const d = medianSucc(a, L, outgoing) - medianSucc(b, L, outgoing);
        if (Math.abs(d) > 1e-6) return d;
        return tie(a, b);
      });
    }
  }

  /** 写回坐标与 graphLayer */
  let maxRight = PAD_X;
  let maxBottom = PAD_Y;
  for (let L = 0; L < buckets.length; L++) {
    const list = buckets[L];
    const x = PAD_X + L * LAYER_GAP_X;
    let y = PAD_Y;
    for (const id of list) {
      const n = nodeMap[id];
      if (!n) continue;
      n.x = x;
      n.y = y;
      n.graphLayer = L;
      y += (Number(n.h) > 0 ? Number(n.h) : 54) + NODE_Y_GAP;
      maxBottom = Math.max(maxBottom, y);
      maxRight = Math.max(maxRight, x + (Number(n.w) > 0 ? Number(n.w) : 112));
    }
  }

  const viewW = Math.max(920, maxRight + PAD_X);
  const viewH = Math.max(360, maxBottom + PAD_Y);
  return { viewW, viewH };
}

/**
 * 正交折线：顺向边在层间用竖线错开车道；逆向/同层走画布下方回绕，避免与主路径贝塞尔交织。
 * @param {Array<{ id: string, x: number, y: number, w: number, h: number, graphLayer?: number }>} nodes
 * @param {Array<{ id?: string, from: string, to: string, kind?: string }>} edgeDefs
 */
export function buildOrthogonalPaths(nodes, edgeDefs) {
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const baseBottom = nodes.length
    ? Math.max(...nodes.map((n) => n.y + (Number(n.h) || 54)))
    : 0;
  const graphBottom = baseBottom + 32;

  const list = [];
  for (const e of edgeDefs) {
    const a = nodeMap[e.from];
    const b = nodeMap[e.to];
    if (!a || !b) continue;
    list.push({ e, a, b });
  }

  /** 顺向边分组：用于车道 */
  const forwardBuckets = new Map();
  for (const item of list) {
    const { a, b } = item;
    const sx = a.x + a.w;
    const ex = b.x;
    if (ex - sx >= 12) {
      const la = a.graphLayer ?? 0;
      const lb = b.graphLayer ?? 0;
      const key = `${la}:${lb}`;
      if (!forwardBuckets.has(key)) forwardBuckets.set(key, []);
      forwardBuckets.get(key).push(item);
    }
  }

  const laneIndex = new Map();
  for (const [, items] of forwardBuckets) {
    items.sort((u, v) => {
      const cy1 = (u.a.y + u.a.h / 2 + u.b.y + u.b.h / 2) / 2;
      const cy2 = (v.a.y + v.a.h / 2 + v.b.y + v.b.h / 2) / 2;
      return cy1 - cy2;
    });
    items.forEach((it, i) => {
      const eid = it.e.id != null ? String(it.e.id) : `${it.e.from}-${it.e.to}`;
      laneIndex.set(eid, i);
    });
  }

  let backwardLane = 0;
  const out = [];
  for (const item of list) {
    const { e, a, b } = item;
    const sx = a.x + a.w;
    const sy = a.y + a.h / 2;
    const ex = b.x;
    const ey = b.y + b.h / 2;
    const gap = ex - sx;
    const eid = e.id != null ? String(e.id) : `${e.from}-${e.to}`;
    let d;

    if (gap >= 12) {
      const la = a.graphLayer ?? 0;
      const lb = b.graphLayer ?? 0;
      const key = `${la}:${lb}`;
      const bucket = forwardBuckets.get(key) ?? [];
      const total = Math.max(1, bucket.length);
      const lane = laneIndex.get(eid) ?? 0;
      const t = (lane + 1) / (total + 1);
      const midx = sx + gap * t;
      d = `M ${sx} ${sy} L ${midx} ${sy} L ${midx} ${ey} L ${ex} ${ey}`;
    } else {
      const y = graphBottom + backwardLane * 12;
      backwardLane += 1;
      d = `M ${sx} ${sy} L ${sx} ${y} L ${ex} ${y} L ${ex} ${ey}`;
    }

    out.push({
      key: eid,
      d,
      kind: e.kind ?? "weak",
    });
  }

  const extraBottom = backwardLane > 0 ? backwardLane * 12 + 24 : 0;
  return { paths: out, extraBottom };
}
