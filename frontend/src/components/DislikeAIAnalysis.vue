<template>
  <el-dialog
    v-model="dialogVisible"
    title="🤖 AI 分析报告"
    width="800px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    destroy-on-close
  >
    <div class="ai-analysis-container">
      <!-- AI 分析报告 -->
      <div class="ai-report" v-if="analysisData.report">
        <h3>📊 AI 分析报告</h3>
        <div class="report-content" v-html="renderMarkdown(analysisData.report)"></div>
      </div>

      <!-- 优化建议 -->
      <div class="optimization-suggestions" v-if="analysisData.suggestions && analysisData.suggestions.length > 0">
        <h3>💡 优化建议 <span class="ai-tag">AI 生成</span></h3>
        <el-checkbox-group v-model="selectedOptimizations">
          <div 
            v-for="(suggestion, index) in analysisData.suggestions" 
            :key="index"
            class="suggestion-item"
          >
            <el-checkbox :label="suggestion">{{ suggestion }}</el-checkbox>
          </div>
        </el-checkbox-group>
      </div>

      <!-- 置信度评分 -->
      <div class="confidence-score" v-if="analysisData.confidence">
        <h3>🎯 置信度评分</h3>
        <el-progress 
          :percentage="analysisData.confidence * 100" 
          :color="getConfidenceColor(analysisData.confidence)"
          :format="formatConfidence"
        />
      </div>

      <!-- 用户补充意见 -->
      <div class="user-comment">
        <h3>📝 补充意见（可选）</h3>
        <el-input
          v-model="userComment"
          type="textarea"
          :rows="3"
          placeholder="请补充您的意见或建议..."
        />
      </div>

      <!-- 优化前后对比 -->
      <div class="comparison" v-if="analysisData.optimized_query || analysisData.expected_improvement">
        <h3>📈 优化前后对比</h3>
        <div class="comparison-grid">
          <div class="comparison-card before">
            <h4>❌ 优化前</h4>
            <div class="comparison-content">
              <div v-if="executionTime" class="metric">
                <span class="label">执行时间</span>
                <span class="value">{{ executionTime }}ms</span>
              </div>
              <div v-if="resultCount" class="metric">
                <span class="label">结果数量</span>
                <span class="value">{{ resultCount }}</span>
              </div>
            </div>
          </div>
          
          <div class="comparison-card after">
            <h4>✅ 优化后</h4>
            <div class="comparison-content">
              <div v-if="analysisData.expected_improvement" class="metric">
                <span class="label">预期提升</span>
                <span class="value highlight">{{ analysisData.expected_improvement }}</span>
              </div>
              <div class="metric">
                <span class="label">预估时间</span>
                <span class="value highlight">~{{ estimateOptimizedTime() }}ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button @click="handleReanalyze" :loading="isReanalyzing">
          🔄 重新分析
        </el-button>
        <el-button type="primary" @click="handleConfirm" :loading="isConfirming">
          ✅ 确认分析
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'

interface AnalysisData {
  report: string
  issues: string[]
  suggestions: string[]
  confidence: number
  optimized_query?: string
  expected_improvement?: string
}

interface Props {
  modelValue: boolean
  queryId?: number
  originalQuery?: string
  userComment?: string
  executionTime?: number
  resultCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  queryId: 0,
  originalQuery: '',
  userComment: '',
  executionTime: 0,
  resultCount: 0
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirmed', data: {
    queryId: number
    selectedOptimizations: string[]
    userComment: string
    analysisData: AnalysisData
  }): void
}>()

// 状态
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const analysisData = ref<AnalysisData>({
  report: '',
  issues: [],
  suggestions: [],
  confidence: 0
})

const selectedOptimizations = ref<string[]>([])
const userComment = ref('')
const isReanalyzing = ref(false)
const isConfirming = ref(false)

// Markdown 渲染
const renderMarkdown = (text: string) => {
  return marked(text)
}

// 置信度颜色
const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#67C23A' // 绿色
  if (confidence >= 0.6) return '#E6A23C' // 黄色
  return '#F56C6C' // 红色
}

// 置信度格式化
const formatConfidence = (percentage: number) => {
  return `${percentage.toFixed(0)}%`
}

// 预估优化后时间
const estimateOptimizedTime = () => {
  if (!props.executionTime || !analysisData.value.expected_improvement) {
    return props.executionTime
  }
  
  const improvement = parseFloat(analysisData.value.expected_improvement.replace('%', ''))
  if (improvement > 0) {
    return Math.round(props.executionTime * (1 - improvement / 100))
  }
  return props.executionTime
}

// 重新分析
const handleReanalyze = async () => {
  isReanalyzing.value = true
  
  try {
    // 调用后端 API 重新分析
    const response = await fetch(`/api/v1/query/feedback/${props.queryId}/reanalyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        original_query: props.originalQuery,
        user_comment: props.userComment
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      analysisData.value = result.analysis
    }
  } catch (error) {
    console.error('重新分析失败:', error)
  } finally {
    isReanalyzing.value = false
  }
}

// 确认分析
const handleConfirm = async () => {
  isConfirming.value = true
  
  try {
    emit('confirmed', {
      queryId: props.queryId || 0,
      selectedOptimizations: selectedOptimizations.value,
      userComment: userComment.value,
      analysisData: analysisData.value
    })
    
    dialogVisible.value = false
  } catch (error) {
    console.error('确认失败:', error)
  } finally {
    isConfirming.value = false
  }
}

// 取消
const handleCancel = () => {
  dialogVisible.value = false
}

// 监听对话框打开
watch(() => props.modelValue, async (newVal) => {
  if (newVal && props.queryId) {
    // 自动触发 AI 分析
    await handleReanalyze()
  }
})
</script>

<style scoped>
.ai-analysis-container {
  max-height: 600px;
  overflow-y: auto;
  padding: 10px;
}

.ai-report {
  margin-bottom: 20px;
}

.report-content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.optimization-suggestions {
  margin-bottom: 20px;
}

.ai-tag {
  background: #409EFF;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  margin-left: 8px;
}

.suggestion-item {
  padding: 8px 0;
  border-bottom: 1px solid #e4e7ed;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.confidence-score {
  margin-bottom: 20px;
}

.user-comment {
  margin-bottom: 20px;
}

.comparison {
  margin-bottom: 20px;
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.comparison-card {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.comparison-card.before {
  border: 2px solid #F56C6C;
}

.comparison-card.after {
  border: 2px solid #67C23A;
}

.comparison-content {
  margin-top: 10px;
}

.metric {
  margin: 10px 0;
}

.metric .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.metric .value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.metric .value.highlight {
  color: #67C23A;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
</style>
