<template>
  <div class="path-analysis">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">🔗</span>
        <span class="title-text">路径分析</span>
      </h1>
      <p class="page-description">分析两个节点之间的关联路径，发现业务关系网络</p>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：查询条件 -->
      <aside class="query-panel">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🔍 路径查询</span>
            </div>
          </template>

          <el-form :model="queryForm" label-position="top">
            <el-form-item label="起始节点 ID">
              <el-input
                v-model="queryForm.sourceNodeId"
                placeholder="例如：CUST_001"
                clearable
              />
            </el-form-item>

            <el-form-item label="目标节点 ID">
              <el-input
                v-model="queryForm.targetNodeId"
                placeholder="例如：ORDER_001"
                clearable
              />
            </el-form-item>

            <el-form-item label="最大深度">
              <el-slider
                v-model="queryForm.maxDepth"
                :min="1"
                :max="10"
                :step="1"
                show-input
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="isLoading"
                @click="analyzePath"
                block
              >
                🔍 分析路径
              </el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <el-form :model="neighborForm" label-position="top">
            <el-form-item label="或查询节点邻居">
              <el-input
                v-model="neighborForm.nodeId"
                placeholder="输入节点 ID"
                clearable
              />
            </el-form-item>

            <el-form-item label="查询深度">
              <el-select v-model="neighborForm.depth" style="width: 100%">
                <el-option label="1 层" :value="1" />
                <el-option label="2 层" :value="2" />
                <el-option label="3 层" :value="3" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button
                type="success"
                :loading="isLoadingNeighbors"
                @click="getNeighbors"
                block
              >
                🌐 查询邻居
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 查询历史 -->
        <el-card class="panel-card" shadow="never" style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <span>📜 查询历史</span>
              <el-button text size="small" @click="clearHistory">
                清空
              </el-button>
            </div>
          </template>

          <div class="history-list">
            <div
              v-for="(item, idx) in queryHistory"
              :key="idx"
              class="history-item"
              @click="loadHistory(item)"
            >
              <div class="history-nodes">
                <span class="node-id">{{ item.source }}</span>
                <span class="arrow">→</span>
                <span class="node-id">{{ item.target }}</span>
              </div>
              <div class="history-meta">
                <el-tag size="small" type="info">深度：{{ item.depth }}</el-tag>
                <el-tag size="small" :type="item.pathCount > 0 ? 'success' : 'warning'">
                  {{ item.pathCount }} 条路径
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </aside>

      <!-- 中间：路径可视化 -->
      <div class="visualization-panel">
        <el-card class="viz-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📊 路径可视化</span>
              <el-tag v-if="result" type="success">
                找到 {{ result.path_count }} 条路径
              </el-tag>
            </div>
          </template>

          <div v-if="!result && !isLoading" class="empty-state">
            <div class="empty-icon">🔗</div>
            <p class="empty-text">暂无路径分析结果</p>
            <p class="empty-hint">在左侧输入起始和目标节点 ID 开始分析</p>
          </div>

          <div v-else-if="isLoading" class="loading-state">
            <el-skeleton :rows="5" animated />
          </div>

          <div v-else-if="result && result.path_count === 0" class="no-result-state">
            <div class="no-result-icon">❌</div>
            <p class="no-result-text">未找到路径</p>
            <p class="no-result-hint">
              {{ result.error || '两个节点之间没有关联路径' }}
            </p>
          </div>

          <div v-else class="result-state">
            <!-- 路径统计 -->
            <div class="path-stats">
              <el-descriptions :column="3" size="small" border>
                <el-descriptions-item label="路径数量">
                  {{ result.path_count }}
                </el-descriptions-item>
                <el-descriptions-item label="最短路径">
                  {{ result.min_depth }} 层
                </el-descriptions-item>
                <el-descriptions-item label="最长路径">
                  {{ result.max_depth }} 层
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 路径列表 -->
            <div class="path-list">
              <div
                v-for="(path, pathIdx) in result.paths"
                :key="pathIdx"
                class="path-item"
              >
                <div class="path-header">
                  <span class="path-index">路径 {{ pathIdx + 1 }}</span>
                  <el-tag size="small">
                    {{ path.filter(n => n.type === 'node').length }} 个节点
                  </el-tag>
                </div>

                <!-- 路径流程图 -->
                <div class="path-flow">
                  <template v-for="(node, nodeIdx) in path" :key="nodeIdx">
                    <div
                      v-if="node.type === 'node'"
                      class="flow-node"
                      :class="getNodeClass(node.node_type)"
                    >
                      <div class="node-icon">{{ getNodeIcon(node.node_type) }}</div>
                      <div class="node-info">
                        <div class="node-name">{{ node.name }}</div>
                        <div class="node-type">{{ node.node_type }}</div>
                      </div>
                    </div>
                    <div
                      v-else-if="node.type === 'relationship'"
                      class="flow-relationship"
                    >
                      <div class="rel-line"></div>
                      <div class="rel-label">{{ node.type_name }}</div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：节点详情 -->
      <aside class="detail-panel" v-if="selectedNode">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📋 节点详情</span>
              <el-button text :icon="Close" size="small" @click="selectedNode = null" />
            </div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="节点 ID">
              {{ selectedNode.id }}
            </el-descriptions-item>
            <el-descriptions-item label="节点类型">
              <el-tag size="small">{{ selectedNode.node_type }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="名称">
              {{ selectedNode.name }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <div class="node-properties">
            <div class="prop-title">属性</div>
            <el-table :data="nodeProperties" size="small" :show-header="false">
              <el-table-column prop="key" label="键" width="120" />
              <el-table-column prop="value" label="值" />
            </el-table>
          </div>
        </el-card>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import GlobalNav from '../components/GlobalNav.vue'

// 查询表单
const queryForm = reactive({
  sourceNodeId: '',
  targetNodeId: '',
  maxDepth: 5
})

const neighborForm = reactive({
  nodeId: '',
  depth: 1
})

// 加载状态
const isLoading = ref(false)
const isLoadingNeighbors = ref(false)

// 查询结果
const result = ref<any>(null)

// 查询历史
const queryHistory = ref<any[]>([])

// 选中的节点
const selectedNode = ref<any>(null)

// 节点属性
const nodeProperties = computed(() => {
  if (!selectedNode.value || !selectedNode.value.properties) return []
  
  return Object.entries(selectedNode.value.properties).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
})

// 分析路径
const analyzePath = async () => {
  if (!queryForm.sourceNodeId || !queryForm.targetNodeId) {
    ElMessage.warning('请输入起始节点和目标节点 ID')
    return
  }

  isLoading.value = true
  result.value = null

  try {
    const response = await fetch('/api/v1/path-analysis/analyze-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(queryForm)
    })

    const data = await response.json()

    if (data.success) {
      result.value = data
      ElMessage.success(`找到 ${data.path_count} 条路径`)
      
      // 添加到历史记录
      addToHistory({
        source: queryForm.sourceNodeId,
        target: queryForm.targetNodeId,
        depth: queryForm.maxDepth,
        pathCount: data.path_count
      })
    } else {
      result.value = data
      ElMessage.warning(data.error || '未找到路径')
    }
  } catch (error) {
    console.error('[PathAnalysis] Error:', error)
    ElMessage.error('路径分析失败：' + error)
  } finally {
    isLoading.value = false
  }
}

// 查询邻居
const getNeighbors = async () => {
  if (!neighborForm.nodeId) {
    ElMessage.warning('请输入节点 ID')
    return
  }

  isLoadingNeighbors.value = true

  try {
    const response = await fetch(
      `/api/v1/path-analysis/node/${neighborForm.nodeId}/neighbors?depth=${neighborForm.depth}`
    )
    const data = await response.json()

    if (data.success) {
      ElMessage.success(`找到 ${data.stats.node_count} 个节点，${data.stats.edge_count} 条关系`)
      // TODO: 显示邻居图谱
    } else {
      ElMessage.warning(data.error || '查询失败')
    }
  } catch (error) {
    console.error('[PathAnalysis] Error:', error)
    ElMessage.error('查询失败：' + error)
  } finally {
    isLoadingNeighbors.value = false
  }
}

// 添加到历史记录
const addToHistory = (item: any) => {
  queryHistory.value.unshift({ ...item, timestamp: Date.now() })
  if (queryHistory.value.length > 10) {
    queryHistory.value.pop()
  }
}

// 加载历史记录
const loadHistory = (item: any) => {
  queryForm.sourceNodeId = item.source
  queryForm.targetNodeId = item.target
  queryForm.maxDepth = item.depth
  analyzePath()
}

// 清空历史
const clearHistory = () => {
  queryHistory.value = []
  ElMessage.success('历史记录已清空')
}

// 获取节点样式类
const getNodeClass = (type: string) => {
  const classes: Record<string, string> = {
    Customer: 'node-customer',
    Order: 'node-order',
    Sale: 'node-sale',
    Payment: 'node-payment',
    Invoice: 'node-invoice',
    Supplier: 'node-supplier',
    PurchaseOrder: 'node-purchase',
    POLine: 'node-pol ine'
  }
  return classes[type] || 'node-default'
}

// 获取节点图标
const getNodeIcon = (type: string) => {
  const icons: Record<string, string> = {
    Customer: '👥',
    Order: '📦',
    Sale: '💰',
    Payment: '💳',
    Invoice: '📄',
    Supplier: '🏢',
    PurchaseOrder: '📝',
    POLine: '📋'
  }
  return icons[type] || '📍'
}

// 点击节点查看详情
const selectNode = (node: any) => {
  selectedNode.value = node
  ElMessage.info(`查看节点详情：${node.name}`)
}

onMounted(() => {
  // 从 localStorage 加载历史记录
  const saved = localStorage.getItem('path-analysis-history')
  if (saved) {
    try {
      queryHistory.value = JSON.parse(saved)
    } catch (e) {
      console.error('[PathAnalysis] Failed to load history:', e)
    }
  }
})

// 监听历史变化并保存
watch(
  () => queryHistory.value,
  (newVal) => {
    localStorage.setItem('path-analysis-history', JSON.stringify(newVal))
  },
  { deep: true }
)
</script>

<style scoped>
.path-analysis {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
  color: white;
}

.page-title {
  font-size: 28px;
  margin: 0 0 8px 0;
}

.title-icon {
  margin-right: 12px;
}

.page-description {
  opacity: 0.9;
  margin: 0;
}

.main-content {
  display: grid;
  grid-template-columns: 320px 1fr 320px;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.query-panel {
  display: flex;
  flex-direction: column;
}

.panel-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.viz-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  min-height: 600px;
}

.empty-state,
.loading-state,
.no-result-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 18px;
  color: #666;
  margin: 8px 0;
}

.empty-hint {
  font-size: 14px;
  color: #999;
}

.no-result-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.no-result-text {
  font-size: 18px;
  color: #f56c6c;
  margin: 8px 0;
}

.no-result-hint {
  font-size: 14px;
  color: #999;
}

.result-state {
  padding: 16px;
}

.path-stats {
  margin-bottom: 24px;
}

.path-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.path-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.path-index {
  font-weight: bold;
  color: #667eea;
}

.path-flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.flow-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.flow-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.node-icon {
  font-size: 20px;
}

.node-info {
  display: flex;
  flex-direction: column;
}

.node-name {
  font-weight: bold;
  font-size: 14px;
}

.node-type {
  font-size: 12px;
  color: #999;
}

.flow-relationship {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
}

.rel-line {
  width: 60px;
  height: 2px;
  background: #667eea;
  position: relative;
}

.rel-line::after {
  content: '→';
  position: absolute;
  right: -8px;
  top: -8px;
  color: #667eea;
}

.rel-label {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.history-item:hover {
  border-color: #667eea;
  background: #f5f7ff;
}

.history-nodes {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.node-id {
  font-family: monospace;
  font-size: 13px;
  color: #333;
}

.arrow {
  color: #667eea;
}

.history-meta {
  display: flex;
  gap: 8px;
}

.detail-panel {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.node-properties {
  margin-top: 16px;
}

.prop-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #666;
}
</style>
