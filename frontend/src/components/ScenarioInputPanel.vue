<script setup>
import { ref } from "vue";

defineProps({
  /** 执行中禁用按钮，防止重复提交 */
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["execute"]);

const activeTab = ref("plan"); // plan | replay
const question = ref("");

const placeholders = {
  plan: "例如：若提前 10 天付款，折扣与现金流影响如何？",
  replay: "例如：回放发票 INV-2026-00123 从创建到挂起的完整事件链",
};

function run() {
  emit("execute", {
    mode: activeTab.value,
    text: question.value.trim(),
  });
}
</script>

<template>
  <section class="panel">
    <h2 class="panel-title">分析与回放</h2>

    <div class="tabs" role="tablist">
      <button
        type="button"
        class="tab"
        :class="{ active: activeTab === 'plan' }"
        role="tab"
        :aria-selected="activeTab === 'plan'"
        @click="activeTab = 'plan'"
      >
        预测规划
      </button>
      <button
        type="button"
        class="tab"
        :class="{ active: activeTab === 'replay' }"
        role="tab"
        :aria-selected="activeTab === 'replay'"
        @click="activeTab = 'replay'"
      >
        事件回放
      </button>
    </div>

    <label class="sr-only" for="scenario-input">假设或问题</label>
    <textarea
      id="scenario-input"
      v-model="question"
      class="textarea"
      rows="4"
      :placeholder="placeholders[activeTab]"
    />

    <div class="actions">
      <button
        type="button"
        class="btn-primary"
        :disabled="loading"
        @click="run"
      >
        {{ loading ? "执行中…" : "立即执行" }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  flex-shrink: 0;
}
.panel-title {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
  font-weight: 650;
  color: #0f172a;
}
.tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 0.65rem;
  border-bottom: 1px solid #e2e8f0;
}
.tab {
  border: none;
  background: transparent;
  padding: 0.45rem 0.75rem;
  font-size: 0.85rem;
  cursor: pointer;
  color: #64748b;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.tab:hover {
  color: #0f172a;
}
.tab.active {
  color: #1d4ed8;
  font-weight: 650;
  border-bottom-color: #2563eb;
}
.textarea {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  min-height: 5.5rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font: inherit;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #0f172a;
}
.textarea::placeholder {
  color: #94a3b8;
}
.textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.65rem;
}
.btn-primary {
  border: none;
  background: #2563eb;
  color: #fff;
  padding: 0.5rem 1.15rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover {
  background: #1d4ed8;
}
.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

/* 📱 手机端优化 (≤768px) */
@media (max-width: 768px) {
  .panel {
    padding: 8px;
    border-radius: 0;
  }

  .panel-title {
    font-size: 14px;
    margin-bottom: 8px;
  }

  .tabs {
    gap: 4px;
    margin-bottom: 8px;
  }

  .tab {
    padding: 6px 10px;
    font-size: 13px;
  }

  .textarea {
    min-height: 80px;
    max-height: 120px;
    font-size: 14px;
    padding: 10px;
  }

  .actions {
    margin-top: 8px;
  }

  .btn-primary {
    width: 100%;
    padding: 12px;
    font-size: 15px;
  }
}

/* 📱 小屏手机优化 (≤375px) */
@media (max-width: 375px) {
  .panel-title {
    font-size: 13px;
  }

  .tab {
    padding: 5px 8px;
    font-size: 12px;
  }

  .textarea {
    min-height: 70px;
    font-size: 13px;
  }

  .btn-primary {
    padding: 10px;
    font-size: 14px;
  }
}
</style>
