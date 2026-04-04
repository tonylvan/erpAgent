<script setup>
import { computed, ref } from "vue";
import { ontologyFromNeo4j, ontologyFromPostgres } from "../data/mockOntology.js";

const mode = ref("neo4j"); // neo4j | postgres

const activeOntology = computed(() =>
  mode.value === "neo4j" ? ontologyFromNeo4j : ontologyFromPostgres
);
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <h2 class="panel-title">本体对象</h2>
      <div class="segmented" role="tablist" aria-label="数据来源">
        <button
          type="button"
          class="seg-btn"
          :class="{ active: mode === 'neo4j' }"
          @click="mode = 'neo4j'"
        >
          Neo4j
        </button>
        <button
          type="button"
          class="seg-btn"
          :class="{ active: mode === 'postgres' }"
          @click="mode = 'postgres'"
        >
          PostgreSQL 元数据
        </button>
      </div>
    </div>
    <p class="panel-desc">
      系统默认从 Neo4j 读取本体；也可由 PostgreSQL
      元数据生成映射视图（演示数据）。
    </p>

    <div class="scroll-area">
      <h3 class="subhead">实体</h3>
      <ul class="entity-list">
        <li v-for="e in activeOntology.entities" :key="e.type" class="entity-item">
          <span class="entity-type">{{ e.type }}</span>
          <span class="entity-label">{{ e.label }}</span>
          <span class="entity-desc">{{ e.description }}</span>
        </li>
      </ul>

      <h3 class="subhead">关系</h3>
      <ul class="rel-list">
        <li v-for="(r, i) in activeOntology.relations" :key="i" class="rel-item">
          <code class="rel-name">{{ r.name }}</code>
          <span class="rel-arrow">{{ r.from }} → {{ r.to }}</span>
        </li>
      </ul>
    </div>
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
  min-height: 0;
  flex: 1;
}
.panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.panel-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 650;
  color: #0f172a;
}
.segmented {
  display: inline-flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.seg-btn {
  border: none;
  background: #f8fafc;
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  cursor: pointer;
  color: #475569;
}
.seg-btn + .seg-btn {
  border-left: 1px solid #e2e8f0;
}
.seg-btn.active {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 600;
}
.panel-desc {
  margin: 0.5rem 0 0.65rem;
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.45;
}
.scroll-area {
  overflow: auto;
  min-height: 0;
  flex: 1;
  padding-right: 0.25rem;
}
.subhead {
  margin: 0.5rem 0 0.35rem;
  font-size: 0.8rem;
  font-weight: 650;
  color: #334155;
}
.entity-list,
.rel-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.entity-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.15rem 0.5rem;
  padding: 0.45rem 0.5rem;
  border-radius: 6px;
  background: #f8fafc;
  margin-bottom: 0.35rem;
  font-size: 0.78rem;
}
.entity-type {
  font-weight: 650;
  color: #0f172a;
  grid-column: 1 / -1;
}
.entity-label {
  color: #64748b;
}
.entity-desc {
  grid-column: 1 / -1;
  color: #94a3b8;
  font-size: 0.72rem;
}
.rel-item {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.35rem;
  padding: 0.35rem 0.5rem;
  border: 1px solid #f1f5f9;
  border-radius: 6px;
  margin-bottom: 0.35rem;
  font-size: 0.75rem;
}
.rel-name {
  background: #f1f5f9;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.72rem;
  color: #0f172a;
}
.rel-arrow {
  color: #64748b;
}

/* 📱 手机端优化 (≤768px) */
@media (max-width: 768px) {
  .panel {
    padding: 6px;
    border-radius: 0;
  }

  .panel-title {
    font-size: 13px;
  }

  .seg-btn {
    padding: 4px 8px;
    font-size: 12px;
  }

  .panel-desc {
    font-size: 11px;
    margin: 4px 0 6px;
  }

  .subhead {
    font-size: 12px;
    margin: 6px 0 4px;
  }

  .entity-item,
  .rel-item {
    font-size: 11px;
    padding: 4px 6px;
  }

  .entity-type {
    font-size: 12px;
  }

  .entity-desc {
    font-size: 10px;
  }

  .rel-name {
    font-size: 10px;
    padding: 1px 4px;
  }
}

/* 📱 小屏手机优化 (≤375px) */
@media (max-width: 375px) {
  .panel-title {
    font-size: 12px;
  }

  .seg-btn {
    font-size: 11px;
  }

  .panel-desc {
    font-size: 10px;
  }

  .entity-item,
  .rel-item {
    font-size: 10px;
  }
}
</style>
