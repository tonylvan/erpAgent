<script setup>
import { computed } from "vue";

const props = defineProps({
  /** { process, conclusion, cypher?, records?, meta?, richHtml? } */
  result: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  emptyMessage: {
    type: String,
    default:
      "点击「立即执行」后，此处展示分析过程与结论。将调用后端自然语言 → Cypher → Neo4j → 整理回答。",
  },
});

const recordsJson = computed(() => {
  const r = props.result?.records;
  if (!r || !Array.isArray(r)) return "";
  try {
    return JSON.stringify(r, null, 2);
  } catch {
    return String(r);
  }
});

const recordsTruncated = computed(() => {
  const s = recordsJson.value;
  if (!s) return "";
  const max = 24000;
  if (s.length <= max) return s;
  return `${s.slice(0, max)}\n\n…（已截断，完整数据见接口返回）`;
});
</script>

<template>
  <section class="panel">
    <h2 class="panel-title">结果呈现</h2>

    <div v-if="loading" class="state-loading">正在调用图谱问答服务…</div>

    <div v-else-if="error" class="state-error">{{ error }}</div>

    <div v-else-if="!result" class="empty">{{ emptyMessage }}</div>

    <article v-else class="rich-body">
      <section v-if="result.process?.length" class="block">
        <h3 class="block-title">分析过程</h3>
        <ol class="steps">
          <li v-for="(step, i) in result.process" :key="i" class="step">
            <span v-if="step.title" class="step-title">{{ step.title }}</span>
            <p class="step-detail">{{ step.detail }}</p>
          </li>
        </ol>
      </section>

      <section v-if="result.cypher" class="block">
        <h3 class="block-title">生成的 Cypher</h3>
        <pre class="code-block">{{ result.cypher }}</pre>
      </section>

      <section v-if="result.records?.length" class="block">
        <h3 class="block-title">
          查询结果（{{ result.records.length }} 行）
        </h3>
        <pre class="code-block json">{{ recordsTruncated }}</pre>
      </section>

      <section v-if="result.conclusion" class="block conclusion-block">
        <h3 class="block-title">结论</h3>
        <p class="conclusion-text">{{ result.conclusion }}</p>
      </section>

      <div
        v-if="result.richHtml"
        class="rich-html"
        v-html="result.richHtml"
      />
    </article>
  </section>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  min-height: 140px;
  flex: 1;
  min-height: 0;
}
.panel-title {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
  font-weight: 650;
  color: #0f172a;
  flex-shrink: 0;
}
.state-loading {
  font-size: 0.85rem;
  color: #2563eb;
  padding: 0.35rem 0;
}
.state-error {
  font-size: 0.85rem;
  color: #b91c1c;
  line-height: 1.5;
  white-space: pre-wrap;
}
.empty {
  font-size: 0.82rem;
  color: #64748b;
  line-height: 1.5;
  flex: 1;
  overflow: auto;
}
.rich-body {
  overflow: auto;
  min-height: 0;
  flex: 1;
  font-size: 0.85rem;
  line-height: 1.55;
  color: #334155;
}
.block {
  margin-bottom: 1rem;
}
.block-title {
  margin: 0 0 0.45rem;
  font-size: 0.8rem;
  font-weight: 650;
  color: #0f172a;
  text-transform: none;
}
.steps {
  margin: 0;
  padding-left: 1.2rem;
}
.step {
  margin-bottom: 0.5rem;
}
.step-title {
  display: block;
  font-weight: 650;
  color: #1e293b;
  margin-bottom: 0.15rem;
}
.step-detail {
  margin: 0;
  color: #475569;
}
.code-block {
  margin: 0;
  padding: 0.6rem 0.75rem;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  font-size: 0.75rem;
  line-height: 1.45;
  overflow: auto;
  max-height: 220px;
}
.code-block.json {
  max-height: 280px;
}
.conclusion-block {
  padding: 0.65rem 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.conclusion-text {
  margin: 0;
  font-weight: 500;
  color: #0f172a;
  white-space: pre-wrap;
}
.rich-html :deep(p) {
  margin: 0 0 0.5rem;
}
.rich-html :deep(ul) {
  margin: 0.25rem 0 0.5rem;
  padding-left: 1.2rem;
}
.rich-html :deep(strong) {
  color: #0f172a;
}
</style>
