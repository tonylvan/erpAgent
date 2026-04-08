<template>
  <div class="ticket-detail-container">
    <!-- 顶部导航 -->
    <GlobalNav />

    <!-- 主内容区 -->
    <div class="ticket-content">
      <!-- 左侧：工单详情 -->
      <div class="ticket-main">
        <!-- 工单标题栏 -->
        <div class="ticket-header">
          <div class="header-left">
            <span class="ticket-id">#{{ ticket.id }}</span>
            <h1 class="ticket-title">{{ ticket.title }}</h1>
          </div>
          <div class="header-right">
            <span :class="['status-badge', ticket.status.toLowerCase()]">
              {{ statusLabels[ticket.status] }}
            </span>
            <span :class="['priority-badge', ticket.priority.toLowerCase()]">
              {{ priorityLabels[ticket.priority] }}
            </span>
          </div>
        </div>

        <!-- 工单基本信息 -->
        <div class="ticket-section">
          <h3 class="section-title">基本信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <label>创建人</label>
              <div class="info-value">{{ ticket.created_by_name || 'Unknown' }}</div>
            </div>
            <div class="info-item">
              <label>负责人</label>
              <div class="info-value">
                <template v-if="ticket.assignee_name">
                  {{ ticket.assignee_name }}
                </template>
                <el-button v-else type="primary" size="small" @click="showAssignDialog = true">
                  分配
                </el-button>
              </div>
            </div>
            <div class="info-item">
              <label>创建时间</label>
              <div class="info-value">{{ formatDate(ticket.created_at) }}</div>
            </div>
            <div class="info-item">
              <label>截止时间</label>
              <div class="info-value" :class="{ 'text-danger': isOverdue }">
                {{ ticket.due_date ? formatDate(ticket.due_date) : '未设置' }}
              </div>
            </div>
            <div class="info-item">
              <label>问题类型</label>
              <div class="info-value">{{ ticket.issue_type || '未分类' }}</div>
            </div>
            <div class="info-item">
              <label>关联预警</label>
              <div class="info-value">
                <el-tag v-if="ticket.alert_id" size="small" type="warning">
                  预警 #{{ ticket.alert_id }}
                </el-tag>
                <span v-else>无</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 工单描述 -->
        <div class="ticket-section">
          <h3 class="section-title">问题描述</h3>
          <div class="ticket-description">
            {{ ticket.description || '暂无描述' }}
          </div>
        </div>

        <!-- 工作流操作按钮 -->
        <div class="ticket-section">
          <h3 class="section-title">操作</h3>
          <div class="action-buttons">
            <el-button 
              v-if="canAssign" 
              type="primary" 
              @click="showAssignDialog = true"
            >
              分配
            </el-button>
            <el-button 
              v-if="canTransfer" 
              type="warning" 
              @click="showTransferDialog = true"
            >
              转派
            </el-button>
            <el-button 
              v-if="canEscalate" 
              type="danger" 
              @click="handleEscalate"
            >
              升级
            </el-button>
            <el-button 
              v-if="canResolve" 
              type="success" 
              @click="showResolveDialog = true"
            >
              解决
            </el-button>
            <el-button 
              v-if="canClose" 
              type="info" 
              @click="showCloseDialog = true"
            >
              关闭
            </el-button>
          </div>
        </div>

        <!-- 操作日志时间线 -->
        <div class="ticket-section">
          <h3 class="section-title">操作日志</h3>
          <el-timeline>
            <el-timeline-item 
              v-for="(log, index) in workflowLogs" 
              :key="index"
              :timestamp="formatDate(log.created_at)"
              placement="top"
            >
              <el-card>
                <div class="log-content">
                  <div class="log-header">
                    <span class="log-action">{{ log.action }}</span>
                    <span class="log-operator">操作人：{{ log.operator_name || log.operator_id }}</span>
                  </div>
                  <div class="log-body">
                    <template v-if="log.from_status && log.to_status">
                      <span>状态变更：{{ log.from_status }} → {{ log.to_status }}</span>
                    </template>
                    <template v-if="log.comment">
                      <p class="log-comment">{{ log.comment }}</p>
                    </template>
                    <template v-if="log.metadata">
                      <pre class="log-metadata">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
                    </template>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

      <!-- 右侧：评论区 -->
      <div class="ticket-sidebar">
        <div class="comments-section">
          <h3 class="section-title">评论 ({{ comments.length }})</h3>
          
          <!-- 评论列表 -->
          <div class="comments-list">
            <div 
              v-for="comment in comments" 
              :key="comment.id"
              :class="['comment-item', { 'internal-comment': comment.is_internal }]"
            >
              <div class="comment-avatar">
                {{ comment.author_name.charAt(0).toUpperCase() }}
              </div>
              <div class="comment-content">
                <div class="comment-header">
                  <span class="comment-author">{{ comment.author_name }}</span>
                  <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
                  <el-tag v-if="comment.is_internal" size="mini" type="warning">内部</el-tag>
                </div>
                <div class="comment-text">{{ comment.content }}</div>
                <div class="comment-actions">
                  <el-button type="text" size="mini" @click="handleReply(comment)">
                    回复
                  </el-button>
                  <el-button 
                    v-if="canEditComment(comment)" 
                    type="text" 
                    size="mini" 
                    @click="handleEditComment(comment)"
                  >
                    编辑
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 发表评论 -->
          <div class="comment-input-section">
            <el-input
              v-model="newComment"
              type="textarea"
              :rows="3"
              placeholder="写下你的评论..."
              maxlength="10000"
              show-word-limit
            />
            <div class="comment-options">
              <el-checkbox v-model="isInternalComment">内部评论（用户不可见）</el-checkbox>
            </div>
            <div class="comment-submit">
              <el-button type="primary" @click="handleAddComment" :loading="submitting">
                发表评论
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分配对话框 -->
    <el-dialog v-model="showAssignDialog" title="分配工单" width="500px">
      <el-form :model="assignForm" label-width="100px">
        <el-form-item label="负责人">
          <el-select v-model="assignForm.assignee_id" placeholder="请选择负责人" style="width: 100%">
            <el-option 
              v-for="user in availableUsers" 
              :key="user.id"
              :label="user.name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注说明">
          <el-input v-model="assignForm.comment" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="submitting">
          确认分配
        </el-button>
      </template>
    </el-dialog>

    <!-- 转派对话框 -->
    <el-dialog v-model="showTransferDialog" title="转派工单" width="500px">
      <el-form :model="transferForm" label-width="100px">
        <el-form-item label="新负责人">
          <el-select v-model="transferForm.new_assignee_id" placeholder="请选择新负责人" style="width: 100%">
            <el-option 
              v-for="user in availableUsers" 
              :key="user.id"
              :label="user.name"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="转派原因">
          <el-input v-model="transferForm.reason" type="textarea" :rows="3" placeholder="请说明转派原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTransferDialog = false">取消</el-button>
        <el-button type="warning" @click="handleTransfer" :loading="submitting">
          确认转派
        </el-button>
      </template>
    </el-dialog>

    <!-- 解决对话框 -->
    <el-dialog v-model="showResolveDialog" title="解决工单" width="500px">
      <el-form :model="resolveForm" label-width="100px">
        <el-form-item label="解决说明">
          <el-input 
            v-model="resolveForm.resolution_notes" 
            type="textarea" 
            :rows="4" 
            placeholder="请描述解决方案" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResolveDialog = false">取消</el-button>
        <el-button type="success" @click="handleResolve" :loading="submitting">
          确认解决
        </el-button>
      </template>
    </el-dialog>

    <!-- 关闭对话框 -->
    <el-dialog v-model="showCloseDialog" title="关闭工单" width="500px">
      <el-form :model="closeForm" label-width="100px">
        <el-form-item label="关闭说明">
          <el-input 
            v-model="closeForm.closing_notes" 
            type="textarea" 
            :rows="3" 
            placeholder="请说明关闭原因" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCloseDialog = false">取消</el-button>
        <el-button type="info" @click="handleClose" :loading="submitting">
          确认关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import GlobalNav from '../components/GlobalNav.vue'
import { api } from '../utils/api'

const route = useRoute()
const router = useRouter()

// 工单数据
const ticket = ref({
  id: '',
  title: '',
  description: '',
  status: 'PENDING',
  priority: 'MEDIUM',
  assignee_id: null,
  assignee_name: null,
  created_by_name: '',
  created_at: '',
  due_date: null,
  issue_type: '',
  alert_id: null
})

// 状态和优先级标签
const statusLabels = {
  PENDING: '待处理',
  IN_PROGRESS: '处理中',
  PENDING_VALIDATION: '待验证',
  RESOLVED: '已解决',
  CLOSED: '已闭环',
  TIMEOUT: '已超时',
  CANCELLED: '已取消'
}

const priorityLabels = {
  LOW: '低',
  MEDIUM: '中',
  HIGH: '高',
  URGENT: '紧急'
}

// 评论数据
const comments = ref([])
const newComment = ref('')
const isInternalComment = ref(false)
const submitting = ref(false)

// 工作流日志
const workflowLogs = ref([])

// 对话框
const showAssignDialog = ref(false)
const showTransferDialog = ref(false)
const showResolveDialog = ref(false)
const showCloseDialog = ref(false)

// 表单数据
const assignForm = ref({
  assignee_id: '',
  comment: ''
})

const transferForm = ref({
  new_assignee_id: '',
  reason: ''
})

const resolveForm = ref({
  resolution_notes: ''
})

const closeForm = ref({
  closing_notes: ''
})

// 可用用户列表（用于分配/转派）
const availableUsers = ref([
  { id: 'user1', name: '张三' },
  { id: 'user2', name: '李四' },
  { id: 'user3', name: '王五' }
])

// 计算属性
const canAssign = computed(() => {
  return ticket.value.status === 'PENDING' && !ticket.value.assignee_id
})

const canTransfer = computed(() => {
  return ticket.value.assignee_id && ticket.value.status !== 'CLOSED'
})

const canEscalate = computed(() => {
  return ticket.value.priority !== 'URGENT' && ticket.value.status !== 'CLOSED'
})

const canResolve = computed(() => {
  return ticket.value.status === 'IN_PROGRESS' || ticket.value.status === 'PENDING_VALIDATION'
})

const canClose = computed(() => {
  return ticket.value.status === 'RESOLVED'
})

const isOverdue = computed(() => {
  if (!ticket.value.due_date) return false
  return new Date(ticket.value.due_date) < new Date()
})

// 加载工单详情
const loadTicket = async () => {
  try {
    const response = await api.get(`/tickets/${route.params.id}`)
    ticket.value = response.data
    await loadComments()
    await loadWorkflowLogs()
  } catch (error) {
    ElMessage.error('加载工单失败：' + (error.response?.data?.detail || error.message))
  }
}

// 加载评论
const loadComments = async () => {
  try {
    const response = await api.get(`/tickets/${route.params.id}/comments`)
    comments.value = response.data.items || []
  } catch (error) {
    console.error('加载评论失败:', error)
  }
}

// 加载工作流日志
const loadWorkflowLogs = async () => {
  try {
    // Note: Need to implement this API
    // const response = await api.get(`/api/v1/tickets/${route.params.id}/logs`)
    // workflowLogs.value = response.data
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

// 发表评论
const handleAddComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  submitting.value = true
  try {
    await api.post(`/api/v1/tickets/${route.params.id}/comments`, {
      ticket_id: route.params.id,
      content: newComment.value,
      is_internal: isInternalComment.value,
      author_id: 'current_user_id', // TODO: Get from auth
      author_name: 'Current User',
      parent_id: null
    })
    
    ElMessage.success('评论成功')
    newComment.value = ''
    isInternalComment.value = false
    await loadComments()
  } catch (error) {
    ElMessage.error('评论失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 分配工单
const handleAssign = async () => {
  if (!assignForm.value.assignee_id) {
    ElMessage.warning('请选择负责人')
    return
  }

  submitting.value = true
  try {
    const user = availableUsers.value.find(u => u.id === assignForm.value.assignee_id)
    await api.post(`/api/v1/tickets/${route.params.id}/assign`, {
      assigned_to: assignForm.value.assignee_id,
      assigned_to_name: user?.name,
      comment: assignForm.value.comment
    })
    
    ElMessage.success('分配成功')
    showAssignDialog.value = false
    await loadTicket()
  } catch (error) {
    ElMessage.error('分配失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 转派工单
const handleTransfer = async () => {
  if (!transferForm.value.new_assignee_id) {
    ElMessage.warning('请选择新负责人')
    return
  }

  submitting.value = true
  try {
    const user = availableUsers.value.find(u => u.id === transferForm.value.new_assignee_id)
    await api.post(`/api/v1/tickets/${route.params.id}/transfer`, {
      new_assignee: transferForm.value.new_assignee_id,
      new_assignee_name: user?.name,
      reason: transferForm.value.reason
    })
    
    ElMessage.success('转派成功')
    showTransferDialog.value = false
    await loadTicket()
  } catch (error) {
    ElMessage.error('转派失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 升级工单
const handleEscalate = async () => {
  try {
    await ElMessageBox.confirm('确定要升级工单优先级吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    submitting.value = true
    await api.post(`/api/v1/tickets/${route.params.id}/escalate`, {
      reason: '手动升级'
    })
    
    ElMessage.success('升级成功')
    await loadTicket()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('升级失败：' + error.message)
    }
  } finally {
    submitting.value = false
  }
}

// 解决工单
const handleResolve = async () => {
  submitting.value = true
  try {
    await api.post(`/api/v1/tickets/${route.params.id}/resolve`, {
      resolution_notes: resolveForm.value.resolution_notes,
      resolved_by: 'current_user_id'
    })
    
    ElMessage.success('解决成功')
    showResolveDialog.value = false
    await loadTicket()
  } catch (error) {
    ElMessage.error('解决失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 关闭工单
const handleClose = async () => {
  submitting.value = true
  try {
    await api.post(`/api/v1/tickets/${route.params.id}/close`, {
      closing_notes: closeForm.value.closing_notes,
      closed_by: 'current_user_id'
    })
    
    ElMessage.success('关闭成功')
    showCloseDialog.value = false
    await loadTicket()
  } catch (error) {
    ElMessage.error('关闭失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 回复评论
const handleReply = (comment) => {
  newComment.value = `@${comment.author_name} `
}

// 编辑评论
const handleEditComment = (comment) => {
  // TODO: Implement edit logic
  ElMessage.info('编辑评论功能开发中')
}

// 是否可以编辑评论
const canEditComment = (comment) => {
  // TODO: Check if current user is the comment author
  return true
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadTicket()
})
</script>

<style scoped>
.ticket-detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.ticket-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.ticket-main {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.ticket-sidebar {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f0f0f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.ticket-id {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.ticket-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.header-right {
  display: flex;
  gap: 10px;
}

.status-badge,
.priority-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.pending { background: #fff3cd; color: #856404; }
.status-badge.in_progress { background: #cfe2ff; color: #084298; }
.status-badge.pending_validation { background: #f8d7da; color: #842029; }
.status-badge.resolved { background: #d1e7dd; color: #0f5132; }
.status-badge.closed { background: #d3d3d3; color: #6c757d; }

.priority-badge.low { background: #e9ecef; color: #495057; }
.priority-badge.medium { background: #cff4fc; color: #055160; }
.priority-badge.high { background: #fff3cd; color: #856404; }
.priority-badge.urgent { background: #f8d7da; color: #842029; }

.ticket-section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e0e0e0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #1a1a1a;
  font-weight: 500;
}

.text-danger {
  color: #dc3545 !important;
}

.ticket-description {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.6;
  color: #333;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-action {
  font-weight: 600;
  color: #667eea;
}

.log-operator {
  font-size: 13px;
  color: #666;
}

.log-body {
  font-size: 14px;
  color: #333;
}

.log-comment {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  font-style: italic;
}

.log-metadata {
  margin-top: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
  max-height: 500px;
  overflow-y: auto;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.comment-item.internal-comment {
  background: #fff3cd;
  border-left: 3px solid #ffc107;
}

.comment-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.comment-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.comment-author {
  font-weight: 600;
  color: #1a1a1a;
}

.comment-time {
  font-size: 12px;
  color: #666;
}

.comment-text {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
}

.comment-actions {
  display: flex;
  gap: 8px;
}

.comment-input-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comment-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comment-submit {
  display: flex;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .ticket-content {
    grid-template-columns: 1fr;
  }
  
  .ticket-sidebar {
    order: -1;
  }
}
</style>
