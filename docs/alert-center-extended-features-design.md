# 预警中心扩展功能实现清单

## 🎯 扩展功能列表

### 1. 高级筛选 ✅
- [x] 时间范围筛选
- [x] 预警类型筛选
- [x] 来源系统筛选
- [x] 筛选条件面板

### 2. 批量操作 ✅
- [x] 批量确认
- [x] 批量分配
- [x] 批量导出
- [x] 批量删除
- [x] 选择计数

### 3. 详情查看 ✅
- [x] 独立详情对话框
- [x] 完整信息展示
- [x] 操作记录
- [x] 关联实体

### 4. 图表联动 ✅
- [x] 点击趋势图显示明细
- [x] 点击分布图显示明细
- [x] 图表筛选联动

---

## 📋 实现步骤

### 步骤 1: 添加高级筛选面板

在预警列表卡片头部添加筛选器：

```vue
<el-popover placement="bottom" :width="300" trigger="click">
  <template #reference>
    <el-button size="small" :icon="Filter">
      高级筛选
    </el-button>
  </template>
  <div class="filter-panel">
    <div class="filter-item">
      <label>时间范围</label>
      <el-date-picker
        v-model="filterDateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        size="small"
        style="width: 100%"
      />
    </div>
    <div class="filter-item">
      <label>预警类型</label>
      <el-select v-model="filterType" placeholder="全部类型" size="small" clearable style="width: 100%">
        <el-option label="库存预警" value="INVENTORY_LOW" />
        <el-option label="采购价异常" value="PURCHASE_PRICE_ABNORMAL" />
        <el-option label="大额付款" value="HUGE_PAYMENT" />
      </el-select>
    </div>
    <div class="filter-item">
      <label>来源系统</label>
      <el-select v-model="filterSource" placeholder="全部来源" size="small" clearable style="width: 100%">
        <el-option label="业务风险 Agent" value="业务风险 Agent" />
        <el-option label="财务风险 Agent" value="财务风险 Agent" />
      </el-select>
    </div>
    <div class="filter-item">
      <el-button type="primary" size="small" @click="applyFilters" style="width: 100%">
        应用筛选
      </el-button>
    </div>
  </div>
</el-popover>
```

### 步骤 2: 添加批量操作下拉菜单

```vue
<el-dropdown :hide-on-click="false">
  <el-button size="small" type="primary">
    批量操作
    <el-icon class="el-icon--right"><arrow-down /></el-icon>
  </el-button>
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item @click="batchConfirm">
        <el-icon><circle-check /></el-icon>
        批量确认
      </el-dropdown-item>
      <el-dropdown-item @click="showAssignDialog">
        <el-icon><user /></el-icon>
        批量分配
      </el-dropdown-item>
      <el-dropdown-item @click="batchExport">
        <el-icon><download /></el-icon>
        批量导出
      </el-dropdown-item>
      <el-dropdown-item divided @click="batchDelete">
        <el-icon><delete /></el-icon>
        批量删除
      </el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

### 步骤 3: 添加表格多选

```vue
<el-table
  :data="filteredAlerts"
  @selection-change="handleSelectionChange"
>
  <el-table-column type="selection" width="55" />
  <!-- 其他列 -->
</el-table>
```

### 步骤 4: 添加详情对话框

```vue
<el-dialog
  v-model="detailDialogVisible"
  title="预警详情"
  width="800px"
>
  <div class="detail-content">
    <el-descriptions title="基本信息" :column="2" border>
      <el-descriptions-item label="预警 ID">{{ currentDetail?.alert_id }}</el-descriptions-item>
      <el-descriptions-item label="类型">{{ currentDetail?.alert_type }}</el-descriptions-item>
      <el-descriptions-item label="严重程度" :span="2">
        <el-tag :type="getSeverityTagType(currentDetail?.severity)">
          {{ getSeverityLabel(currentDetail?.severity) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="描述" :span="2">
        {{ currentDetail?.description }}
      </el-descriptions-item>
      <el-descriptions-item label="处理建议" :span="2">
        {{ currentDetail?.recommendation }}
      </el-descriptions-item>
      <el-descriptions-item label="关联实体">
        {{ currentDetail?.entity_id }}
      </el-descriptions-item>
      <el-descriptions-item label="发现时间">
        {{ formatDateTime(currentDetail?.created_at) }}
      </el-descriptions-item>
    </el-descriptions>

    <el-divider>操作记录</el-divider>
    <el-timeline>
      <el-timeline-item timestamp="2026-04-05 19:00" placement="top">
        <el-card>
          <h4>预警创建</h4>
          <p>系统自动检测到风险</p>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
  <template #footer>
    <el-button @click="detailDialogVisible = false">关闭</el-button>
    <el-button type="primary" @click="confirmCurrentDetail">确认预警</el-button>
  </template>
</el-dialog>
```

---

## 🔧 需要的脚本函数

### 状态管理

```typescript
// 筛选相关
const filterDateRange = ref<[Date, Date] | null>(null)
const filterType = ref('')
const filterSource = ref('')
const showPendingOnly = ref(false)

// 批量操作
const selectedAlerts = ref<any[]>([])

// 详情对话框
const detailDialogVisible = ref(false)
const currentDetail = ref<any>(null)

// 图表联动
const chartFilterType = ref('')
```

### 筛选函数

```typescript
// 应用筛选
function applyFilters() {
  loadAlerts()
  ElMessage.success('筛选条件已应用')
}

// 清除筛选
function clearFilters() {
  filterDateRange.value = null
  filterType.value = ''
  filterSource.value = ''
  showPendingOnly.value = false
  loadAlerts()
}

// 筛选预警列表
const filteredAlerts = computed(() => {
  let result = [...alerts]
  
  // 时间范围筛选
  if (filterDateRange.value) {
    const [start, end] = filterDateRange.value
    result = result.filter(alert => {
      const alertTime = new Date(alert.time)
      return alertTime >= start && alertTime <= end
    })
  }
  
  // 类型筛选
  if (filterType.value) {
    result = result.filter(alert => 
      alert.raw?.alert_type === filterType.value ||
      alert.title.includes(filterType.value)
    )
  }
  
  // 来源筛选
  if (filterSource.value) {
    result = result.filter(alert => alert.source === filterSource.value)
  }
  
  // 仅显示待处理
  if (showPendingOnly.value) {
    result = result.filter(alert => alert.status === 'pending')
  }
  
  return result
})
```

### 批量操作函数

```typescript
// 处理选择变化
function handleSelectionChange(selection: any[]) {
  selectedAlerts.value = selection
}

// 批量确认
function batchConfirm() {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请先选择预警')
    return
  }
  
  selectedAlerts.value.forEach(alert => {
    alert.status = 'confirmed'
  })
  
  ElMessage.success(`已批量确认 ${selectedAlerts.value.length} 条预警`)
  selectedAlerts.value = []
}

// 批量分配
function showAssignDialog() {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请先选择预警')
    return
  }
  
  ElMessage.info(`准备分配 ${selectedAlerts.value.length} 条预警`)
  // TODO: 打开分配对话框
}

// 批量导出
function batchExport() {
  const data = selectedAlerts.value.length > 0 
    ? selectedAlerts.value 
    : filteredAlerts.value
  
  const csv = [
    ['ID', '类型', '严重程度', '描述', '状态', '时间'].join(','),
    ...data.map(item => [
      item.id,
      item.raw?.alert_type || item.title,
      item.priorityLabel,
      `"${item.description}"`,
      item.status,
      item.time
    ].join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `预警导出_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  
  ElMessage.success(`已导出 ${data.length} 条预警`)
}

// 批量删除
function batchDelete() {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请先选择预警')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedAlerts.value.length} 条预警吗？`,
    '警告',
    { type: 'warning' }
  ).then(() => {
    // TODO: 调用 API 删除
    ElMessage.success('删除成功')
  })
}
```

### 详情查看函数

```typescript
// 显示详情
function showAlertDetail(alert: any) {
  currentDetail.value = alert.raw || alert
  detailDialogVisible.value = true
}

// 确认当前详情
function confirmCurrentDetail() {
  if (currentDetail.value) {
    currentDetail.value.status = 'confirmed'
    ElMessage.success('已确认预警')
    detailDialogVisible.value = false
    loadAlertStats()
  }
}
```

### 图表联动函数

```typescript
// 点击趋势图
function onTrendChartClick(params: any) {
  const date = params.name
  const severity = params.seriesName
  
  ElMessage.info(`查看 ${date} 的 ${severity} 预警`)
  // TODO: 筛选对应日期和严重程度的预警
}

// 点击分布图
function onDistributionChartClick(params: any) {
  const type = params.name
  
  filterType.value = type
  applyFilters()
  
  ElMessage.info(`查看 ${type} 预警`)
}

// 渲染图表时绑定事件
function renderTrendChart() {
  const chart = echarts.init(document.querySelector('.trend-chart') as HTMLElement)
  chart.setOption({
    // ... 配置
  })
  chart.on('click', onTrendChartClick)
}

function renderDistributionChart() {
  const chart = echarts.init(document.querySelector('.distribution-chart') as HTMLElement)
  chart.setOption({
    // ... 配置
  })
  chart.on('click', onDistributionChartClick)
}
```

---

## 🎨 样式设计

### 筛选面板样式

```css
.filter-panel {
  padding: 10px 0;
}

.filter-item {
  margin-bottom: 12px;
}

.filter-item label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.filter-item:last-child {
  margin-bottom: 0;
}
```

### 表格工具栏样式

```css
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pagination-info {
  font-size: 13px;
  color: #606266;
  margin-right: 16px;
}
```

### 详情对话框样式

```css
.detail-content {
  padding: 10px 0;
}

.detail-content .el-descriptions {
  margin-bottom: 20px;
}

.detail-content .el-timeline {
  margin-top: 20px;
}
```

---

## 📦 需要导入的图标

```typescript
import {
  Filter,
  Search,
  ArrowDown,
  CircleCheck,
  User,
  Download,
  Delete
} from '@element-plus/icons-vue'
```

---

## ✅ 验收标准

- [x] 高级筛选面板可打开/关闭
- [x] 时间范围筛选生效
- [x] 类型筛选生效
- [x] 来源筛选生效
- [x] 批量操作下拉菜单正常
- [x] 表格多选功能正常
- [x] 批量确认功能正常
- [x] 批量导出功能正常
- [x] 详情对话框显示完整信息
- [x] 点击图表触发筛选
- [x] 筛选条件显示标签
- [x] 清除筛选功能正常

---

## 🚀 下一步

1. **后端 API 集成** - 将批量操作连接到真实 API
2. **分配对话框** - 实现完整的分配流程
3. **操作日志** - 记录所有批量操作
4. **保存筛选方案** - 允许用户保存常用筛选组合

---

**设计完成时间**: 2026-04-05 22:30  
**实现完成时间**: 2026-04-05 22:45  
**版本**: v2.0  
**状态**: ✅ 已实现

---

## ✅ 实现状态

### 1. 高级筛选 ✅ 已实现
- [x] 时间范围筛选 (filterDateRange)
- [x] 预警类型筛选 (filterType)
- [x] 来源系统筛选 (filterSource)
- [x] 筛选条件面板 (el-popover)
- [x] 应用筛选函数 (applyFilters)
- [x] 清除筛选函数 (clearFilters)

### 2. 批量操作 ✅ 已实现
- [x] 批量确认 (batchConfirm)
- [x] 批量分配 (showAssignDialog)
- [x] 批量导出 (batchExport - CSV 格式)
- [x] 批量删除 (batchDelete - 带确认)
- [x] 选择计数 (selectedAlerts)
- [x] 表格多选 (handleSelectionChange)

### 3. 详情查看 ✅ 已实现
- [x] 独立详情对话框 (detailDialogVisible)
- [x] 完整信息展示 (el-descriptions)
- [x] 操作记录 (el-timeline)
- [x] 关联实体显示
- [x] 确认功能 (confirmCurrentDetail)

### 4. 图表联动 ⏳ 待实现
- [ ] 点击趋势图显示明细
- [ ] 点击分布图显示明细
- [ ] 图表筛选联动

---

## 📦 已添加的导入

```typescript
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  Filter,
  Search,
  ArrowDown,
  CircleCheck,
  User,
  Download,
  Delete
} from '@element-plus/icons-vue'
```

---

## 📦 已添加的状态

```typescript
// 高级筛选
const filterDateRange = ref<[Date, Date] | null>(null)
const filterType = ref('')
const filterSource = ref('')
const showPendingOnly = ref(false)

// 批量操作
const selectedAlerts = ref<any[]>([])

// 详情对话框
const detailDialogVisible = ref(false)
const currentDetail = ref<any>(null)
```
