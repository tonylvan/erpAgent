<template>
  <div class="graph-v2">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="nav-left">
        <button class="nav-btn" @click="navigateTo('alert')">
          🚨 预警中心
        </button>
        <button class="nav-btn" @click="navigateTo('query')">
          💬 智能问数
        </button>
        <button class="nav-btn active">
          🔍 返回图谱
        </button>
      </div>
      <div class="nav-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索节点..."
          size="small"
          style="width: 200px"
          clearable
          :prefix-icon="Search"
        />
        <el-button :icon="Plus" size="small" @click="addNode">
          添加节点
        </el-button>
        <el-dropdown trigger="click">
          <button class="user-menu">
            <el-avatar :size="24" src="https://picsum.photos/40/40"></el-avatar>
            <span>Admin</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>图谱设置</el-dropdown-item>
              <el-dropdown-item>导出图谱</el-dropdown-item>
              <el-dropdown-item divided>系统设置</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧本体面板 -->
      <aside class="ontology-panel">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📚 本体对象</span>
              <el-button text size="small" @click="toggleOntology">
                {{ ontologyExpanded ? '收起' : '展开' }}
              </el-button>
            </div>
          </template>
          
          <div v-show="ontologyExpanded" class="ontology-list">
            <div
              v-for="(type, idx) in ontologyTypes"
              :key="idx"
              class="ontology-item"
              :class="{ active: selectedType === type.name }"
              @click="selectType(type)"
            >
              <span class="ontology-icon">{{ type.icon }}</span>
              <span class="ontology-name">{{ type.label }}</span>
              <el-badge :value="type.count" size="small" class="ontology-count" />
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🔍 快速筛选</span>
              <el-button text size="small" @click="resetFilters">
                重置
              </el-button>
            </div>
          </template>
          
          <div class="filter-list">
            <el-checkbox-group v-model="selectedFilters">
              <el-checkbox
                v-for="(filter, idx) in filters"
                :key="idx"
                :label="filter.value"
              >
                {{ filter.label }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </el-card>
      </aside>

      <!-- 中间画布区 -->
      <div class="canvas-section">
        <!-- 工具栏 -->
        <div class="canvas-toolbar">
          <el-button-group>
            <el-button :icon="ZoomIn" @click="zoomIn" title="放大" />
            <el-button :icon="ZoomOut" @click="zoomOut" title="缩小" />
            <el-button :icon="Refresh" @click="resetView" title="重置视图" />
            <el-divider direction="vertical" />
            <el-button :icon="Grid" @click="toggleGrid" title="网格" />
            <el-button :icon="FullScreen" @click="toggleFullscreen" title="全屏" />
          </el-button-group>
          
          <div class="canvas-info">
            <span>节点：{{ nodeCount }}</span>
            <span>关系：{{ edgeCount }}</span>
          </div>
        </div>

        <!-- 图谱画布 -->
        <div ref="graphContainer" class="graph-canvas"></div>

        <!-- 节点详情面板 -->
        <div v-if="selectedNode" class="node-detail-panel">
          <div class="panel-header">
            <span class="panel-title">{{ selectedNode.name }}</span>
            <el-button text :icon="Close" @click="closeNodeDetail" />
          </div>
          <div class="panel-content">
            <div class="node-property">
              <span class="property-label">类型:</span>
              <span class="property-value">{{ selectedNode.type }}</span>
            </div>
            <div class="node-property">
              <span class="property-label">ID:</span>
              <span class="property-value">{{ selectedNode.id }}</span>
            </div>
            <div class="node-property">
              <span class="property-label">描述:</span>
              <span class="property-value">{{ selectedNode.description || '暂无描述' }}</span>
            </div>
            <div class="node-actions">
              <el-button size="small" type="primary" @click="editNode">
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteNode">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧场景输入面板 -->
      <aside class="scenario-panel">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>💬 场景输入</span>
            </div>
          </template>
          
          <div class="scenario-input">
            <el-input
              v-model="scenarioText"
              type="textarea"
              :rows="4"
              placeholder="输入 P2P/O2C 等场景描述..."
            />
            <el-button type="primary" style="width: 100%; margin-top: 12px" @click="executeScenario">
              立即执行
            </el-button>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📝 推荐场景</span>
            </div>
          </template>
          
          <div class="scenario-list">
            <div
              v-for="(scenario, idx) in scenarios"
              :key="idx"
              class="scenario-item"
              @click="loadScenario(scenario)"
            >
              <div class="scenario-icon">{{ scenario.icon }}</div>
              <div class="scenario-content">
                <div class="scenario-title">{{ scenario.title }}</div>
                <div class="scenario-desc">{{ scenario.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📊 分析结果</span>
            </div>
          </template>
          
          <div class="result-list">
            <div
              v-for="(result, idx) in results"
              :key="idx"
              class="result-item"
            >
              <div class="result-icon">{{ result.icon }}</div>
              <div class="result-content">
                <div class="result-title">{{ result.title }}</div>
                <div class="result-desc">{{ result.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus, ZoomIn, ZoomOut, Refresh, Grid, FullScreen, Close } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

// 响应式数据
const searchQuery = ref('')
const ontologyExpanded = ref(true)
const selectedType = ref('')
const selectedFilters = ref([])
const scenarioText = ref('')
const selectedNode = ref(null)
const nodeCount = ref(672)
const edgeCount = ref(1149)

// 本体类型
const ontologyTypes = reactive([
  { name: 'Invoice', label: '发票', icon: '📄', count: 113 },
  { name: 'Payment', label: '付款', icon: '💰', count: 110 },
  { name: 'PurchaseOrder', label: '采购单', icon: '📋', count: 34 },
  { name: 'Supplier', label: '供应商', icon: '🏢', count: 52 },
  { name: 'Customer', label: '客户', icon: '👥', count: 12 },
  { name: 'SalesOrder', label: '销售单', icon: '🛒', count: 20 },
])

// 筛选器
const filters = reactive([
  { label: '高危预警', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '提示', value: 'info' },
  { label: '已处理', value: 'processed' },
])

// 推荐场景
const scenarios = reactive([
  { icon: '🔄', title: 'P2P 流程', desc: '采购到付款全流程分析', type: 'p2p' },
  { icon: '💵', title: 'O2C 流程', desc: '订单到收款全流程分析', type: 'o2c' },
  { icon: '📊', title: '财务分析', desc: '财务健康度评估', type: 'finance' },
  { icon: '⚠️', title: '风险预警', desc: '企业风险识别', type: 'risk' },
])

// 分析结果
const results = reactive([
  { icon: '✅', title: '流程完整', desc: 'P2P 流程节点完整率 95%' },
  { icon: '⚠️', title: '发现异常', desc: '3 个节点存在数据异常' },
  { icon: '📈', title: '效率提升', desc: '流程优化可提升 15% 效率' },
])

// 导航
function navigateTo(page: string) {
  if (page === 'alert') {
    router.push('/')
  } else if (page === 'query') {
    router.push('/smart-query')
  }
}

// 选择类型
function selectType(type: any) {
  selectedType.value = type.name
  // 过滤图谱显示
}

// 切换本体面板
function toggleOntology() {
  ontologyExpanded.value = !ontologyExpanded.value
}

// 重置筛选
function resetFilters() {
  selectedFilters.value = []
}

// 画布操作
function zoomIn() {
  // 放大图谱
}

function zoomOut() {
  // 缩小图谱
}

function resetView() {
  // 重置视图
}

function toggleGrid() {
  // 切换网格
}

function toggleFullscreen() {
  // 全屏
}

// 节点操作
function addNode() {
  // 添加节点
}

function editNode() {
  // 编辑节点
}

function deleteNode() {
  // 删除节点
}

function closeNodeDetail() {
  selectedNode.value = null
}

// 场景操作
function executeScenario() {
  // 执行场景分析
}

function loadScenario(scenario: any) {
  scenarioText.value = scenario.desc
}

onMounted(() => {
  // 初始化图谱
  initGraph()
})

function initGraph() {
  // 初始化 ECharts 图谱
}
</script>

<style scoped>
/* 容器 */
.graph-v2 {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部导航 */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.nav-left {
  display: flex;
  gap: 8px;
}

.nav-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #f0f0f0;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: #e0e0e0;
}

.nav-btn.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 8px;
}

.user-menu:hover {
  background: #f0f0f0;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 侧边面板 */
.ontology-panel,
.scenario-panel {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 本体列表 */
.ontology-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ontology-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.ontology-item:hover {
  background: #f5f5f5;
}

.ontology-item.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.ontology-icon {
  font-size: 20px;
}

.ontology-name {
  flex: 1;
  font-size: 14px;
}

.ontology-count {
  margin-left: auto;
}

/* 筛选列表 */
.filter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 画布区 */
.canvas-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: relative;
}

.canvas-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
}

.canvas-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

.graph-canvas {
  flex: 1;
  background: #fafafa;
}

/* 节点详情面板 */
.node-detail-panel {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.panel-content {
  padding: 16px;
}

.node-property {
  margin-bottom: 12px;
}

.property-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.property-value {
  font-size: 14px;
  color: #333;
}

.node-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

/* 场景输入 */
.scenario-input {
  display: flex;
  flex-direction: column;
}

/* 场景列表 */
.scenario-list,
.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-item,
.result-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-item:hover,
.result-item:hover {
  background: #f5f5f5;
}

.scenario-icon,
.result-icon {
  font-size: 24px;
}

.scenario-content,
.result-content {
  flex: 1;
  min-width: 0;
}

.scenario-title,
.result-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.scenario-desc,
.result-desc {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}
</style>
