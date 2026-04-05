<template>
  <div class="alert-center-page">
    <!-- 顶部导航栏 - 毛玻璃效果 -->
    <nav class="top-navigation">
      <div class="nav-content">
        <div class="nav-brand">🚨 预警中心</div>
        <div class="nav-buttons">
          <el-button type="danger" size="small" round disabled class="nav-btn active">
            🚨 预警中心
          </el-button>
          <el-button type="primary" size="small" round @click="$emit('close')" class="nav-btn">
            💬 智能问数
          </el-button>
          <el-button type="info" size="small" round @click="$emit('close')" class="nav-btn">
            🔍 返回图谱
          </el-button>
        </div>
      </div>
    </nav>

    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <h1 class="page-title">🚨 企业预警中心</h1>
        <p class="page-subtitle">实时监控业务风险，智能决策支持</p>
      </div>
    </header>

    <!-- 统计卡片 -->
    <section class="stats-section">
      <div class="stats-grid">
        <!-- 高危预警 -->
        <div class="stats-card critical-card" style="animation-delay: 0.1s" @click="showDetailModal('CRITICAL')">
          <div class="card-shimmer"></div>
          <div class="card-content">
            <div class="stat-icon">🔴</div>
            <div class="stat-value">{{ stats.critical }}</div>
            <div class="stat-label">高危预警</div>
          </div>
        </div>

        <!-- 警告预警 -->
        <div class="stats-card warning-card" style="animation-delay: 0.2s" @click="showDetailModal('HIGH')">
          <div class="card-shimmer"></div>
          <div class="card-content">
            <div class="stat-icon">🟠</div>
            <div class="stat-value">{{ stats.warning }}</div>
            <div class="stat-label">警告预警</div>
          </div>
        </div>

        <!-- 提示预警 -->
        <div class="stats-card info-card" style="animation-delay: 0.3s" @click="showDetailModal('MEDIUM')">
          <div class="card-shimmer"></div>
          <div class="card-content">
            <div class="stat-icon">🟡</div>
            <div class="stat-value">{{ stats.info }}</div>
            <div class="stat-label">提示预警</div>
          </div>
        </div>

        <!-- 已处理 -->
        <div class="stats-card success-card" style="animation-delay: 0.4s" @click="showDetailModal('LOW')">
          <div class="card-shimmer"></div>
          <div class="card-content">
            <div class="stat-icon">✅</div>
            <div class="stat-value">{{ stats.resolved }}</div>
            <div class="stat-label">已处理</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 财务风险专项 -->
    <section class="financial-section">
      <div class="section-card">
        <div class="section-header">
          <span class="section-icon">💰</span>
          <h2 class="section-title">财务风险专项</h2>
        </div>

        <div class="financial-content">
          <!-- 健康度评分 -->
          <div class="health-score-container">
            <svg class="score-circle" width="200" height="200" viewBox="0 0 200 200">
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                </linearGradient>
              </defs>
              <!-- 背景圆环 -->
              <circle
                cx="100"
                cy="100"
                r="80"
                fill="none"
                stroke="#e0e0e0"
                stroke-width="12"
              />
              <!-- 进度圆环 -->
              <circle
                cx="100"
                cy="100"
                r="80"
                fill="none"
                stroke="url(#scoreGradient)"
                stroke-width="12"
                stroke-linecap="round"
                :stroke-dasharray="502"
                :stroke-dashoffset="502 - (502 * healthScore) / 100"
                class="score-progress"
              />
            </svg>
            <div class="score-value">
              {{ healthScore }}
              <span class="score-total">/100</span>
            </div>
            <div class="score-label">{{ scoreStatus }}</div>
          </div>

          <!-- 财务指标 -->
          <div class="financial-indicators">
            <div class="indicator-card" v-if="indicators.lowCurrentRatio">
              <div class="indicator-icon">⚠️</div>
              <div class="indicator-content">
                <div class="indicator-title">流动比率</div>
                <div class="indicator-value">0.8</div>
                <div class="indicator-desc">低于 1.0 警戒线</div>
              </div>
            </div>

            <div class="indicator-card" v-if="indicators.highDebtToEquity">
              <div class="indicator-icon">⚠️</div>
              <div class="indicator-content">
                <div class="indicator-title">负债权益比</div>
                <div class="indicator-value">2.5</div>
                <div class="indicator-desc">高于 2.0 警戒线</div>
              </div>
            </div>

            <div class="indicator-card" v-if="indicators.lowROE">
              <div class="indicator-icon">📉</div>
              <div class="indicator-content">
                <div class="indicator-title">ROE</div>
                <div class="indicator-value">3%</div>
                <div class="indicator-desc">低于 5% 标准</div>
              </div>
            </div>

            <div class="indicator-card critical" v-if="indicators.lowCashFlow">
              <div class="indicator-icon">🔴</div>
              <div class="indicator-content">
                <div class="indicator-title">现金流</div>
                <div class="indicator-value">¥50 万</div>
                <div class="indicator-desc">低于安全线¥100 万</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 预警列表 -->
    <section class="alert-list-section">
      <div class="section-card">
        <div class="section-header">
          <span class="section-icon">⚠️</span>
          <h2 class="section-title">预警列表</h2>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索预警..."
              size="small"
              class="search-input"
              clearable
            >
              <template #prefix>
                <span>🔍</span>
              </template>
            </el-input>
          </div>
        </div>

        <div class="alert-list">
          <div
            v-for="alert in filteredAlerts"
            :key="alert.id"
            class="alert-item"
            :class="alert.levelClass"
          >
            <div class="alert-icon">{{ alert.icon }}</div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-description">{{ alert.description }}</div>
              <div class="alert-meta">
                <span class="alert-assignee">👤 {{ alert.assignee }}</span>
                <span class="alert-time">⏰ {{ alert.timeAgo }}</span>
              </div>
            </div>
            <div class="alert-actions">
              <el-button size="small" type="primary" @click="handleAssign(alert)">
                分配
              </el-button>
              <el-button size="small" type="success" @click="handleResolve(alert)">
                处理
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 明细对话框 -->
    <el-dialog
      v-model="detailModalVisible"
      :title="modalTitle"
      width="900px"
      destroy-on-close
    >
      <el-table
        :data="filteredAlerts"
        stripe
        border
        max-height="500"
      >
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="alert_type" label="类型" width="180">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'CRITICAL' ? 'danger' : row.severity === 'HIGH' ? 'warning' : 'info'" size="small">
              {{ row.alert_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'CRITICAL' ? 'danger' : row.severity === 'HIGH' ? 'warning' : 'info'" size="small" effect="dark">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="发现时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleViewDetail(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailModalVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleExport">导出明细</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 统计数据
const stats = ref({
  critical: 12,
  warning: 28,
  info: 56,
  resolved: 342,
  financial: 5
})

// 明细对话框
const detailModalVisible = ref(false)
const currentFilterSeverity = ref('')
const modalTitle = ref('')
const modalTagType = ref('danger')

// 显示明细对话框
function showDetailModal(severity) {
  currentFilterSeverity.value = severity
  
  const severityInfo = {
    'CRITICAL': { title: '🔴 高危预警明细', tagType: 'danger' },
    'HIGH': { title: '🟠 警告明细', tagType: 'warning' },
    'MEDIUM': { title: '🟡 提示明细', tagType: 'info' },
    'LOW': { title: '✅ 已处理明细', tagType: 'success' }
  }
  
  const info = severityInfo[severity] || severityInfo['CRITICAL']
  modalTitle.value = info.title
  modalTagType.value = info.tagType
  
  detailModalVisible.value = true
  
  ElMessage.success(`显示 ${severity} 级别预警明细`)
}

// 财务健康度
const healthScore = ref(65)
const indicators = ref({
  lowCurrentRatio: true,
  highDebtToEquity: true,
  lowROE: true,
  lowCashFlow: true
})

// 搜索查询
const searchQuery = ref('')

// 预警数据 (模拟数据)
const alerts = ref([
  {
    id: 1,
    level: 'critical',
    levelText: '高危',
    icon: '🔴',
    title: '现金流不足',
    description: '当前：¥50 万 | 安全线：¥100 万',
    assignee: '王五 (CFO)',
    timeAgo: '刚刚',
    levelClass: 'critical'
  },
  {
    id: 2,
    level: 'warning',
    levelText: '警告',
    icon: '🟠',
    title: '应收账款逾期 - A 公司',
    description: '逾期金额：¥120 万 | 逾期天数：45 天',
    assignee: '李四 (客户经理)',
    timeAgo: '2 小时前',
    levelClass: 'warning'
  },
  {
    id: 3,
    level: 'warning',
    levelText: '警告',
    icon: '🟠',
    title: '预算偏差超标 - 市场部',
    description: '预算：¥100 万 | 实际：¥130 万 | 偏差：30%',
    assignee: '赵六 (市场总监)',
    timeAgo: '5 小时前',
    levelClass: 'warning'
  },
  {
    id: 4,
    level: 'info',
    levelText: '提示',
    icon: '🟡',
    title: '库存预警 - iPhone 15 Pro',
    description: '当前库存：50 | 安全库存：100',
    assignee: '张三 (库存管理员)',
    timeAgo: '昨天',
    levelClass: 'info'
  },
  {
    id: 5,
    level: 'critical',
    levelText: '高危',
    icon: '🔴',
    title: '供应商风险 - 核心芯片断供',
    description: '主要供应商产能下降 60%',
    assignee: '采购部',
    timeAgo: '2 天前',
    levelClass: 'critical'
  },
  {
    id: 6,
    level: 'info',
    levelText: '提示',
    icon: '🟡',
    title: '合同到期提醒 - 办公场地',
    description: '租赁合同 30 天后到期',
    assignee: '行政部',
    timeAgo: '3 天前',
    levelClass: 'info'
  }
])

// 计算属性
const scoreClass = computed(() => {
  if (healthScore.value >= 80) return 'good'
  if (healthScore.value >= 60) return 'warning'
  return 'danger'
})

const scoreStatus = computed(() => {
  if (healthScore.value >= 80) return '良好'
  if (healthScore.value >= 60) return '需关注'
  return '风险'
})

const filteredAlerts = computed(() => {
  // 如果是明细对话框，按严重程度筛选
  if (detailModalVisible.value && currentFilterSeverity.value) {
    const severityMap = {
      'CRITICAL': 'critical',
      'HIGH': 'critical',
      'MEDIUM': 'info',
      'LOW': 'info'
    }
    const targetLevel = severityMap[currentFilterSeverity.value]
    return alerts.value.filter(alert => alert.levelClass === targetLevel)
  }
  
  // 否则按搜索查询筛选
  if (!searchQuery.value) return alerts.value
  const query = searchQuery.value.toLowerCase()
  return alerts.value.filter(alert =>
    alert.title.toLowerCase().includes(query) ||
    alert.description.toLowerCase().includes(query) ||
    alert.assignee.toLowerCase().includes(query)
  )
})

// 查看明细
function handleViewDetail(alert) {
  ElMessage.info(`查看预警详情：${alert.title}`)
}

// 导出明细
function handleExport() {
  ElMessage.success(`已导出 ${filteredAlerts.value.length} 条预警明细`)
}

// 方法
const handleAssign = (alert) => {
  console.log('分配预警:', alert)
  ElMessage.success(`已分配预警：${alert.title}`)
}

const handleResolve = (alert) => {
  console.log('处理预警:', alert)
  ElMessage.success(`已处理预警：${alert.title}`)
}

// 挂载时加载数据
onMounted(() => {
  console.log('✅ 预警中心已加载 (UI-UX-Pro-Max 版本)')
})
</script>

<style scoped>
/* ==================== CSS 变量主题 ==================== */
:root {
  --critical-bg: linear-gradient(135deg, #ff0844 0%, #ffb199 100%);
  --warning-bg: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
  --info-bg: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --success-bg: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  --finance-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* ==================== 页面容器 ==================== */
.alert-center-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding-top: 80px;
}

/* ==================== 顶部导航栏 ==================== */
.top-navigation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  z-index: 1000;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.nav-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 30px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-buttons {
  display: flex;
  gap: 12px;
}

.nav-btn {
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-btn.active {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(255, 8, 68, 0.3);
}

/* ==================== 页面头部 ==================== */
.page-header {
  text-align: center;
  padding: 40px 20px 30px;
}

.header-content {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 42px;
  font-weight: 800;
  margin: 0 0 12px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px;
}

.page-subtitle {
  font-size: 18px;
  color: #666;
  margin: 0;
  font-weight: 400;
}

/* ==================== 统计卡片区域 ==================== */
.stats-section {
  max-width: 1400px;
  margin: 0 auto 30px;
  padding: 0 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

/* ==================== 统计卡片设计 ==================== */
.stats-card {
  border-radius: 20px;
  padding: 28px;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(30px);
}

.stats-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
  animation: shimmer 3s infinite;
}

.stats-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.critical-card {
  background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%);
}

.warning-card {
  background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
}

.info-card {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.success-card {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.card-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.stat-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.9;
}

.stat-value {
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 8px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.stat-label {
  font-size: 15px;
  opacity: 0.95;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-weight: 600;
}

/* ==================== 财务风险专项 ==================== */
.financial-section {
  max-width: 1400px;
  margin: 0 auto 30px;
  padding: 0 30px;
}

.section-card {
  background: white;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  animation: fadeInUp 0.8s ease-out 0.3s forwards;
  opacity: 0;
  transform: translateY(30px);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f0f0f0;
}

.section-icon {
  font-size: 32px;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.search-input {
  width: 280px;
}

.financial-content {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 40px;
  align-items: center;
}

/* ==================== 健康度评分圆环 ==================== */
.health-score-container {
  position: relative;
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-circle {
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
}

.score-progress {
  transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
  animation: progressFill 1.5s ease-out 0.5s forwards;
}

.score-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-total {
  font-size: 16px;
  font-weight: 500;
  margin-top: -8px;
}

.score-label {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 16px;
  color: #666;
  font-weight: 600;
}

/* ==================== 财务指标卡片 ==================== */
.financial-indicators {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.indicator-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 16px;
  border-left: 4px solid #ffc107;
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
  transform: translateX(20px);
}

.indicator-card:nth-child(1) { animation-delay: 0.5s; }
.indicator-card:nth-child(2) { animation-delay: 0.6s; }
.indicator-card:nth-child(3) { animation-delay: 0.7s; }
.indicator-card:nth-child(4) { animation-delay: 0.8s; }

.indicator-card:hover {
  transform: translateX(8px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.indicator-card.critical {
  border-left-color: #ff0844;
  background: linear-gradient(135deg, rgba(255, 8, 68, 0.08) 0%, rgba(255, 177, 153, 0.08) 100%);
}

.indicator-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.indicator-content {
  flex: 1;
}

.indicator-title {
  font-size: 13px;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.indicator-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  line-height: 1;
  margin-bottom: 4px;
}

.indicator-desc {
  font-size: 12px;
  color: #999;
}

/* ==================== 预警列表 ==================== */
.alert-list-section {
  max-width: 1400px;
  margin: 0 auto 40px;
  padding: 0 30px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border-left: 5px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
  transform: translateX(-20px);
}

.alert-item:nth-child(1) { animation-delay: 0.6s; }
.alert-item:nth-child(2) { animation-delay: 0.65s; }
.alert-item:nth-child(3) { animation-delay: 0.7s; }
.alert-item:nth-child(4) { animation-delay: 0.75s; }
.alert-item:nth-child(5) { animation-delay: 0.8s; }
.alert-item:nth-child(6) { animation-delay: 0.85s; }

.alert-item:hover {
  transform: translateX(8px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
}

.alert-item.critical {
  border-left-color: #ff0844;
  background: linear-gradient(to right, rgba(255, 8, 68, 0.05), transparent);
}

.alert-item.warning {
  border-left-color: #f5576c;
}

.alert-item.info {
  border-left-color: #4facfe;
}

.alert-icon {
  font-size: 32px;
  margin-right: 20px;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: 17px;
  font-weight: 700;
  color: #333;
  margin-bottom: 6px;
}

.alert-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.5;
}

.alert-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #999;
}

.alert-assignee,
.alert-time {
  display: flex;
  align-items: center;
  gap: 6px;
}

.alert-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  margin-left: 20px;
}

/* ==================== 动画效果 ==================== */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes progressFill {
  from {
    stroke-dashoffset: 502;
  }
}

/* ==================== 响应式布局 ==================== */
@media (max-width: 1200px) {
  .financial-content {
    grid-template-columns: 1fr;
    gap: 30px;
  }

  .health-score-container {
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 32px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .stat-value {
    font-size: 40px;
  }

  .nav-content {
    padding: 0 16px;
  }

  .nav-brand {
    font-size: 20px;
  }

  .nav-buttons {
    gap: 8px;
  }

  .section-card {
    padding: 20px;
  }

  .alert-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .alert-actions {
    width: 100%;
    margin-left: 0;
  }

  .alert-actions .el-button {
    flex: 1;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .financial-indicators {
    grid-template-columns: 1fr;
  }

  .search-input {
    width: 100%;
  }
}
</style>
