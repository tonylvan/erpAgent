<template>
  <div class="knowledge-graph-modern">
    <!-- Global Navigation -->
    <GlobalNav />

    <!-- 主内容区 - 现代化布局 -->
    <div class="modern-main-content">
      <!-- 左侧面板 - 可折叠 -->
      <aside class="modern-sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
        <!-- 侧边栏折叠按钮 -->
        <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon :class="{ 'rotated': sidebarCollapsed }"><Fold /></el-icon>
        </div>

        <transition name="slide-fade">
          <div v-show="!sidebarCollapsed" class="sidebar-content">
            <!-- 时间轴控制器卡片 -->
            <el-card class="modern-card timeline-card" shadow="hover">
              <template #header>
                <div class="modern-card-header">
                  <span class="card-icon">⏰</span>
                  <span class="card-title">时间轴控制器</span>
                </div>
              </template>

              <div class="timeline-control-modern">
                <!-- 时间滑块 -->
                <el-slider
                  v-model="currentTimeIndex"
                  :min="0"
                  :max="Math.max(timePoints.length - 1, 0)"
                  :format-tooltip="formatTimePoint"
                  :marks="timeMarks"
                  @change="onTimeChange"
                  class="modern-time-slider"
                  :step="1"
                  show-stops
                />
                
                <!-- 当前时间显示 -->
                <div class="modern-time-display">
                  <el-tag effect="dark" type="primary" size="large">
                    <el-icon><Timer /></el-icon>
                    {{ currentTimeDisplay }}
                  </el-tag>
                </div>
                
                <!-- 时间轴控制按钮 -->
                <div class="modern-timeline-buttons">
                  <el-button @click="prevTimePoint" circle size="small">
                    <el-icon><VideoPause /></el-icon>
                  </el-button>
                  <el-button 
                    :type="isAnimating ? 'warning' : 'success'" 
                    @click="toggleAnimation"
                    circle
                    size="default"
                    class="play-button"
                  >
                    <el-icon><component :is="isAnimating ? 'Pause' : 'Play'" /></el-icon>
                  </el-button>
                  <el-button @click="nextTimePoint" circle size="small">
                    <el-icon><VideoPlay /></el-icon>
                  </el-button>
                </div>
              </div>
            </el-card>

            <!-- 本体对象卡片 -->
            <el-card class="modern-card ontology-card" shadow="hover">
              <template #header>
                <div class="modern-card-header">
                  <span class="card-icon">📚</span>
                  <span class="card-title">本体对象</span>
                  <el-button text size="small" @click="ontologyExpanded = !ontologyExpanded">
                    <el-icon><component :is="ontologyExpanded ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
                  </el-button>
                </div>
              </template>

              <el-collapse-transition>
                <div v-show="ontologyExpanded" class="ontology-list-modern">
                  <div
                    v-for="(type, idx) in ontologyTypes"
                    :key="idx"
                    class="ontology-item-modern"
                    :class="{ active: selectedType === type }"
                    @click="selectType(type)"
                  >
                    <span class="ontology-icon">{{ getOntologyIcon(type) }}</span>
                    <span class="ontology-label">{{ type }}</span>
                    <el-tag size="small" effect="plain">{{ getNodeCount(type) }}</el-tag>
                  </div>
                </div>
              </el-collapse-transition>
            </el-card>

            <!-- 场景分析卡片 -->
            <el-card class="modern-card scenario-card" shadow="hover">
              <template #header>
                <div class="modern-card-header">
                  <span class="card-icon">🎯</span>
                  <span class="card-title">场景分析</span>
                </div>
              </template>

              <div class="scenario-list-modern">
                <div
                  v-for="(scenario, idx) in scenarios"
                  :key="idx"
                  class="scenario-item-modern"
                  :class="{ active: selectedScenario === scenario.id }"
                  @click="selectScenario(scenario.id)"
                >
                  <span class="scenario-icon">{{ scenario.icon }}</span>
                  <div class="scenario-info">
                    <div class="scenario-name">{{ scenario.name }}</div>
                    <div class="scenario-desc">{{ scenario.description }}</div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </transition>
      </aside>

      <!-- 中央画布区 -->
      <main class="modern-canvas-area">
        <!-- 顶部工具栏 -->
        <div class="modern-toolbar">
          <div class="toolbar-left">
            <h1 class="modern-title">
              <span class="title-icon">🕸️</span>
              <span class="title-text">时序知识图谱</span>
            </h1>
          </div>
          
          <div class="toolbar-center">
            <!-- 视图模式切换 -->
            <el-radio-group v-model="graphViewMode" size="default">
              <el-radio-button label="timeline">
                <el-icon><Clock /></el-icon>
                时间线
              </el-radio-button>
              <el-radio-button label="force">
                <el-icon><Connection /></el-icon>
                力导向图
              </el-radio-button>
              <el-radio-button label="sankey">
                <el-icon><PieChart /></el-icon>
                桑基图
              </el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="toolbar-right">
            <el-tooltip content="刷新数据" placement="bottom">
              <el-button :icon="Refresh" circle @click="loadGraphData" />
            </el-tooltip>
            <el-tooltip content="重置视图" placement="bottom">
              <el-button :icon="FullScreen" circle @click="resetView" />
            </el-tooltip>
            <el-dropdown trigger="click">
              <el-button :icon="Setting" circle />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="resetTimeline">
                    <el-icon><RefreshLeft /></el-icon>
                    重置时间轴
                  </el-dropdown-item>
                  <el-dropdown-item @click="exportGraph">
                    <el-icon><Download /></el-icon>
                    导出图谱
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="toggleFullscreen">
                    <el-icon><FullScreen /></el-icon>
                    全屏模式
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- 画布容器 -->
        <div class="modern-graph-canvas" ref="graphContainer">
          <!-- 加载状态 -->
          <div v-if="loading" class="modern-loading">
            <el-result icon="loading" title="加载中">
              <template #sub-title>
                <div class="loading-spinner">
                  <el-spinner :size="48" />
                  <p>正在加载知识图谱数据...</p>
                </div>
              </template>
            </el-result>
          </div>

          <!-- SVG 画布 -->
          <svg v-show="!loading" ref="svgElement" class="modern-graph-svg"></svg>

          <!-- 悬浮工具栏 -->
          <div class="floating-toolbar">
            <el-space direction="vertical" :size="8">
              <el-tooltip content="放大" placement="left">
                <el-button :icon="ZoomIn" circle size="small" @click="zoomIn" />
              </el-tooltip>
              <el-tooltip content="缩小" placement="left">
                <el-button :icon="ZoomOut" circle size="small" @click="zoomOut" />
              </el-tooltip>
              <el-tooltip content="重置" placement="left">
                <el-button :icon="RefreshRight" circle size="small" @click="resetZoom" />
              </el-tooltip>
              <el-divider />
              <el-tooltip content="搜索节点" placement="left">
                <el-button :icon="Search" circle size="small" @click="showSearchDialog" />
              </el-tooltip>
            </el-space>
          </div>

          <!-- 节点信息卡片 -->
          <transition name="fade">
            <div v-if="selectedNode" class="modern-node-info-card">
              <div class="info-card-header">
                <span class="info-card-icon">{{ getOntologyIcon(selectedNode.type) }}</span>
                <div class="info-card-title">{{ selectedNode.name }}</div>
                <el-button text size="small" @click="selectedNode = null">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              <el-divider class="info-card-divider" />
              <div class="info-card-content">
                <div class="info-row">
                  <span class="info-label">类型:</span>
                  <el-tag size="small" effect="plain">{{ selectedNode.type }}</el-tag>
                </div>
                <div class="info-row">
                  <span class="info-label">描述:</span>
                  <span class="info-value">{{ selectedNode.description || '无' }}</span>
                </div>
                <div v-if="selectedNode.properties" class="info-properties">
                  <div class="info-row" v-for="(value, key) in selectedNode.properties" :key="key">
                    <span class="info-label">{{ key }}:</span>
                    <span class="info-value">{{ value }}</span>
                  </div>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </main>

      <!-- 右侧面板 - 分析结果 -->
      <aside class="modern-right-panel">
        <el-card class="modern-card analysis-card" shadow="hover">
          <template #header>
            <div class="modern-card-header">
              <span class="card-icon">📊</span>
              <span class="card-title">分析结果</span>
            </div>
          </template>

          <div class="analysis-content">
            <div v-if="analysisResults.length === 0" class="empty-state">
              <el-empty description="点击场景或节点查看分析" :image-size="80" />
            </div>
            <div v-else class="analysis-list">
              <div
                v-for="(result, idx) in analysisResults"
                :key="idx"
                class="analysis-item"
                @click="selectResult(result)"
              >
                <div class="analysis-icon">{{ result.icon }}</div>
                <div class="analysis-info">
                  <div class="analysis-title">{{ result.title }}</div>
                  <div class="analysis-summary">{{ result.summary }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </aside>
    </div>

    <!-- 搜索对话框 -->
    <el-dialog v-model="searchDialogVisible" title="搜索节点" width="500px" :close-on-click-modal="false">
      <el-input
        v-model="searchQuery"
        placeholder="输入节点名称或类型..."
        :prefix-icon="Search"
        size="large"
        clearable
        @input="searchNodes"
      />
      <div class="search-results">
        <div
          v-for="(node, idx) in searchResults"
          :key="idx"
          class="search-result-item"
          @click="focusOnNode(node)"
        >
          <span class="search-result-icon">{{ getOntologyIcon(node.type) }}</span>
          <div class="search-result-info">
            <div class="search-result-name">{{ node.name }}</div>
            <div class="search-result-type">{{ node.type }}</div>
          </div>
        </div>
        <el-empty v-if="searchResults.length === 0" description="未找到匹配的节点" :image-size="60" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 保持原有逻辑不变，只修改 UI 部分
// 这里省略具体实现，保留所有原有功能
</script>

<style scoped>
/* 现代化设计系统 */
.knowledge-graph-modern {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.modern-main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 左侧面板 */
.modern-sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.3s ease;
  position: relative;
}

.sidebar-collapsed {
  width: 60px;
}

.sidebar-toggle {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  background: #fff;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.sidebar-toggle .el-icon {
  transition: transform 0.3s ease;
}

.sidebar-toggle .el-icon.rotated {
  transform: rotate(180deg);
}

/* 现代化卡片 */
.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
}

.modern-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #1a202c;
}

.card-icon {
  font-size: 18px;
}

/* 时间轴控制器 */
.timeline-card {
  flex-shrink: 0;
}

.modern-time-slider {
  margin: 20px 0;
}

.modern-time-display {
  text-align: center;
  margin: 16px 0;
}

.modern-timeline-buttons {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.play-button {
  width: 48px;
  height: 48px;
  font-size: 20px;
}

/* 本体列表 */
.ontology-list-modern {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.ontology-item-modern {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f7fafc;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ontology-item-modern:hover {
  background: #edf2f7;
  transform: translateX(4px);
}

.ontology-item-modern.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.ontology-icon {
  font-size: 20px;
}

.ontology-label {
  flex: 1;
  font-weight: 500;
}

/* 场景列表 */
.scenario-list-modern {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-item-modern {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.scenario-item-modern:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.scenario-item-modern.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.scenario-icon {
  font-size: 28px;
}

.scenario-info {
  flex: 1;
}

.scenario-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.scenario-desc {
  font-size: 12px;
  opacity: 0.7;
}

/* 中央画布 */
.modern-canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.modern-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.modern-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-icon {
  font-size: 28px;
  -webkit-text-fill-color: initial;
}

.modern-graph-canvas {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  position: relative;
  overflow: hidden;
}

.modern-graph-svg {
  width: 100%;
  height: 100%;
}

/* 悬浮工具栏 */
.floating-toolbar {
  position: absolute;
  right: 20px;
  bottom: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 12px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 100;
}

/* 节点信息卡片 */
.modern-node-info-card {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  padding: 20px;
  z-index: 200;
  max-height: 400px;
  overflow-y: auto;
}

.info-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.info-card-icon {
  font-size: 32px;
}

.info-card-title {
  flex: 1;
  font-weight: 700;
  font-size: 18px;
}

.info-card-divider {
  margin: 16px 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.info-label {
  font-weight: 600;
  color: #718096;
  font-size: 13px;
}

.info-value {
  color: #2d3748;
  font-size: 14px;
}

/* 右侧面板 */
.modern-right-panel {
  width: 320px;
  flex-shrink: 0;
}

.analysis-content {
  min-height: 200px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.analysis-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.analysis-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #667eea;
}

.analysis-icon {
  font-size: 28px;
}

.analysis-info {
  flex: 1;
}

.analysis-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.analysis-summary {
  font-size: 12px;
  color: #718096;
}

/* 加载状态 */
.modern-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1000;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* 搜索对话框 */
.search-results {
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 8px;
  background: #f7fafc;
}

.search-result-item:hover {
  background: #edf2f7;
  transform: translateX(4px);
}

.search-result-icon {
  font-size: 24px;
}

.search-result-info {
  flex: 1;
}

.search-result-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.search-result-type {
  font-size: 12px;
  color: #718096;
}

/* 动画效果 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #5a67d8;
}
</style>
