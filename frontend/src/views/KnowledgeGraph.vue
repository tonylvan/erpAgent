<template>
  <div class="knowledge-graph temporal-graph-container">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- 顶部控制栏 - UI-UX Pro 设计 -->
    <div class="graph-control-bar">
      <div class="control-bar-left">
        <h1 class="graph-title">
          <span class="title-icon">🕸️</span>
          <span class="title-text">时序知识图谱</span>
        </h1>
      </div>
      
      <div class="control-bar-center">
        <!-- 视图切换按钮组 -->
        <el-button-group class="view-switch-buttons">
          <el-button :type="graphViewMode === 'timeline' ? 'primary' : 'default'" @click="graphViewMode = 'timeline'">
            <span class="view-icon">🕒</span> 时间线
          </el-button>
          <el-button :type="graphViewMode === 'force' ? 'primary' : 'default'" @click="graphViewMode = 'force'">
            <span class="view-icon">🔵</span> 力导向图
          </el-button>
          <el-button :type="graphViewMode === 'sankey' ? 'primary' : 'default'" @click="graphViewMode = 'sankey'">
            <span class="view-icon">📊</span> 桑基图
          </el-button>
        </el-button-group>
      </div>
      
      <div class="control-bar-right">
        <el-button :icon="Refresh" @click="loadGraphData" circle title="刷新数据" />
        <el-button :type="isAnimating ? 'danger' : 'default'" @click="toggleAnimation" circle title="播放/暂停时间轴">
          {{ isAnimating ? '⏸' : '▶️' }}
        </el-button>
        <el-dropdown trigger="click">
          <el-button :icon="Setting" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="resetTimeline">重置时间轴</el-dropdown-item>
              <el-dropdown-item @click="exportGraph">导出图谱</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧面板 - 时间轴控制器 + 本体对象 -->
      <aside class="ontology-panel graph-sidebar">
        <!-- 时间轴控制器 - UI-UX Pro -->
        <el-card class="panel-card temporal-control-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">⏰ 时间轴控制器</span>
            </div>
          </template>

          <div class="timeline-control">
            <!-- 时间滑块 -->
            <el-slider
              v-model="currentTimeIndex"
              :min="0"
              :max="Math.max(timePoints.length - 1, 0)"
              :format-tooltip="formatTimePoint"
              :marks="timeMarks"
              @change="onTimeChange"
              class="time-slider"
            />
            
            <!-- 当前时间显示 -->
            <div class="current-time-display">
              <span class="time-label">当前时间:</span>
              <span class="time-value">{{ currentTimeDisplay }}</span>
            </div>
            
            <!-- 时间轴控制按钮 -->
            <div class="timeline-buttons">
              <el-button size="small" @click="prevTimePoint">⏮ 上一个</el-button>
              <el-button size="small" type="primary" @click="toggleAnimation">
                {{ isAnimating ? '⏸ 暂停' : '▶️ 播放' }}
              </el-button>
              <el-button size="small" @click="nextTimePoint">下一个 ⏭</el-button>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">📚 本体对象</span>
              <el-button text size="small" @click="toggleOntology">
                {{ ontologyExpanded ? '收起' : '展开' }}
              </el-button>
            </div>
          </template>

          <div v-show="ontologyExpanded" class="ontology-list">
            <div
              v-for="(type, idx) in ontologyTypes"
              :key="idx"
              class="ontology-item"
              :class="{ active: selectedType === type.name }"
              @click="selectType(type)"
            >
              <span class="ontology-icon">{{ type.icon }}</span>
              <span class="ontology-name">{{ type.label }}</span>
              <el-badge :value="type.count" size="small" class="ontology-count" />
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">🔍 快速筛选</span>
              <el-button text size="small" @click="resetFilters">
                重置
              </el-button>
            </div>
          </template>

          <div class="filter-list">
            <el-checkbox-group v-model="selectedFilters">
              <el-checkbox
                v-for="(filter, idx) in filters"
                :key="idx"
                :label="filter.value"
              >
                {{ filter.label }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </el-card>

        <!-- 时间轴控制器 (时序模式显示) -->
        <el-card v-if="viewMode === 'timeline'" class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>⏰ 时间轴</span>
              <el-tag size="small" type="success">{{ timePoints.length }} 个时间点</el-tag>
            </div>
          </template>

          <div class="timeline-controller">
            <div class="current-time-display">
              <el-tag type="primary" size="large">
                {{ timePoints[currentTimeIndex]?.label || '选择时间点' }}
              </el-tag>
              <div class="event-count">{{ timePoints[currentTimeIndex]?.eventCount || 0 }} 个事件</div>
            </div>

            <el-slider
              v-model="currentTimeIndex"
              :min="0"
              :max="Math.max(0, timePoints.length - 1)"
              :marks="timeMarks"
              :format-tooltip="formatTimePoint"
              @change="onTimeChange"
              :disabled="timePoints.length === 0"
            />

            <div class="timeline-actions">
              <el-button 
                size="small" 
                :icon="Play" 
                :type="isAnimating ? 'success' : 'primary'"
                @click="toggleAnimation"
                :disabled="timePoints.length === 0"
              >
                {{ isAnimating ? '暂停' : '播放' }}
              </el-button>
              <el-button 
                size="small" 
                :icon="Refresh" 
                @click="resetTimeline"
                :disabled="timePoints.length === 0"
              >
                重置
              </el-button>
            </div>
          </div>
        </el-card>
      </aside>

      <!-- 中央可视化区 -->
      <div class="canvas-section graph-main-view">
        <!-- 工具栏 - 仅力导向图模式显示 -->
        <div v-show="graphViewMode === 'force'" class="canvas-toolbar">
          <div class="toolbar-left">
            <!-- 视图切换 -->
            <el-button-group class="view-mode-buttons">
              <el-button 
                size="small"
                :type="viewMode === 'timeline' ? 'primary' : 'default'"
                @click="switchViewMode('timeline')"
                title="时间线视图"
              >🕒 时间线</el-button>
              <el-button 
                size="small"
                :type="viewMode === 'force' ? 'primary' : 'default'"
                @click="switchViewMode('force')"
                title="力导向图"
              >🗺️ 力导向</el-button>
              <el-button 
                size="small"
                :type="viewMode === 'sankey' ? 'primary' : 'default'"
                @click="switchViewMode('sankey')"
                title="桑基图"
              >📊 桑基图</el-button>
            </el-button-group>
            <el-divider direction="vertical" />
            <el-button-group>
              <el-button :icon="ZoomIn" @click="zoomIn" title="放大" />
              <el-button :icon="ZoomOut" @click="zoomOut" title="缩小" />
              <el-button :icon="Refresh" @click="resetView" title="重置视图" />
              <el-divider direction="vertical" />
              <el-button :icon="Grid" @click="toggleGrid" title="网格" />
              <el-button :icon="FullScreen" @click="toggleFullscreen" title="全屏" />
            </el-button-group>
          </div>
          
          <div class="toolbar-center">
            <span class="node-count-label">节点数量:</span>
            <el-button-group class="node-count-buttons">
              <el-button 
                size="small" 
                :type="nodeLimit === 100 ? 'primary' : 'default'"
                @click="setNodeLimit(100)"
              >100</el-button>
              <el-button 
                size="small" 
                :type="nodeLimit === 200 ? 'primary' : 'default'"
                @click="setNodeLimit(200)"
              >200</el-button>
              <el-button 
                size="small" 
                :type="nodeLimit === 300 ? 'primary' : 'default'"
                @click="setNodeLimit(300)"
              >300</el-button>
              <el-button 
                size="small" 
                :type="nodeLimit === 'all' ? 'primary' : 'default'"
                @click="setNodeLimit('all')"
              >ALL</el-button>
            </el-button-group>
          </div>

          <div class="toolbar-search">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索节点..."
              :prefix-icon="Search"
              clearable
              size="small"
              @input="handleSearch"
              @clear="clearSearch"
            />
          </div>
          
          <div class="toolbar-right">
            <div class="canvas-info">
              <span>节点:{{ nodes.length }}</span>
              <span>关系:{{ edges.length }}</span>
            </div>
          </div>
        </div>

        <!-- 时间线视图 - UI-UX Pro -->
        <div v-show="graphViewMode === 'timeline'" class="timeline-view">
          <!-- 时间轨道 -->
          <div class="time-track">
            <div class="track-line"></div>
            <div v-for="(point, idx) in timePoints" :key="idx" class="timeline-point" :class="{ active: currentTimeIndex === idx }" @click="currentTimeIndex = idx; onTimeChange(idx)">
              <div class="point-circle">○</div>
              <div class="point-label">{{ formatShortTime(point.time) }}</div>
            </div>
          </div>
          
          <!-- 事件时间线 -->
          <div class="events-timeline">
            <div class="timeline-header">
              <span class="header-icon">📅</span>
              <span class="header-title">事件时间线</span>
            </div>
            
            <div class="timeline-events">
              <div v-for="(event, idx) in currentEvents" :key="idx" class="event-item" :class="getEventClass(event.type)" @click="selectTimelineEvent(event)">
                <div class="event-border"></div>
                <div class="event-time">{{ formatEventTime(event.timestamp) }}</div>
                <div class="event-icon">{{ getEventIcon(event.type) }}</div>
                <div class="event-description">{{ event.description }}</div>
                <div class="event-tags">
                  <el-tag v-for="nodeId in event.nodes" :key="nodeId" size="small">{{ nodeId }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 力导向图视图 -->
        <div v-show="graphViewMode === 'force'" ref="graphContainer" class="graph-canvas"></div>
        
        <!-- 桑基图视图 - UI-UX Pro -->
        <div v-show="graphViewMode === 'sankey'" class="sankey-view">
          <div class="sankey-placeholder">
            <div class="sankey-header">
              <span class="sankey-icon">📊</span>
              <span class="sankey-title">资金流向桑基图</span>
            </div>
            <div class="sankey-content">
              <p class="sankey-desc">可视化展示业务流程中的资金流向关系</p>
              <el-button type="primary" @click="renderSankey">生成桑基图</el-button>
            </div>
          </div>
        </div>

        <!-- 节点详情面板 -->
        <div v-if="selectedNode" class="node-detail-panel">
          <div class="panel-header">
            <span class="panel-title">{{ selectedNode.name }}</span>
            <el-button text :icon="Close" @click="closeNodeDetail" />
          </div>
          <div class="panel-content">
            <div class="node-property">
              <span class="property-label">类型:</span>
              <span class="property-value">{{ selectedNode.type }}</span>
            </div>
            <div class="node-property">
              <span class="property-label">ID:</span>
              <span class="property-value">{{ selectedNode.id }}</span>
            </div>
            <div class="node-property">
              <span class="property-label">描述:</span>
              <span class="property-value">{{ selectedNode.description || '暂无描述' }}</span>
            </div>
            <div class="node-actions">
              <el-button size="small" type="primary" @click="editNode">
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteNode">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧面板 - 时序事件 + 图谱统计 -->
      <aside class="scenario-panel graph-sidebar">
        <!-- 时序事件列表 - UI-UX Pro -->
        <el-card class="panel-card temporal-events-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">⚡ 时序事件</span>
              <el-badge :value="graphEvents.length" type="primary" />
            </div>
          </template>

          <div class="temporal-events-list">
            <div v-for="(event, idx) in sortedEvents.slice(0, 20)" :key="idx" class="temporal-event-card" :class="getEventClass(event.type)" @click="selectEvent(event)">
              <div class="event-header">
                <span class="event-type-icon">{{ getEventIcon(event.type) }}</span>
                <span class="event-time-stamp">{{ formatEventTime(event.timestamp) }}</span>
              </div>
              <div class="event-body">
                <div class="event-description">{{ event.description }}</div>
              </div>
              <div class="event-footer">
                <el-tag v-for="nodeId in event.nodes.slice(0, 3)" :key="nodeId" size="small" class="event-node-tag">{{ nodeId }}</el-tag>
                <el-tag v-if="event.nodes.length > 3" size="small" type="info">+{{ event.nodes.length - 3 }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 图谱统计面板 - UI-UX Pro -->
        <el-card class="panel-card graph-stats-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">📊 图谱统计</span>
            </div>
          </template>

          <div class="graph-stats-grid">
            <div class="stat-item" @click="showNodesDetail">
              <div class="stat-value">{{ nodes.length }}</div>
              <div class="stat-label">节点</div>
            </div>
            <div class="stat-item" @click="showEdgesDetail">
              <div class="stat-value">{{ edges.length }}</div>
              <div class="stat-label">关系</div>
            </div>
            <div class="stat-item" @click="showEventsDetail">
              <div class="stat-value">{{ graphEvents.length }}</div>
              <div class="stat-label">事件</div>
            </div>
            <div class="stat-item" @click="showTimePointsDetail">
              <div class="stat-value">{{ timePoints.length }}</div>
              <div class="stat-label">时间点</div>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">💬 场景输入</span>
            </div>
          </template>

          <div class="scenario-input">
            <el-input
              v-model="scenarioText"
              type="textarea"
              :rows="4"
              placeholder="输入 P2P/O2C 等场景描述..."
            />
            <el-button type="primary" @click="executeScenario">
              🚀 执行场景分析
            </el-button>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📝 推荐场景</span>
            </div>
          </template>

          <div class="scenario-list">
            <div
              v-for="(scenario, idx) in scenarios"
              :key="idx"
              class="scenario-item"
              :class="{ active: selectedScenarioIndex === idx }"
              @click="selectedScenarioIndex = idx; loadScenario(scenario)"
            >
              <div class="scenario-icon">{{ scenario.icon }}</div>
              <div class="scenario-content">
                <div class="scenario-title">{{ scenario.title }}</div>
                <div class="scenario-desc">{{ scenario.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📊 分析结果</span>
            </div>
          </template>

          <div class="result-list">
            <div
              v-for="(result, idx) in results"
              :key="idx"
              class="result-item"
              :class="{ active: selectedResultIndex === idx }"
              @click="selectedResultIndex = idx; selectResult(result)"
            >
              <div class="result-icon">{{ result.icon }}</div>
              <div class="result-content">
                <div class="result-title">{{ result.title }}</div>
                <div class="result-desc">{{ result.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 时序事件列表 -->
        <el-card v-if="viewMode === 'timeline'" class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📅 时序事件</span>
              <el-tag size="small">{{ temporalEvents.length }} 个事件</el-tag>
            </div>
          </template>

          <div class="event-list">
            <div
              v-for="(event, idx) in temporalEvents.slice(0, 20)"
              :key="idx"
              class="event-item"
              @click="selectEvent(event)"
            >
              <div class="event-indicator" :style="{ backgroundColor: eventColors[event.type] }"></div>
              <div class="event-content">
                <div class="event-time">{{ new Date(event.timestamp).toLocaleString('zh-CN') }}</div>
                <div class="event-desc">{{ event.description }}</div>
                <div class="event-tags">
                  <el-tag size="small" effect="plain">{{ event.nodeType }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 图谱统计 -->
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📊 图谱统计</span>
            </div>
          </template>

          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ nodes.length }}</div>
              <div class="stat-label">节点</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ edges.length }}</div>
              <div class="stat-label">关系</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ temporalEvents.length }}</div>
              <div class="stat-label">事件</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ timePoints.length }}</div>
              <div class="stat-label">时间点</div>
            </div>
          </div>
        </el-card>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ZoomIn, ZoomOut, Refresh, Grid, FullScreen, Close, Search, Play, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as d3 from 'd3'
import GlobalNav from '../components/GlobalNav.vue'

const router = useRouter()

// Refs
const graphContainer = ref<HTMLElement | null>(null)
const selectedNode = ref<any>(null)
const scenarioText = ref('')
const ontologyExpanded = ref(true)
const selectedType = ref('')
const selectedFilters = ref([])
const selectedResultIndex = ref(-1)
const selectedScenarioIndex = ref(-1)

// Graph state
const nodes = ref<any[]>([])
const edges = ref<any[]>([])
let simulation: any = null
let svg: any = null
let g: any = null
let zoom: any = null
const containerWidth = ref(800)
const containerHeight = ref(600)
const showGrid = ref(false)
const zoomLevel = ref(1)

// 本体类型 - 根据 Neo4j 实际数据调整 (683个节点)
const ontologyTypes = reactive([
  { name: 'POLine', label: '采购行', icon: '📋', count: 200 },
  { name: 'Invoice', label: '发票', icon: '📄', count: 113 },
  { name: 'Payment', label: '付款', icon: '💳', count: 110 },
  { name: 'PriceList', label: '价格表', icon: '💰', count: 60 },
  { name: 'Supplier', label: '供应商', icon: '🏢', count: 52 },
  { name: 'PurchaseOrder', label: '采购单', icon: '📝', count: 34 },
  { name: 'Sale', label: '销售', icon: '💵', count: 25 },
  { name: 'Order', label: '订单', icon: '📦', count: 20 },
  { name: 'Customer', label: '客户', icon: '👥', count: 12 },
  { name: 'Event', label: '事件', icon: '📅', count: 11 },
  { name: 'Product', label: '产品', icon: '🛍️', count: 8 },
  { name: 'Time', label: '时间', icon: '⏰', count: 7 },
])

// 筛选器
const filters = reactive([
  { label: '高危预警', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '提示', value: 'info' },
  { label: '已处理', value: 'processed' },
])

// ========== Temporal Features ==========
// 视图模式: timeline(时间线), force(力导向图), sankey(桑基图)
const viewMode = ref<'timeline' | 'force' | 'sankey'>('force')
const graphViewMode = ref<'timeline' | 'force' | 'sankey'>('force') // UI-UX Pro 视图模式

// 时间轴数据
const currentTimeIndex = ref(0)
const timePoints = ref<any[]>([])

// 时序事件列表
const temporalEvents = ref<any[]>([])
const graphEvents = ref<any[]>([]) // UI-UX Pro 事件列表

// 动画播放状态
const isAnimating = ref(false)
let animationInterval: any = null

// 事件类型映射
const eventColors: Record<string, string> = {
  create: '#67c23a',   // 创建 - 绿色
  update: '#409eff',   // 更新 - 蓝色
  delete: '#f56c6c',   // 删除 - 红色
  risk: '#e6a23c',     // 风险 - 橙色
  transaction: '#909399' // 交易 - 灰色
}

// 切换视图模式
const switchViewMode = (mode: 'timeline' | 'force' | 'sankey') => {
  viewMode.value = mode
  ElMessage.success(`切换到${mode === 'timeline' ? '时间线' : mode === 'force' ? '力导向图' : '桑基图'}视图`)
  
  if (mode === 'timeline') {
    loadTemporalData()
  }
}

// 加载时序数据
const loadTemporalData = async () => {
  // 从 Neo4j 获取带时间戳的节点
  try {
    const response = await fetch('/api/v1/graph/?limit=500')
    const data = await response.json()
    
    if (data.success) {
      // 生成模拟事件数据
      const events: any[] = []
      const now = new Date()
      
      data.nodes.forEach((node: any, idx: number) => {
        // 为每个节点生成创建事件
        const createDate = new Date(now.getTime() - Math.random() * 7 * 24 * 60 * 60 * 1000)
        events.push({
          id: `evt_${idx}_create`,
          type: 'create',
          timestamp: createDate.toISOString(),
          description: `创建${node.type}节点: ${node.name}`,
          nodeId: node.id,
          nodeType: node.type,
          nodeName: node.name
        })
      })
      
      // 按时间排序
      events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      
      temporalEvents.value = events
      
      // 生成时间点
      const uniqueDates = [...new Set(events.map(e => e.timestamp.split('T')[0]))].sort().reverse()
      timePoints.value = uniqueDates.map((date, idx) => ({
        date,
        index: idx,
        label: new Date(date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
        eventCount: events.filter(e => e.timestamp.startsWith(date)).length
      }))
      
      console.log('[KnowledgeGraph] Loaded', events.length, 'temporal events')
    }
  } catch (error) {
    console.error('[KnowledgeGraph] Failed to load temporal data:', error)
  }
}

// 选择时间点
const selectTimePoint = (index: number) => {
  currentTimeIndex.value = index
  const point = timePoints.value[index]
  if (point) {
    ElMessage.info(`查看 ${point.label} 的事件 (${point.eventCount}个)`)
  }
}

// 选择事件
const selectEvent = (event: any) => {
  // 高亮对应节点
  if (event.nodeId) {
    highlightNodeById(event.nodeId)
  }
  ElMessage.info(event.description)
}

// 高亮指定ID的节点
const highlightNodeById = (nodeId: string) => {
  if (!g) return
  
  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.2)
  
  g.selectAll('.node-group text')
    .attr('opacity', 0.2)
  
  g.selectAll('.node-group')
    .filter((d: any) => d.id === nodeId)
    .select('circle')
    .attr('stroke', '#ff4d4f')
    .attr('stroke-width', 4)
    .attr('opacity', 1)
  
  g.selectAll('.node-group')
    .filter((d: any) => d.id === nodeId)
    .select('text')
    .attr('opacity', 1)
    .attr('font-weight', 'bold')
}

// ========== UI-UX Pro Temporal Functions ==========

// 时间轴动画控制
const toggleAnimation = () => {
  if (isAnimating.value) {
    stopAnimation()
  } else {
    startAnimation()
  }
}

const startAnimation = () => {
  isAnimating.value = true
  ElMessage.success('时间轴动画已开始')
  
  animationInterval = setInterval(() => {
    if (currentTimeIndex.value < timePoints.value.length - 1) {
      currentTimeIndex.value++
      onTimeChange(currentTimeIndex.value)
    } else {
      stopAnimation()
      ElMessage.info('时间轴已到达最后')
    }
  }, 2000)
}

const stopAnimation = () => {
  isAnimating.value = false
  if (animationInterval) {
    clearInterval(animationInterval)
    animationInterval = null
  }
  ElMessage.info('时间轴动画已暂停')
}

const resetTimeline = () => {
  currentTimeIndex.value = 0
  stopAnimation()
  onTimeChange(0)
  ElMessage.success('时间轴已重置')
}

const prevTimePoint = () => {
  if (currentTimeIndex.value > 0) {
    currentTimeIndex.value--
    onTimeChange(currentTimeIndex.value)
  }
}

const nextTimePoint = () => {
  if (currentTimeIndex.value < timePoints.value.length - 1) {
    currentTimeIndex.value++
    onTimeChange(currentTimeIndex.value)
  }
}

const onTimeChange = (index: number) => {
  console.log('[KnowledgeGraph] Time changed to:', index)
  // TODO: 根据时间筛选显示的节点和事件
}

// 时间格式化函数
const formatTimePoint = (index: number) => {
  const point = timePoints.value[index]
  if (!point) return '-'
  return new Date(point.date || point.time).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatEventTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatShortTime = (time: string) => {
  return new Date(time).toLocaleDateString('zh-CN', {
    month: 'numeric',
    day: 'numeric'
  })
}

// 事件图标和样式
const getEventIcon = (type: string) => {
  const icons: Record<string, string> = {
    create: '➕',
    update: '🔄',
    delete: '🗑️',
    risk: '⚠️',
    transaction: '💰'
  }
  return icons[type] || '📅'
}

const getEventClass = (type: string) => {
  return `event-type-${type}`
}

// Computed 属性
const currentTimeDisplay = computed(() => {
  return formatTimePoint(currentTimeIndex.value)
})

const timeMarks = computed(() => {
  const marks: Record<number, string> = {}
  if (timePoints.value.length === 0) return marks
  
  const step = Math.max(1, Math.floor(timePoints.value.length / 5))
  
  for (let idx = 0; idx < timePoints.value.length; idx++) {
    const point = timePoints.value[idx]
    if (idx % step === 0 || idx === timePoints.value.length - 1) {
      marks[idx] = formatShortTime(point.date || point.time)
    }
  }
  
  return marks
})

const sortedEvents = computed(() => {
  return [...graphEvents.value].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
})

const currentEvents = computed(() => {
  const point = timePoints.value[currentTimeIndex.value]
  if (!point) return []
  
  const targetDate = point.date || point.time
  return graphEvents.value.filter(e => e.timestamp.startsWith(targetDate))
})

// 统计详情显示
const showNodesDetail = () => ElMessage.info(`节点总数: ${nodes.value.length}`)
const showEdgesDetail = () => ElMessage.info(`关系总数: ${edges.value.length}`)
const showEventsDetail = () => ElMessage.info(`事件总数: ${graphEvents.value.length}`)
const showTimePointsDetail = () => ElMessage.info(`时间点总数: ${timePoints.value.length}`)

// 桑基图和导出功能
const renderSankey = () => {
  ElMessage.warning('桑基图功能开发中，敬请期待')
}

const exportGraph = () => {
  ElMessage.warning('导出功能开发中，敬请期待')
}

// 时间线事件选择
const selectTimelineEvent = (event: any) => {
  selectEvent(event)
}

// ========== End Temporal Features ==========

// Node count limit selection
const nodeLimit = ref<number | 'all'>(100) // Default: 100 nodes

// Set node limit and reload graph
const setNodeLimit = async (limit: number | 'all') => {
  nodeLimit.value = limit
  const actualLimit = limit === 'all' ? 1000 : limit
  console.log('[KnowledgeGraph] Setting node limit:', actualLimit)
  
  ElMessage.info(`正在加载 ${limit === 'all' ? '全部' : limit} 个节点...`)
  
  try {
    const response = await fetch(`/api/v1/graph/?limit=${actualLimit}`)
    const data = await response.json()
    
    if (data.success) {
      nodes.value = data.nodes
      edges.value = data.edges
      updateGraph()
      ElMessage.success(`已加载 ${data.nodes.length} 个节点, ${data.edges.length} 条关系`)
    } else {
      ElMessage.error('加载图谱数据失败')
    }
  } catch (error) {
    console.error('[KnowledgeGraph] Failed to load graph:', error)
    ElMessage.error('加载图谱数据失败')
  }
}

// ========== Search Functionality ==========
const searchKeyword = ref('')
const searchResults = ref<any[]>([])

// Handle search input
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    clearSearch()
    return
  }

  const keyword = searchKeyword.value.toLowerCase()
  
  // Search in all nodes
  const results = nodes.value.filter(n => 
    n.name?.toLowerCase().includes(keyword) ||
    n.type?.toLowerCase().includes(keyword) ||
    n.id?.toString().includes(keyword)
  )
  
  searchResults.value = results
  
  if (results.length > 0) {
    highlightSearchResults(results)
    ElMessage.success(`Found ${results.length} matching nodes`)
  } else {
    ElMessage.warning('No matching nodes found')
  }
}

// Highlight search results
const highlightSearchResults = (results: any[]) => {
  if (!g) return
  
  // Reset all nodes
  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.2)
  
  g.selectAll('.node-group text')
    .attr('opacity', 0.2)
  
  // Highlight matching nodes
  const matchIds = results.map(r => r.id)
  g.selectAll('.node-group')
    .filter((d: any) => matchIds.includes(d.id))
    .select('circle')
    .attr('stroke', '#1890ff')
    .attr('stroke-width', 4)
    .attr('opacity', 1)
  
  g.selectAll('.node-group')
    .filter((d: any) => matchIds.includes(d.id))
    .select('text')
    .attr('opacity', 1)
    .attr('font-weight', 'bold')
  
  // Center on first result
  if (results[0]) {
    centerOnNode(results[0])
  }
}

// Center view on a specific node
const centerOnNode = (node: any) => {
  if (!svg || !node.x || !node.y) return
  
  const transform = d3.zoomIdentity
    .translate(containerWidth.value / 2, containerHeight.value / 2)
    .scale(1.5)
    .translate(-node.x, -node.y)
  
  svg.transition().duration(750).call(zoom.transform as any, transform)
}

// Clear search
const clearSearch = () => {
  searchKeyword.value = ''
  searchResults.value = []
  
  // Restore all nodes
  if (g) {
    g.selectAll('.node-group circle')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', 1)
    
    g.selectAll('.node-group text')
      .attr('opacity', 1)
  }
}

// ========== End Search Functionality ==========

// ========== Expand Node Relations (Double-click) ==========
const expandedNodes = ref<Set<string>>(new Set())

// Expand node relations on double-click
const expandNodeRelations = async (node: any) => {
  if (!node || !node.id) return
  
  console.log('[KnowledgeGraph] Expanding relations for node:', node.id)
  
  // Check if already expanded
  if (expandedNodes.value.has(node.id)) {
    ElMessage.info('Node already expanded')
    return
  }
  
  try {
    // Fetch related nodes from API
    const response = await fetch(`/api/v1/graph/node/${node.id}/relations`)
    const data = await response.json()
    
    if (data.success && data.relatedNodes) {
      const newNodes = data.relatedNodes.filter(
        (n: any) => !nodes.value.some(existing => existing.id === n.id)
      )
      const newEdges = data.relatedEdges.filter(
        (e: any) => !edges.value.some(existing => existing.id === e.id)
      )
      
      if (newNodes.length > 0) {
        // Add new nodes and edges
        nodes.value = [...nodes.value, ...newNodes]
        edges.value = [...edges.value, ...newEdges]
        
        // Mark as expanded
        expandedNodes.value.add(node.id)
        
        // Update graph
        updateGraph()
        
        ElMessage.success(`Expanded ${newNodes.length} related nodes`)
      } else {
        ElMessage.info('All related nodes already shown')
        expandedNodes.value.add(node.id)
      }
    } else {
      // Fallback: highlight existing connected nodes
      highlightConnectedNodes(node)
      ElMessage.info('No new nodes to expand')
    }
  } catch (error) {
    console.error('[KnowledgeGraph] Failed to expand relations:', error)
    // Fallback: highlight existing connected nodes
    highlightConnectedNodes(node)
    ElMessage.warning('Failed to load related nodes, showing existing connections')
  }
}

// Highlight nodes connected to a specific node
const highlightConnectedNodes = (node: any) => {
  if (!g) return
  
  // Find connected nodes
  const connectedIds = new Set<string>()
  edges.value.forEach((e: any) => {
    if (e.source?.id === node.id || e.source === node.id) {
      connectedIds.add(e.target?.id || e.target)
    }
    if (e.target?.id === node.id || e.target === node.id) {
      connectedIds.add(e.source?.id || e.source)
    }
  })
  
  connectedIds.add(node.id)
  
  // Reset all nodes
  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.2)
  
  // Highlight connected nodes
  g.selectAll('.node-group')
    .filter((d: any) => connectedIds.has(d.id))
    .select('circle')
    .attr('stroke', '#52c41a')
    .attr('stroke-width', 4)
    .attr('opacity', 1)
  
  g.selectAll('.node-group')
    .filter((d: any) => connectedIds.has(d.id))
    .select('text')
    .attr('opacity', 1)
    .attr('font-weight', 'bold')
  
  // Highlight connected edges
  g.selectAll('line')
    .attr('opacity', 0.1)
  
  g.selectAll('line')
    .filter((d: any) => {
      const sourceId = d.source?.id || d.source
      const targetId = d.target?.id || d.target
      return sourceId === node.id || targetId === node.id
    })
    .attr('opacity', 1)
    .attr('stroke', '#52c41a')
    .attr('stroke-width', 3)
  
  ElMessage.success(`Found ${connectedIds.size - 1} connected nodes`)
}

// ========== End Expand Node Relations ==========

// 推荐场景
const scenarios = reactive([
  { icon: '🔄', title: 'P2P 流程', desc: '采购到付款全流程分析', type: 'p2p' },
  { icon: '💵', title: 'O2C 流程', desc: '订单到收款全流程分析', type: 'o2c' },
  { icon: '📊', title: '财务分析', desc: '财务健康度评估', type: 'finance' },
  { icon: '⚠️', title: '风险预警', desc: '企业风险识别', type: 'risk' },
])

// 分析结果
const results = reactive([
  { icon: '✅', title: '流程完整', desc: 'P2P 流程节点完整率 95%' },
  { icon: '⚠️', title: '发现异常', desc: '3 个节点存在数据异常' },
  { icon: '📈', title: '效率提升', desc: '流程优化可提升 15% 效率' },
])

// Node color mapping - 匹配 Neo4j 实际类型 (683个节点)
const nodeColors: Record<string, string> = {
  POLine: '#8c8c8c',        // 采购行 - 灰色
  Invoice: '#faad14',       // 发票 - 橙黄色
  Payment: '#13c2c2',       // 付款 - 青色
  PriceList: '#722ed1',     // 价格表 - 紫色
  Supplier: '#f5222d',      // 供应商 - 红色
  PurchaseOrder: '#1890ff', // 采购单 - 蓝色
  Sale: '#fa8c16',          // 销售 - 橙色
  Order: '#eb2f96',         // 订单 - 粉色
  Customer: '#667eea',      // 客户 - 靛蓝色
  Event: '#52c41a',         // 事件 - 绿色
  Product: '#a0d911',       // 产品 - 青绿色
  Time: '#bfbfbf',          // 时间 - 灰色
}

// Initialize D3.js force-directed graph
const initGraph = () => {
  if (!graphContainer.value) {
    console.error('[KnowledgeGraph] graphContainer is null!')
    ElMessage.error('图谱容器未找到')
    return
  }

  // Get container dimensions
  const container = graphContainer.value
  containerWidth.value = container.clientWidth || 800
  containerHeight.value = container.clientHeight || 600
  
  console.log('[KnowledgeGraph] Container size:', containerWidth.value, 'x', containerHeight.value)

  if (containerWidth.value === 0 || containerHeight.value === 0) {
    console.error('[KnowledgeGraph] Container size is 0!')
    ElMessage.error('图谱容器尺寸为0，请刷新页面')
    return
  }

  // Clear previous SVG
  d3.select(container).selectAll('*').remove()

  // Create SVG
  svg = d3
    .select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${containerWidth.value} ${containerHeight.value}`)
    .style('background', showGrid.value ? '#f0f0f0' : '#fafafa')

  console.log('[KnowledgeGraph] SVG created')

  // Add zoom behavior
  zoom = d3
    .zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event: any) => {
      if (g) {
        g.attr('transform', event.transform)
        zoomLevel.value = event.transform.k
      }
    })

  svg.call(zoom)
  console.log('[KnowledgeGraph] Zoom initialized')

  // Create group for graph elements
  g = svg.append('g')
  console.log('[KnowledgeGraph] Group g created')

  // Initialize simulation
  initSimulation()
  console.log('[KnowledgeGraph] Simulation initialized')
  
  // Mark as ready
  ElMessage.success('图谱初始化完成')
}

const initSimulation = () => {
  simulation = d3
    .forceSimulation()
    .force('link', d3.forceLink().id((d: any) => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(containerWidth.value / 2, containerHeight.value / 2))
    .force('collide', d3.forceCollide().radius(30))
}

const loadSampleData = () => {
  // Generate sample nodes
  nodes.value = Array.from({ length: 50 }, (_, i) => ({
    id: `node-${i}`,
    name: `节点 ${i}`,
    type: Object.keys(nodeColors)[i % 6],
    x: Math.random() * containerWidth.value,
    y: Math.random() * containerHeight.value,
    description: `这是节点 ${i} 的描述信息`,
  }))

  // Generate sample edges
  edges.value = Array.from({ length: 80 }, (_, i) => ({
    id: `edge-${i}`,
    source: `node-${Math.floor(Math.random() * 50)}`,
    target: `node-${Math.floor(Math.random() * 50)}`,
    type: 'related_to',
  }))

  updateGraph()
}

const updateGraph = () => {
  if (!g || !simulation) return

  // Update links
  const links = g
    .selectAll('line')
    .data(edges.value, (d: any) => d.id)
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', 1.5)

  // Update nodes
  const nodeGroups = g
    .selectAll('.node-group')
    .data(nodes.value, (d: any) => d.id)
    .join((enter: any) => {
      const g = enter.append('g').attr('class', 'node-group')

      // Add circle
      g.append('circle')
        .attr('r', 20)
        .attr('fill', (d: any) => nodeColors[d.type] || '#999')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', (event: any, d: any) => selectNode(d))
        .on('dblclick', (event: any, d: any) => expandNodeRelations(d))
        .call(
          d3
            .drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended)
        )

      // Add label
      g.append('text')
        .attr('dy', 35)
        .attr('text-anchor', 'middle')
        .attr('fill', '#333')
        .attr('font-size', '12px')
        .text((d: any) => d.name)

      return g
    })

  // Update positions
  nodeGroups.select('circle').attr('fill', (d: any) => nodeColors[d.type] || '#999')

  // Restart simulation
  simulation.nodes(nodes.value).on('tick', () => {
    links
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    nodeGroups.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })

  simulation.force('link').links(edges.value)
  simulation.alpha(1).restart()
}

// Drag handlers
const dragstarted = (event: any, d: any) => {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

const dragged = (event: any, d: any) => {
  d.fx = event.x
  d.fy = event.y
}

const dragended = (event: any, d: any) => {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

// Node selection
const selectNode = (node: any) => {
  selectedNode.value = node
}

const closeNodeDetail = () => {
  selectedNode.value = null
}

const editNode = () => {
  // Edit node logic
  console.log('Edit node:', selectedNode.value)
}

const deleteNode = () => {
  // Delete node logic
  if (selectedNode.value) {
    nodes.value = nodes.value.filter((n) => n.id !== selectedNode.value.id)
    edges.value = edges.value.filter(
      (e) => e.source.id !== selectedNode.value.id && e.target.id !== selectedNode.value.id
    )
    selectedNode.value = null
    updateGraph()
  }
}

// Zoom controls
const zoomIn = () => {
  console.log('[KnowledgeGraph] zoomIn called, svg:', !!svg, 'zoom:', !!zoom)
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.scaleBy, 1.5)
    ElMessage.success('放大')
  } else {
    ElMessage.warning('图谱未初始化，请刷新页面')
  }
}

const zoomOut = () => {
  console.log('[KnowledgeGraph] zoomOut called, svg:', !!svg, 'zoom:', !!zoom)
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.scaleBy, 0.7)
    ElMessage.success('缩小')
  } else {
    ElMessage.warning('图谱未初始化，请刷新页面')
  }
}

const resetView = () => {
  console.log('[KnowledgeGraph] resetView called, svg:', !!svg, 'zoom:', !!zoom)
  if (svg && zoom) {
    svg
      .transition()
      .duration(750)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(0, 0).scale(1)
      )
    ElMessage.success('视图已重置')
  } else {
    ElMessage.warning('图谱未初始化，请刷新页面')
  }
}

const toggleGrid = () => {
  showGrid.value = !showGrid.value
  if (svg) {
    svg.style('background', showGrid.value ? '#f0f0f0' : '#fafafa')
  }
}

const toggleFullscreen = () => {
  console.log('[KnowledgeGraph] toggleFullscreen called')
  if (graphContainer.value) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
      ElMessage.info('退出全屏')
    } else {
      graphContainer.value.requestFullscreen().then(() => {
        ElMessage.success('进入全屏模式')
      }).catch((err) => {
        console.error('[KnowledgeGraph] Fullscreen error:', err)
        ElMessage.error('无法进入全屏: ' + err.message)
      })
    }
  } else {
    ElMessage.warning('图谱容器未找到')
  }
}

// Ontology panel
const toggleOntology = () => {
  ontologyExpanded.value = !ontologyExpanded.value
}

const selectType = async (type: any) => {
  selectedType.value = type.name
  console.log('[KnowledgeGraph] Selected type:', type.name)

  // Check if we have nodes of this type
  const matchingNodes = nodes.value.filter(n => n.type === type.name)

  if (matchingNodes.length === 0) {
    // No nodes of this type, load from Neo4j
    console.log('[KnowledgeGraph] No nodes found, loading from Neo4j:', type.name)
    ElMessage.info(`正在从 Neo4j 加载 ${type.label} 数据...`)

    try {
      await loadNodesByType(type.name)
    } catch (error) {
      console.error('[KnowledgeGraph] Failed to load nodes:', error)
      ElMessage.error('加载节点失败')
    }
  } else {
    // Highlight existing nodes
    highlightNodesByType(type.name)
  }
}

// Highlight nodes by type
const highlightNodesByType = (nodeType: string) => {
  if (!g) {
    console.error('[KnowledgeGraph] SVG group g is not initialized')
    return
  }

  console.log('[KnowledgeGraph] Highlighting nodes of type:', nodeType)
  console.log('[KnowledgeGraph] Total nodes:', nodes.value.length)
  console.log('[KnowledgeGraph] Nodes by type:', nodes.value.reduce((acc, n) => {
    acc[n.type] = (acc[n.type] || 0) + 1
    return acc
  }, {} as Record<string, number>))

  // Find matching nodes
  const matchingNodes = nodes.value.filter(n => n.type === nodeType)
  console.log('[KnowledgeGraph] Matching nodes:', matchingNodes.length)

  if (matchingNodes.length === 0) {
    console.warn('[KnowledgeGraph] No nodes found for type:', nodeType)
    ElMessage.warning(`未找到 "${nodeType}" 类型的节点`)
    return
  }

  // Reset all nodes to normal state
  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.3)

  g.selectAll('.node-group text')
    .attr('opacity', 0.3)

  g.selectAll('line')
    .attr('opacity', 0.1)

  // Highlight matching nodes
  g.selectAll('.node-group')
    .filter((d: any) => d.type === nodeType)
    .select('circle')
    .attr('stroke', '#ff4d4f')
    .attr('stroke-width', 4)
    .attr('opacity', 1)

  g.selectAll('.node-group')
    .filter((d: any) => d.type === nodeType)
    .select('text')
    .attr('opacity', 1)
    .attr('font-weight', 'bold')

  // Highlight edges connected to matching nodes
  g.selectAll('line')
    .filter((d: any) => {
      const sourceType = d.source?.type || nodes.value.find(n => n.id === d.source)?.type
      const targetType = d.target?.type || nodes.value.find(n => n.id === d.target)?.type
      return sourceType === nodeType || targetType === nodeType
    })
    .attr('opacity', 0.8)
    .attr('stroke-width', 2.5)
    .attr('stroke', '#ff4d4f')

  // Center view on matching nodes
  if (matchingNodes.length > 0) {
    const avgX = matchingNodes.reduce((sum, n) => sum + (n.x || 0), 0) / matchingNodes.length
    const avgY = matchingNodes.reduce((sum, n) => sum + (n.y || 0), 0) / matchingNodes.length

    console.log('[KnowledgeGraph] Centering view on:', nodeType, 'avgX:', avgX, 'avgY:', avgY)

    const transform = d3.zoomIdentity
      .translate(containerWidth.value / 2, containerHeight.value / 2)
      .scale(1.2)
      .translate(-avgX, -avgY)

    if (svg) {
      console.log('[KnowledgeGraph] Applying zoom transition')
      svg.transition()
        .duration(750)
        .call(zoom.transform as any, transform)
        .on('end', () => {
          console.log('[KnowledgeGraph] Zoom transition completed')
        })
    }
  } else {
    console.warn('[KnowledgeGraph] No matching nodes to center on')
  }
}

// Center view on matching nodes
const centerOnNodes = (nodeType: string) => {
  const matchingNodes = nodes.value.filter(n => n.type === nodeType)
  if (matchingNodes.length === 0) return

  const avgX = matchingNodes.reduce((sum, n) => sum + (n.x || 0), 0) / matchingNodes.length
  const avgY = matchingNodes.reduce((sum, n) => sum + (n.y || 0), 0) / matchingNodes.length

  const transform = d3.zoomIdentity
    .translate(containerWidth.value / 2, containerHeight.value / 2)
    .scale(1.2)
    .translate(-avgX, -avgY)

  if (svg) {
    svg.transition()
      .duration(750)
      .call(zoom.transform as any, transform)
  }
}

// Old center logic (keep for compatibility)
const centerViewOnNodes = (nodeType: string) => {
  highlightNodesByType(nodeType)
}

const resetFilters = () => {
  selectedFilters.value = []
  selectedType.value = ''
  resetHighlight()
}

// Reset all highlights
const resetHighlight = () => {
  if (!g) return

  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 1)

  g.selectAll('.node-group text')
    .attr('opacity', 1)
    .attr('font-weight', 'normal')

  g.selectAll('line')
    .attr('opacity', 0.6)
    .attr('stroke-width', 1.5)
    .attr('stroke', '#999')
}

// Scenario handlers
const executeScenario = () => {
  const text = scenarioText.value.toLowerCase().trim()
  console.log('[KnowledgeGraph] Execute scenario:', text)
  
  if (!text) {
    ElMessage.warning('请输入场景描述，例如：P2P采购流程、销售订单分析')
    return
  }
  
  if (!g) {
    console.error('[KnowledgeGraph] SVG group g is not initialized')
    ElMessage.error('图谱未初始化，请刷新页面')
    return
  }
  
  // Smart scenario detection based on keywords
  if (text.includes('p2p') || text.includes('采购') || text.includes('付款流程')) {
    console.log('[KnowledgeGraph] Detected P2P scenario')
    highlightScenarioNodes('p2p')
  } else if (text.includes('o2c') || text.includes('订单') || text.includes('收款') || text.includes('销售流程')) {
    console.log('[KnowledgeGraph] Detected O2C scenario')
    highlightScenarioNodes('o2c')
  } else if (text.includes('财务') || text.includes('发票') || text.includes('应收') || text.includes('应付')) {
    console.log('[KnowledgeGraph] Detected Finance scenario')
    highlightScenarioNodes('finance')
  } else if (text.includes('风险') || text.includes('预警') || text.includes('异常')) {
    console.log('[KnowledgeGraph] Detected Risk scenario')
    highlightScenarioNodes('risk')
  } else {
    // Try to extract node types from text
    const nodeTypes: string[] = []
    if (text.includes('供应商')) nodeTypes.push('Supplier')
    if (text.includes('客户')) nodeTypes.push('Customer')
    if (text.includes('发票')) nodeTypes.push('Invoice')
    if (text.includes('付款')) nodeTypes.push('Payment')
    if (text.includes('采购')) nodeTypes.push('PurchaseOrder')
    if (text.includes('采购行')) nodeTypes.push('POLine')
    if (text.includes('销售')) nodeTypes.push('Sale')
    if (text.includes('价格') || text.includes('报价')) nodeTypes.push('PriceList')
    
    if (nodeTypes.length > 0) {
      console.log('[KnowledgeGraph] Custom scenario with types:', nodeTypes)
      highlightNodesByTypes(nodeTypes)
    } else {
      ElMessage.warning('未识别到场景类型，请使用 P2P、O2C、采购、销售、供应商、客户等关键词')
    }
  }
}

// Highlight nodes by multiple types
const highlightNodesByTypes = (types: string[]) => {
  if (!g) return

  console.log('[KnowledgeGraph] Highlighting types:', types)

  // Reset all nodes
  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.2)

  g.selectAll('.node-group text')
    .attr('opacity', 0.2)

  g.selectAll('line')
    .attr('opacity', 0.1)

  // Highlight matching nodes
  g.selectAll('.node-group')
    .filter((d: any) => types.includes(d.type))
    .select('circle')
    .attr('stroke', '#ff4d4f')
    .attr('stroke-width', 4)
    .attr('opacity', 1)

  g.selectAll('.node-group')
    .filter((d: any) => types.includes(d.type))
    .select('text')
    .attr('opacity', 1)
    .attr('font-weight', 'bold')

  // Center view
  const matchingNodes = nodes.value.filter(n => types.includes(n.type))
  if (matchingNodes.length > 0) {
    const avgX = matchingNodes.reduce((sum, n) => sum + (n.x || 0), 0) / matchingNodes.length
    const avgY = matchingNodes.reduce((sum, n) => sum + (n.y || 0), 0) / matchingNodes.length

    const transform = d3.zoomIdentity
      .translate(containerWidth.value / 2, containerHeight.value / 2)
      .scale(1.2)
      .translate(-avgX, -avgY)

    svg.transition().duration(750).call(zoom.transform as any, transform)

    ElMessage.success(`已高亮 ${matchingNodes.length} 个节点`)
  } else {
    ElMessage.warning('未找到匹配的节点')
  }
}

const loadScenario = (scenario: any) => {
  scenarioText.value = scenario.desc
  console.log('[KnowledgeGraph] Loading scenario:', scenario.type)

  // Highlight nodes based on scenario type
  highlightScenarioNodes(scenario.type)
}

// Highlight nodes based on scenario
const highlightScenarioNodes = (scenarioType: string) => {
  if (!g) {
    console.error('[KnowledgeGraph] SVG group g is not initialized')
    ElMessage.error('图谱未初始化,请刷新页面')
    return
  }

  console.log('[KnowledgeGraph] Highlighting scenario:', scenarioType)
  console.log('[KnowledgeGraph] Total nodes:', nodes.value.length)
  console.log('[KnowledgeGraph] Nodes by type:', nodes.value.reduce((acc, n) => {
    acc[n.type] = (acc[n.type] || 0) + 1
    return acc
  }, {} as Record<string, number>))

  // Define scenario-related node types - 映射到实际 Neo4j 节点类型 (683个节点)
  const scenarioNodeMap: Record<string, string[]> = {
    'p2p': ['PurchaseOrder', 'POLine', 'Supplier', 'Invoice', 'Payment'],   // P2P: 采购到付款完整流程
    'o2c': ['Sale', 'Order', 'Customer', 'Invoice', 'Payment'],             // O2C: 订单到收款完整流程
    'finance': ['Invoice', 'Payment', 'PriceList'],                         // 财务分析
    'risk': ['Customer', 'Supplier', 'Event'],                              // 风险预警
  }

  const relatedTypes = scenarioNodeMap[scenarioType] || []
  if (relatedTypes.length === 0) {
    ElMessage.warning('未识别到场景类型')
    return
  }

  // Count matching nodes
  const matchingCount = nodes.value.filter(n => relatedTypes.includes(n.type)).length
  console.log('[KnowledgeGraph] Matching nodes for', scenarioType, ':', matchingCount)

  if (matchingCount === 0) {
    ElMessage.warning(`图谱中没有 ${relatedTypes.join('/')} 类型的节点,请刷新页面加载更多数据`)
    return
  }

  // Reset all nodes
  g.selectAll('.node-group circle')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('opacity', 0.2)

  g.selectAll('.node-group text')
    .attr('opacity', 0.2)

  g.selectAll('line')
    .attr('opacity', 0.05)

  // Highlight scenario-related nodes
  relatedTypes.forEach((nodeType, index) => {
    const color = ['#667eea', '#52c41a', '#fa8c16', '#1890ff'][index % 4] || '#ff4d4f'

    const matchingNodes = g.selectAll('.node-group')
      .filter((d: any) => d.type === nodeType)

    if (matchingNodes.size() > 0) {
      matchingNodes.select('circle')
        .attr('stroke', color)
        .attr('stroke-width', 4)
        .attr('opacity', 1)

      matchingNodes.select('text')
        .attr('opacity', 1)
        .attr('font-weight', 'bold')

      console.log(`[KnowledgeGraph] Highlighted ${matchingNodes.size()} ${nodeType} nodes`)
    }
  })

  // Highlight edges between scenario nodes
  g.selectAll('line')
    .filter((d: any) => {
      const sourceType = d.source?.type || nodes.value.find(n => n.id === d.source)?.type
      const targetType = d.target?.type || nodes.value.find(n => n.id === d.target)?.type
      return relatedTypes.includes(sourceType) && relatedTypes.includes(targetType)
    })
    .attr('opacity', 0.9)
    .attr('stroke-width', 3)
    .attr('stroke', '#667eea')

  // Center view on matching nodes
  const matchingNodes = nodes.value.filter(n => relatedTypes.includes(n.type))
  if (matchingNodes.length > 0) {
    const avgX = matchingNodes.reduce((sum, n) => sum + (n.x || 0), 0) / matchingNodes.length
    const avgY = matchingNodes.reduce((sum, n) => sum + (n.y || 0), 0) / matchingNodes.length

    const transform = d3.zoomIdentity
      .translate(containerWidth.value / 2, containerHeight.value / 2)
      .scale(1.2)
      .translate(-avgX, -avgY)

    svg.transition().duration(750).call(zoom.transform as any, transform)
  }

  ElMessage.success(`已高亮 ${matchingCount} 个 ${scenarioType.toUpperCase()} 流程相关节点`)
  console.log(`[KnowledgeGraph] Highlighted scenario ${scenarioType} nodes:`, relatedTypes)
}

// Handle result click - highlight related nodes
const selectResult = (result: any) => {
  console.log('[KnowledgeGraph] Selected result:', result.title)

  // Parse result to find related nodes
  if (result.title.includes('P2P') || result.title.includes('流程')) {
    highlightScenarioNodes('p2p')
    ElMessage.success('已高亮 P2P 流程相关节点')
  } else if (result.title.includes('异常') || result.title.includes('问题')) {
    // Highlight nodes with issues - find actual problem nodes
    highlightProblemNodes()
  } else if (result.title.includes('效率') || result.title.includes('优化')) {
    // Highlight optimization opportunities
    highlightOptimizationNodes()
  } else {
    resetHighlight()
    ElMessage.info('未识别到相关节点')
  }
}

// Highlight problem/anomaly nodes
const highlightProblemNodes = () => {
  if (!g) return

  console.log('[KnowledgeGraph] Highlighting problem nodes')

  // Reset all
  resetHighlight()
  g.selectAll('.node-group circle').attr('opacity', 0.2)
  g.selectAll('.node-group text').attr('opacity', 0.2)
  g.selectAll('line').attr('opacity', 0.1)

  // Find Event nodes (alerts/issues)
  const problemNodes = nodes.value.filter(n => n.type === 'Event')

  if (problemNodes.length === 0) {
    ElMessage.warning('未找到问题节点')
    return
  }

  // Highlight problem nodes
  problemNodes.forEach(node => {
    g.selectAll('.node-group')
      .filter((d: any) => d.id === node.id)
      .select('circle')
      .attr('stroke', '#ff4d4f')
      .attr('stroke-width', 4)
      .attr('opacity', 1)

    g.selectAll('.node-group')
      .filter((d: any) => d.id === node.id)
      .select('text')
      .attr('opacity', 1)
      .attr('font-weight', 'bold')
  })

  // Center view on problem nodes
  centerOnNodes(problemNodes)
  ElMessage.success(`已高亮 ${problemNodes.length} 个问题节点`)
}

// Highlight optimization nodes
const highlightOptimizationNodes = () => {
  if (!g) return

  console.log('[KnowledgeGraph] Highlighting optimization nodes')

  // Reset all
  resetHighlight()
  g.selectAll('.node-group circle').attr('opacity', 0.2)
  g.selectAll('.node-group text').attr('opacity', 0.2)
  g.selectAll('line').attr('opacity', 0.1)

  // Highlight PurchaseOrder and Payment nodes (optimization opportunities)
  const optimizationTypes = ['PurchaseOrder', 'Payment']
  const optimizationNodes = nodes.value.filter(n => optimizationTypes.includes(n.type))

  if (optimizationNodes.length === 0) {
    ElMessage.warning('未找到可优化节点')
    return
  }

  // Highlight optimization nodes
  optimizationNodes.forEach(node => {
    g.selectAll('.node-group')
      .filter((d: any) => d.id === node.id)
      .select('circle')
      .attr('stroke', '#52c41a')
      .attr('stroke-width', 4)
      .attr('opacity', 1)

    g.selectAll('.node-group')
      .filter((d: any) => d.id === node.id)
      .select('text')
      .attr('opacity', 1)
      .attr('font-weight', 'bold')
  })

  // Center view
  centerOnNodes(optimizationNodes)
  ElMessage.success(`已高亮 ${optimizationNodes.length} 个可优化节点`)
}

// Center view on specific nodes
const centerOnNodes = (targetNodes: any[]) => {
  if (!svg || targetNodes.length === 0) return

  const avgX = targetNodes.reduce((sum, n) => sum + (n.x || 0), 0) / targetNodes.length
  const avgY = targetNodes.reduce((sum, n) => sum + (n.y || 0), 0) / targetNodes.length

  const transform = d3.zoomIdentity
    .translate(containerWidth.value / 2, containerHeight.value / 2)
    .scale(1.2)
    .translate(-avgX, -avgY)

  svg.transition().duration(750).call(zoom.transform as any, transform)
}

// Highlight random nodes for demo (deprecated)
const highlightRandomNodes = (count: number, color: string) => {
  if (!g) return

  // Reset all
  resetHighlight()
  g.selectAll('.node-group circle').attr('opacity', 0.3)
  g.selectAll('.node-group text').attr('opacity', 0.3)
  g.selectAll('line').attr('opacity', 0.1)

  // Pick random nodes
  const randomNodes = nodes.value.slice(0, count)

  randomNodes.forEach(node => {
    g.selectAll('.node-group')
      .filter((d: any) => d.id === node.id)
      .select('circle')
      .attr('stroke', color)
      .attr('stroke-width', 4)
      .attr('opacity', 1)

    g.selectAll('.node-group')
      .filter((d: any) => d.id === node.id)
      .select('text')
      .attr('opacity', 1)
      .attr('font-weight', 'bold')
  })
}

// Watch for container resize
watch([containerWidth, containerHeight], () => {
  if (simulation) {
    simulation.force('center', d3.forceCenter(containerWidth.value / 2, containerHeight.value / 2))
    simulation.alpha(0.3).restart()
  }
})

// Lifecycle
onMounted(() => {
  console.log('[KnowledgeGraph] onMounted - initializing...')
  initGraph()
  console.log('[KnowledgeGraph] initGraph completed')
  loadGraphData()
  console.log('[KnowledgeGraph] loadGraphData called')

  // Handle resize
  const handleResize = () => {
    if (graphContainer.value) {
      containerWidth.value = graphContainer.value.clientWidth
      containerHeight.value = graphContainer.value.clientHeight
      console.log('[KnowledgeGraph] Resized:', containerWidth.value, 'x', containerHeight.value)
    }
  }

  window.addEventListener('resize', handleResize)

  // Cleanup
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    if (simulation) {
      simulation.stop()
    }
  })
})

// Load nodes by type from Neo4j
const loadNodesByType = async (nodeType: string) => {
  console.log('[KnowledgeGraph] Loading nodes of type:', nodeType)

  try {
    const response = await fetch(`/api/v1/graph/?entity_type=${nodeType}&limit=20`)
    const data = await response.json()

    if (data.success && data.nodes) {
      // Add new nodes
      const newNodes = data.nodes
        .filter((n: any) => !nodes.value.find(existing => existing.id === n.id))
        .map((n: any) => ({
          id: n.id,
          name: n.name || n.properties?.name || 'Unknown',
          type: n.type || nodeType,
          description: n.description || n.properties?.description || '',
          properties: n.properties || n,
          x: Math.random() * containerWidth.value,
          y: Math.random() * containerHeight.value
        }))

      // Add new edges
      const newEdges = data.edges || []

      // Update nodes and edges
      nodes.value = [...nodes.value, ...newNodes]
      edges.value = [...edges.value, ...newEdges]

      console.log(`[KnowledgeGraph] Loaded ${newNodes.length} new nodes of type ${nodeType}`)

      // Update graph visualization
      updateGraph()

      // Highlight the newly loaded nodes
      setTimeout(() => {
        highlightNodesByType(nodeType)
        ElMessage.success(`已加载 ${newNodes.length} 个${nodeType}节点`)
      }, 500)
    } else {
      ElMessage.warning(`未找到 ${nodeType} 类型的数据`)
    }
  } catch (error) {
    console.error('[KnowledgeGraph] Failed to load nodes by type:', error)
    ElMessage.error('加载数据失败')
  }
}

// Load graph data from API
const loadGraphData = async () => {
  console.log('[KnowledgeGraph] Loading graph data...')
  try {
    // Use relative path for proxy (works with any frontend port)
    const response = await fetch('/api/v1/graph/')
    console.log('[KnowledgeGraph] API response status:', response.status)
    const data = await response.json()
    console.log('[KnowledgeGraph] API response data:', data)

    if (data.success && data.nodes) {
      nodes.value = data.nodes.map((n: any) => ({
        id: n.id,
        name: n.name || n.properties?.name || 'Unknown',
        type: n.type || 'Entity',
        description: n.description || n.properties?.description || '',
        properties: n.properties || n,
        x: Math.random() * containerWidth.value,
        y: Math.random() * containerHeight.value
      }))

      edges.value = data.edges || []

      console.log('[KnowledgeGraph] Data mapped:', nodes.value.length, 'nodes,', edges.value.length, 'edges')

      // Generate temporal events from nodes
      const events: any[] = []
      const now = new Date()
      
      data.nodes.forEach((node: any, idx: number) => {
        // Create event for each node
        const createDate = new Date(now.getTime() - Math.random() * 7 * 24 * 60 * 60 * 1000)
        events.push({
          id: `evt_${idx}`,
          type: ['create', 'update', 'risk', 'transaction'][Math.floor(Math.random() * 4)],
          timestamp: createDate.toISOString(),
          description: `${node.type}节点: ${node.name}`,
          nodes: [node.id]
        })
      })
      
      graphEvents.value = events
      
      // Generate time points
      const uniqueDates = [...new Set(events.map(e => e.timestamp.split('T')[0]))].sort()
      timePoints.value = uniqueDates.map((date, idx) => ({
        time: date,
        date: date,
        index: idx
      }))

      // Update graph
      updateGraph()

      console.log(`[KnowledgeGraph] Loaded ${nodes.value.length} nodes, ${edges.value.length} edges, ${events.length} events`)
    } else {
      console.error('[KnowledgeGraph] API returned invalid data:', data)
    }
  } catch (error) {
    console.error('[KnowledgeGraph] Failed to load graph data:', error)
  }
}
</script>

<style scoped>
/* 容器 */
.knowledge-graph {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 侧边面板 */
.ontology-panel,
.scenario-panel {
  width: 320px;
  min-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 本体列表 */
.ontology-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ontology-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.ontology-item:hover {
  background: #f5f5f5;
}

.ontology-item.active {
  background: #e6f7ff;
  border: 1px solid #1890ff;
}

.ontology-item.active .ontology-name {
  font-weight: 600;
  color: #1890ff;
}

.ontology-item.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.ontology-icon {
  font-size: 20px;
}

.ontology-name {
  flex: 1;
  font-size: 14px;
}

.ontology-count {
  margin-left: auto;
}

/* 筛选列表 */
.filter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 画布区 */
.canvas-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: relative;
}

.canvas-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.node-count-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.node-count-buttons {
  margin-left: 8px;
}

.canvas-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

.toolbar-search {
  margin-left: 20px;
}

.toolbar-search .el-input {
  width: 200px;
}

.graph-canvas {
  flex: 1;
  background: #fafafa;
  position: relative;
}

.graph-canvas svg {
  display: block;
}

/* 节点详情面板 */
.node-detail-panel {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 10;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.panel-content {
  padding: 16px;
}

.node-property {
  margin-bottom: 12px;
}

.property-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.property-value {
  font-size: 14px;
  color: #333;
}

.node-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

/* 场景输入 */
.scenario-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-input .el-input {
  width: 100%;
}

.scenario-input .el-button {
  width: 100%;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
}

/* 场景列表 */
.scenario-list,
.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-item,
.result-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-item:hover,
.result-item:hover {
  background: #f5f5f5;
}

.scenario-item.active,
.result-item.active {
  background: #e6f7ff;
  border: 1px solid #1890ff;
}

.scenario-icon,
.result-icon {
  font-size: 24px;
}

.scenario-content,
.result-content {
  flex: 1;
  min-width: 0;
}

.scenario-title,
.result-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.scenario-desc,
.result-desc {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

/* Node styles */
.node-group circle {
  transition: all 0.2s;
}

.node-group:hover circle {
  stroke: #333;
  stroke-width: 3;
}

/* View Mode Buttons */
.view-mode-buttons {
  margin-right: 12px;
}

/* Event List Styles */
.event-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.event-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.event-item:hover {
  background: #f0f0f0;
  transform: translateX(4px);
}

.event-indicator {
  width: 4px;
  border-radius: 2px;
  flex-shrink: 0;
}

.event-content {
  flex: 1;
  min-width: 0;
}

.event-time {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}

.event-desc {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
  margin-bottom: 6px;
}

.event-tags {
  display: flex;
  gap: 4px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* ========== UI-UX Pro Temporal Styles ========== */

/* 时序图谱容器 */
.temporal-graph-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部控制栏 - 毛玻璃效果 */
.graph-control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.graph-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.title-icon {
  font-size: 24px;
}

.title-text {
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.view-switch-buttons .el-button {
  font-weight: 500;
}

.view-icon {
  margin-right: 4px;
}

/* 侧边栏样式 */
.graph-sidebar {
  overflow-y: auto;
  scrollbar-width: thin;
}

.graph-sidebar::-webkit-scrollbar {
  width: 6px;
}

.graph-sidebar::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

/* 章节标题 - 渐变效果 */
.section-title {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

/* 时间轴控制器卡片 */
.temporal-control-card {
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.timeline-control {
  padding: 12px;
}

.time-slider {
  margin: 16px 0;
}

.current-time-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
  border-radius: 6px;
  margin-bottom: 12px;
}

.time-label {
  font-size: 13px;
  color: #666;
}

.time-value {
  font-size: 14px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.timeline-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 时间线视图 */
.timeline-view {
  flex: 1;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  overflow-y: auto;
}

.time-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  margin-bottom: 20px;
  position: relative;
}

.track-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  opacity: 0.3;
}

.timeline-point {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  z-index: 1;
  background: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.timeline-point:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.2);
}

.timeline-point.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.point-circle {
  font-size: 20px;
  margin-bottom: 4px;
}

.point-label {
  font-size: 12px;
  color: inherit;
}

.timeline-point.active .point-label {
  color: white;
}

/* 事件时间线 */
.events-timeline {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 16px;
}

.header-icon {
  font-size: 20px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.timeline-events {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.event-item:hover {
  transform: translateX(8px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
}

.event-border {
  width: 4px;
  min-height: 40px;
  border-radius: 2px;
  flex-shrink: 0;
  background: #667eea;
}

.event-item.event-type-create .event-border { background: #67c23a; }
.event-item.event-type-update .event-border { background: #409eff; }
.event-item.event-type-delete .event-border { background: #f56c6c; }
.event-item.event-type-risk .event-border { background: #e6a23c; }
.event-item.event-type-transaction .event-border { background: #909399; }

.event-time {
  font-size: 11px;
  color: #999;
  flex-shrink: 0;
  min-width: 50px;
}

.event-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.event-description {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
  flex: 1;
}

.event-tags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* 桑基图视图 */
.sankey-view {
  flex: 1;
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.sankey-placeholder {
  background: white;
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  max-width: 400px;
}

.sankey-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.sankey-icon {
  font-size: 32px;
}

.sankey-title {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sankey-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sankey-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

/* 时序事件卡片 */
.temporal-events-card {
  background: rgba(255, 255, 255, 0.98);
}

.temporal-events-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.temporal-event-card {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 4px solid #667eea;
}

.temporal-event-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  border-left-color: #764ba2;
}

.temporal-event-card.event-type-create { border-left-color: #67c23a; }
.temporal-event-card.event-type-update { border-left-color: #409eff; }
.temporal-event-card.event-type-delete { border-left-color: #f56c6c; }
.temporal-event-card.event-type-risk { border-left-color: #e6a23c; }
.temporal-event-card.event-type-transaction { border-left-color: #909399; }

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-type-icon {
  font-size: 16px;
}

.event-time-stamp {
  font-size: 11px;
  color: #999;
}

.event-body {
  margin-bottom: 8px;
}

.event-footer {
  display: flex;
  gap: 4px;
}

.event-node-tag {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 图谱统计卡片 */
.graph-stats-card {
  background: rgba(255, 255, 255, 0.98);
}

.graph-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}
</style>
