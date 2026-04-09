<template>
  <div class="community-detection">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">👥</span>
        <span class="title-text">社群发现</span>
      </h1>
      <p class="page-description">基于 Louvain 算法自动识别图谱中的社群结构</p>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：控制面板 -->
      <aside class="control-panel">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>⚙️ 算法配置</span>
            </div>
          </template>

          <el-form :model="configForm" label-position="top">
            <el-form-item label="算法选择">
              <el-select v-model="configForm.algorithm" style="width: 100%">
                <el-option label="Louvain (推荐)" value="louvain" />
                <el-option label="标签传播" value="label_propagation" />
                <el-option label="基于节点类型" value="type_based" />
              </el-select>
            </el-form-item>

            <el-form-item label="最大迭代次数">
              <el-slider
                v-model="configForm.maxIterations"
                :min="10"
                :max="500"
                :step="10"
                show-input
              />
            </el-form-item>

            <el-form-item label="分辨率参数">
              <el-input-number
                v-model="configForm.resolution"
                :min="0.1"
                :max="5.0"
                :step="0.1"
                style="width: 100%"
              />
              <div class="form-hint">
                值越大，社群数量越多（推荐 1.0）
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="isDetecting"
                @click="detectCommunities"
                block
              >
                🔍 开始检测
              </el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <!-- 社群统计 -->
          <div v-if="result" class="stats-panel">
            <div class="stat-item">
              <div class="stat-value">{{ result.community_count }}</div>
              <div class="stat-label">社群数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ result.total_nodes }}</div>
              <div class="stat-label">总节点数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ result.total_edges }}</div>
              <div class="stat-label">总边数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ result.modularity }}</div>
              <div class="stat-label">模块度</div>
            </div>
          </div>
        </el-card>

        <!-- 社群列表 -->
        <el-card class="panel-card" shadow="never" style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <span>📊 社群列表</span>
              <el-tag type="success">{{ result?.community_count || 0 }} 个</el-tag>
            </div>
          </template>

          <div class="community-list">
            <div
              v-for="comm in sortedCommunities"
              :key="comm.community_id"
              class="community-item"
              :style="{ borderLeftColor: getCommunityColor(comm.community_id) }"
              @click="selectCommunity(comm)"
            >
              <div class="comm-header">
                <span class="comm-name">社群 {{ comm.community_id + 1 }}</span>
                <el-tag size="small" :type="comm.node_count > 50 ? 'success' : 'primary'">
                  {{ comm.node_count }} 节点
                </el-tag>
              </div>
              <div class="comm-stats">
                <span>🔗 {{ comm.edge_count }} 边</span>
                <span>📊 密度 {{ comm.density }}</span>
              </div>
              <div class="comm-types">
                <el-tag
                  v-for="(count, type) in comm.top_types"
                  :key="type"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ type }}: {{ count }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </aside>

      <!-- 中间：社群可视化 -->
      <div class="visualization-panel">
        <el-card class="viz-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>🎨 社群可视化</span>
              <div class="viz-controls">
                <el-button size="small" @click="resetView">🔄 重置视图</el-button>
                <el-button size="small" @click="toggleLabels">🏷️ 显示标签</el-button>
              </div>
            </div>
          </template>

          <div v-if="!result" class="empty-state">
            <div class="empty-icon">👥</div>
            <p class="empty-text">暂无社群检测结果</p>
            <p class="empty-hint">点击左侧"开始检测"按钮分析图谱社群结构</p>
          </div>

          <div v-else-if="isDetecting" class="loading-state">
            <el-skeleton :rows="10" animated />
          </div>

          <div v-else ref="vizContainer" class="viz-container"></div>
        </el-card>
      </div>

      <!-- 右侧：节点详情 -->
      <aside class="detail-panel" v-if="selectedNode">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📋 节点详情</span>
              <el-button text size="small" @click="selectedNode = null">
                ✕
              </el-button>
            </div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="节点 ID">
              {{ selectedNode.id }}
            </el-descriptions-item>
            <el-descriptions-item label="节点类型">
              <el-tag size="small">{{ selectedNode.type }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="所属社群">
              <el-tag size="small" :color="getCommunityColor(selectedNode.community)">
                社群 {{ selectedNode.community + 1 }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="名称">
              {{ selectedNode.name }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <div class="node-properties">
            <div class="prop-title">属性</div>
            <el-table :data="nodeProperties" size="small" :show-header="false">
              <el-table-column prop="key" label="键" width="120" />
              <el-table-column prop="value" label="值" />
            </el-table>
          </div>
        </el-card>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import GlobalNav from '../components/GlobalNav.vue'
import * as d3 from 'd3'

// 配置表单
const configForm = reactive({
  algorithm: 'louvain',
  maxIterations: 100,
  resolution: 1.0
})

// 加载状态
const isDetecting = ref(false)

// 检测结果
const result = ref<any>(null)

// 选中的社群和节点
const selectedCommunity = ref<any>(null)
const selectedNode = ref<any>(null)

// 可视化容器
const vizContainer = ref<HTMLElement | null>(null)

// 排序后的社群列表
const sortedCommunities = computed(() => {
  if (!result.value || !result.value.communities) return []
  return result.value.communities.sort((a: any, b: any) => b.node_count - a.node_count)
})

// 节点属性
const nodeProperties = computed(() => {
  if (!selectedNode.value || !selectedNode.value.properties) return []
  
  return Object.entries(selectedNode.value.properties).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
})

// 社群颜色映射
const communityColors = [
  '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe',
  '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140',
  '#30cfd0', '#330867', '#a8edea', '#fed6e3', '#f5f7fa'
]

const getCommunityColor = (communityId: number) => {
  return communityColors[communityId % communityColors.length]
}

// 检测社群
const detectCommunities = async () => {
  isDetecting.value = true
  result.value = null

  try {
    const response = await fetch('/api/v1/community/detect-communities', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configForm)
    })

    const data = await response.json()

    if (data.success) {
      result.value = data
      ElMessage.success(`发现 ${data.community_count} 个社群，模块度 ${data.modularity}`)
      
      // 渲染可视化
      nextTick(() => {
        renderVisualization(data.nodes)
      })
    } else {
      ElMessage.warning(data.error || '社群检测失败')
    }
  } catch (error) {
    console.error('[CommunityDetection] Error:', error)
    ElMessage.error('社群检测失败：' + error)
  } finally {
    isDetecting.value = false
  }
}

// 选择社群
const selectCommunity = (comm: any) => {
  selectedCommunity.value = comm
  ElMessage.info(`查看社群 ${comm.community_id + 1}：${comm.node_count} 个节点`)
}

// 重置视图
const resetView = () => {
  if (result.value) {
    renderVisualization(result.value.nodes)
    ElMessage.success('视图已重置')
  }
}

// 显示/隐藏标签
let showLabels = true
const toggleLabels = () => {
  showLabels = !showLabels
  if (result.value) {
    renderVisualization(result.value.nodes)
  }
}

// 渲染社群可视化
const renderVisualization = (nodes: any[]) => {
  if (!vizContainer.value) return

  // 清空容器
  vizContainer.value.innerHTML = ''

  const width = vizContainer.value.clientWidth
  const height = 600

  // 创建 SVG
  const svg = d3.select(vizContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .call(d3.zoom().on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))
    .append('g')

  const g = svg.append('g')

  // 创建力导向图
  const simulation = d3.forceSimulation(nodes)
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(25))
    .force('x', d3.forceX(width / 2).strength(0.1))
    .force('y', d3.forceY(height / 2).strength(0.1))

  // 绘制节点
  const node = g.selectAll('.community-node')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'community-node')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
    .on('click', (event, d) => {
      selectedNode.value = d
      ElMessage.info(`节点：${d.name}`)
    })

  // 节点圆圈
  node.append('circle')
    .attr('r', 12)
    .attr('fill', (d: any) => getCommunityColor(d.community))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)

  // 节点标签
  if (showLabels) {
    node.append('text')
      .attr('dx', 15)
      .attr('dy', 4)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text((d: any) => d.name?.substring(0, 15) || d.id)
  }

  // 更新位置
  simulation.on('tick', () => {
    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })

  // 拖拽函数
  function dragstarted(event: any, d: any) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  function dragged(event: any, d: any) {
    d.fx = event.x
    d.fy = event.y
  }

  function dragended(event: any, d: any) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

onMounted(() => {
  // 页面加载时不自动检测，等待用户点击
})
</script>

<style scoped>
.community-detection {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
  color: white;
}

.page-title {
  font-size: 28px;
  margin: 0 0 8px 0;
}

.title-icon {
  margin-right: 12px;
}

.page-description {
  opacity: 0.9;
  margin: 0;
}

.main-content {
  display: grid;
  grid-template-columns: 360px 1fr 320px;
  gap: 20px;
  max-width: 1800px;
  margin: 0 auto;
}

.control-panel {
  display: flex;
  flex-direction: column;
}

.panel-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.viz-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  min-height: 600px;
}

.viz-container {
  width: 100%;
  height: 600px;
  overflow: hidden;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  height: 600px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 18px;
  color: #666;
  margin: 8px 0;
}

.empty-hint {
  font-size: 14px;
  color: #999;
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
}

.community-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.community-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-left: 4px solid;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.community-item:hover {
  background: #f5f7ff;
  transform: translateX(4px);
}

.comm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comm-name {
  font-weight: bold;
  color: #333;
}

.comm-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.comm-types {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.viz-controls {
  display: flex;
  gap: 8px;
}

.detail-panel {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.node-properties {
  margin-top: 16px;
}

.prop-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #666;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
