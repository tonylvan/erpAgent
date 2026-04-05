<template>
  <div class="smart-query-v2">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="nav-left">
        <button class="nav-btn" @click="navigateTo('alert')">
          🚨 预警中心
        </button>
        <button class="nav-btn active">
          💬 智能问数
        </button>
        <button class="nav-btn" @click="navigateTo('graph')">
          🔍 返回图谱
        </button>
      </div>
      <div class="nav-right">
        <el-dropdown trigger="click">
          <button class="user-menu">
            <el-avatar :size="24" src="https://picsum.photos/40/40"></el-avatar>
            <span>Admin</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>查询历史</el-dropdown-item>
              <el-dropdown-item>收藏管理</el-dropdown-item>
              <el-dropdown-item divided>设置</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧聊天区 -->
      <div class="chat-section">
        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <!-- 欢迎状态 -->
          <div v-if="messages.length === 0" class="welcome-state">
            <div class="welcome-card">
              <div class="welcome-icon">💬</div>
              <h2>GSD 智能问数助手</h2>
              <p class="welcome-desc">基于知识图谱的 ERP 数据智能查询</p>
              
              <!-- 快捷问题 -->
              <div class="quick-questions">
                <p class="section-title">💡 试试问我</p>
                <div class="question-grid">
                  <button
                    v-for="(q, idx) in quickQuestions"
                    :key="idx"
                    class="question-chip"
                    @click="sendQuickQuestion(q)"
                  >
                    {{ q }}
                  </button>
                </div>
              </div>

              <!-- 功能特性 -->
              <div class="features">
                <div class="feature-item">
                  <div class="feature-icon">📊</div>
                  <div class="feature-text">
                    <div class="feature-title">数据查询</div>
                    <div class="feature-desc">销售/采购/库存/财务</div>
                  </div>
                </div>
                <div class="feature-item">
                  <div class="feature-icon">📈</div>
                  <div class="feature-text">
                    <div class="feature-title">趋势分析</div>
                    <div class="feature-desc">同比/环比/预测</div>
                  </div>
                </div>
                <div class="feature-item">
                  <div class="feature-icon">🔍</div>
                  <div class="feature-text">
                    <div class="feature-title">深度洞察</div>
                    <div class="feature-desc">业务建议/风险预警</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-else class="message-list">
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="message-wrapper"
              :class="[msg.role, { 'with-feedback': msg.role === 'assistant' }]"
            >
              <div class="message-bubble">
                <div class="message-header">
                  <span class="message-avatar">
                    {{ msg.role === 'user' ? '👤' : '🤖' }}
                  </span>
                  <span class="message-name">
                    {{ msg.role === 'user' ? '你' : 'GSD 助手' }}
                  </span>
                  <span class="message-time">{{ msg.time }}</span>
                </div>
                <div class="message-body">
                  <!-- 文本内容 -->
                  <div v-if="msg.type === 'text'" class="text-content" v-html="formatText(msg.content)"></div>
                  
                  <!-- 图表内容 -->
                  <div v-else-if="msg.type === 'chart'" class="chart-content">
                    <div :id="'chart-' + idx" class="echart-container"></div>
                  </div>
                  
                  <!-- 表格内容 -->
                  <div v-else-if="msg.type === 'table'" class="table-content">
                    <el-table :data="msg.data?.records || []" style="width: 100%" size="small">
                      <el-table-column
                        v-for="col in msg.data?.columns || []"
                        :key="col"
                        :prop="col"
                        :label="col"
                      />
                    </el-table>
                  </div>
                  
                  <!-- 统计卡片 -->
                  <div v-else-if="msg.type === 'stats'" class="stats-content">
                    <el-row :gutter="12">
                      <el-col :span="6" v-for="(stat, i) in msg.data?.stats || []" :key="i">
                        <el-card shadow="hover" class="stat-card">
                          <div class="stat-label">{{ stat.label }}</div>
                          <div class="stat-value">{{ stat.value }}</div>
                          <div v-if="stat.trend" :class="['stat-trend', stat.trend > 0 ? 'up' : 'down']">
                            {{ stat.trend > 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}%
                          </div>
                        </el-card>
                      </el-col>
                    </el-row>
                  </div>
                </div>
                
                <!-- 反馈按钮 -->
                <div v-if="msg.role === 'assistant' && !msg.feedback" class="feedback-actions">
                  <el-button size="small" text @click="addFeedback(idx, 'like')">
                    👍 有用
                  </el-button>
                  <el-button size="small" text @click="addFeedback(idx, 'dislike')">
                    👎 改进
                  </el-button>
                </div>
                
                <!-- 追问建议 -->
                <div v-if="msg.suggested_questions?.length" class="suggested-questions">
                  <p class="suggested-title">💡 你可能还想问</p>
                  <div class="suggested-chips">
                    <button
                      v-for="q in msg.suggested_questions"
                      :key="q"
                      class="suggested-chip"
                      @click="sendQuickQuestion(q)"
                    >
                      {{ q }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-state">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
            <span class="loading-text">GSD 正在思考...</span>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-section">
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="输入你的问题，例如：查询最近 10 笔付款单..."
              @keydown.enter.exact="handleEnter"
              :disabled="isLoading"
              resize="none"
              class="query-input"
            />
            <el-button
              type="primary"
              size="large"
              :loading="isLoading"
              @click="sendMessage"
              class="send-btn"
              :icon="isLoading ? 'Loading' : 'Promotion'"
            >
              {{ isLoading ? '思考中...' : '发送' }}
            </el-button>
          </div>
          <div class="input-hint">
            <span>💡 按 Enter 发送，Shift+Enter 换行</span>
            <span>📊 支持自然语言查询 ERP 数据</span>
          </div>
        </div>
      </div>

      <!-- 右侧边栏 -->
      <aside class="sidebar-section">
        <!-- 查询历史 -->
        <el-card class="sidebar-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🕐 查询历史</span>
              <el-button text size="small" @click="clearHistory">
                清空
              </el-button>
            </div>
          </template>
          <div class="history-list">
            <div
              v-for="(item, idx) in queryHistory"
              :key="idx"
              class="history-item"
              @click="loadHistory(item)"
            >
              <div class="history-icon">💬</div>
              <div class="history-content">
                <div class="history-query">{{ item.query }}</div>
                <div class="history-time">{{ item.time }}</div>
              </div>
            </div>
            <div v-if="queryHistory.length === 0" class="empty-state">
              <p>暂无查询历史</p>
            </div>
          </div>
        </el-card>

        <!-- 收藏管理 -->
        <el-card class="sidebar-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>⭐ 收藏查询</span>
              <el-button text size="small">
                管理
              </el-button>
            </div>
          </template>
          <div class="favorites-list">
            <div
              v-for="(item, idx) in favorites"
              :key="idx"
              class="favorite-item"
              @click="loadFavorite(item)"
            >
              <div class="favorite-icon">⭐</div>
              <div class="favorite-query">{{ item.query }}</div>
            </div>
            <div v-if="favorites.length === 0" class="empty-state">
              <p>暂无收藏</p>
            </div>
          </div>
        </el-card>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const router = useRouter()

// 响应式数据
const inputMessage = ref('')
const isLoading = ref(false)
const messages = reactive<any[]>([])
const messagesContainer = ref(null)
const queryHistory = reactive<any[]>([])
const favorites = reactive<any[]>([])

// 快捷问题
const quickQuestions = [
  '查询最近 10 笔付款单',
  '本月销售排行 Top 10',
  '库存预警商品有哪些',
  '供应商付款趋势分析',
  '应收账款逾期客户列表',
  '采购订单执行情况分析'
]

// 导航
function navigateTo(page: string) {
  if (page === 'alert') {
    // 跳转到预警中心页面
    router.push('/')
  } else if (page === 'graph') {
    // 跳转到知识图谱页面
    router.push('/graph')
  }
}

// 发送消息
async function sendMessage() {
  const content = inputMessage.value.trim()
  if (!content || isLoading.value) return

  // 添加用户消息
  messages.push({
    role: 'user',
    type: 'text',
    content: content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    // 调用后端 API
    const response = await fetch('/api/v1/smart-query-v40/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: content,
        session_id: getSessionId()
      })
    })

    if (!response.ok) throw new Error(`API 错误：${response.status}`)

    const data = await response.json()

    // 添加机器人回复
    messages.push({
      role: 'assistant',
      type: data.data_type || 'text',
      content: data.answer,
      data: data.data,
      suggested_questions: data.suggested_questions,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })

    // 渲染图表
    if (data.data_type === 'chart' && data.data?.chart) {
      await nextTick()
      renderChart(data.data.chart)
    }

    // 添加到历史
    queryHistory.unshift({
      query: content,
      time: new Date().toLocaleString('zh-CN')
    })

  } catch (error: any) {
    messages.push({
      role: 'assistant',
      type: 'text',
      content: `❌ 查询失败：${error.message}`,
      error: true,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
    ElMessage.error('查询失败，请稍后重试')
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 发送快捷问题
function sendQuickQuestion(question: string) {
  inputMessage.value = question
  sendMessage()
}

// 处理回车
function handleEnter(e: KeyboardEvent) {
  if (!e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 格式化文本
function formatText(text: string) {
  if (!text) return ''
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
  text = text.replace(/^- (.*$)/gm, '<li>$1</li>')
  return text
}

// 渲染图表
function renderChart(chartData: any) {
  const chartIndex = messages.length - 1
  const chartEl = document.getElementById(`chart-${chartIndex}`)
  if (!chartEl) return

  const chart = echarts.init(chartEl)
  chart.setOption({
    title: { text: chartData.title || '数据图表', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: chartData.xAxis?.data || [] },
    yAxis: { type: 'value' },
    series: chartData.series || []
  })
}

// 添加反馈
function addFeedback(index: number, type: 'like' | 'dislike') {
  messages[index].feedback = type
  ElMessage.success(type === 'like' ? '感谢反馈！' : '我们会改进的！')
}

// 获取 Session ID
function getSessionId() {
  let sessionId = localStorage.getItem('smart_query_session')
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('smart_query_session', sessionId)
  }
  return sessionId
}

// 清空历史
function clearHistory() {
  queryHistory.splice(0)
  ElMessage.success('已清空查询历史')
}

// 加载历史
function loadHistory(item: any) {
  inputMessage.value = item.query
  sendMessage()
}

// 加载收藏
function loadFavorite(item: any) {
  inputMessage.value = item.query
  sendMessage()
}

onMounted(() => {
  console.log('SmartQuery v2 已挂载')
})
</script>

<style scoped>
/* 容器 */
.smart-query-v2 {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部导航 */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.nav-left {
  display: flex;
  gap: 8px;
}

.nav-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #f0f0f0;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: #e0e0e0;
}

.nav-btn.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 8px;
}

.user-menu:hover {
  background: #f0f0f0;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

/* 聊天区 */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

/* 欢迎状态 */
.welcome-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.welcome-card {
  max-width: 600px;
  text-align: center;
  padding: 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-card h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #333;
}

.welcome-desc {
  color: #666;
  margin-bottom: 32px;
}

/* 快捷问题 */
.section-title {
  text-align: left;
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
}

.question-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 32px;
}

.question-chip {
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background: white;
  color: #667eea;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  font-size: 14px;
}

.question-chip:hover {
  border-color: #667eea;
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 功能特性 */
.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
}

.feature-icon {
  font-size: 32px;
}

.feature-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.feature-desc {
  font-size: 12px;
  color: #666;
}

/* 消息列表 */
.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-wrapper {
  display: flex;
  gap: 12px;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-bubble {
  max-width: 70%;
  padding: 16px 20px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-wrapper.user .message-bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 16px 16px 0 16px;
}

.message-wrapper.assistant .message-bubble {
  border-radius: 16px 16px 16px 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #999;
}

.message-avatar {
  font-size: 16px;
}

.message-name {
  font-weight: 600;
}

.message-time {
  margin-left: auto;
}

.message-body {
  line-height: 1.6;
}

/* 反馈按钮 */
.feedback-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

/* 追问建议 */
.suggested-questions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.suggested-title {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.suggested-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggested-chip {
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 16px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.suggested-chip:hover {
  background: #667eea;
  color: white;
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* 输入区 */
.input-section {
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.query-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  resize: none;
}

.send-btn {
  min-width: 100px;
  border-radius: 12px;
}

.input-hint {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

/* 侧边栏 */
.sidebar-section {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-list,
.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.history-item,
.favorite-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover,
.favorite-item:hover {
  background: #f5f5f5;
}

.history-icon,
.favorite-icon {
  font-size: 20px;
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-query {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #999;
  font-size: 14px;
}

/* 图表内容 */
.chart-content {
  margin-top: 16px;
  height: 300px;
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.echart-container {
  width: 100%;
  height: 100%;
}

/* 统计卡片 */
.stats-content {
  margin-top: 16px;
}

.stat-card {
  text-align: center;
  padding: 16px;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
}

.stat-trend.up {
  color: #f56c6c;
}

.stat-trend.down {
  color: #67c23a;
}
</style>
