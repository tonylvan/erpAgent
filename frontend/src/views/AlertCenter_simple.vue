<template>
  <div class="alert-center-page">
    <!-- 顶部模块切换导航 -->
    <div class="module-nav">
      <el-button type="danger" size="small" disabled>🚨 预警中心</el-button>
      <el-button type="primary" size="small" @click="$emit('close')">💬 智能问数</el-button>
      <el-button type="info" size="small" @click="$emit('close')">🔍 返回图谱</el-button>
    </div>

    <div class="alert-header">
      <h1>🚨 企业预警中心</h1>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card critical">
        <div class="stat-icon">🔴</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.critical }}</div>
          <div class="stat-label">高危预警</div>
        </div>
      </el-card>

      <el-card class="stat-card warning">
        <div class="stat-icon">🟠</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.warning }}</div>
          <div class="stat-label">警告预警</div>
        </div>
      </el-card>

      <el-card class="stat-card info">
        <div class="stat-icon">🟡</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.info }}</div>
          <div class="stat-label">提示预警</div>
        </div>
      </el-card>

      <el-card class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.resolved }}</div>
          <div class="stat-label">已处理</div>
        </div>
      </el-card>

      <el-card class="stat-card financial">
        <div class="stat-icon">💰</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.financial }}</div>
          <div class="stat-label">财务风险</div>
        </div>
      </el-card>
    </div>

    <!-- 财务风险专项 -->
    <el-card class="financial-section">
      <template #header>
        <div class="card-header">
          <span>💰 财务风险专项</span>
        </div>
      </template>

      <div class="financial-content">
        <div class="health-score">
          <div class="score-title">财务健康度评分</div>
          <div class="score-value" :class="scoreClass">{{ healthScore }}/100</div>
          <div class="score-status" :class="scoreClass">{{ scoreStatus }}</div>
        </div>

        <div class="risk-indicators">
          <div class="indicator" v-if="indicators.lowCurrentRatio">
            <span class="indicator-icon">⚠️</span>
            <span>流动比率：0.8 (低于 1.0)</span>
          </div>
          <div class="indicator" v-if="indicators.highDebtToEquity">
            <span class="indicator-icon">⚠️</span>
            <span>负债权益比：2.5 (高于 2.0)</span>
          </div>
          <div class="indicator" v-if="indicators.lowROE">
            <span class="indicator-icon">⚠️</span>
            <span>ROE: 3% (低于 5%)</span>
          </div>
          <div class="indicator" v-if="indicators.lowCashFlow">
            <span class="indicator-icon">🔴</span>
            <span>现金流：¥50 万 (低于安全线¥100 万)</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 预警列表 -->
    <el-card class="alert-list-section">
      <template #header>
        <div class="card-header">
          <span>⚠️ 预警列表</span>
        </div>
      </template>

      <el-table :data="alerts" style="width: 100%">
        <el-table-column prop="level" label="等级" width="80">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="assignee" label="负责人" width="120" />
        <el-table-column prop="timeout" label="超时" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// 统计数据
const stats = ref({
  critical: 12,
  warning: 28,
  info: 56,
  resolved: 342,
  financial: 5
})

// 财务健康度
const healthScore = ref(65)
const indicators = ref({
  lowCurrentRatio: true,
  highDebtToEquity: true,
  lowROE: true,
  lowCashFlow: true
})

// 预警数据 (模拟数据)
const alerts = ref([
  {
    id: 1,
    level: '🔴 高危',
    title: '现金流不足',
    description: '当前：¥50 万 | 安全线：¥100 万',
    assignee: '王五 (CFO)',
    timeout: '剩余 1 小时'
  },
  {
    id: 2,
    level: '🟠 警告',
    title: '应收账款逾期 - A 公司',
    description: '逾期金额：¥120 万 | 逾期天数：45 天',
    assignee: '李四 (客户经理)',
    timeout: '剩余 23 小时'
  },
  {
    id: 3,
    level: '🟠 警告',
    title: '预算偏差超标 - 市场部',
    description: '预算：¥100 万 | 实际：¥130 万 | 偏差：30%',
    assignee: '赵六 (市场总监)',
    timeout: '剩余 48 小时'
  },
  {
    id: 4,
    level: '🟡 提示',
    title: '库存预警 - iPhone 15 Pro',
    description: '当前库存：50 | 安全库存：100',
    assignee: '张三 (库存管理员)',
    timeout: '剩余 72 小时'
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

// 方法
const getLevelType = (level) => {
  if (level.includes('高危')) return 'danger'
  if (level.includes('警告')) return 'warning'
  return 'info'
}

// 挂载时加载数据
onMounted(() => {
  console.log('✅ 预警中心已加载 (使用模拟数据)')
})
</script>

<style scoped>
.alert-center-page {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部模块切换导航 */
.module-nav {
  display: flex;
  gap: 10px;
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 100;
}

.alert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  position: relative;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.stat-icon {
  font-size: 40px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

/* 财务风险专项 */
.financial-section {
  margin-bottom: 20px;
}

.financial-content {
  display: flex;
  gap: 30px;
  padding: 20px;
  background: white;
  border-radius: 12px;
}

.health-score {
  text-align: center;
  min-width: 200px;
}

.score-title {
  font-size: 16px;
  color: #666;
  margin-bottom: 10px;
}

.score-value {
  font-size: 48px;
  font-weight: bold;
}

.score-value.good {
  color: #67C23A;
}

.score-value.warning {
  color: #E6A23C;
}

.score-value.danger {
  color: #F56C6C;
}

.score-status {
  font-size: 18px;
  margin-top: 10px;
}

.score-status.good {
  color: #67C23A;
}

.score-status.warning {
  color: #E6A23C;
}

.score-status.danger {
  color: #F56C6C;
}

.risk-indicators {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.indicator-icon {
  font-size: 20px;
}

/* 预警列表 */
.alert-list-section {
  background: white;
}
</style>
