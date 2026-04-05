<template>
  <div class="alert-center-v2">
    <!-- Top Navigation -->
    <header class="top-nav">
      <div class="nav-left">
        <button 
          class="nav-btn" 
          :class="{ active: currentPage === 'alert' }"
          @click="switchPage('alert')"
        >
          🚨 预警中心
        </button>
        <button 
          class="nav-btn" 
          :class="{ active: currentPage === 'query' }"
          @click="switchPage('query')"
        >
          💬 智能问数
        </button>
        <button 
          class="nav-btn" 
          :class="{ active: currentPage === 'graph' }"
          @click="switchPage('graph')"
        >
          🔍 知识图谱
        </button>
      </div>
      <div class="nav-right">
        <el-badge :value="alertCount" :max="99" class="notification-badge" v-if="currentPage === 'alert'">
          <el-button text :icon="Bell"></el-button>
        </el-badge>
        <el-dropdown trigger="click">
          <button class="user-menu">
            <el-avatar :size="24" src="https://picsum.photos/40/40"></el-avatar>
            <span>Admin</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>Profile</el-dropdown-item>
              <el-dropdown-item>Settings</el-dropdown-item>
              <el-dropdown-item divided>Logout</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- ==================== Alert Center Page ==================== -->
      <div v-show="currentPage === 'alert'" class="page-content alert-page">
        <!-- Statistics Cards -->
        <div class="stats-row">
          <el-card class="stat-card critical" shadow="hover" @click="showDetailModal('CRITICAL')">
            <div class="stat-icon">🔴</div>
            <div class="stat-content">
              <div class="stat-value">{{ statsData.by_severity.CRITICAL || 0 }}</div>
              <div class="stat-label">高危预警</div>
            </div>
            <div class="stat-trend down">↓ 12%</div>
          </el-card>

          <el-card class="stat-card warning" shadow="hover" @click="showDetailModal('HIGH')">
            <div class="stat-icon">🟠</div>
            <div class="stat-content">
              <div class="stat-value">{{ statsData.by_severity.HIGH || 0 }}</div>
              <div class="stat-label">警告预警</div>
            </div>
            <div class="stat-trend down">↓ 8%</div>
          </el-card>

          <el-card class="stat-card info" shadow="hover" @click="showDetailModal('MEDIUM')">
            <div class="stat-icon">🟡</div>
            <div class="stat-content">
              <div class="stat-value">{{ statsData.by_severity.MEDIUM || 0 }}</div>
              <div class="stat-label">提示预警</div>
            </div>
            <div class="stat-trend up">↑ 5%</div>
          </el-card>

          <el-card class="stat-card success" shadow="hover" @click="showDetailModal('LOW')">
            <div class="stat-icon">✅</div>
            <div class="stat-content">
              <div class="stat-value">{{ statsData.resolved || 0 }}</div>
              <div class="stat-label">已处理</div>
            </div>
            <div class="stat-trend up">↑ 23%</div>
          </el-card>
        </div>

        <!-- Alert List -->
        <el-card class="risk-card" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="card-title">
                <span class="title-icon">⚠️</span>
                <span>风险预警列表</span>
              </div>
              <div class="card-actions">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索预警..."
                  prefix-icon="Search"
                  style="width: 200px"
                />
              </div>
            </div>
          </template>

          <div class="alert-list">
            <div 
              v-for="alert in filteredAlerts" 
              :key="alert.alert_id"
              class="alert-item"
              :class="`priority-${alert.severity.toLowerCase()}`"
            >
              <div class="alert-icon">{{ getSeverityIcon(alert.severity) }}</div>
              <div class="alert-content">
                <div class="alert-header">
                  <el-tag :type="getSeverityTagType(alert.severity)" size="small" effect="dark">
                    {{ alert.severity }}
                  </el-tag>
                  <span class="alert-type">{{ formatAlertType(alert.alert_type) }}</span>
                  <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
                </div>
                <div class="alert-description">{{ alert.description }}</div>
                <div class="alert-recommendation">💡 {{ alert.recommendation }}</div>
              </div>
              <div class="alert-actions">
                <el-button size="small" type="primary" @click="viewDetail(alert)">查看</el-button>
                <el-button size="small" type="success" @click="confirmAlert(alert)">确认</el-button>
              </div>
            </div>

            <el-empty v-if="filteredAlerts.length === 0" description="暂无预警数据" />
          </div>
        </el-card>
      </div>

      <!-- ==================== Smart Query Page ==================== -->
      <div v-show="currentPage === 'query'" class="page-content query-page">
        <div class="query-container">
          <h2>💬 智能问数</h2>
          <p class="query-subtitle">通过自然语言查询企业数据</p>
          
          <div class="query-input-wrapper">
            <el-input
              v-model="queryInput"
              type="textarea"
              :rows="3"
              placeholder="请输入您的问题，例如：本周销售情况如何？"
              @keyup.enter.ctrl="sendQuery"
            />
            <el-button 
              type="primary" 
              size="large" 
              :loading="queryLoading"
              @click="sendQuery"
              class="query-btn"
            >
              {{ queryLoading ? '思考中...' : '立即查询' }}
            </el-button>
          </div>

          <div class="suggested-questions" v-if="suggestedQuestions.length > 0">
            <h4>推荐问题</h4>
            <div class="question-tags">
              <el-tag
                v-for="(q, index) in suggestedQuestions"
                :key="index"
                size="large"
                round
                effect="plain"
                @click="useSuggestedQuestion(q)"
              >
                {{ q }}
              </el-tag>
            </div>
          </div>

          <div class="query-history" v-if="queryHistory.length > 0">
            <h4>查询历史</h4>
            <div class="history-list">
              <div 
                v-for="(item, index) in queryHistory" 
                :key="index"
                class="history-item"
                @click="useSuggestedQuestion(item.query)"
              >
                <span class="history-query">{{ item.query }}</span>
                <span class="history-time">{{ item.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================== Knowledge Graph Page ==================== -->
      <div v-show="currentPage === 'graph'" class="page-content graph-page">
        <div class="graph-container">
          <div class="graph-toolbar">
            <el-button-group>
              <el-button :icon="Refresh" @click="loadGraphData">刷新</el-button>
              <el-button :icon="ZoomIn" @click="zoomIn">放大</el-button>
              <el-button :icon="ZoomOut" @click="zoomOut">缩小</el-button>
            </el-button-group>
            <span class="graph-title">🔍 知识图谱</span>
          </div>

          <div class="graph-content">
            <div class="graph-stats">
              <el-statistic title="节点数" :value="graphStats.nodes" />
              <el-statistic title="关系数" :value="graphStats.relationships" />
              <el-statistic title="事件数" :value="graphStats.events" />
            </div>

            <div class="graph-visualization">
              <div v-if="graphLoading" class="graph-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
              <div v-else class="graph-placeholder">
                <el-empty description="知识图谱可视化区域 (集成 D3.js/ECharts)" />
              </div>
            </div>

            <div class="graph-nodes-list">
              <h4>节点列表</h4>
              <el-table :data="graphNodes" size="small" max-height="300">
                <el-table-column prop="name" label="名称" />
                <el-table-column prop="type" label="类型" width="100" />
              </el-table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <el-dialog
      v-model="detailModalVisible"
      :title="modalTitle"
      width="1000px"
      destroy-on-close
    >
      <el-table
        :data="filteredDetailAlerts"
        stripe
        border
        max-height="500"
      >
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="alert_type" label="类型" width="180">
          <template #default="{ row }">
            <el-tag :type="getSeverityTagType(row.severity)" size="small">
              {{ formatAlertType(row.alert_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityTagType(row.severity)" size="small" effect="dark">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="recommendation" label="建议" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="发现时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewDetail(row)">查看</el-button>
            <el-button size="small" type="success" @click="confirmAlert(row)">确认</el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailModalVisible = false">关闭</el-button>
          <el-button type="primary" @click="exportDetail">导出明细</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, Search, Refresh, ZoomIn, ZoomOut, Loading } from '@element-plus/icons-vue'

// Page state
const currentPage = ref('alert')

// Switch page
function switchPage(page) {
  currentPage.value = page
  console.log('Switch to page:', page)
  
  if (page === 'query') {
    loadSuggestedQuestions()
  } else if (page === 'graph') {
    loadGraphData()
  }
}

// ==================== Alert Center Data ====================
const statsData = ref({
  total: 0,
  by_severity: {
    CRITICAL: 0,
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0
  },
  resolved: 0
})

const alerts = ref([])
const searchQuery = ref('')

// Load alert stats
async function loadAlertStats() {
  try {
    const res = await fetch('http://localhost:8005/api/v1/alerts/stats')
    const data = await res.json()
    statsData.value = data
  } catch (error) {
    console.error('Failed to load alert stats:', error)
    // Fallback to mock data
    statsData.value = {
      total: 3,
      by_severity: { CRITICAL: 2, HIGH: 1, MEDIUM: 0, LOW: 0 },
      resolved: 0
    }
  }
}

// Load alerts
async function loadAlerts() {
  try {
    const res = await fetch('http://localhost:8005/api/v1/alerts')
    const data = await res.json()
    alerts.value = data
  } catch (error) {
    console.error('Failed to load alerts:', error)
    // Fallback to mock data
    alerts.value = [
      {
        alert_id: 'risk_001',
        alert_type: 'INVENTORY_LOW',
        severity: 'CRITICAL',
        description: '库存低于安全线：当前 -100 个，安全库存 100 个',
        recommendation: '立即补货 200 件，联系供应商确认交货时间',
        created_at: '2026-04-05T19:00:00'
      },
      {
        alert_id: 'risk_002',
        alert_type: 'PURCHASE_PRICE_ABNORMAL',
        severity: 'HIGH',
        description: '采购价格异常：单价 $190,000.00，超出正常范围 200%',
        recommendation: '核实价格，确认是否为英伟达 H100 芯片的市场价格',
        created_at: '2026-04-05T19:05:00'
      },
      {
        alert_id: 'risk_003',
        alert_type: 'HUGE_PAYMENT',
        severity: 'CRITICAL',
        description: '异常大额付款：金额 $150,000,000.00，超出正常阈值 100 倍',
        recommendation: '立即人工审核，确认付款真实性，防止欺诈',
        created_at: '2026-04-05T19:10:00'
      }
    ]
  }
}

// Filtered alerts
const filteredAlerts = computed(() => {
  if (!searchQuery.value) return alerts.value
  const query = searchQuery.value.toLowerCase()
  return alerts.value.filter(alert =>
    alert.description.toLowerCase().includes(query) ||
    alert.alert_type.toLowerCase().includes(query)
  )
})

// Alert count badge
const alertCount = computed(() => {
  return (statsData.value.by_severity.CRITICAL || 0) + 
         (statsData.value.by_severity.HIGH || 0)
})

// ==================== Detail Modal ====================
const detailModalVisible = ref(false)
const currentFilterSeverity = ref('')
const modalTitle = ref('')

// Show detail modal
function showDetailModal(severity) {
  currentFilterSeverity.value = severity
  
  const severityInfo = {
    'CRITICAL': '🔴 高危预警明细',
    'HIGH': '🟠 警告明细',
    'MEDIUM': '🟡 提示明细',
    'LOW': '✅ 已处理明细'
  }
  
  modalTitle.value = severityInfo[severity] || '预警明细'
  detailModalVisible.value = true
  
  ElMessage.success(`显示 ${severity} 级别预警明细`)
}

// Filtered detail alerts
const filteredDetailAlerts = computed(() => {
  if (!detailModalVisible.value || !currentFilterSeverity.value) return []
  
  const severity = currentFilterSeverity.value
  
  // For LOW (resolved), filter by status
  if (severity === 'LOW') {
    return alerts.value.filter(alert => alert.status !== 'pending')
  }
  
  // For others, filter by severity
  return alerts.value.filter(alert => alert.severity === severity)
})

// Export detail
function exportDetail() {
  ElMessage.success(`已导出 ${filteredDetailAlerts.value.length} 条预警明细`)
}

// View detail
function viewDetail(alert) {
  ElMessage.info(`查看预警详情：${alert.alert_type}`)
}

// Confirm alert
function confirmAlert(alert) {
  ElMessage.success(`已确认预警：${alert.alert_type}`)
}

// Get severity icon
function getSeverityIcon(severity) {
  const icons = {
    'CRITICAL': '🔴',
    'HIGH': '🟠',
    'MEDIUM': '🟡',
    'LOW': '🟢'
  }
  return icons[severity] || '⚪'
}

// Get severity tag type
function getSeverityTagType(severity) {
  const types = {
    'CRITICAL': 'danger',
    'HIGH': 'warning',
    'MEDIUM': 'info',
    'LOW': 'success'
  }
  return types[severity] || 'info'
}

// Format alert type
function formatAlertType(type) {
  const mapping = {
    'INVENTORY_LOW': '库存预警',
    'PURCHASE_PRICE_ABNORMAL': '采购价异常',
    'HUGE_PAYMENT': '大额付款',
    'FINANCIAL_RISK': '财务风险'
  }
  return mapping[type] || type
}

// Format time
function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ==================== Smart Query Data ====================
const queryInput = ref('')
const queryLoading = ref(false)
const queryHistory = ref([])
const suggestedQuestions = ref([])

// Load suggested questions
async function loadSuggestedQuestions() {
  if (suggestedQuestions.value.length > 0) return
  
  try {
    const res = await fetch('http://localhost:8005/api/v1/smart-query/suggested-questions')
    const data = await res.json()
    suggestedQuestions.value = data.questions || []
  } catch (error) {
    console.error('Failed to load suggested questions:', error)
    suggestedQuestions.value = [
      '本周销售情况如何？',
      'Top 10 客户有哪些？',
      '库存预警商品有哪些？',
      '本月回款情况如何？'
    ]
  }
}

// Send query
async function sendQuery() {
  if (!queryInput.value.trim()) return
  
  queryLoading.value = true
  
  try {
    // Mock response
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    queryHistory.value.unshift({
      query: queryInput.value,
      time: new Date().toLocaleTimeString()
    })
    
    ElMessage.success('查询完成')
  } catch (error) {
    console.error('Query failed:', error)
    ElMessage.error('查询失败')
  } finally {
    queryLoading.value = false
  }
}

// Use suggested question
function useSuggestedQuestion(question) {
  queryInput.value = question
  sendQuery()
}

// ==================== Knowledge Graph Data ====================
const graphLoading = ref(false)
const graphData = ref(null)
const graphStats = ref({
  nodes: 0,
  relationships: 0,
  events: 0
})
const graphNodes = ref([])

// Load graph data
async function loadGraphData() {
  graphLoading.value = true
  
  try {
    // Mock data
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    graphStats.value = {
      nodes: 156,
      relationships: 423,
      events: 89
    }
    
    graphNodes.value = [
      { name: '客户 A', type: '客户' },
      { name: '订单 001', type: '订单' },
      { name: '产品 X', type: '产品' }
    ]
    
    ElMessage.success('图谱数据加载完成')
  } catch (error) {
    console.error('Failed to load graph data:', error)
    ElMessage.error('图谱加载失败')
  } finally {
    graphLoading.value = false
  }
}

// Zoom controls
function zoomIn() {
  ElMessage.info('放大图谱')
}

function zoomOut() {
  ElMessage.info('缩小图谱')
}

// ==================== Lifecycle ====================
onMounted(() => {
  loadAlertStats()
  loadAlerts()
})
</script>

<style scoped>
.alert-center-v2 {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Top Navigation */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  flex-shrink: 0;
}

.nav-left {
  display: flex;
  gap: 12px;
}

.nav-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  background: #f0f0f0;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.nav-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.nav-btn:hover {
  transform: translateY(-2px);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
}

/* Main Content */
.main-content {
  flex: 1;
  overflow: hidden;
  padding: 24px;
}

.page-content {
  height: 100%;
  overflow-y: auto;
}

/* Statistics Cards */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  padding: 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-card.critical {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
}

.stat-card.warning {
  background: linear-gradient(135deg, #ffa502 0%, #ff7f50 100%);
  color: white;
}

.stat-card.info {
  background: linear-gradient(135deg, #ffd700 0%, #ffec8b 100%);
  color: #333;
}

.stat-card.success {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  color: white;
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.stat-trend {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 12px;
  font-weight: bold;
}

.stat-trend.up {
  color: rgba(255, 255, 255, 0.9);
}

.stat-trend.down {
  color: rgba(255, 255, 255, 0.9);
}

/* Alert List */
.risk-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
  background: #fafafa;
  transition: all 0.3s;
}

.alert-item:hover {
  background: #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.alert-item.priority-critical {
  border-left-color: #ff6b6b;
}

.alert-item.priority-high {
  border-left-color: #ffa502;
}

.alert-item.priority-medium {
  border-left-color: #ffd700;
}

.alert-item.priority-low {
  border-left-color: #52c41a;
}

.alert-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.alert-type {
  font-weight: bold;
  color: #333;
}

.alert-time {
  color: #999;
  font-size: 12px;
}

.alert-description {
  color: #333;
  margin-bottom: 8px;
  line-height: 1.5;
}

.alert-recommendation {
  color: #666;
  font-size: 13px;
  line-height: 1.4;
}

.alert-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

/* Query Page */
.query-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  color: white;
}

.query-subtitle {
  margin-bottom: 32px;
  opacity: 0.9;
}

.query-input-wrapper {
  margin-bottom: 32px;
}

.query-btn {
  margin-top: 16px;
  width: 100%;
}

.suggested-questions,
.query-history {
  background: rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 12px;
  margin-top: 24px;
  text-align: left;
}

.question-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.2);
}

.history-query {
  flex: 1;
}

.history-time {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

/* Graph Page */
.graph-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.graph-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.graph-title {
  font-size: 18px;
  font-weight: bold;
}

.graph-content {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr 300px;
  gap: 16px;
  padding: 24px;
}

.graph-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.graph-visualization {
  background: #f5f5f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.graph-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #666;
}

.graph-nodes-list {
  overflow-y: auto;
}

/* Dialog Footer */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .graph-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .nav-left {
    gap: 8px;
  }
  
  .nav-btn {
    padding: 8px 12px;
    font-size: 12px;
  }
}
</style>
