<template>
  <div class="financial-risk-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1>💰 财务风险预警</h1>
        <p class="subtitle">实时监控企业财务健康度，主动预警潜在风险</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <!-- 财务健康度评分卡片 -->
    <el-card class="health-score-card" shadow="hover">
      <div class="health-score-content">
        <div class="score-left">
          <div class="score-title">💰 财务健康度评分</div>
          <div class="score-gauge">
            <el-progress
              type="dashboard"
              :percentage="healthScore.overall_score"
              :color="getScoreColor(healthScore.overall_score)"
              :format="formatScore"
            />
          </div>
          <div class="score-level" :class="getLevelClass(healthScore.level)">
            {{ getLevelText(healthScore.level) }}
          </div>
        </div>
        <div class="score-right">
          <div class="dimension-list">
            <div 
              v-for="(score, dim) in healthScore.dimension_scores" 
              :key="dim"
              class="dimension-item"
            >
              <span class="dimension-name">{{ getDimensionName(dim) }}</span>
              <el-progress
                :percentage="score"
                :status="score >= 60 ? 'success' : 'exception'"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="dimension-value">{{ score }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card critical" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon">🔴</div>
            <div class="stat-info">
              <div class="stat-value">{{ riskSummary.critical_count }}</div>
              <div class="stat-label">高危风险</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon">🟠</div>
            <div class="stat-info">
              <div class="stat-value">{{ riskSummary.warning_count }}</div>
              <div class="stat-label">警告风险</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card info" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon">🟡</div>
            <div class="stat-info">
              <div class="stat-value">{{ riskSummary.info_count }}</div>
              <div class="stat-label">提示风险</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card total" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <div class="stat-value">{{ riskSummary.total_risks }}</div>
              <div class="stat-label">总风险数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险分类统计 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📋 风险分类统计</span>
            </div>
          </template>
          <div class="chart-container">
            <div ref="riskTypeChart" class="chart"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📈 风险趋势</span>
            </div>
          </template>
          <div class="chart-container">
            <div ref="riskTrendChart" class="chart"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险列表 -->
    <el-card class="risk-list-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>⚠️ 风险列表</span>
          <el-tabs v-model="riskFilter" @change="filterRisks" size="small">
            <el-tab-pane label="全部" name="all" />
            <el-tab-pane label="高危" name="CRITICAL" />
            <el-tab-pane label="警告" name="WARNING" />
            <el-tab-pane label="提示" name="INFO" />
          </el-tabs>
        </div>
      </template>

      <el-table :data="filteredRisks" style="width: 100%" :header-cell-style="{background: '#f5f7fa'}">
        <el-table-column prop="severity" label="等级" width="80">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityText(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <span class="risk-type-icon">{{ getRiskTypeIcon(row.type) }}</span>
            {{ getRiskTypeName(row.type) }}
          </template>
        </el-table-column>
        <el-table-column prop="title" label="风险描述" min-width="250">
          <template #default="{ row }">
            <div class="risk-title">{{ row.title }}</div>
            <div class="risk-detail">{{ row.detail }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="风险评分" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.risk_score"
              :status="row.risk_score >= 70 ? 'exception' : 'warning'"
              :stroke-width="10"
            />
          </template>
        </el-table-column>
        <el-table-column prop="assigned_to" label="负责人" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.assigned_to" size="small">{{ row.assigned_to }}</el-tag>
            <span v-else class="unassigned">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleRisk(row)">
              处理
            </el-button>
            <el-button size="small" @click="viewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 风险详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="风险详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedRisk" class="risk-detail-dialog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="风险 ID">{{ selectedRisk.id }}</el-descriptions-item>
          <el-descriptions-item label="风险类型">{{ getRiskTypeName(selectedRisk.type) }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityType(selectedRisk.severity)">
              {{ getSeverityText(selectedRisk.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险评分">{{ selectedRisk.risk_score }}</el-descriptions-item>
          <el-descriptions-item label="发现时间">{{ selectedRisk.detected_at }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedRisk.status)">
              {{ getStatusText(selectedRisk.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人" :span="2">
            {{ selectedRisk.assigned_to || '未分配' }}
          </el-descriptions-item>
          <el-descriptions-item label="风险描述" :span="2">
            {{ selectedRisk.detail }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 风险传播分析 -->
        <div class="propagation-section" v-if="selectedRisk.propagation">
          <h4>🔗 风险传播路径</h4>
          <ul>
            <li v-for="(path, idx) in selectedRisk.propagation.paths" :key="idx">
              {{ path }}
            </li>
          </ul>
        </div>

        <!-- 处理建议 -->
        <div class="recommendation-section">
          <h4>💡 处理建议</h4>
          <el-alert
            v-for="(rec, idx) in selectedRisk.recommendations"
            :key="idx"
            :title="rec"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 10px"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="assignRisk">分配处理</el-button>
      </template>
    </el-dialog>

    <!-- 处理对话框 -->
    <el-dialog
      v-model="handleDialogVisible"
      title="处理风险"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="handleForm" label-width="100px">
        <el-form-item label="处理状态">
          <el-select v-model="handleForm.status" placeholder="请选择状态">
            <el-option label="待处理" value="OPEN" />
            <el-option label="处理中" value="IN_PROGRESS" />
            <el-option label="待验证" value="PENDING_REVIEW" />
            <el-option label="已闭环" value="RESOLVED" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="handleForm.assigned_to" placeholder="输入负责人姓名" />
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input
            v-model="handleForm.comment"
            type="textarea"
            :rows="4"
            placeholder="输入处理说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitHandle" :loading="submitting">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8005'

// 加载状态
const loading = ref(false)
const submitting = ref(false)

// 健康度评分
const healthScore = ref({
  overall_score: 0,
  dimension_scores: {},
  level: 'NEEDS_ATTENTION',
  recommendations: []
})

// 风险汇总
const riskSummary = ref({
  total_risks: 0,
  critical_count: 0,
  warning_count: 0,
  info_count: 0,
  cashflow_risks: 0,
  ar_risks: 0,
  ap_risks: 0,
  ratio_risks: 0,
  budget_risks: 0,
  overall_health_score: 0
})

// 风险列表
const allRisks = ref([])
const filteredRisks = ref([])
const riskFilter = ref('all')

// 图表引用
const riskTypeChart = ref(null)
const riskTrendChart = ref(null)

// 对话框
const detailDialogVisible = ref(false)
const handleDialogVisible = ref(false)
const selectedRisk = ref(null)

// 处理表单
const handleForm = reactive({
  risk_id: '',
  status: 'OPEN',
  assigned_to: '',
  comment: ''
})

// 初始化
onMounted(() => {
  loadAllData()
  window.addEventListener('resize', resizeCharts)
})

// 加载所有数据
async function loadAllData() {
  loading.value = true
  try {
    await Promise.all([
      loadHealthScore(),
      loadRiskSummary(),
      loadRiskList()
    ])
    initCharts()
  } catch (error) {
    ElMessage.error('加载数据失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载健康度评分
async function loadHealthScore() {
  try {
    const response = await axios.get(`${API_BASE}/api/v1/financial/health-score/COMP-001`)
    healthScore.value = response.data.data || response.data
  } catch (error) {
    // 使用模拟数据
    healthScore.value = {
      overall_score: 65,
      dimension_scores: {
        liquidity: 55,
        leverage: 60,
        profitability: 70,
        cashflow: 75
      },
      level: 'NEEDS_ATTENTION',
      recommendations: ['优化短期资产结构', '降低财务杠杆']
    }
  }
}

// 加载风险汇总
async function loadRiskSummary() {
  try {
    const response = await axios.get(`${API_BASE}/api/v1/financial/risk-summary`)
    riskSummary.value = response.data.data || response.data
  } catch (error) {
    // 使用模拟数据
    riskSummary.value = {
      total_risks: 12,
      critical_count: 2,
      warning_count: 5,
      info_count: 5,
      cashflow_risks: 3,
      ar_risks: 4,
      ap_risks: 2,
      ratio_risks: 2,
      budget_risks: 1,
      overall_health_score: 65
    }
  }
}

// 加载风险列表
async function loadRiskList() {
  try {
    const response = await axios.get(`${API_BASE}/api/v1/financial/risks`)
    allRisks.value = response.data.data || response.data || []
    filterRisks()
  } catch (error) {
    // 使用模拟数据
    allRisks.value = [
      {
        id: 'CFR-001',
        type: 'CASHFLOW',
        severity: 'CRITICAL',
        title: '现金流不足',
        detail: '当前余额 ¥50 万，低于安全线 ¥100 万',
        risk_score: 85,
        assigned_to: '王五 (CFO)',
        status: 'OPEN',
        detected_at: '2026-04-05 10:30'
      },
      {
        id: 'ARR-001',
        type: 'AR',
        severity: 'WARNING',
        title: '应收账款逾期 - A 公司',
        detail: '逾期金额 ¥120 万，逾期 45 天',
        risk_score: 70,
        assigned_to: '李四 (客户经理)',
        status: 'IN_PROGRESS',
        detected_at: '2026-04-05 09:15'
      },
      {
        id: 'BVR-001',
        type: 'BUDGET',
        severity: 'WARNING',
        title: '预算偏差超标 - 市场部',
        detail: '预算 ¥100 万，实际 ¥130 万，偏差 30%',
        risk_score: 60,
        assigned_to: '赵六 (市场总监)',
        status: 'OPEN',
        detected_at: '2026-04-04 16:20'
      },
      {
        id: 'FRR-001',
        type: 'RATIO',
        severity: 'WARNING',
        title: '财务比率异常',
        detail: '流动比率 0.8，负债权益比 2.5，ROE 3%',
        risk_score: 65,
        assigned_to: '财务部',
        status: 'OPEN',
        detected_at: '2026-04-04 14:00'
      }
    ]
    filterRisks()
  }
}

// 筛选风险
function filterRisks() {
  if (riskFilter.value === 'all') {
    filteredRisks.value = allRisks.value
  } else {
    filteredRisks.value = allRisks.value.filter(r => r.severity === riskFilter.value)
  }
}

// 初始化图表
function initCharts() {
  initRiskTypeChart()
  initRiskTrendChart()
}

// 风险类型图表
function initRiskTypeChart() {
  if (!riskTypeChart.value) return
  
  const chart = echarts.init(riskTypeChart.value)
  const option = {
    tooltip: { trigger: 'item' },
    legend: { top: '5%', left: 'center' },
    series: [
      {
        name: '风险类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold' }
        },
        labelLine: { show: false },
        data: [
          { value: riskSummary.value.cashflow_risks, name: '现金流' },
          { value: riskSummary.value.ar_risks, name: '应收账款' },
          { value: riskSummary.value.ap_risks, name: '应付账款' },
          { value: riskSummary.value.ratio_risks, name: '财务比率' },
          { value: riskSummary.value.budget_risks, name: '预算偏差' }
        ]
      }
    ]
  }
  chart.setOption(option)
}

// 风险趋势图表
function initRiskTrendChart() {
  if (!riskTrendChart.value) return
  
  const chart = echarts.init(riskTrendChart.value)
  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '高危',
        type: 'line',
        data: [3, 2, 2, 3, 2, 1, 2],
        itemStyle: { color: '#F56C6C' }
      },
      {
        name: '警告',
        type: 'line',
        data: [5, 6, 5, 4, 5, 6, 5],
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: '提示',
        type: 'line',
        data: [8, 7, 6, 7, 8, 7, 6],
        itemStyle: { color: '#E6C229' }
      }
    ]
  }
  chart.setOption(option)
}

// 调整图表大小
function resizeCharts() {
  if (riskTypeChart.value) echarts.getInstanceByDom(riskTypeChart.value)?.resize()
  if (riskTrendChart.value) echarts.getInstanceByDom(riskTrendChart.value)?.resize()
}

// 刷新数据
function refreshData() {
  loadAllData()
  ElMessage.success('数据已刷新')
}

// 导出报告
function exportReport() {
  ElMessage.success('报告导出功能开发中')
}

// 处理风险
function handleRisk(row) {
  selectedRisk.value = row
  handleForm.risk_id = row.id
  handleForm.status = row.status
  handleForm.assigned_to = row.assigned_to || ''
  handleForm.comment = ''
  handleDialogVisible.value = true
}

// 查看详情
function viewDetail(row) {
  selectedRisk.value = {
    ...row,
    propagation: {
      paths: [
        '现金流不足 → 无法支付供应商 → 供应链中断风险',
        '现金流不足 → 项目资金短缺 → 项目延期风险'
      ]
    },
    recommendations: [
      '🔴 立即启动融资或加快回款',
      '🔴 审查并削减非必要支出',
      '⚠️ 与供应商协商延长账期'
    ]
  }
  detailDialogVisible.value = true
}

// 分配风险
function assignRisk() {
  ElMessage.success('分配处理功能开发中')
  detailDialogVisible.value = false
}

// 提交处理
async function submitHandle() {
  submitting.value = true
  try {
    // TODO: 调用 API 更新风险状态
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('处理已提交')
    handleDialogVisible.value = false
    loadRiskList()
  } catch (error) {
    ElMessage.error('提交失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 辅助函数
function getScoreColor(score) {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

function formatScore(score) {
  return `${score}分`
}

function getLevelClass(level) {
  return `level-${level.toLowerCase()}`
}

function getLevelText(level) {
  const map = {
    'HEALTHY': '健康',
    'NEEDS_ATTENTION': '需关注',
    'AT_RISK': '有风险',
    'CRITICAL': '严重'
  }
  return map[level] || level
}

function getDimensionName(dim) {
  const map = {
    'liquidity': '流动性',
    'leverage': '杠杆',
    'profitability': '盈利',
    'cashflow': '现金流'
  }
  return map[dim] || dim
}

function getSeverityType(severity) {
  const map = {
    'CRITICAL': 'danger',
    'WARNING': 'warning',
    'INFO': 'info'
  }
  return map[severity] || 'info'
}

function getSeverityText(severity) {
  const map = {
    'CRITICAL': '高危',
    'WARNING': '警告',
    'INFO': '提示'
  }
  return map[severity] || severity
}

function getRiskTypeIcon(type) {
  const map = {
    'CASHFLOW': '💰',
    'AR': '📋',
    'AP': '💳',
    'RATIO': '📊',
    'BUDGET': '📈'
  }
  return map[type] || '⚠️'
}

function getRiskTypeName(type) {
  const map = {
    'CASHFLOW': '现金流',
    'AR': '应收账款',
    'AP': '应付账款',
    'RATIO': '财务比率',
    'BUDGET': '预算偏差'
  }
  return map[type] || type
}

function getStatusType(status) {
  const map = {
    'OPEN': 'info',
    'IN_PROGRESS': 'warning',
    'PENDING_REVIEW': 'warning',
    'RESOLVED': 'success'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    'OPEN': '待处理',
    'IN_PROGRESS': '处理中',
    'PENDING_REVIEW': '待验证',
    'RESOLVED': '已闭环'
  }
  return map[status] || status
}
</script>

<style scoped>
.financial-risk-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.health-score-card {
  margin-bottom: 20px;
}

.health-score-content {
  display: flex;
  gap: 40px;
}

.score-left {
  flex: 1;
  text-align: center;
}

.score-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #303133;
}

.score-gauge {
  margin-bottom: 15px;
}

.score-level {
  font-size: 20px;
  font-weight: bold;
  padding: 8px 20px;
  border-radius: 20px;
  display: inline-block;
}

.level-healthy {
  background: #f0f9ff;
  color: #67C23A;
}

.level-needs_attention {
  background: #fdf6ec;
  color: #E6A23C;
}

.level-at_risk {
  background: #fef0f0;
  color: #F56C6C;
}

.level-critical {
  background: #fef0f0;
  color: #F56C6C;
}

.score-right {
  flex: 1.5;
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.dimension-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.dimension-name {
  width: 80px;
  font-size: 14px;
  color: #606266;
}

.dimension-value {
  width: 50px;
  text-align: right;
  font-weight: bold;
  font-size: 14px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 40px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-card.critical .stat-value { color: #F56C6C; }
.stat-card.warning .stat-value { color: #E6A23C; }
.stat-card.info .stat-value { color: #E6C229; }
.stat-card.total .stat-value { color: #409EFF; }

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.chart-container {
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}

.risk-list-card {
  border-radius: 8px;
}

.risk-title {
  font-weight: bold;
  color: #303133;
}

.risk-detail {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.unassigned {
  color: #909399;
  font-size: 12px;
}

.risk-detail-dialog h4 {
  margin: 20px 0 10px 0;
  color: #303133;
}

.propagation-section ul {
  margin: 10px 0;
  padding-left: 20px;
  color: #606266;
}

.recommendation-section {
  margin-top: 20px;
}
</style>
