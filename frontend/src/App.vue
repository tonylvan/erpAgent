<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { postIntelligenceQuery } from "./api/intelligence.js";
import P2PGraphCanvas from "./components/P2PGraphCanvas.vue";
import OntologyObjectsPanel from "./components/OntologyObjectsPanel.vue";
import ScenarioInputPanel from "./components/ScenarioInputPanel.vue";
import ResultPanel from "./components/ResultPanel.vue";

const result = ref(null);
const loading = ref(false);
const error = ref("");

/** 左侧面板宽度占比（可拖动分隔条，类似 Split View） */
const workspaceEl = ref(null);
const splitPct = ref(58);
const resizing = ref(false);

function clampSplit(v) {
  return Math.min(82, Math.max(22, v));
}

function onSplitResizeStart(e) {
  e.preventDefault();
  resizing.value = true;
}

function onSplitResizeMove(e) {
  if (!resizing.value || !workspaceEl.value) return;
  const rect = workspaceEl.value.getBoundingClientRect();
  const x = e.clientX - rect.left;
  splitPct.value = clampSplit((x / rect.width) * 100);
}

function onSplitResizeEnd() {
  resizing.value = false;
}

onMounted(() => {
  window.addEventListener("mousemove", onSplitResizeMove);
  window.addEventListener("mouseup", onSplitResizeEnd);
});

onUnmounted(() => {
  window.removeEventListener("mousemove", onSplitResizeMove);
  window.removeEventListener("mouseup", onSplitResizeEnd);
});

async function onExecute({ mode, text }) {
  error.value = "";
  if (!text) {
    result.value = {
      process: [
        {
          title: "校验",
          detail: "未输入内容。请在上方文本框中填写假设、问题或需回放的对象。",
        },
      ],
      conclusion: "",
    };
    return;
  }

  loading.value = true;
  result.value = null;

  try {
    const data = await postIntelligenceQuery(text);
    const modeLabel = mode === "plan" ? "预测规划" : "事件回放";
    result.value = {
      process: [
        {
          title: "图谱问答",
          detail: `模式：${modeLabel}。已调用后端「自然语言 → Cypher → Neo4j → LLM 整理」。`,
        },
      ],
      conclusion: data.answer ?? "",
      cypher: data.cypher ?? null,
      records: data.records ?? null,
      meta: data.meta ?? {},
    };
  } catch (e) {
    result.value = null;
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    ref="workspaceEl"
    class="workspace"
    :class="{ 'is-resizing': resizing }"
  >
    <div class="pane-left" :style="{ width: splitPct + '%' }">
      <P2PGraphCanvas />
    </div>
    <div
      class="splitter"
      title="拖动调整左右面板宽度"
      role="separator"
      aria-orientation="vertical"
      :aria-valuenow="Math.round(splitPct)"
      @mousedown="onSplitResizeStart"
    />
    <div class="pane-right">
      <OntologyObjectsPanel class="block-ontology" />
      <ScenarioInputPanel
        class="block-scenario"
        :loading="loading"
        @execute="onExecute"
      />
      <ResultPanel
        class="block-result"
        :result="result"
        :loading="loading"
        :error="error"
      />
    </div>
  </div>
</template>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
body {
  font-family:
    system-ui,
    -apple-system,
    "Segoe UI",
    Roboto,
    "Helvetica Neue",
    Arial,
    sans-serif;
  color: #0f172a;
  background: #e2e8f0;
}
</style>

<style scoped>
.workspace {
  display: flex;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  --splitter-bg: transparent;
  --splitter-bg-hover: rgba(15, 23, 42, 0.06);
}
.workspace.is-resizing {
  cursor: col-resize;
  user-select: none;
}
.pane-left {
  flex: 0 0 auto;
  min-width: 200px;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.splitter {
  flex: 0 0 6px;
  width: 6px;
  background: var(--splitter-bg);
  cursor: col-resize;
  position: relative;
  z-index: 2;
  transition: background 0.12s ease;
}
.splitter:hover,
.workspace.is-resizing .splitter {
  background: var(--splitter-bg-hover);
}
.splitter::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: -4px;
  right: -4px;
}
.pane-right {
  flex: 1 1 auto;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  box-sizing: border-box;
  background: #f1f5f9;
  border-left: 1px solid #e2e8f0;
  min-height: 0;
}
.block-ontology {
  flex: 1 1 36%;
  min-height: 120px;
}
.block-scenario {
  flex: 0 0 auto;
}
.block-result {
  flex: 1 1 28%;
  min-height: 140px;
}

@media (max-width: 900px) {
  .workspace {
    flex-direction: column;
    overflow: auto;
    height: auto;
    min-height: 100%;
  }
  .pane-left {
    width: 100% !important;
    flex: 0 0 auto;
    min-height: 320px;
  }
  .splitter {
    display: none;
  }
  .pane-right {
    flex: 1 1 auto;
    width: 100%;
    min-width: 0;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }
}
</style>
