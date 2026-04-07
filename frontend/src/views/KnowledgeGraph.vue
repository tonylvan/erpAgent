<template>
  <div class="knowledge-graph">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧本体面板 -->
      <aside class="ontology-panel">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📚 本体对象</span>
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
              <span>🔍 快速筛选</span>
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
      </aside>

      <!-- 中间画布区 -->
      <div class="canvas-section">
        <!-- 工具栏 -->
        <div class="canvas-toolbar">
          <el-button-group>
            <el-button :icon="ZoomIn" @click="zoomIn" title="放大" />
            <el-button :icon="ZoomOut" @click="zoomOut" title="缩小" />
            <el-button :icon="Refresh" @click="resetView" title="重置视图" />
            <el-divider direction="vertical" />
            <el-button :icon="Grid" @click="toggleGrid" title="网格" />
            <el-button :icon="FullScreen" @click="toggleFullscreen" title="全屏" />
          </el-button-group>
          
          <div class="canvas-info">
            <span>节点：{{ nodes.length }}</span>
            <span>关系：{{ edges.length }}</span>
          </div>
        </div>

        <!-- 图谱画布 -->
        <div ref="graphContainer" class="graph-canvas"></div>

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

      <!-- 右侧场景输入面板 -->
      <aside class="scenario-panel">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>💬 场景输入</span>
            </div>
          </template>
          
          <div class="scenario-input">
            <el-input
              v-model="scenarioText"
              type="textarea"
              :rows="4"
              placeholder="输入 P2P/O2C 等场景描述..."
            />
            <el-button type="primary" style="width: 100%; margin-top: 12px" @click="executeScenario">
              立即执行
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
              @click="loadScenario(scenario)"
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
            >
              <div class="result-icon">{{ result.icon }}</div>
              <div class="result-content">
                <div class="result-title">{{ result.title }}</div>
                <div class="result-desc">{{ result.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ZoomIn, ZoomOut, Refresh, Grid, FullScreen, Close } from '@element-plus/icons-vue'
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

// 本体类型
const ontologyTypes = reactive([
  { name: 'Invoice', label: '发票', icon: '📄', count: 113 },
  { name: 'Payment', label: '付款', icon: '💰', count: 110 },
  { name: 'PurchaseOrder', label: '采购单', icon: '📋', count: 34 },
  { name: 'Supplier', label: '供应商', icon: '🏢', count: 52 },
  { name: 'Customer', label: '客户', icon: '👥', count: 12 },
  { name: 'SalesOrder', label: '销售单', icon: '🛒', count: 20 },
])

// 筛选器
const filters = reactive([
  { label: '高危预警', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '提示', value: 'info' },
  { label: '已处理', value: 'processed' },
])

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

// Node color mapping
const nodeColors: Record<string, string> = {
  Invoice: '#667eea',
  Payment: '#52c41a',
  PurchaseOrder: '#fa8c16',
  Supplier: '#1890ff',
  Customer: '#722ed1',
  SalesOrder: '#eb2f96',
}

// Initialize D3.js force-directed graph
const initGraph = () => {
  if (!graphContainer.value) return

  // Get container dimensions
  const container = graphContainer.value
  containerWidth.value = container.clientWidth
  containerHeight.value = container.clientHeight

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

  // Add zoom behavior
  zoom = d3
    .zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event: any) => {
      g.attr('transform', event.transform)
      zoomLevel.value = event.transform.k
    })

  svg.call(zoom)

  // Create group for graph elements
  g = svg.append('g')

  // Initialize simulation
  initSimulation()

  // Note: Data will be loaded by loadGraphData() in onMounted
  // loadSampleData() removed to use real API data
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
  if (svg) {
    svg.transition().call(zoom.scaleBy, 1.3)
  }
}

const zoomOut = () => {
  if (svg) {
    svg.transition().call(zoom.scaleBy, 0.7)
  }
}

const resetView = () => {
  if (svg) {
    svg
      .transition()
      .duration(750)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(0, 0).scale(1)
      )
  }
}

const toggleGrid = () => {
  showGrid.value = !showGrid.value
  if (svg) {
    svg.style('background', showGrid.value ? '#f0f0f0' : '#fafafa')
  }
}

const toggleFullscreen = () => {
  if (graphContainer.value) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      graphContainer.value.requestFullscreen()
    }
  }
}

// Ontology panel
const toggleOntology = () => {
  ontologyExpanded.value = !ontologyExpanded.value
}

const selectType = (type: any) => {
  selectedType.value = type.name
  // Filter nodes by type
  // This would filter the displayed nodes
}

const resetFilters = () => {
  selectedFilters.value = []
}

// Scenario handlers
const executeScenario = () => {
  console.log('Execute scenario:', scenarioText.value)
}

const loadScenario = (scenario: any) => {
  scenarioText.value = scenario.desc
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
  initGraph()
  loadGraphData()
  
  // Handle resize
  const handleResize = () => {
    if (graphContainer.value) {
      containerWidth.value = graphContainer.value.clientWidth
      containerHeight.value = graphContainer.value.clientHeight
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

// Load graph data from API
const loadGraphData = async () => {
  try {
    const response = await fetch('http://localhost:8007/api/v1/graph/')
    const data = await response.json()
    
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
      
      // Update graph
      updateGraph()
      
      console.log(`Loaded ${nodes.value.length} nodes, ${edges.value.length} edges`)
    }
  } catch (error) {
    console.error('Failed to load graph data:', error)
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
  width: 280px;
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

.canvas-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
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
</style>
