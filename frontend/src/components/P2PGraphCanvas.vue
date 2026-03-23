<script setup>
import { computed, onMounted, ref, useTemplateRef } from "vue";
import { apiUrl } from "../api/baseUrl.js";
import { DEMO_EDGES, DEMO_NODES } from "../data/demoP2PGraph.js";
import {
  buildOrthogonalPaths,
  centerGraphInViewport,
  layoutOntology,
} from "../utils/graphLayout.js";
import { normalizeGraphNode } from "../utils/graphNormalize.js";

/**
 * P2P 时序知识图谱 — 对象 / 事件 / 关系 / 属性 + Neo4j 动态子图
 */
defineProps({
  title: {
    type: String,
    default: "采购到付款 · 时序知识图谱",
  },
});

const svgEl = useTemplateRef("svgRoot");

function packLayout(nodeList, edgeList) {
  layoutOntology(nodeList, edgeList);
  const { extraBottom } = buildOrthogonalPaths(nodeList, edgeList);
  const { viewW, viewH } = centerGraphInViewport(nodeList, extraBottom);
  return { viewW, viewH };
}

const initialDemo = (() => {
  const n = DEMO_NODES.map((x) => normalizeGraphNode({ ...x }));
  const e = JSON.parse(JSON.stringify(DEMO_EDGES));
  const { viewW, viewH } = packLayout(n, e);
  return { nodes: n, edges: e, viewW, viewH };
})();

/** role: object | event | relation | property */
const nodes = ref(initialDemo.nodes);
/** 边：kind flow=主链路, assoc=横向关联, weak=弱连接 */
const edgeDefs = ref(initialDemo.edges);

const viewW = ref(initialDemo.viewW);
const viewH = ref(initialDemo.viewH);

const graphLoading = ref(false);
const graphError = ref("");
const graphSource = ref("demo"); // demo | neo4j
const graphMeta = ref(null);

function applyDemoGraph(keepMeta = false) {
  const n = DEMO_NODES.map((x) => normalizeGraphNode({ ...x }));
  const e = JSON.parse(JSON.stringify(DEMO_EDGES));
  const { viewW: vw, viewH: vh } = packLayout(n, e);
  nodes.value = n;
  edgeDefs.value = e;
  viewW.value = vw;
  viewH.value = vh;
  graphSource.value = "demo";
  if (!keepMeta) graphMeta.value = null;
}

async function loadGraphFromNeo4j() {
  graphLoading.value = true;
  graphError.value = "";
  try {
    const res = await fetch(apiUrl("/api/graph/ontology"));
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      let msg = err.detail ?? res.statusText ?? "加载失败";
      if (typeof msg !== "string") msg = JSON.stringify(msg);
      if (res.status === 404) {
        msg =
          "接口 404：请确认后端已启动，且浏览器能访问 /docs 中的 GET /api/graph/ontology；若改端口请同步修改 frontend/.env.development 里的 VITE_API_BASE。";
      }
      throw new Error(msg);
    }
    const data = await res.json();
    graphMeta.value = data.meta ?? null;
    const nextNodes = data.nodes ?? [];
    const nextEdges = data.edges ?? [];
    if (!nextNodes.length) {
      const m = data.meta ?? {};
      const parts = [];
      if (m.hint) parts.push(m.hint);
      else parts.push("Neo4j 返回的节点列表为空，已保留演示数据。");
      if (m.neo4j_total_nodes != null) {
        parts.push(
          `（诊断：库内总节点 ${m.neo4j_total_nodes}，过滤后可见 ${m.neo4j_visible_nodes ?? "?"}` +
            `，有向关系 ${m.neo4j_total_relationships ?? "?"} 条）`,
        );
      }
      graphError.value = parts.join("");
      applyDemoGraph(true);
      return;
    }
    graphError.value = "";
    const normalized = nextNodes.map(normalizeGraphNode);
    const edgeList = nextEdges.map((e) => ({
      id: e.id,
      from: e.source,
      to: e.target,
      kind: e.kind ?? "weak",
    }));
    const { viewW: vw, viewH: vh } = packLayout(normalized, edgeList);
    nodes.value = normalized;
    edgeDefs.value = edgeList;
    viewW.value = vw;
    viewH.value = vh;
    graphSource.value = "neo4j";
    resetView();
  } catch (e) {
    graphError.value = e instanceof Error ? e.message : String(e);
    applyDemoGraph();
  } finally {
    graphLoading.value = false;
  }
}

onMounted(() => {
  loadGraphFromNeo4j();
});

const panX = ref(0);
const panY = ref(0);
const scale = ref(1);

const MIN_SCALE = 0.25;
const MAX_SCALE = 4;

const viewTransform = computed(
  () => `translate(${panX.value}, ${panY.value}) scale(${scale.value})`,
);

const computedEdges = computed(() => {
  const { paths } = buildOrthogonalPaths(nodes.value, edgeDefs.value);
  return paths;
});

function clientToSvg(clientX, clientY) {
  const svg = svgEl.value;
  if (!svg) return { x: 0, y: 0 };
  const pt = new DOMPoint(clientX, clientY);
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  return pt.matrixTransform(ctm.inverse());
}

function svgToWorld(sx, sy) {
  const s = scale.value;
  return {
    x: (sx - panX.value) / s,
    y: (sy - panY.value) / s,
  };
}

function zoomAtPoint(mx, my, nextScale) {
  const s = scale.value;
  const clamped = Math.min(MAX_SCALE, Math.max(MIN_SCALE, nextScale));
  if (clamped === s) return;
  panX.value = mx - ((mx - panX.value) * clamped) / s;
  panY.value = my - ((my - panY.value) * clamped) / s;
  scale.value = clamped;
}

function onWheel(e) {
  e.preventDefault();
  const factor = e.deltaY > 0 ? 0.92 : 1.08;
  const p = clientToSvg(e.clientX, e.clientY);
  zoomAtPoint(p.x, p.y, scale.value * factor);
}

function zoomIn() {
  const svg = svgEl.value;
  if (!svg) return;
  const r = svg.getBoundingClientRect();
  zoomAtPoint(
    clientToSvg(r.left + r.width / 2, r.top + r.height / 2).x,
    clientToSvg(r.left + r.width / 2, r.top + r.height / 2).y,
    scale.value * 1.15,
  );
}

function zoomOut() {
  const svg = svgEl.value;
  if (!svg) return;
  const r = svg.getBoundingClientRect();
  const cx = clientToSvg(r.left + r.width / 2, r.top + r.height / 2);
  zoomAtPoint(cx.x, cx.y, scale.value / 1.15);
}

function resetView() {
  panX.value = 0;
  panY.value = 0;
  scale.value = 1;
}

const drag = ref(null);
const panDrag = ref(null);

function clampNode(n) {
  n.x = Math.min(Math.max(n.x, -60), viewW.value - n.w + 100);
  n.y = Math.min(Math.max(n.y, -30), viewH.value - n.h + 80);
}

function onNodePointerDown(e, n) {
  if (e.button !== 0) return;
  e.stopPropagation();
  e.preventDefault();
  const p = clientToSvg(e.clientX, e.clientY);
  const w = svgToWorld(p.x, p.y);
  drag.value = {
    id: n.id,
    grabX: w.x - n.x,
    grabY: w.y - n.y,
    pointerId: e.pointerId,
  };
  e.currentTarget.setPointerCapture(e.pointerId);
}

function onNodePointerMove(e, n) {
  if (!drag.value || drag.value.id !== n.id) return;
  e.preventDefault();
  const p = clientToSvg(e.clientX, e.clientY);
  const w = svgToWorld(p.x, p.y);
  n.x = w.x - drag.value.grabX;
  n.y = w.y - drag.value.grabY;
  clampNode(n);
}

function onNodePointerUp(e, n) {
  if (!drag.value || drag.value.id !== n.id) return;
  drag.value = null;
  try {
    e.currentTarget.releasePointerCapture(e.pointerId);
  } catch {
    /* ignore */
  }
}

function onNodePointerCancel() {
  drag.value = null;
}

function onPanPointerDown(e) {
  if (e.button !== 0) return;
  e.preventDefault();
  const p = clientToSvg(e.clientX, e.clientY);
  panDrag.value = {
    pointerId: e.pointerId,
    startSvgX: p.x,
    startSvgY: p.y,
    startPanX: panX.value,
    startPanY: panY.value,
  };
  e.currentTarget.setPointerCapture(e.pointerId);
}

function onPanPointerMove(e) {
  if (!panDrag.value || panDrag.value.pointerId !== e.pointerId) return;
  e.preventDefault();
  const p = clientToSvg(e.clientX, e.clientY);
  const d = panDrag.value;
  panX.value = d.startPanX + (p.x - d.startSvgX);
  panY.value = d.startPanY + (p.y - d.startSvgY);
}

function onPanPointerUp(e) {
  if (!panDrag.value || panDrag.value.pointerId !== e.pointerId) return;
  panDrag.value = null;
  try {
    e.currentTarget.releasePointerCapture(e.pointerId);
  } catch {
    /* ignore */
  }
}

function onPanPointerCancel() {
  panDrag.value = null;
}

const zoomPct = computed(() => Math.round(scale.value * 100));

function diamondPoints(n) {
  const cx = n.w / 2;
  const cy = n.h / 2;
  return `${cx},0 ${n.w},${cy} ${cx},${n.h} 0,${cy}`;
}

function roleLabel(role) {
  if (role === "object") return "对象";
  if (role === "master") return "主数据";
  if (role === "subobject") return "子对象";
  if (role === "event") return "事件";
  if (role === "property") return "属性";
  return "关系";
}

function nodeShadowFilter(role) {
  if (role === "object") return "url(#shadow-object)";
  if (role === "master") return "url(#shadow-master)";
  if (role === "subobject") return "url(#shadow-subobject)";
  if (role === "event") return "url(#shadow-event)";
  if (role === "property") return "url(#shadow-property)";
  if (role === "relation") return "url(#shadow-relation)";
  return "url(#shadow-object)";
}
</script>

<template>
  <div class="canvas-root">
    <header class="canvas-toolbar">
      <span class="canvas-title">{{ title }}</span>
      <div class="toolbar-actions">
        <span class="canvas-badge" :class="{ 'badge-live': graphSource === 'neo4j' }">
          {{
            graphLoading
              ? "加载 Neo4j…"
              : graphSource === "neo4j"
                ? graphMeta?.graph_mode === "schema"
                  ? "Neo4j 知识图谱"
                  : graphMeta?.panorama
                    ? "Neo4j 全景"
                    : "Neo4j 子图"
                : "演示数据"
          }}
        </span>
        <button
          type="button"
          class="reload-btn"
          title="重新从 Neo4j 加载"
          :disabled="graphLoading"
          @click="loadGraphFromNeo4j"
        >
          刷新
        </button>
        <div class="zoom-controls" role="group" aria-label="画布缩放">
          <button type="button" class="icon-btn" title="缩小" @click="zoomOut">−</button>
          <button type="button" class="zoom-pct" title="复位视图" @click="resetView">
            {{ zoomPct }}%
          </button>
          <button type="button" class="icon-btn" title="放大" @click="zoomIn">+</button>
        </div>
      </div>
    </header>
    <div class="canvas-surface">
      <div class="grid-bg" aria-hidden="true" />
      <svg
        ref="svgRoot"
        class="graph-svg"
        :viewBox="`0 0 ${viewW} ${viewH}`"
        xmlns="http://www.w3.org/2000/svg"
        @wheel.prevent="onWheel"
      >
        <defs>
          <linearGradient id="grad-object" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#f0f9ff" />
            <stop offset="45%" stop-color="#bae6fd" />
            <stop offset="100%" stop-color="#38bdf8" />
          </linearGradient>
          <linearGradient id="grad-object-stroke" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#e0f2fe" />
            <stop offset="100%" stop-color="#0284c7" />
          </linearGradient>
          <linearGradient id="grad-event" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#fffbeb" />
            <stop offset="45%" stop-color="#fde68a" />
            <stop offset="100%" stop-color="#f59e0b" />
          </linearGradient>
          <linearGradient id="grad-event-stroke" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fef3c7" />
            <stop offset="100%" stop-color="#d97706" />
          </linearGradient>
          <linearGradient id="grad-relation" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#f5f3ff" />
            <stop offset="50%" stop-color="#c4b5fd" />
            <stop offset="100%" stop-color="#7c3aed" />
          </linearGradient>
          <linearGradient id="grad-property" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ecfdf5" />
            <stop offset="45%" stop-color="#a7f3d0" />
            <stop offset="100%" stop-color="#10b981" />
          </linearGradient>
          <linearGradient id="grad-property-stroke" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#d1fae5" />
            <stop offset="100%" stop-color="#047857" />
          </linearGradient>
          <linearGradient id="grad-master" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#fffbeb" />
            <stop offset="45%" stop-color="#fde68a" />
            <stop offset="100%" stop-color="#d97706" />
          </linearGradient>
          <linearGradient id="grad-master-stroke" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#fef3c7" />
            <stop offset="100%" stop-color="#b45309" />
          </linearGradient>
          <linearGradient id="grad-subobject" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#f8fafc" />
            <stop offset="50%" stop-color="#cbd5e1" />
            <stop offset="100%" stop-color="#64748b" />
          </linearGradient>
          <linearGradient id="grad-subobject-stroke" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#e2e8f0" />
            <stop offset="100%" stop-color="#475569" />
          </linearGradient>
          <filter
            id="shadow-object"
            x="-0.35"
            y="-0.35"
            width="1.7"
            height="1.8"
            color-interpolation-filters="sRGB"
          >
            <feDropShadow dx="0" dy="3" stdDeviation="2.5" floodOpacity="0.28" />
            <feDropShadow dx="0" dy="10" stdDeviation="6" floodOpacity="0.12" />
          </filter>
          <filter
            id="shadow-event"
            x="-0.4"
            y="-0.4"
            width="1.8"
            height="1.9"
            color-interpolation-filters="sRGB"
          >
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.35" flood-color="#f59e0b" />
            <feDropShadow dx="0" dy="8" stdDeviation="5" floodOpacity="0.15" />
          </filter>
          <filter
            id="shadow-relation"
            x="-0.35"
            y="-0.35"
            width="1.7"
            height="1.8"
            color-interpolation-filters="sRGB"
          >
            <feDropShadow dx="0" dy="2" stdDeviation="1.8" floodOpacity="0.4" flood-color="#7c3aed" />
            <feDropShadow dx="0" dy="6" stdDeviation="4" floodOpacity="0.12" />
          </filter>
          <filter
            id="shadow-property"
            x="-0.35"
            y="-0.35"
            width="1.7"
            height="1.8"
            color-interpolation-filters="sRGB"
          >
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.3" flood-color="#10b981" />
            <feDropShadow dx="0" dy="8" stdDeviation="5" floodOpacity="0.12" />
          </filter>
          <filter
            id="shadow-master"
            x="-0.35"
            y="-0.35"
            width="1.7"
            height="1.8"
            color-interpolation-filters="sRGB"
          >
            <feDropShadow dx="0" dy="3" stdDeviation="2.5" floodOpacity="0.32" flood-color="#d97706" />
            <feDropShadow dx="0" dy="10" stdDeviation="6" floodOpacity="0.12" />
          </filter>
          <filter
            id="shadow-subobject"
            x="-0.35"
            y="-0.35"
            width="1.7"
            height="1.8"
            color-interpolation-filters="sRGB"
          >
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.28" flood-color="#64748b" />
            <feDropShadow dx="0" dy="8" stdDeviation="5" floodOpacity="0.1" />
          </filter>
          <marker
            id="arrow-edge"
            markerWidth="9"
            markerHeight="9"
            refX="8"
            refY="4.5"
            orient="auto"
          >
            <path d="M0,0 L9,4.5 L0,9 Z" fill="#334155" opacity="0.9" />
          </marker>
        </defs>

        <g class="world" :transform="viewTransform">
          <rect
            class="pan-layer"
            x="0"
            y="0"
            :width="viewW"
            :height="viewH"
            fill="transparent"
            @pointerdown="onPanPointerDown"
            @pointermove="onPanPointerMove"
            @pointerup="onPanPointerUp"
            @pointercancel="onPanPointerCancel"
          />

          <!-- 底：时间参考带 -->
          <rect
            x="32"
            :y="viewH - 32"
            :width="viewW - 64"
            height="6"
            rx="3"
            fill="url(#grad-object)"
            opacity="0.25"
          />
          <text x="36" :y="viewH - 14" class="axis-label">t₀</text>
          <text :x="viewW / 2 - 52" :y="viewH - 14" class="axis-label">时序 · 业务流</text>
          <text :x="viewW - 56" :y="viewH - 14" class="axis-label">tₙ</text>

          <g class="edges">
            <path
              v-for="ed in computedEdges"
              :key="ed.key"
              :d="ed.d"
              :class="['edge-path', `edge-${ed.kind}`]"
              fill="none"
              marker-end="url(#arrow-edge)"
            />
          </g>

          <g
            v-for="n in nodes"
            :key="n.id"
            class="node-group"
            :class="[
              'node-' + n.role,
              { grabbing: drag?.id === n.id },
            ]"
            :transform="`translate(${n.x}, ${n.y})`"
            :filter="nodeShadowFilter(n.role)"
            @pointerdown="onNodePointerDown($event, n)"
            @pointermove="onNodePointerMove($event, n)"
            @pointerup="onNodePointerUp($event, n)"
            @pointercancel="onNodePointerCancel"
          >
            <title>{{ roleLabel(n.role) }}：{{ n.title }}{{ n.sub ? ` · ${n.sub}` : "" }}</title>

            <!-- 业务对象 -->
            <template v-if="n.shape === 'card' && n.role === 'object'">
              <ellipse
                :cx="n.w / 2"
                :cy="n.h + 6"
                rx="n.w * 0.42"
                ry="7"
                class="ground-shadow"
              />
              <rect
                :width="n.w"
                :height="n.h"
                :rx="n.rx"
                fill="url(#grad-object)"
                stroke="url(#grad-object-stroke)"
                stroke-width="1.5"
                class="shape-3d"
              />
              <rect
                :width="n.w - 2"
                :height="n.h * 0.38"
                :x="1"
                :y="1"
                :rx="n.rx - 1"
                fill="#fff"
                opacity="0.22"
              />
              <text :x="n.w / 2" y="24" class="lbl-title">{{ n.title }}</text>
              <text
                v-if="n.sub"
                :x="n.w / 2"
                y="42"
                class="lbl-sub"
              >
                {{ n.sub }}
              </text>
            </template>

            <!-- 主数据实体 -->
            <template v-else-if="n.shape === 'card' && n.role === 'master'">
              <ellipse
                :cx="n.w / 2"
                :cy="n.h + 6"
                rx="n.w * 0.42"
                ry="7"
                class="ground-shadow"
              />
              <rect
                :width="n.w"
                :height="n.h"
                :rx="n.rx"
                fill="url(#grad-master)"
                stroke="url(#grad-master-stroke)"
                stroke-width="1.6"
                class="shape-3d"
              />
              <text :x="n.w / 2" y="26" class="lbl-title lbl-master">{{ n.title }}</text>
              <text
                v-if="n.sub"
                :x="n.w / 2"
                y="44"
                class="lbl-sub lbl-master-sub"
              >
                {{ n.sub }}
              </text>
            </template>

            <!-- 子对象 -->
            <template v-else-if="n.shape === 'card' && n.role === 'subobject'">
              <ellipse
                :cx="n.w / 2"
                :cy="n.h + 5"
                rx="n.w * 0.42"
                ry="6"
                class="ground-shadow"
              />
              <rect
                :width="n.w"
                :height="n.h"
                :rx="n.rx"
                fill="url(#grad-subobject)"
                stroke="url(#grad-subobject-stroke)"
                stroke-width="1.5"
                class="shape-3d"
              />
              <text :x="n.w / 2" y="22" class="lbl-title lbl-subobject">{{ n.title }}</text>
              <text
                v-if="n.sub"
                :x="n.w / 2"
                y="38"
                class="lbl-sub lbl-subobject-sub"
              >
                {{ n.sub }}
              </text>
            </template>

            <!-- 属性：小号卡片 -->
            <template v-else-if="n.shape === 'card' && n.role === 'property'">
              <ellipse
                :cx="n.w / 2"
                :cy="n.h + 5"
                rx="n.w * 0.42"
                ry="6"
                class="ground-shadow"
              />
              <rect
                :width="n.w"
                :height="n.h"
                :rx="n.rx"
                fill="url(#grad-property)"
                stroke="url(#grad-property-stroke)"
                stroke-width="1.5"
                class="shape-3d"
              />
              <text :x="n.w / 2" y="20" class="lbl-title lbl-property">{{ n.title }}</text>
              <text
                v-if="n.sub"
                :x="n.w / 2"
                y="36"
                class="lbl-sub lbl-property-sub"
              >
                {{ n.sub }}
              </text>
            </template>

            <!-- 事件：神经元球体 -->
            <template v-else-if="n.shape === 'neuron'">
              <ellipse
                :cx="n.w / 2"
                :cy="n.h + 5"
                :rx="n.w * 0.38"
                ry="6"
                class="ground-shadow"
              />
              <circle
                :cx="n.w / 2"
                :cy="n.h / 2"
                :r="n.w / 2 - 1"
                fill="url(#grad-event)"
                stroke="url(#grad-event-stroke)"
                stroke-width="1.5"
                class="shape-3d"
              />
              <circle
                :cx="n.w / 2 - 6"
                :cy="n.h / 2 - 6"
                :r="n.w * 0.12"
                fill="#fff"
                opacity="0.45"
              />
              <text :x="n.w / 2" :y="n.h / 2 + 4" class="lbl-neuron">{{ n.title }}</text>
            </template>

            <!-- 关系：菱形 -->
            <template v-else-if="n.shape === 'diamond'">
              <polygon
                :points="diamondPoints(n)"
                fill="url(#grad-relation)"
                stroke="#6d28d9"
                stroke-width="1.4"
                class="shape-3d"
              />
              <text :x="n.w / 2" :y="n.h / 2 + 4" class="lbl-diamond">{{ n.title }}</text>
            </template>

            <!-- 兜底：role/shape 与上述分支不一致时仍显示，避免「有数据但画布全空」 -->
            <template v-else>
              <rect
                :width="Math.max(n.w || 96, 80)"
                :height="Math.max(n.h || 40, 36)"
                :rx="n.rx || 8"
                fill="#e2e8f0"
                stroke="#64748b"
                stroke-width="1.2"
              />
              <text
                :x="Math.max(n.w || 96, 80) / 2"
                y="22"
                class="lbl-title"
                text-anchor="middle"
              >
                {{ n.title }}
              </text>
            </template>
          </g>
        </g>
      </svg>
      <p v-if="graphError" class="graph-error">{{ graphError }}</p>
      <p v-else-if="graphMeta?.hint && graphSource === 'neo4j'" class="graph-info">{{ graphMeta.hint }}</p>
      <p class="canvas-hint">
        金：主数据 · 蓝：业务对象 · 灰：子对象 · 橙：事件 · 紫：关系 · 绿：属性。全景模式会拉取关系子图并补全库内节点（含孤立主数据/子对象，上限见后端配置）。滚轮缩放，空白处平移，节点可拖拽。
      </p>
    </div>
  </div>
</template>

<style scoped>
.canvas-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: linear-gradient(180deg, #e8eef5 0%, #f1f5f9 40%, #e2e8f0 100%);
  border-right: 1px solid #e2e8f0;
}
.canvas-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.55rem 0.75rem;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}
.canvas-title {
  font-weight: 650;
  font-size: 0.95rem;
  color: #0f172a;
}
.canvas-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.45rem;
  border-radius: 6px;
  background: linear-gradient(135deg, #e0e7ff 0%, #e0f2fe 100%);
  color: #3730a3;
  font-weight: 600;
}
.canvas-badge.badge-live {
  background: linear-gradient(135deg, #dcfce7 0%, #d1fae5 100%);
  color: #14532d;
}
.reload-btn {
  font-size: 0.72rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  cursor: pointer;
  font-weight: 600;
}
.reload-btn:hover:not(:disabled) {
  background: #f1f5f9;
}
.reload-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.graph-error {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  color: #b91c1c;
  text-align: center;
  max-width: 44rem;
  line-height: 1.4;
}
.graph-info {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  color: #92400e;
  text-align: center;
  max-width: 44rem;
  line-height: 1.45;
  background: rgba(254, 243, 199, 0.65);
  padding: 0.35rem 0.5rem;
  border-radius: 6px;
}
.lbl-property {
  font-size: 11px;
  fill: #064e3b;
}
.lbl-property-sub {
  font-size: 9px;
  fill: #047857;
}
.lbl-master {
  fill: #78350f;
}
.lbl-master-sub {
  fill: #92400e;
  font-size: 10px;
}
.lbl-subobject {
  font-size: 11px;
  fill: #1e293b;
}
.lbl-subobject-sub {
  font-size: 9px;
  fill: #475569;
}
.zoom-controls {
  display: inline-flex;
  align-items: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: #f8fafc;
}
.icon-btn {
  width: 2rem;
  height: 2rem;
  border: none;
  background: transparent;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  color: #334155;
}
.icon-btn:hover {
  background: #e2e8f0;
}
.zoom-pct {
  min-width: 3.25rem;
  padding: 0 0.35rem;
  border: none;
  border-left: 1px solid #e2e8f0;
  border-right: 1px solid #e2e8f0;
  background: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}
.zoom-pct:hover {
  background: #f1f5f9;
}
.canvas-surface {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.75rem;
}
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 50% 30%, rgba(56, 189, 248, 0.06) 0%, transparent 50%),
    linear-gradient(rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px);
  background-size:
    100% 100%,
    24px 24px,
    24px 24px;
  pointer-events: none;
}
.graph-svg {
  position: relative;
  width: 100%;
  max-width: 100%;
  height: auto;
  min-height: 280px;
  flex: 1;
  z-index: 1;
  touch-action: none;
  user-select: none;
}
.pan-layer {
  cursor: grab;
}
.pan-layer:active {
  cursor: grabbing;
}
.world {
  pointer-events: auto;
}
.node-group {
  cursor: grab;
}
.node-group.grabbing {
  cursor: grabbing;
}
.ground-shadow {
  fill: rgba(15, 23, 42, 0.12);
  pointer-events: none;
}
.shape-3d {
  pointer-events: auto;
}
.lbl-title {
  text-anchor: middle;
  fill: #0c4a6e;
  font-size: 13px;
  font-weight: 700;
  pointer-events: none;
}
.lbl-sub {
  text-anchor: middle;
  fill: #0369a1;
  font-size: 10px;
  font-weight: 600;
  pointer-events: none;
}
.lbl-neuron {
  text-anchor: middle;
  fill: #78350f;
  font-size: 9.5px;
  font-weight: 700;
  pointer-events: none;
}
.lbl-diamond {
  text-anchor: middle;
  fill: #4c1d95;
  font-size: 9px;
  font-weight: 700;
  pointer-events: none;
}
.axis-label {
  fill: #64748b;
  font-size: 10px;
}
.edge-path {
  stroke-width: 2.5;
  pointer-events: none;
}
.edge-flow {
  stroke: #2563eb;
  stroke-width: 2.8;
  opacity: 0.95;
}
.edge-assoc {
  stroke: #0d9488;
  stroke-width: 2.2;
  opacity: 0.88;
  stroke-dasharray: 6 4;
}
.edge-weak {
  stroke: #7c3aed;
  stroke-width: 2;
  opacity: 0.8;
  stroke-dasharray: 4 5;
}
.canvas-hint {
  position: relative;
  z-index: 1;
  margin: 0.5rem 0 0;
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  max-width: 44rem;
  padding: 0 0.5rem;
  flex-shrink: 0;
  line-height: 1.45;
}
</style>
