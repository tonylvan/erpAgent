<template>
  <div class="smart-query-page">
    <div class="page-header">
      <h1>📊 GSD 智能问数助手</h1>
      <div class="header-buttons">
        <el-button @click="goBack">
          🔙 返回图谱
        </el-button>
      </div>
    </div>

    <!-- 登录对话框 -->
    <el-dialog v-model="showLoginDialog" title="用户登录" width="400px">
      <el-form :model="loginForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" @keyup.enter="login" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLoginDialog = false">取消</el-button>
        <el-button type="primary" @click="login">登录</el-button>
      </template>
    </el-dialog>

    <div class="query-container">
      <!-- 左侧：输入和历史 -->
      <div class="left-panel">
        <el-card class="input-card">
          <template #header>
            <span>💬 输入问题</span>
          </template>
          <el-input
            v-model="queryText"
            type="textarea"
            :rows="4"
            placeholder="请输入你的问题，例如：查询本月销售趋势"
            @keyup.ctrl.enter="executeQuery"
          />
          <div class="button-row">
            <el-button 
              type="primary" 
              @click="executeQuery" 
              :loading="loading"
              size="large"
            >
              立即执行
            </el-button>
            <el-button @click="clearQuery" size="large">清空</el-button>
          </div>
        </el-card>

        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span>🕐 查询历史</span>
              <el-button type="danger" text size="small" @click="clearHistory">清空</el-button>
            </div>
          </template>
          <div class="history-list">
            <div
              v-for="(item, idx) in history"
              :key="idx"
              class="history-item"
              @click="loadHistory(item)"
            >
              <div class="history-query">{{ item.query }}</div>
              <div class="history-time">{{ item.time }}</div>
            </div>
            <div v-if="history.length === 0" class="empty-tip">暂无历史</div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：结果展示 -->
      <div class="right-panel">
        <ResultPanel
          :result="result"
          :loading="loading"
          :error="error"
          empty-message="点击「立即执行」后，此处展示分析过程与结论。将调用后端自然语言 → Cypher → Neo4j → 整理回答"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ResultPanel from '../components/ResultPanel.vue'

const emit = defineEmits(['close'])
const queryText = ref('')
const result = ref(null)
const loading = ref(false)
const error = ref('')
const history = ref([])
const authToken = ref(localStorage.getItem('auth_token') || '')
const isLoggedIn = ref(!!authToken.value)
const showLoginDialog = ref(false)
const loginForm = ref({
  username: '',
  password: ''
})

// 快速问题
const quickQuestions = [
  // 销售分析
  '查询本月销售趋势',
  '显示 Top 10 客户排行',
  '各产品类别销售额统计',
  '本周销售订单完成情况',
  
  // 采购分析
  '本月采购金额统计',
  '供应商交货及时率',
  '采购订单执行进度',
  '供应商排名分析',
  
  // 库存分析
  '库存预警商品有哪些',
  '呆滞库存分析',
  '库存周转率计算',
  
  // 财务分析
  '查询未付款的订单',
  '应收账款账龄分析',
  '应付账款汇总',
  '现金流状况分析',
  
  // 综合查询
  '本月经营概况',
  '各部门费用对比',
  '月度利润分析'
]

// 执行查询
async function executeQuery() {
  if (!queryText.value.trim()) {
    error.value = '请输入查询内容'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    // 构建请求头（包含 JWT Token）
    const headers = {
      'Content-Type': 'application/json',
    }
    
    if (authToken.value) {
      headers['Authorization'] = `Bearer ${authToken.value}`
    }

    // 调用后端智能问数 API
    const response = await fetch('http://localhost:8005/api/v1/smart-query-v40/query', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query: queryText.value,
        session_id: 'user-' + Date.now()
      })
    })
    
    // 处理 401 未授权
    if (response.status === 401) {
      isLoggedIn.value = false
      localStorage.removeItem('auth_token')
      authToken.value = ''
      throw new Error('认证已过期，请重新登录')
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    
    result.value = {
      process: data.process || [{ title: '查询执行', detail: '已完成' }],
      conclusion: data.answer || data.conclusion || '',
      cypher: data.cypher || null,
      records: data.records || null,
      meta: data.meta || {}
    }

    // 添加到历史
    addToHistory(queryText.value)
    
  } catch (e) {
    error.value = e instanceof Error ? e.message : '查询失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 添加到历史
function addToHistory(query) {
  const item = {
    query,
    time: new Date().toLocaleString('zh-CN'),
    timestamp: Date.now()
  }
  history.value.unshift(item)
  // 限制历史数量
  if (history.value.length > 20) {
    history.value.pop()
  }
  // 保存到 localStorage
  localStorage.setItem('smart-query-history', JSON.stringify(history.value))
}

// 加载历史
function loadHistory(item) {
  queryText.value = item.query
}

// 清空历史
function clearHistory() {
  history.value = []
  localStorage.removeItem('smart-query-history')
}

// 清空查询
function clearQuery() {
  queryText.value = ''
  result.value = null
  error.value = ''
}

// 用户登录
async function login() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  try {
    const response = await fetch('http://localhost:8005/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: loginForm.value.username,
        password: loginForm.value.password
      })
    })

    if (response.ok) {
      const data = await response.json()
      authToken.value = data.access_token || data.token
      isLoggedIn.value = true
      localStorage.setItem('auth_token', authToken.value)
      showLoginDialog.value = false
      ElMessage.success('登录成功')
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录失败：' + e.message)
  }
}

// 用户登出
function logout() {
  authToken.value = ''
  isLoggedIn.value = false
  localStorage.removeItem('auth_token')
  ElMessage.info('已退出登录')
}

// 返回主页
function goBack() {
  emit('close')
}

// 加载历史
onMounted(() => {
  const saved = localStorage.getItem('smart-query-history')
  if (saved) {
    try {
      history.value = JSON.parse(saved)
    } catch (e) {
      history.value = []
    }
  }
})
</script>

<style scoped>
.smart-query-page {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.page-header h1 {
  margin: 0;
  font-size: 26px;
  color: #333;
  font-weight: 600;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.query-container {
  display: flex;
  gap: 20px;
  height: calc(100vh - 140px);
}

.left-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-panel {
  flex: 1;
  min-width: 0;
}

.input-card, .history-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.input-card:hover, .history-card:hover {
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.button-row {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  justify-content: flex-end;
}

.button-row .el-button {
  min-width: 100px;
  font-weight: 500;
}

.history-list {
  max-height: 400px;
  overflow-y: auto;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.history-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.history-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 6px;
  margin-bottom: 4px;
}

.history-item:hover {
  background: linear-gradient(90deg, #667eea15 0%, #764ba215 100%);
  transform: translateX(4px);
}

.history-query {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
