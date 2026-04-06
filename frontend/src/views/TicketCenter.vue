<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Edit,
  Check,
  Close,
  Clock,
  User,
  Search,
  Plus,
  Filter,
  Refresh,
  ArrowRight,
  TrendCharts,
  DataAnalysis,
  Calendar
} from '@element-plus/icons-vue'
import GlobalNav from '../components/GlobalNav.vue'

const router = useRouter()

// ==================== State ====================

const loading = ref(false)
const tickets = ref<any[]>([])
const stats = ref<any>({})

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Filters
const filterStatus = ref('')
const filterPriority = ref('')
const filterCategory = ref('')
const searchKeyword = ref('')

// Dialog
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'view'>('create')
const currentTicket = ref<any>(null)

// Form
const form = ref({
  title: '',
  category: '',
  priority: 'MEDIUM',
  description: '',
  created_by: ''
})

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

const getPriorityIcon = (priority: string) => {
  const map: Record<string, string> = {
    'LOW': '🟢',
    'MEDIUM': '🟡',
    'HIGH': '🟠',
    'URGENT': '🔴'
  }
  return map[priority] || '⚪'
}

const getStatusIcon = (status: string) => {
  const map: Record<string, string> = {
    'OPEN': '⏳',
    'IN_PROGRESS': '🔄',
    'RESOLVED': '✅',
    'CLOSED': '🔒'
  }
  return map[status] || '📋'
}

// ==================== Actions ====================

const fetchStats = async () => {
  try {
    const response = await fetch('http://localhost:8006/api/v1/tickets/stats')
    const data = await response.json()
    console.log('Ticket stats:', data)
    
    // Ensure by_status exists with default values
    stats.value = {
      total: data.total || 0,
      open: data.open || 0,
      by_status: {
        OPEN: data.by_status?.OPEN || 0,
        IN_PROGRESS: data.by_status?.IN_PROGRESS || 0,
        RESOLVED: data.by_status?.RESOLVED || 0,
        CLOSED: data.by_status?.CLOSED || 0
      },
      by_priority: data.by_priority || {},
      by_category: data.by_category || {}
    }
  } catch (error) {
    console.error('Failed to fetch ticket stats:', error)
    // Set default values on error
    stats.value = {
      total: 0,
      open: 0,
      by_status: {
        OPEN: 0,
        IN_PROGRESS: 0,
        RESOLVED: 0,
        CLOSED: 0
      },
      by_priority: {},
      by_category: {}
    }
  }
}

const fetchTickets = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      size: pageSize.value.toString()
    })
    if (filterStatus.value) params.append('status', filterStatus.value)
    if (filterPriority.value) params.append('priority', filterPriority.value)
    if (filterCategory.value) params.append('category', filterCategory.value)
    if (searchKeyword.value) params.append('keyword', searchKeyword.value)
    
    const response = await fetch(`http://localhost:8006/api/v1/tickets/?${params}`)
    tickets.value = await response.json()
    total.value = tickets.value.length
  } catch (error) {
    console.error('Failed to fetch tickets:', error)
    ElMessage.error('加载工单列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentTicket.value = null
  form.value = {
    title: '',
    category: '',
    priority: 'MEDIUM',
    description: '',
    created_by: ''
  }
  dialogVisible.value = true
}

const openViewDialog = (ticket: any) => {
  // Navigate to ticket detail page
  router.push(`/tickets/${ticket.id}`)
}

const submitForm = async () => {
  try {
    const response = await fetch('http://localhost:8006/api/v1/tickets/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    
    if (response.ok) {
      ElMessage.success('✅ 工单创建成功')
      dialogVisible.value = false
      fetchTickets()
      fetchStats()
    } else {
      ElMessage.error('❌ 创建工单失败')
    }
  } catch (error) {
    console.error('Failed to create ticket:', error)
    ElMessage.error('❌ 创建工单失败')
  }
}

const assignTicket = async (ticketId: number, assignTo: string) => {
  try {
    const response = await fetch(`http://localhost:8006/api/v1/tickets/${ticketId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assigned_to: assignTo })
    })
    
    if (response.ok) {
      ElMessage.success('✅ 工单已分配')
      fetchTickets()
    } else {
      ElMessage.error('❌ 分配工单失败')
    }
  } catch (error) {
    console.error('Failed to assign ticket:', error)
    ElMessage.error('❌ 分配工单失败')
  }
}

const closeTicket = async (ticketId: number) => {
  try {
    const response = await fetch(`http://localhost:8006/api/v1/tickets/${ticketId}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolved_by: 'current_user' })
    })
    
    if (response.ok) {
      ElMessage.success('✅ 工单已关闭')
      fetchTickets()
      fetchStats()
    } else {
      ElMessage.error('❌ 关闭工单失败')
    }
  } catch (error) {
    console.error('Failed to close ticket:', error)
    ElMessage.error('❌ 关闭工单失败')
  }
}

const resetFilters = () => {
  filterStatus.value = ''
  filterPriority.value = ''
  filterCategory.value = ''
  searchKeyword.value = ''
  fetchTickets()
}

const ticketRowClassName = ({ row, rowIndex }: { row: any, rowIndex: number }) => {
  return `ticket-row priority-${row.priority?.toLowerCase()}`
}

onMounted(() => {
  fetchStats()
  fetchTickets()
})
</script>

<template>
  <div class="ticket-center-pro">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- Page Content -->
    <div class="page-content">
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索工单标题、描述..."
            clearable
            @keyup.enter="fetchTickets"
          />
        </div>
        <el-button class="btn-create" type="primary" :icon="Plus" @click="openCreateDialog">
          创建工单
        </el-button>
      </div>

      <!-- Statistics Cards -->
      <section class="stats-section">
      <div class="stats-grid">
        <el-card class="stat-card stat-total glass">
          <div class="stat-header">
            <div class="stat-icon-wrap icon-total">
              <el-icon :size="32"><DataAnalysis /></el-icon>
            </div>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">总工单数</div>
          </div>
          <div class="stat-progress">
            <el-progress :percentage="100" :show-text="false" stroke-width="4" color="#667eea" />
          </div>
        </el-card>

        <el-card class="stat-card stat-open glass">
          <div class="stat-header">
            <div class="stat-icon-wrap icon-open">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.open || 0 }}</div>
            <div class="stat-label">待处理</div>
          </div>
          <div class="stat-progress">
            <el-progress 
              :percentage="stats.total ? Math.round((stats.open / stats.total) * 100) : 0" 
              :show-text="false" 
              stroke-width="4" 
              color="#f093fb" 
            />
          </div>
        </el-card>

        <el-card class="stat-card stat-in-progress glass">
          <div class="stat-header">
            <div class="stat-icon-wrap icon-progress">
              <el-icon :size="32"><Edit /></el-icon>
            </div>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.by_status?.IN_PROGRESS || 0 }}</div>
            <div class="stat-label">处理中</div>
          </div>
          <div class="stat-progress">
            <el-progress 
              :percentage="stats.total ? Math.round((stats.by_status?.IN_PROGRESS / stats.total) * 100) : 0" 
              :show-text="false" 
              stroke-width="4" 
              color="#4facfe" 
            />
          </div>
        </el-card>

        <el-card class="stat-card stat-resolved glass">
          <div class="stat-header">
            <div class="stat-icon-wrap icon-resolved">
              <el-icon :size="32"><Check /></el-icon>
            </div>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.by_status?.RESOLVED || 0 }}</div>
            <div class="stat-label">已解决</div>
          </div>
          <div class="stat-progress">
            <el-progress 
              :percentage="stats.total ? Math.round((stats.by_status?.RESOLVED / stats.total) * 100) : 0" 
              :show-text="false" 
              stroke-width="4" 
              color="#43e97b" 
            />
          </div>
        </el-card>
      </div>
    </section>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Filters Panel -->
      <section class="filters-panel glass">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Filter /></el-icon>
            <span>筛选条件</span>
          </div>
          <el-button text :icon="Refresh" @click="fetchTickets">刷新数据</el-button>
        </div>
        
        <div class="panel-body">
          <div class="filter-group">
            <label>状态</label>
            <el-select v-model="filterStatus" placeholder="全部状态" clearable @change="fetchTickets">
              <el-option
                v-for="opt in [
                  { value: 'OPEN', label: '⏳ 待处理' },
                  { value: 'IN_PROGRESS', label: '🔄 处理中' },
                  { value: 'RESOLVED', label: '✅ 已解决' },
                  { value: 'CLOSED', label: '🔒 已关闭' }
                ]"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>

          <div class="filter-group">
            <label>优先级</label>
            <el-select v-model="filterPriority" placeholder="全部优先级" clearable @change="fetchTickets">
              <el-option
                v-for="opt in [
                  { value: 'LOW', label: '🟢 低' },
                  { value: 'MEDIUM', label: '🟡 中' },
                  { value: 'HIGH', label: '🟠 高' },
                  { value: 'URGENT', label: '🔴 紧急' }
                ]"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>

          <div class="filter-group">
            <label>分类</label>
            <el-select v-model="filterCategory" placeholder="全部分类" clearable @change="fetchTickets">
              <el-option label="IT Support" value="IT Support" />
              <el-option label="Finance" value="Finance" />
              <el-option label="Warehouse" value="Warehouse" />
              <el-option label="Procurement" value="Procurement" />
              <el-option label="Sales" value="Sales" />
              <el-option label="HR" value="HR" />
              <el-option label="Other" value="Other" />
            </el-select>
          </div>

          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="fetchTickets">查询</el-button>
            <el-button :icon="Close" @click="resetFilters">重置</el-button>
          </div>
        </div>
      </section>

      <!-- Ticket List -->
      <section class="ticket-list-panel glass">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Document /></el-icon>
            <span>工单列表</span>
            <el-tag v-if="total > 0" type="info">{{ total }} 条记录</el-tag>
          </div>
        </div>

        <div class="ticket-table-wrap">
          <el-table
            :data="tickets"
            v-loading="loading"
            style="width: 100%"
            @row-click="openViewDialog"
            :row-class-name="ticketRowClassName"
          >
            <el-table-column prop="id" label="ID" width="70" align="center">
              <template #default="{ row }">
                <span class="ticket-id">#{{ row.id }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="title" label="标题" min-width="220">
              <template #default="{ row }">
                <div class="ticket-title">
                  <span class="priority-dot" :title="row.priority">{{ getPriorityIcon(row.priority) }}</span>
                  <span>{{ row.title }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small" effect="light">
                  {{ getStatusIcon(row.status) }} {{ getStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="priority" label="优先级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small" effect="dark">
                  {{ getPriorityLabel(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="category" label="分类" width="130" align="center">
              <template #default="{ row }">
                <span class="category-tag">{{ row.category }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="created_by" label="创建人" width="160" align="center">
              <template #default="{ row }">
                <div class="user-info">
                  <el-avatar :size="24">{{ row.created_by?.charAt(0)?.toUpperCase() || 'U' }}</el-avatar>
                  <span>{{ row.created_by }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="assigned_to" label="处理人" width="160" align="center">
              <template #default="{ row }">
                <div v-if="row.assigned_to" class="user-info">
                  <el-avatar :size="24" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                    {{ row.assigned_to?.charAt(0)?.toUpperCase() || 'A' }}
                  </el-avatar>
                  <span>{{ row.assigned_to }}</span>
                </div>
                <span v-else class="unassigned">未分配</span>
              </template>
            </el-table-column>

            <el-table-column label="创建时间" width="170" align="center">
              <template #default="{ row }">
                <div class="time-info">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ new Date(row.created_at).toLocaleString('zh-CN') }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="fetchTickets"
            @size-change="fetchTickets"
          />
        </div>
      </section>
    </main>
    </div>

    <!-- Create/View Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '✨ 创建新工单' : '📋 工单详情'"
      width="700px"
      :close-on-click-modal="false"
      class="ticket-dialog"
    >
      <div v-if="dialogMode === 'create'" class="create-form">
        <el-form :model="form" label-width="90px" label-position="top">
          <el-form-item label="工单标题" required>
            <el-input v-model="form.title" placeholder="请输入简明扼要的标题" />
          </el-form-item>

          <el-form-item label="工单分类" required>
            <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
              <el-option v-for="cat in ['IT Support', 'Finance', 'Warehouse', 'Procurement', 'Sales', 'HR', 'Other']" 
                :key="cat" :label="cat" :value="cat" />
            </el-select>
          </el-form-item>

          <el-form-item label="优先级" required>
            <el-select v-model="form.priority" placeholder="请选择优先级" style="width: 100%">
              <el-option label="🟢 低" value="LOW" />
              <el-option label="🟡 中" value="MEDIUM" />
              <el-option label="🟠 高" value="HIGH" />
              <el-option label="🔴 紧急" value="URGENT" />
            </el-select>
          </el-form-item>

          <el-form-item label="问题描述" required>
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="5"
              placeholder="请详细描述您遇到的问题..."
            />
          </el-form-item>

          <el-form-item label="创建人邮箱">
            <el-input v-model="form.created_by" placeholder="请输入您的工作邮箱" />
          </el-form-item>
        </el-form>
      </div>

      <div v-else-if="currentTicket" class="ticket-detail">
        <div class="detail-header">
          <div class="detail-title">
            <span class="priority-badge" :class="currentTicket.priority.toLowerCase()">
              {{ getPriorityIcon(currentTicket.priority) }} {{ getPriorityLabel(currentTicket.priority) }}
            </span>
            <h2>{{ currentTicket.title }}</h2>
          </div>
          <el-tag :type="getStatusType(currentTicket.status)" size="large">
            {{ getStatusIcon(currentTicket.status) }} {{ getStatusLabel(currentTicket.status) }}
          </el-tag>
        </div>

        <el-descriptions :column="2" border class="detail-descriptions">
          <el-descriptions-item label="工单 ID">{{ currentTicket.id }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ currentTicket.category }}</el-descriptions-item>
          <el-descriptions-item label="创建人">
            <div class="user-badge">
              <el-avatar :size="28">{{ currentTicket.created_by?.charAt(0)?.toUpperCase() || 'U' }}</el-avatar>
              <span>{{ currentTicket.created_by }}</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="处理人">
            <div v-if="currentTicket.assigned_to" class="user-badge">
              <el-avatar :size="28" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                {{ currentTicket.assigned_to?.charAt(0)?.toUpperCase() || 'A' }}
              </el-avatar>
              <span>{{ currentTicket.assigned_to }}</span>
            </div>
            <span v-else class="unassigned">未分配</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            <div class="time-badge">
              <el-icon><Calendar /></el-icon>
              {{ new Date(currentTicket.created_at).toLocaleString('zh-CN') }}
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            <div class="time-badge">
              <el-icon><Clock /></el-icon>
              {{ new Date(currentTicket.updated_at).toLocaleString('zh-CN') }}
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h3>📝 问题描述</h3>
          <div class="description-content">{{ currentTicket.description || '暂无描述' }}</div>
        </div>

        <div class="ticket-actions">
          <el-button v-if="currentTicket.status === 'OPEN'" type="primary" @click="assignTicket(currentTicket.id, 'current_user')">
            <el-icon><User /></el-icon>
            分配给我
          </el-button>
          <el-button v-if="currentTicket.status !== 'CLOSED'" type="success" @click="closeTicket(currentTicket.id)">
            <el-icon><Check /></el-icon>
            关闭工单
          </el-button>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button v-if="dialogMode === 'create'" type="primary" @click="submitForm">
            立即创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.ticket-center-pro {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --success-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --info-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --glass-bg: rgba(255, 255, 255, 0.95);
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.15);
  
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  position: relative;
  overflow-x: hidden;
}

.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.top-nav {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  margin: 20px 20px 0;
  border-radius: 16px;
  box-shadow: var(--shadow-md);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.brand-text h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-text span {
  font-size: 12px;
  color: #718096;
  display: block;
}

.nav-center {
  flex: 1;
  max-width: 500px;
  margin: 0 40px;
}

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0aec0;
  z-index: 1;
}

.search-box :deep(.el-input__wrapper) {
  padding-left: 44px !important;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
}

.btn-create {
  background: var(--primary-gradient);
  border: none;
  padding: 12px 28px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.btn-create:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.stats-section {
  position: relative;
  padding: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.stat-card {
  border: none;
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

.stat-total::before { background: var(--primary-gradient); }
.stat-open::before { background: var(--warning-gradient); }
.stat-in-progress::before { background: var(--info-gradient); }
.stat-resolved::before { background: var(--success-gradient); }

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.icon-total { background: var(--primary-gradient); }
.icon-open { background: var(--warning-gradient); }
.icon-progress { background: var(--info-gradient); }
.icon-resolved { background: var(--success-gradient); }

.stat-body {
  margin-bottom: 16px;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 14px;
  color: #718096;
  margin-top: 4px;
}

.stat-progress {
  height: 4px;
}

.main-content {
  position: relative;
  z-index: 10;
  padding: 24px 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.filters-panel,
.ticket-list-panel {
  border-radius: 16px;
  box-shadow: var(--shadow-md);
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

.panel-body {
  padding: 20px 24px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 160px;
}

.filter-group label {
  font-size: 13px;
  font-weight: 500;
  color: #4a5568;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  margin-left: auto;
}

.ticket-table-wrap {
  padding: 0 24px 24px;
}

.ticket-id {
  font-weight: 600;
  color: #667eea;
}

.ticket-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.priority-dot {
  font-size: 14px;
}

.category-tag {
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unassigned {
  color: #a0aec0;
  font-style: italic;
}

.time-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #718096;
  font-size: 13px;
}

.pagination-wrap {
  padding: 16px 24px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #e2e8f0;
}

.ticket-row:hover {
  background: rgba(102, 126, 234, 0.04) !important;
  cursor: pointer;
}

.ticket-row.priority-urgent:hover {
  background: rgba(245, 87, 108, 0.08) !important;
}

.ticket-row.priority-high:hover {
  background: rgba(250, 147, 133, 0.08) !important;
}

.ticket-detail .detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e2e8f0;
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 13px;
  width: fit-content;
}

.priority-badge.urgent {
  background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
  color: white;
}

.priority-badge.high {
  background: linear-gradient(135deg, #fa9375 0%, #f5576c 100%);
  color: white;
}

.priority-badge.medium {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: white;
}

.priority-badge.low {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  color: white;
}

.detail-title h2 {
  margin: 0;
  font-size: 20px;
  color: #1a202c;
}

.detail-descriptions {
  margin-bottom: 24px;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #4a5568;
}

.detail-section h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #1a202c;
}

.description-content {
  padding: 16px;
  background: #f7fafc;
  border-radius: 8px;
  color: #4a5568;
  line-height: 1.6;
  white-space: pre-wrap;
}

.ticket-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.create-form,
.ticket-detail {
  padding: 8px 0;
}

/* Responsive */
@media (max-width: 768px) {
  .top-nav {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }
  
  .nav-center {
    width: 100%;
    margin: 0;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .panel-body {
    flex-direction: column;
  }
  
  .filter-actions {
    margin-left: 0;
    width: 100%;
  }
}

/* Page Content */
.page-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 20px 0;
}

/* Toolbar */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.search-box {
  flex: 1;
  max-width: 400px;
  position: relative;
}

.search-box .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  font-size: 18px;
  pointer-events: none;
}

.search-box :deep(.el-input__wrapper) {
  padding-left: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.btn-create {
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.btn-create:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
  }
  
  .search-box {
    max-width: 100%;
    width: 100%;
  }
  
  .btn-create {
    width: 100%;
  }
}
</style>