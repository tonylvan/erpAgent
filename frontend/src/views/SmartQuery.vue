<template>
  <div class="smart-query-pro">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- 主内容区 -->
    <div class="main-content-pro">
      <!-- 聊天区域 -->
      <div class="chat-section-pro">
        <!-- 消息容器 -->
        <div class="messages-container-pro" ref="messagesContainer">
          <!-- 欢迎状态 -->
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-card-pro">
              <div class="welcome-header">
                <div class="welcome-icon-pro">💬</div>
                <h2 class="welcome-title">GSD 智能问数助手</h2>
                <p class="welcome-subtitle">基于知识图谱的 ERP 数据智能查询</p>
              </div>

              <!-- 功能特性卡片 -->
              <div class="features-grid">
                <div class="feature-card">
                  <div class="feature-icon">📊</div>
                  <h3>数据查询</h3>
                  <p>销售/采购/库存/财务全链路数据</p>
                </div>
                <div class="feature-card">
                  <div class="feature-icon">📈</div>
                  <h3>趋势分析</h3>
                  <p>同比/环比/预测智能分析</p>
                </div>
                <div class="feature-card">
                  <div class="feature-icon">🔍</div>
                  <h3>深度洞察</h3>
                  <p>业务建议/风险预警/决策支持</p>
                </div>
                <div class="feature-card">
                  <div class="feature-icon">🤖</div>
                  <h3>AI 驱动</h3>
                  <p>大语言模型 + 知识图谱双引擎</p>
                </div>
              </div>

              <!-- 快捷问题 -->
              <div class="quick-questions-section">
                <p class="section-title">
                  <el-icon><Lightning /></el-icon>
                  快捷提问
                </p>
                <div class="question-chips">
                  <el-tag
                    v-for="(q, idx) in quickQuestions"
                    :key="idx"
                    class="question-chip-pro"
                    effect="plain"
                    round
                    @click="sendQuickQuestion(q)"
                  >
                    {{ q }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-else class="messages-list-pro">
            <transition-group name="message-fade">
              <div
                v-for="(msg, idx) in messages"
                :key="idx"
                class="message-item-pro"
                :class="[msg.role]"
              >
                <div class="message-avatar-pro">
                  <el-avatar :icon="msg.role === 'user' ? 'User' : 'Cpu'" :size="40" />
                </div>
                <div class="message-content-pro">
                  <div class="message-meta">
                    <span class="message-name">
                      {{ msg.role === 'user' ? '你' : 'AI 助手' }}
                    </span>
                    <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
                  </div>
                  <div class="message-bubble-pro">
                    <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
                    
                    <!-- 数据可视化 -->
                    <div v-if="msg.data" class="message-data">
                      <div v-if="msg.data.chart" class="chart-container">
                        <v-chart :option="msg.data.chart" autoresize />
                      </div>
                      <el-table v-if="msg.data.table" :data="msg.data.table" stripe size="small">
                        <el-table-column 
                          v-for="col in msg.data.table[0] ? Object.keys(msg.data.table[0]) : []" 
                          :key="col"
                          :prop="col"
                          :label="col"
                        />
                      </el-table>
                    </div>

                    <!-- 追问建议 -->
                    <div v-if="msg.suggestedQuestions && msg.suggestedQuestions.length > 0" class="suggested-section">
                      <p class="suggested-title">
                        <el-icon><QuestionFilled /></el-icon>
                        你可能还想问
                      </p>
                      <div class="suggested-chips">
                        <el-tag
                          v-for="(sq, sidx) in msg.suggestedQuestions"
                          :key="sidx"
                          class="suggested-chip-pro"
                          effect="plain"
                          round
                          size="small"
                          @click="sendQuickQuestion(sq)"
                        >
                          {{ sq }}
                        </el-tag>
                      </div>
                    </div>

                    <!-- 反馈按钮 -->
                    <div v-if="msg.role === 'assistant'" class="feedback-actions">
                      <el-button size="small" text :icon="Check" @click="handleFeedback(msg.id, 'up')" />
                      <el-button size="small" text :icon="Close" @click="handleFeedback(msg.id, 'down')" />
                      <el-button size="small" text :icon="CopyDocument" @click="copyMessage(msg.content)" />
                    </div>
                  </div>
                </div>
              </div>
            </transition-group>

            <!-- 加载状态 -->
            <div v-if="loading" class="loading-indicator">
              <div class="typing-bubble">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="loading-text">AI 正在思考中...</span>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-section-pro">
          <div class="input-wrapper-pro">
            <el-input
              v-model="queryInput"
              type="textarea"
              :rows="3"
              placeholder="请输入你的问题，例如：本周销售情况如何？支持自然语言提问..."
              :autosize="{ minRows: 2, maxRows: 6 }"
              @keydown.ctrl.enter="sendMessage"
            />
            <div class="input-actions">
              <div class="input-tips">
                <el-icon><InfoFilled /></el-icon>
                <span>按 Ctrl+Enter 快速发送</span>
              </div>
              <el-button 
                type="primary" 
                :icon="Promotion" 
                :loading="loading"
                @click="sendMessage"
                round
                size="large"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage } from 'element-plus'

// Storage key for message history
const STORAGE_KEY = 'smart-query-history'
const MAX_HISTORY = 50 // Keep last 50 messages
import {
  Bell,
  ChatDotRound,
  Connection,
  Star,
  Clock,
  Lightning,
  QuestionFilled,
  Check,
  Close,
  CopyDocument,
  Promotion,
  InfoFilled
} from '@element-plus/icons-vue'
import GlobalNav from '../components/GlobalNav.vue'

// ==================== State ====================

const router = useRouter()
const currentPage = ref<'alert' | 'query' | 'graph'>('query')
const messagesContainer = ref<HTMLElement | null>(null)

// Chat state
const queryInput = ref('')
const loading = ref(false)
const messages = ref<any[]>([])

// Quick questions
const quickQuestions = ref([
  '本周销售情况如何？',
  '库存预警商品有哪些？',
  '客户回款排行 Top10',
  '本月采购趋势分析'
])

// ==================== Methods ====================

function navigateTo(page: 'alert' | 'graph') {
  if (page === 'alert') {
    router.push('/')
  } else if (page === 'graph') {
    router.push('/graph')
  }
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function renderMarkdown(text: string): string {
  // Simple markdown rendering
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

async function sendMessage() {
  const content = queryInput.value.trim()
  if (!content || loading.value) return

  // Add user message
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content,
    timestamp: Date.now()
  })

  queryInput.value = ''
  loading.value = true
  saveMessages() // Save immediately after user message

  // Scroll to bottom
  await nextTick()
  scrollToBottom()

  // Store the message ID for potential later update
  const userMessageId = messages.value[messages.value.length - 1].id

  try {
    // Create AbortController for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30s timeout

    // Call backend API (non-blocking, user can navigate away)
    const response = await fetch('/api/v1/smart-query-v2/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: content
      }),
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    // Add AI response
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: data.answer || '查询完成',
      timestamp: Date.now(),
      data: data.chart_config ? { chart: data.chart_config } : 
            data.data_type === 'table' ? { table: data.data } : null,
      suggestedQuestions: data.follow_up || [
        '详细数据是多少？',
        '与上月对比如何？',
        '导出这个报告'
      ]
    })
  } catch (error: any) {
    // Only show error if still on this page
    if (error.name === 'AbortError') {
      ElMessage.warning('请求超时，请稍后重试')
    } else {
      ElMessage.error('查询失败，请稍后重试')
    }
    
    // Add error message to history
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，查询过程中出现错误。请稍后重试。',
      timestamp: Date.now(),
      isError: true
    })
  } finally {
    loading.value = false
    saveMessages() // Save after response
    await nextTick()
    scrollToBottom()
  }
}

function sendQuickQuestion(question: string) {
  queryInput.value = question
  sendMessage()
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleFeedback(messageId: number, type: 'up' | 'down') {
  ElMessage.success(type === 'up' ? '感谢点赞！' : '已收到反馈')
}

async function copyMessage(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// ==================== Storage Functions ====================

function saveMessages() {
  try {
    const data = {
      messages: messages.value.slice(-MAX_HISTORY),
      timestamp: Date.now()
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {
    console.warn('[SmartQuery] Failed to save messages:', e)
  }
}

function loadMessages() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      if (data.messages && Array.isArray(data.messages)) {
        messages.value = data.messages
        console.log('[SmartQuery] Restored', data.messages.length, 'messages from history')
      }
    }
  } catch (e) {
    console.warn('[SmartQuery] Failed to load messages:', e)
  }
}

function clearHistory() {
  messages.value = []
  localStorage.removeItem(STORAGE_KEY)
  ElMessage.success('历史记录已清空')
}

// ==================== Lifecycle ====================

onMounted(() => {
  document.title = '智能问数 Pro - GSD 平台'
  loadMessages()
  
  // Auto-scroll to bottom after restoring messages
  nextTick(() => {
    scrollToBottom()
  })
})

// Watch messages and auto-save
watch(messages, () => {
  saveMessages()
}, { deep: true })

// Allow navigation even during loading
onBeforeRouteLeave((to, from, next) => {
  // User can leave freely, messages are saved
  next()
})

// Cleanup on unmount
onUnmounted(() => {
  saveMessages()
})
</script>

<style scoped>
/* ==================== Variables ==================== */

.smart-query-pro {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --success-gradient: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  --warning-gradient: linear-gradient(135deg, #fa8c16 0%, #ffc53d 100%);
  --danger-gradient: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.16);
  --shadow-xl: 0 12px 48px rgba(0, 0, 0, 0.2);
  
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
  
  --transition-fast: 150ms ease;
  --transition-base: 300ms ease;
  --transition-slow: 500ms ease;

  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

/* ==================== Top Navigation ==================== */

.top-nav-pro {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px) saturate(180%);
  box-shadow: var(--shadow-md);
  z-index: 1000;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-text {
  font-size: 20px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-links {
  display: flex;
  gap: 12px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar {
  cursor: pointer;
  border: 2px solid transparent;
  transition: var(--transition-fast);
}

.user-avatar:hover {
  border-color: #667eea;
  transform: scale(1.05);
}

/* ==================== Main Content ==================== */

.main-content-pro {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 24px;
}

.chat-section-pro {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

/* ==================== Messages Container ==================== */

.messages-container-pro {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

.messages-container-pro::-webkit-scrollbar {
  width: 8px;
}

.messages-container-pro::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: var(--radius-full);
}

.messages-container-pro::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: var(--radius-full);
}

/* ==================== Welcome Section ==================== */

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.welcome-card-pro {
  max-width: 800px;
  width: 100%;
  padding: 40px;
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  text-align: center;
}

.welcome-header {
  margin-bottom: 40px;
}

.welcome-icon-pro {
  font-size: 64px;
  margin-bottom: 16px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
}

.welcome-subtitle {
  font-size: 16px;
  color: #64748b;
}

/* ==================== Features Grid ==================== */

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.feature-card {
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-radius: var(--radius-lg);
  border: 1px solid #e2e8f0;
  transition: var(--transition-base);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: #667eea;
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 13px;
  color: #64748b;
}

/* ==================== Quick Questions ==================== */

.quick-questions-section {
  text-align: left;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 16px;
}

.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.question-chip-pro {
  padding: 10px 20px;
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition-fast);
  border: 2px solid #e2e8f0 !important;
  background: white !important;
  color: #64748b !important;
}

.question-chip-pro:hover {
  border-color: #667eea !important;
  color: #667eea !important;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* ==================== Messages List ==================== */

.messages-list-pro {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.message-item-pro {
  display: flex;
  gap: 16px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item-pro.user {
  flex-direction: row-reverse;
}

.message-avatar-pro {
  flex-shrink: 0;
}

.message-content-pro {
  flex: 1;
  max-width: 70%;
}

.message-item-pro.user .message-content-pro {
  max-width: 70%;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.message-name {
  font-weight: 600;
  color: #0f172a;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
}

.message-bubble-pro {
  padding: 20px;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid #e2e8f0;
}

.message-item-pro.user .message-bubble-pro {
  background: var(--primary-gradient);
  color: white;
  border: none;
}

.message-item-pro.user .message-name,
.message-item-pro.user .message-time {
  color: rgba(255, 255, 255, 0.9);
}

.message-text {
  line-height: 1.8;
  font-size: 15px;
}

.message-text :deep(strong) {
  color: #667eea;
  font-weight: 600;
}

.message-item-pro.user .message-text :deep(strong) {
  color: white;
}

/* ==================== Suggested Questions ==================== */

.suggested-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.suggested-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 12px;
}

.suggested-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggested-chip-pro {
  cursor: pointer;
  transition: var(--transition-fast);
  border: 1px dashed #cbd5e1 !important;
  background: #f8fafc !important;
}

.suggested-chip-pro:hover {
  border-color: #667eea !important;
  background: #667eea !important;
  color: white !important;
}

/* ==================== Feedback Actions ==================== */

.feedback-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

/* ==================== Loading Indicator ==================== */

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
}

.typing-bubble {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.typing-bubble span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-bubble span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-bubble span:nth-child(3) {
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

.loading-text {
  font-size: 14px;
  color: #64748b;
}

/* ==================== Input Section ==================== */

.input-section-pro {
  padding: 24px;
  background: white;
  border-top: 1px solid #e2e8f0;
}

.input-wrapper-pro {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-wrapper-pro :deep(.el-textarea__inner) {
  border-radius: var(--radius-lg);
  resize: none;
  border: 2px solid #e2e8f0;
  transition: var(--transition-fast);
  font-size: 15px;
  line-height: 1.6;
}

.input-wrapper-pro :deep(.el-textarea__inner:hover) {
  border-color: #cbd5e1;
}

.input-wrapper-pro :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

/* ==================== Transitions ==================== */

.message-fade-enter-active,
.message-fade-leave-active {
  transition: all 0.3s ease;
}

.message-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* ==================== Responsive ==================== */

@media (max-width: 1024px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .message-content-pro {
    max-width: 85%;
  }
}

@media (max-width: 768px) {
  .top-nav-pro {
    padding: 12px 16px;
  }
  
  .nav-links {
    display: none;
  }
  
  .main-content-pro {
    padding: 12px;
  }
  
  .welcome-card-pro {
    padding: 24px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>
