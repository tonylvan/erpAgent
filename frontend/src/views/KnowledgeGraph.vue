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
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ZoomIn, ZoomOut, Refresh, Grid, FullScreen, Close } from '@element-plus/icons-vue'
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
          zoom.transform,
          d3.zoomIdentity.translate(centerX, centerY).scale(zoomLevel.value)
        )
    }
  }
  
  // Update stats
  console.log(`[KnowledgeGraph] Highlighted ${matchingNodes.length} nodes of type ${nodeType}`)
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
  const text = scenarioText.value.toLowerCase()
  console.log('[KnowledgeGraph] Execute scenario:', text)
  
  // Smart scenario detection based on keywords
  if (text.includes('p2p') || text.includes('采购') || text.includes('付款')) {
    console.log('[KnowledgeGraph] Detected P2P scenario')
    highlightScenarioNodes('p2p')
  } else if (text.includes('o2c') || text.includes('订单') || text.includes('收款') || text.includes('销售')) {
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
    if (text.includes('销售')) nodeTypes.push('Sale')
    
    if (nodeTypes.length > 0) {
      console.log('[KnowledgeGraph] Custom scenario with types:', nodeTypes)
      highlightNodesByTypes(nodeTypes)
    } else {
      ElMessage.warning('未识别到场景类型，请使用 P2P、O2C、采购、销售等关键词')
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
  if (!g) return
  
  // Define scenario-related node types - 映射到实际 Neo4j 节点类型 (683个节点)
  const scenarioNodeMap: Record<string, string[]> = {
    'p2p': ['PurchaseOrder', 'POLine', 'Supplier', 'Invoice', 'Payment'],   // P2P: 采购到付款完整流程
    'o2c': ['Sale', 'Order', 'Customer', 'Invoice', 'Payment'],             // O2C: 订单到收款完整流程
    'finance': ['Invoice', 'Payment', 'PriceList'],                         // 财务分析
    'risk': ['Customer', 'Supplier', 'Event'],                              // 风险预警
  }
  
  const relatedTypes = scenarioNodeMap[scenarioType] || []
  if (relatedTypes.length === 0) return
  
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
    const color = ['#667eea', '#52c41a', '#fa8c16', '#1890ff'][index] || '#ff4d4f'
    
    g.selectAll('.node-group')
      .filter((d: any) => d.type === nodeType)
      .select('circle')
      .attr('stroke', color)
      .attr('stroke-width', 4)
      .attr('opacity', 1)
    
    g.selectAll('.node-group')
      .filter((d: any) => d.type === nodeType)
      .select('text')
      .attr('opacity', 1)
      .attr('font-weight', 'bold')
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
      
      // Update graph
      updateGraph()
      
      console.log(`[KnowledgeGraph] Loaded ${nodes.value.length} nodes, ${edges.value.length} edges`)
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
</style>
