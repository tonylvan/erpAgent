<template>
  <div class="alert-ticket-integration">
    <!-- 顶部导航 -->
    <GlobalNav />

    <div class="integration-content">
      <!-- 左侧：预警列表 -->
      <div class="alert-panel">
        <div class="panel-header">
          <h2>🔔 预警中心</h2>
          <el-button type="primary" size="small" @click="refreshAlerts">
            刷新
          </el-button>
        </div>

        <!-- 预警筛选 -->
        <div class="filter-section">
          <el-select v-model="alertFilter.severity" placeholder="预警级别" clearable>
            <el-option label="紧急" value="CRITICAL" />
            <el-option label="重要" value="HIGH" />
            <el-option label="警告" value="MEDIUM" />
            <el-option label="提示" value="LOW" />
          </el-select>
          <el-select v-model="alertFilter.status" placeholder="状态" clearable>
            <el-option label="未处理" value="UNACK" />
            <el-option label="已确认" value="ACKNOWLEDGED" />
            <el-option label="已解决" value="RESOLVED" />
          </el-select>
        </div>

        <!-- 预警列表 -->
        <div class="alert-list">
          <div
            v-for="alert in alerts"
            :key="alert.id"
            :class="['alert-item', alert.severity.toLowerCase(), { 'has-ticket': alert.hasLinkedTicket }]"
            @click="selectAlert(alert)"
          >
            <div class="alert-header">
              <span class="alert-type">{{ alert.type }}</span>
              <el-tag :type="getSeverityType(alert.severity)" size="small">
                {{ getSeverityLabel(alert.severity) }}
              </el-tag>
            </div>
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-meta">
              <span class="alert-time">{{ formatDate(alert.created_at) }}</span>
              <el-tag v-if="alert.hasLinkedTicket" type="success" size="mini">
                已生成工单
              </el-tag>
              <el-button
                v-else
                type="primary"
                size="mini"
                @click.stop="createTicketFromAlert(alert)"
              >
                生成工单
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：关联关系 -->
      <div class="mapping-panel">
        <div class="panel-header">
          <h2>🔗 关联关系</h2>
        </div>

        <div v-if="selectedAlert" class="mapping-detail">
          <h3>当前预警</h3>
          <div class="alert-detail-card">
            <div class="detail-row">
              <label>预警 ID:</label>
              <span>{{ selectedAlert.id }}</span>
            </div>
            <div class="detail-row">
              <label>类型:</label>
              <span>{{ selectedAlert.type }}</span>
            </div>
            <div class="detail-row">
              <label>级别:</label>
              <span>{{ getSeverityLabel(selectedAlert.severity) }}</span>
            </div>
            <div class="detail-row">
              <label>内容:</label>
              <p>{{ selectedAlert.content }}</p>
            </div>
          </div>

          <h3>关联工单</h3>
          <div v-if="selectedAlert.linkedTickets && selectedAlert.linkedTickets.length > 0" class="linked-tickets">
            <div
              v-for="ticket in selectedAlert.linkedTickets"
              :key="ticket.id"
              class="ticket-link-card"
            >
              <div class="ticket-link-header">
                <span class="ticket-id">#{{ ticket.id }}</span>
                <el-tag :type="getPriorityType(ticket.priority)" size="small">
                  {{ getPriorityLabel(ticket.priority) }}
                </el-tag>
              </div>
              <div class="ticket-link-title">{{ ticket.title }}</div>
              <div class="ticket-link-status">
                <el-tag :type="getStatusType(ticket.status)" size="mini">
                  {{ getStatusLabel(ticket.status) }}
                </el-tag>
              </div>
              <el-button
                type="text"
                size="small"
                @click="navigateToTicket(ticket.id)"
              >
                查看详情 →
              </el-button>
            </div>
          </div>
          <div v-else class="no-linked-tickets">
            <el-empty description="暂无关联工单" />
          </div>
        </div>
        <div v-else class="no-selection">
          <el-empty description="请选择一个预警" />
        </div>
      </div>

      <!-- 右侧：智能问数 -->
      <div class="smart-query-panel">
        <div class="panel-header">
          <h2>💡 智能问数</h2>
        </div>

        <!-- 快捷查询 -->
        <div class="quick-queries">
          <el-button
            v-for="query in quickQueries"
            :key="query.id"
            :type="query.type"
            size="small"
            @click="runQuery(query)"
          >
            {{ query.icon }} {{ query.name }}
          </el-button>
        </div>

        <!-- 查询结果 -->
        <div v-if="queryResult" class="query-result">
          <h3>{{ queryResult.title }}</h3>
          
          <!-- 关键指标 -->
          <div class="metrics-grid">
            <div
              v-for="(value, key) in queryResult.metrics"
              :key="key"
              class="metric-card"
            >
              <div class="metric-label">{{ key }}</div>
              <div class="metric-value">{{ value }}</div>
            </div>
          </div>

          <!-- 异常描述 -->
          <div v-if="queryResult.anomaly" class="anomaly-section">
            <h4>⚠️ 异常检测</h4>
            <p>{{ queryResult.anomaly }}</p>
          </div>

          <!-- 工单建议 -->
          <div v-if="queryResult.suggestion" class="suggestion-section">
            <h4>📋 建议操作</h4>
            <el-alert
              :title="queryResult.suggestion.title"
              :type="getSuggestionType(queryResult.suggestion.priority)"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>{{ queryResult.suggestion.description }}</p>
                <div class="suggestion-actions">
                  <el-button
                    type="primary"
                    size="small"
                    @click="createTicketFromSuggestion(queryResult.suggestion)"
                  >
                    一键生成工单
                  </el-button>
                  <el-button size="small" @click="dismissSuggestion">
                    暂不处理
                  </el-button>
                </div>
              </template>
            </el-alert>
          </div>
        </div>
        <div v-else class="no-query-result">
          <el-empty description="运行智能查询查看分析结果" />
        </div>
      </div>
    </div>

    <!-- 生成工单对话框 -->
    <el-dialog
      v-model="showTicketDialog"
      title="从预警生成工单"
      width="600px"
    >
      <el-form :model="ticketForm" label-width="100px">
        <el-form-item label="工单标题">
          <el-input v-model="ticketForm.title" :value="generateTicketTitle()" readonly />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="ticketForm.priority" style="width: 100%">
            <el-option label="紧急" value="URGENT" />
            <el-option label="高" value="HIGH" />
            <el-option label="中" value="MEDIUM" />
            <el-option label="低" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题类型">
          <el-select v-model="ticketForm.issue_type" style="width: 100%">
            <el-option label="库存异常" value="库存异常" />
            <el-option label="付款逾期" value="付款逾期" />
            <el-option label="客户流失" value="客户流失" />
            <el-option label="交货逾期" value="交货逾期" />
            <el-option label="销售异常" value="销售异常" />
            <el-option label="财务风险" value="财务风险" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="ticketForm.assignee_id" placeholder="选择负责人" style="width: 100%">
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="user.name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注说明">
          <el-input v-model="ticketForm.comment" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTicketDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCreateTicket" :loading="creating">
          确认创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import GlobalNav from '@/components/GlobalNav.vue'
import { api } from '@/utils/api'

const router = useRouter()

// 预警数据
const alerts = ref([])
const alertFilter = ref({
  severity: '',
  status: ''
})
const selectedAlert = ref(null)

// 智能问数
const quickQueries = ref([
  { id: 'inventory', name: '库存分析', type: 'warning', icon: '📦' },
  { id: 'sales', name: '销售分析', type: 'success', icon: '📊' },
  { id: 'financial', name: '财务分析', type: 'danger', icon: '💰' },
  { id: 'customer', name: '客户分析', type: 'info', icon: '👥' }
])
const queryResult = ref(null)

// 对话框
const showTicketDialog = ref(false)
const creating = ref(false)
const ticketForm = ref({
  alert_id: '',
  title: '',
  priority: 'MEDIUM',
  issue_type: '',
  assignee_id: '',
  comment: ''
})

// 可用用户
const availableUsers = ref([
  { id: 'user1', name: '张三' },
  { id: 'user2', name: '李四' },
  { id: 'user3', name: '王五' }
])

// 加载预警列表
const loadAlerts = async () => {
  try {
    const response = await api.get('/api/v1/alerts')
    alerts.value = response.data || []
  } catch (error) {
    ElMessage.error('加载预警失败：' + error.message)
  }
}

// 刷新预警
const refreshAlerts = () => {
  loadAlerts()
  ElMessage.success('预警已刷新')
}

// 选择预警
const selectAlert = (alert) => {
  selectedAlert.value = alert
}

// 从预警创建工单
const createTicketFromAlert = (alert) => {
  ticketForm.value.alert_id = alert.id
  ticketForm.value.priority = mapSeverityToPriority(alert.severity)
  ticketForm.value.issue_type = mapAlertTypeToIssueType(alert.type)
  showTicketDialog.value = true
}

// 运行智能查询
const runQuery = async (query) => {
  try {
    ElMessage.info(`正在运行${query.name}...`)
    
    // 调用智能问数 API
    const response = await api.post('/api/v1/smart-query/run', {
      query_type: query.id
    })
    
    queryResult.value = response.data
    ElMessage.success(`${query.name}完成`)
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  }
}

// 从智能问数建议创建工单
const createTicketFromSuggestion = (suggestion) => {
  ticketForm.value.title = suggestion.title
  ticketForm.value.priority = suggestion.priority
  ticketForm.value.issue_type = suggestion.issue_type
  showTicketDialog.value = true
}

// 关闭建议
const dismissSuggestion = () => {
  queryResult.value.suggestion = null
}

// 确认创建工单
const confirmCreateTicket = async () => {
  creating.value = true
  try {
    const response = await api.post('/api/v1/tickets', {
      title: ticketForm.value.title,
      priority: ticketForm.value.priority,
      issue_type: ticketForm.value.issue_type,
      assignee_id: ticketForm.value.assignee_id,
      alert_id: ticketForm.value.alert_id,
      description: ticketForm.value.comment
    })
    
    ElMessage.success('工单创建成功')
    showTicketDialog.value = false
    await loadAlerts()
    
    // 跳转到工单详情
    router.push(`/tickets/${response.data.id}`)
  } catch (error) {
    ElMessage.error('创建失败：' + error.message)
  } finally {
    creating.value = false
  }
}

// 跳转到工单详情
const navigateToTicket = (ticketId) => {
  router.push(`/tickets/${ticketId}`)
}

// 生成工单标题
const generateTicketTitle = () => {
  const alert = alerts.value.find(a => a.id === ticketForm.value.alert_id)
  if (!alert) return ''
  return `[${getSeverityLabel(alert.severity)}] ${alert.type} - ${alert.title}`
}

// 辅助函数
const mapSeverityToPriority = (severity) => {
  const mapping = {
    'CRITICAL': 'URGENT',
    'HIGH': 'HIGH',
    'MEDIUM': 'MEDIUM',
    'LOW': 'LOW'
  }
  return mapping[severity] || 'MEDIUM'
}

const mapAlertTypeToIssueType = (type) => {
  const mapping = {
    'INVENTORY_WARNING': '库存异常',
    'PAYMENT_OVERDUE': '付款逾期',
    'CUSTOMER_CHURN': '客户流失',
    'DELIVERY_OVERDUE': '交货逾期',
    'SALES_ANOMALY': '销售异常',
    'CASH_FLOW_RISK': '财务风险'
  }
  return mapping[type] || '其他'
}

const getSeverityType = (severity) => {
  const mapping = {
    'CRITICAL': 'danger',
    'HIGH': 'warning',
    'MEDIUM': 'warning',
    'LOW': 'info'
  }
  return mapping[severity] || 'info'
}

const getSeverityLabel = (severity) => {
  const mapping = {
    'CRITICAL': '紧急',
    'HIGH': '重要',
    'MEDIUM': '警告',
    'LOW': '提示'
  }
  return mapping[severity] || severity
}

const getPriorityType = (priority) => {
  const mapping = {
    'URGENT': 'danger',
    'HIGH': 'warning',
    'MEDIUM': 'info',
    'LOW': 'success'
  }
  return mapping[priority] || 'info'
}

const getPriorityLabel = (priority) => {
  const mapping = {
    'URGENT': '紧急',
    'HIGH': '高',
    'MEDIUM': '中',
    'LOW': '低'
  }
  return mapping[priority] || priority
}

const getStatusType = (status) => {
  const mapping = {
    'PENDING': 'info',
    'IN_PROGRESS': 'warning',
    'RESOLVED': 'success',
    'CLOSED': 'success'
  }
  return mapping[status] || 'info'
}

const getStatusLabel = (status) => {
  const mapping = {
    'PENDING': '待处理',
    'IN_PROGRESS': '处理中',
    'RESOLVED': '已解决',
    'CLOSED': '已关闭'
  }
  return mapping[status] || status
}

const getSuggestionType = (priority) => {
  const mapping = {
    'URGENT': 'error',
    'HIGH': 'warning',
    'MEDIUM': 'warning',
    'LOW': 'info'
  }
  return mapping[priority] || 'info'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alert-ticket-integration {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.integration-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  max-width: 1800px;
  margin: 0 auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.panel-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: white;
  margin: 0;
}

.alert-panel,
.mapping-panel,
.smart-query-panel {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.filter-section {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-section .el-select {
  flex: 1;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 4px solid transparent;
}

.alert-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
}

.alert-item.critical { border-left-color: #dc3545; }
.alert-item.high { border-left-color: #ffc107; }
.alert-item.medium { border-left-color: #17a2b8; }
.alert-item.low { border-left-color: #28a745; }

.alert-item.has-ticket {
  opacity: 0.7;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-type {
  font-weight: 600;
  color: #1a1a1a;
}

.alert-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alert-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.mapping-detail h3,
.query-result h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 15px 0 10px 0;
  color: #1a1a1a;
}

.alert-detail-card,
.ticket-link-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
}

.detail-row {
  display: flex;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-row label {
  font-weight: 600;
  width: 80px;
  color: #666;
}

.ticket-link-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ticket-id {
  font-weight: 600;
  color: #667eea;
}

.ticket-link-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.ticket-link-status {
  margin-bottom: 8px;
}

.quick-queries {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.metric-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 15px;
  border-radius: 8px;
  color: white;
}

.metric-label {
  font-size: 12px;
  opacity: 0.9;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  margin-top: 5px;
}

.anomaly-section {
  background: #fff3cd;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
  margin-bottom: 15px;
}

.anomaly-section h4 {
  margin: 0 0 8px 0;
  color: #856404;
}

.anomaly-section p {
  margin: 0;
  color: #856404;
  font-size: 14px;
}

.suggestion-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.no-linked-tickets,
.no-selection,
.no-query-result {
  text-align: center;
  padding: 40px 20px;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .integration-content {
    grid-template-columns: 1fr 1fr;
  }
  
  .smart-query-panel {
    grid-column: span 2;
  }
}

@media (max-width: 900px) {
  .integration-content {
    grid-template-columns: 1fr;
  }
  
  .smart-query-panel {
    grid-column: span 1;
  }
}
</style>
