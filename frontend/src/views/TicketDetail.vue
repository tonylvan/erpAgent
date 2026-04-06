<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Clock,
  User,
  Flag,
  Category,
  Edit,
  Delete,
  Refresh,
  Check,
  Close,
  Upload,
  Document
} from '@element-plus/icons-vue'
import GlobalNav from '../components/GlobalNav.vue'

// ==================== Route & Router ====================

const route = useRoute()
const router = useRouter()
const ticketId = computed(() => route.params.id as string)

// ==================== State ====================

const loading = ref(false)
const ticket = ref<any>(null)
const comments = ref<any[]>([])
const commentForm = ref('')

// Dialog
const editDialogVisible = ref(false)
const editForm = ref<any>({})

// ==================== API Functions ====================

const fetchTicket = async () => {
  loading.value = true
  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}`)
    if (!response.ok) {
      if (response.status === 404) {
        ElMessage.error('工单不存在')
        router.push('/tickets')
        return
      }
      throw new Error('Failed to fetch ticket')
    }
    ticket.value = await response.json()
    console.log('Ticket detail:', ticket.value)
  } catch (error) {
    console.error('Error fetching ticket:', error)
    ElMessage.error('加载工单失败')
  } finally {
    loading.value = false
  }
}

const fetchComments = async () => {
  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}/comments`)
    if (response.ok) {
      comments.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching comments:', error)
  }
}

const addComment = async () => {
  if (!commentForm.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: commentForm.value,
        created_by: 'current_user' // TODO: Replace with actual user
      })
    })

    if (response.ok) {
      ElMessage.success('评论添加成功')
      commentForm.value = ''
      await fetchComments()
    } else {
      ElMessage.error('添加评论失败')
    }
  } catch (error) {
    console.error('Error adding comment:', error)
    ElMessage.error('添加评论失败')
  }
}

// ==================== Workflow Actions ====================

const assignTicket = async () => {
  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}/assign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        assigned_to: 'user_id' // TODO: Replace with actual user selection
      })
    })

    if (response.ok) {
      ElMessage.success('工单分配成功')
      await fetchTicket()
    } else {
      ElMessage.error('分配工单失败')
    }
  } catch (error) {
    console.error('Error assigning ticket:', error)
    ElMessage.error('分配工单失败')
  }
}

const resolveTicket = async () => {
  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}/resolve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        resolution: '问题已解决' // TODO: Replace with actual resolution
      })
    })

    if (response.ok) {
      ElMessage.success('工单已解决')
      await fetchTicket()
    } else {
      ElMessage.error('解决工单失败')
    }
  } catch (error) {
    console.error('Error resolving ticket:', error)
    ElMessage.error('解决工单失败')
  }
}

const closeTicket = async () => {
  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}/close`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        close_reason: '工单已关闭'
      })
    })

    if (response.ok) {
      ElMessage.success('工单已关闭')
      await fetchTicket()
    } else {
      ElMessage.error('关闭工单失败')
    }
  } catch (error) {
    console.error('Error closing ticket:', error)
    ElMessage.error('关闭工单失败')
  }
}

const reopenTicket = async () => {
  try {
    const response = await fetch(`http://localhost:8005/api/v1/tickets/${ticketId.value}/reopen`, {
      method: 'POST'
    })

    if (response.ok) {
      ElMessage.success('工单已重新打开')
      await fetchTicket()
    } else {
      ElMessage.error('重新打开工单失败')
    }
  } catch (error) {
    console.error('Error reopening ticket:', error)
    ElMessage.error('重新打开工单失败')
  }
}

// ==================== Helpers ====================

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'OPEN': 'info',
    'IN_PROGRESS': 'warning',
    'RESOLVED': 'success',
    'CLOSED': 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    'OPEN': '待处理',
    'IN_PROGRESS': '处理中',
    'RESOLVED': '已解决',
    'CLOSED': '已关闭'
  }
  return map[status] || status
}

const getPriorityType = (priority: string) => {
  const map: Record<string, string> = {
    'LOW': 'info',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'URGENT': 'danger'
  }
  return map[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  const map: Record<string, string> = {
    'LOW': '低',
    'MEDIUM': '中',
    'HIGH': '高',
    'URGENT': '紧急'
  }
  return map[priority] || priority
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const goBack = () => {
  router.push('/tickets')
}

// ==================== Lifecycle ====================

onMounted(() => {
  fetchTicket()
  fetchComments()
})
</script>

<template>
  <div class="ticket-detail-page">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- Main Content -->
    <div class="detail-content glass">
      <!-- Header -->
      <div class="detail-header">
        <div class="header-left">
          <el-button @click="goBack" :icon="ArrowLeft" circle class="back-btn" />
          <div class="header-title">
            <h1>{{ ticket?.title || '工单详情' }}</h1>
            <el-tag v-if="ticket" :type="getStatusType(ticket.status)" size="large">
              {{ getStatusLabel(ticket.status) }}
            </el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button v-if="ticket?.status === 'OPEN'" @click="assignTicket" :icon="User">
            分配工单
          </el-button>
          <el-button v-if="ticket?.status === 'IN_PROGRESS'" @click="resolveTicket" :icon="Check" type="success">
            解决工单
          </el-button>
          <el-button v-if="ticket?.status === 'RESOLVED'" @click="closeTicket" :icon="Close" type="danger">
            关闭工单
          </el-button>
          <el-button v-if="ticket?.status === 'CLOSED'" @click="reopenTicket" :icon="Refresh" type="warning">
            重新打开
          </el-button>
          <el-button :icon="Edit" @click="editDialogVisible = true">编辑</el-button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>

      <!-- Ticket Detail -->
      <div v-else-if="ticket" class="ticket-detail-content">
        <!-- Info Grid -->
        <div class="info-grid">
          <el-card class="info-card glass-card">
            <template #header>
              <div class="card-header">
                <el-icon><Flag /></el-icon>
                <span>基本信息</span>
              </div>
            </template>
            <el-descriptions :column="1" size="default">
              <el-descriptions-item label="工单 ID">{{ ticket.id }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(ticket.status)">
                  {{ getStatusLabel(ticket.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="优先级">
                <el-tag :type="getPriorityType(ticket.priority)">
                  {{ getPriorityLabel(ticket.priority) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="分类">
                <el-tag>{{ ticket.category }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="info-card glass-card">
            <template #header>
              <div class="card-header">
                <el-icon><User /></el-icon>
                <span>人员信息</span>
              </div>
            </template>
            <el-descriptions :column="1" size="default">
              <el-descriptions-item label="创建人">{{ ticket.created_by || 'N/A' }}</el-descriptions-item>
              <el-descriptions-item label="处理人">
                {{ ticket.assigned_to || '未分配' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="info-card glass-card">
            <template #header>
              <div class="card-header">
                <el-icon><Clock /></el-icon>
                <span>时间信息</span>
              </div>
            </template>
            <el-descriptions :column="1" size="default">
              <el-descriptions-item label="创建时间">{{ formatDate(ticket.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDate(ticket.updated_at) }}</el-descriptions-item>
              <el-descriptions-item v-if="ticket.resolved_at" label="解决时间">
                {{ formatDate(ticket.resolved_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="info-card glass-card">
            <template #header>
              <div class="card-header">
                <el-icon><Document /></el-icon>
                <span>来源信息</span>
              </div>
            </template>
            <el-descriptions :column="1" size="default">
              <el-descriptions-item label="来源">{{ ticket.source || '手动创建' }}</el-descriptions-item>
              <el-descriptions-item v-if="ticket.source_id" label="来源 ID">
                {{ ticket.source_id }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>

        <!-- Description -->
        <el-card class="description-card glass-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>工单描述</span>
            </div>
          </template>
          <div class="description-content" v-html="ticket.description"></div>
        </el-card>

        <!-- Comments Section -->
        <el-card class="comments-card glass-card">
          <template #header>
            <div class="card-header">
              <el-icon><Edit /></el-icon>
              <span>评论 ({{ comments.length }})</span>
            </div>
          </template>
          
          <!-- Comment List -->
          <div class="comment-list">
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-avatar">
                <el-avatar :size="40">{{ comment.created_by?.charAt(0)?.toUpperCase() || 'U' }}</el-avatar>
              </div>
              <div class="comment-content">
                <div class="comment-header">
                  <span class="comment-author">{{ comment.created_by || 'Unknown' }}</span>
                  <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
                </div>
                <div class="comment-text">{{ comment.content }}</div>
              </div>
            </div>
            <div v-if="comments.length === 0" class="no-comments">
              <el-empty description="暂无评论" :image-size="80" />
            </div>
          </div>

          <!-- Add Comment -->
          <div class="comment-form">
            <el-input
              v-model="commentForm"
              type="textarea"
              :rows="3"
              placeholder="添加评论..."
              class="comment-input"
            />
            <el-button type="primary" @click="addComment" :icon="Upload" style="margin-top: 10px;">
              发表评论
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- Error State -->
      <div v-else class="error-container">
        <el-result icon="error" title="工单不存在" sub-title="该工单可能已被删除或不存在">
          <template #extra>
            <el-button type="primary" @click="goBack">返回工单列表</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- Edit Dialog -->
    <el-dialog v-model="editDialogVisible" title="编辑工单" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="editForm.priority">
            <el-option label="低" value="LOW" />
            <el-option label="中" value="MEDIUM" />
            <el-option label="高" value="HIGH" />
            <el-option label="紧急" value="URGENT" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="editForm.category" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="editDialogVisible = false">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.ticket-detail-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.detail-content {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 16px;
  padding: 30px;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  font-size: 18px;
  width: 40px;
  height: 40px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.back-btn:hover {
  transform: translateX(-3px);
}

.header-title h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  color: #2d3748;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-container,
.error-container {
  padding: 60px 20px;
  text-align: center;
}

.ticket-detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.info-card,
.description-card,
.comments-card {
  border: none;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.info-card:hover,
.description-card:hover,
.comments-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #667eea;
  font-size: 16px;
}

.card-header .el-icon {
  font-size: 18px;
}

.description-content {
  line-height: 1.8;
  color: #4a5568;
  padding: 10px 0;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.comment-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  transition: all 0.3s ease;
}

.comment-item:hover {
  background: rgba(255, 255, 255, 0.8);
}

.comment-avatar {
  flex-shrink: 0;
}

.comment-content {
  flex: 1;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
  font-weight: 600;
  color: #2d3748;
}

.comment-time {
  font-size: 12px;
  color: #a0aec0;
}

.comment-text {
  color: #4a5568;
  line-height: 1.6;
}

.no-comments {
  padding: 20px;
  text-align: center;
}

.comment-form {
  border-top: 1px solid rgba(102, 126, 234, 0.1);
  padding-top: 20px;
}

.comment-input {
  width: 100%;
}

/* Responsive Design */
@media (max-width: 768px) {
  .detail-content {
    padding: 20px;
  }

  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-actions {
    flex-wrap: wrap;
    width: 100%;
  }

  .header-actions .el-button {
    flex: 1;
    min-width: 120px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
