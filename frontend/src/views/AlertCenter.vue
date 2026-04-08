<template>
  <div class="alert-center-v3">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- Alert Center Page -->
    <div v-if="currentPage === 'alert'" class="page-content">
      <!-- Statistics Cards -->
      <div class="stats-cards">
        <div class="stats-card critical-card" @click="showDetailModal('CRITICAL')">
          <div class="card-icon">🔴</div>
          <div class="card-value">{{ stats.critical }}</div>
          <div class="card-label">Critical</div>
        </div>
        <div class="stats-card warning-card" @click="showDetailModal('HIGH')">
          <div class="card-icon">🟠</div>
          <div class="card-value">{{ stats.high }}</div>
          <div class="card-label">High</div>
        </div>
        <div class="stats-card info-card" @click="showDetailModal('MEDIUM')">
          <div class="card-icon">🟡</div>
          <div class="card-value">{{ stats.medium }}</div>
          <div class="card-label">Medium</div>
        </div>
        <div class="stats-card success-card" @click="showDetailModal('LOW')">
          <div class="card-icon">✅</div>
          <div class="card-value">{{ stats.low }}</div>
          <div class="card-label">Processed</div>
        </div>
      </div>

      <!-- Filter Toolbar -->
      <div class="filter-toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="Search alerts..."
          :prefix-icon="Search"
          style="width: 300px"
          clearable
          @input="handleSearch"
        />
        <el-select
          v-model="levelFilter"
          placeholder="All Levels"
          multiple
          collapse-tags
          collapse-tags-tooltip
          style="width: 200px"
          @change="handleFilter"
        >
          <el-option label="Critical" value="CRITICAL" />
          <el-option label="High" value="HIGH" />
          <el-option label="Medium" value="MEDIUM" />
          <el-option label="Low" value="LOW" />
        </el-select>
        <el-select
          v-model="statusFilter"
          placeholder="All Status"
          multiple
          collapse-tags
          collapse-tags-tooltip
          style="width: 200px"
          @change="handleFilter"
        >
          <el-option label="Unread" value="UNREAD" />
          <el-option label="Read" value="READ" />
          <el-option label="Acknowledged" value="ACKNOWLEDGED" />
        </el-select>
        <el-button type="primary" @click="handleBatchAcknowledge" :disabled="selectedAlerts.length === 0">
          Batch Acknowledge
        </el-button>
      </div>

      <!-- Alert List Table -->
      <div class="table-container">
        <el-table
          :data="alertList"
          v-loading="loading"
          stripe
          border
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column label="Level" width="100">
            <template #default="{ row }">
              <el-tag :type="getLevelTagType(row.level)">
                {{ row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="Title" min-width="300" />
          <el-table-column prop="business_module" label="Module" width="150" />
          <el-table-column prop="status" label="Status" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="Time" width="180" />
          <el-table-column label="Actions" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">View</el-button>
              <el-button 
                size="small" 
                type="primary" 
                @click="acknowledgeAlert(row.id)"
                :disabled="row.status === 'ACKNOWLEDGED'"
              >
                Acknowledge
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <!-- Smart Query Page Placeholder -->
    <div v-else-if="currentPage === 'query'" class="page-placeholder">
      <el-empty description="Smart Query page - redirecting..." />
    </div>

    <!-- Knowledge Graph Page Placeholder -->
    <div v-else-if="currentPage === 'graph'" class="page-placeholder">
      <el-empty description="Knowledge Graph page - coming soon" />
    </div>

    <!-- Detail Modal -->
    <el-dialog
      v-model="detailModalVisible"
      :title="modalTitle"
      width="900px"
      destroy-on-close
    >
      <el-table :data="filteredAlerts" stripe border>
        <el-table-column prop="title" label="Title" min-width="300" />
        <el-table-column prop="level" label="Level" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="Status" width="120" />
        <el-table-column prop="business_module" label="Module" width="150" />
        <el-table-column prop="created_at" label="Time" width="180" />
        <el-table-column label="Actions" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">View</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="detailModalVisible = false">Close</el-button>
        <el-button type="primary" @click="exportDetails">Export CSV</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Bell, 
  Search, 
  Refresh, 
  Connection,
  Loading 
} from '@element-plus/icons-vue'
import GlobalNav from '../components/GlobalNav.vue'
import { api } from '../utils/api'

// ==================== Types ====================

interface Alert {
  id: number
  title: string
  level: string
  status: string
  created_at: string
  business_module: string
  description?: string
}

interface AlertStats {
  critical: number
  high: number
  medium: number
  low: number
  total: number
}

// ==================== State ====================

const router = useRouter()

// Page state
const currentPage = ref<'alert' | 'query' | 'graph'>('alert')
const loading = ref(false)

// Alert data
const stats = ref<AlertStats>({
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
  total: 0
})

const alertList = ref<Alert[]>([])
const selectedAlerts = ref<Alert[]>([])

// Filters
const searchQuery = ref('')
const levelFilter = ref<string[]>([])
const statusFilter = ref<string[]>([])

// Pagination
const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// Modal
const detailModalVisible = ref(false)
const modalTitle = ref('Alert Details')
const currentFilterSeverity = ref('')

// ==================== API Calls ====================

async function fetchAlertStats() {
  try {
    console.log('[AlertCenter] Fetching alert stats...')
    const data = await api.get('/alerts/stats')
    console.log('[AlertCenter] Stats received:', data)
    stats.value = data
  } catch (error: any) {
    console.error('[AlertCenter] Failed to fetch alert stats:', error)
    console.error('[AlertCenter] Error message:', error.message)
    // Show notification only if not network error
    if (error.message && !error.message.includes('undefined') && !error.message.includes('404')) {
      ElMessage.error('Failed to load alert statistics')
    }
  }
}

async function fetchAlerts() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (levelFilter.value.length > 0) {
      params.append('level', levelFilter.value.join(','))
    }
    if (statusFilter.value.length > 0) {
      params.append('status', statusFilter.value.join(','))
    }
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    params.append('page', pagination.value.page.toString())
    params.append('size', pagination.value.size.toString())

    console.log('[AlertCenter] Fetching alerts with params:', params.toString())
    const data = await api.get(`/alerts?${params.toString()}`)
    console.log('[AlertCenter] Alerts received:', data?.length ?? 0, 'items')
    // Ensure data is an array
    alertList.value = Array.isArray(data) ? data : []
    pagination.value.total = alertList.value.length
  } catch (error: any) {
    console.error('[AlertCenter] Failed to fetch alerts:', error)
    console.error('[AlertCenter] Error message:', error.message)
    // Ensure alertList is always an array
    alertList.value = []
    if (error.message && !error.message.includes('undefined') && !error.message.includes('404')) {
      ElMessage.error('Failed to load alerts')
    }
  } finally {
    loading.value = false
  }
}

// ==================== Handlers ====================

function switchPage(page: 'alert' | 'query' | 'graph') {
  currentPage.value = page
  
  if (page === 'query') {
    router.push('/smart-query')
  } else if (page === 'graph') {
    // Navigate to graph page
    ElMessage.info('Knowledge Graph page coming soon')
  }
}

function refreshData() {
  fetchAlertStats()
  fetchAlerts()
  ElMessage.success('Data refreshed')
}

function handleSearch() {
  pagination.value.page = 1
  fetchAlerts()
}

function handleFilter() {
  pagination.value.page = 1
  fetchAlerts()
}

function handlePageChange() {
  fetchAlerts()
}

function handleSelectionChange(selection: Alert[]) {
  selectedAlerts.value = selection
}

function showDetailModal(severity: string) {
  currentFilterSeverity.value = severity
  modalTitle.value = `${severity} Alerts`
  levelFilter.value = [severity]
  fetchAlerts()
  detailModalVisible.value = true
}

function viewDetail(alert: Alert) {
  ElMessageBox.alert(
    alert.description || 'No description available',
    `Alert: ${alert.title}`,
    {
      confirmButtonText: 'Close'
    }
  )
}

async function acknowledgeAlert(alertId: number) {
  try {
    const response = await fetch(`${API_BASE}/${alertId}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    const result = await response.json()
    
    if (result.success) {
      ElMessage.success('Alert acknowledged')
      fetchAlertStats()
      fetchAlerts()
    }
  } catch (error) {
    console.error('Failed to acknowledge alert:', error)
    ElMessage.error('Failed to acknowledge alert')
  }
}

async function handleBatchAcknowledge() {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('Please select alerts to acknowledge')
    return
  }

  try {
    const ids = selectedAlerts.value.map(a => a.id)
    const response = await fetch(`${API_BASE}/batch-acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    })
    const result = await response.json()
    
    if (result.success) {
      ElMessage.success(`Acknowledged ${result.acknowledged_count} alerts`)
      fetchAlertStats()
      fetchAlerts()
      selectedAlerts.value = []
    }
  } catch (error) {
    console.error('Failed to batch acknowledge:', error)
    ElMessage.error('Failed to batch acknowledge')
  }
}

function exportDetails() {
  ElMessage.info('Export functionality will be implemented in next iteration')
}

// ==================== Helpers ====================

function getLevelTagType(level: string): 'danger' | 'warning' | 'info' | 'success' | 'primary' {
  const map: Record<string, 'danger' | 'warning' | 'info' | 'success' | 'primary'> = {
    'CRITICAL': 'danger',
    'HIGH': 'warning',
    'MEDIUM': 'info',
    'LOW': 'success'
  }
  return map[level] || 'primary'
}

function getStatusTagType(status: string): 'info' | 'success' | 'warning' | 'primary' {
  const map: Record<string, 'info' | 'success' | 'warning' | 'primary'> = {
    'UNREAD': 'info',
    'READ': 'warning',
    'ACKNOWLEDGED': 'success'
  }
  return map[status] || 'primary'
}

const filteredAlerts = computed(() => {
  if (currentFilterSeverity.value) {
    return alertList.value.filter(a => a.level === currentFilterSeverity.value)
  }
  return alertList.value
})

// ==================== Lifecycle ====================

onMounted(() => {
  fetchAlertStats()
  fetchAlerts()
})
</script>

<style scoped>
.alert-center-v3 {
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
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: bold;
  color: #667eea;
}

.nav-links {
  display: flex;
  gap: 12px;
}

.nav-actions {
  display: flex;
  gap: 8px;
}

/* Page Content */
.page-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.page-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Statistics Cards */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stats-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.card-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.card-label {
  font-size: 14px;
  color: #666;
}

.critical-card .card-value { color: #ff4d4f; }
.warning-card .card-value { color: #fa8c16; }
.info-card .card-value { color: #fadb14; }
.success-card .card-value { color: #52c41a; }

/* Filter Toolbar */
.filter-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Table */
.table-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* ==================== Responsive Design ==================== */

/* Tablet (≤1024px) */
@media (max-width: 1024px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .filter-toolbar {
    flex-wrap: wrap;
  }
  
  .filter-toolbar .el-input {
    width: 100% !important;
  }
  
  .filter-toolbar .el-select {
    width: calc(50% - 8px) !important;
  }
}

/* Mobile (≤768px) */
@media (max-width: 768px) {
  /* Navigation */
  .top-nav {
    flex-direction: column;
    gap: 12px;
    padding: 12px;
  }
  
  .nav-brand {
    font-size: 18px;
  }
  
  .nav-links {
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }
  
  .nav-links .el-button {
    padding: 8px 12px;
    font-size: 14px;
  }
  
  /* Page Content */
  .page-content {
    padding: 12px;
  }
  
  /* Statistics Cards */
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .stats-card {
    padding: 16px;
  }
  
  .card-icon {
    font-size: 36px;
  }
  
  .card-value {
    font-size: 28px;
  }
  
  .card-label {
    font-size: 12px;
  }
  
  /* Filter Toolbar */
  .filter-toolbar {
    flex-direction: column;
    gap: 8px;
    padding: 12px;
  }
  
  .filter-toolbar .el-input,
  .filter-toolbar .el-select {
    width: 100% !important;
  }
  
  /* Table */
  .table-container {
    padding: 12px;
    overflow-x: auto;
  }
  
  /* Buttons */
  .el-button {
    padding: 10px 16px;
    min-height: 44px; /* Touch-friendly */
  }
}

/* Small Mobile (≤480px) */
@media (max-width: 480px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .nav-links {
    flex-direction: column;
    width: 100%;
  }
  
  .nav-links .el-button {
    width: 100%;
  }
}
</style>
