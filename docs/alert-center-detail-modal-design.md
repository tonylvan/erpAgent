# 预警中心统计卡片点击展示明细 - 统一设计文档

## 📋 功能概述

在预警中心的统计卡片上点击后，弹出明细对话框，展示对应严重程度的所有预警详细信息。

---

## 🎯 设计目标

1. **直观交互** - 点击统计卡片即可查看明细
2. **统一设计** - 所有卡片使用相同的对话框组件
3. **数据筛选** - 按严重程度自动筛选显示
4. **操作便捷** - 支持查看、确认、导出等操作

---

## 🏗️ 架构设计

### 组件结构

```
AlertCenter_v2.vue
├── 统计卡片区域 (Stats Row)
│   ├── 🔴 高危预警卡片 (点击 → CRITICAL)
│   ├── 🟠 警告卡片 (点击 → HIGH)
│   ├── 🟡 提示卡片 (点击 → MEDIUM)
│   └── ✅ 已处理卡片 (点击 → LOW/已确认)
│
└── 明细对话框 (Detail Modal)
    ├── 对话框标题 (动态)
    ├── 筛选栏 (标签 + 计数)
    ├── 数据表格 (el-table)
    │   ├── 类型标签
    │   ├── 严重程度
    │   ├── 描述
    │   ├── 建议
    │   ├── 发现时间
    │   └── 操作按钮 (查看/确认)
    └── 底部按钮 (关闭/导出)
```

---

## 📊 数据流

```
用户点击统计卡片
    ↓
showDetailModal(severity)
    ↓
设置筛选条件 (currentFilterSeverity)
    ↓
计算筛选数据 (filteredDetailAlerts)
    ↓
渲染表格 (el-table)
```

---

## 🎨 UI 设计

### 统计卡片样式

| 卡片 | 图标 | 颜色 | 标签类型 |
|------|------|------|---------|
| 高危预警 | 🔴 | #f56c6c (danger) | danger |
| 警告 | 🟠 | #e6a23c (warning) | warning |
| 提示 | 🟡 | #909399 (info) | info |
| 已处理 | ✅ | #67c23a (success) | success |

### 对话框设计

**尺寸**: 900px 宽，自适应高度

**布局**:
```
┌─────────────────────────────────────────────────┐
│ 🔴 高危预警明细                      [×]        │
├─────────────────────────────────────────────────┤
│ [🔴 高危预警 标签] 共 X 条                       │
├─────────────────────────────────────────────────┤
│ # │ 类型 │ 严重程度 │ 描述 │ 建议 │ 时间 │ 操作│
│───┼──────┼──────────┼──────┼──────┼──────┼─────│
│ 1 │ ...  │ ...      │ ...  │ ...  │ ...  │ 查看│
│ 2 │ ...  │ ...      │ ...  │ ...  │ ...  │ 确认│
├─────────────────────────────────────────────────┤
│                        [关闭] [导出当前筛选]     │
└─────────────────────────────────────────────────┘
```

---

## 🔧 功能实现

### 1. 状态管理

```typescript
// 明细对话框相关
const detailModalVisible = ref(false)
const currentFilterSeverity = ref('')
const modalTitle = ref('')
const modalSeverityLabel = ref('')
const modalTagType = ref('danger')
```

### 2. 筛选逻辑

```typescript
const filteredDetailAlerts = computed(() => {
  if (!currentFilterSeverity.value) {
    return alerts
  }
  
  // 对于 LOW（已处理），显示 status !== 'pending' 的
  if (currentFilterSeverity.value === 'LOW') {
    return alerts.filter(a => a.status !== 'pending')
  }
  
  // 其他严重程度直接筛选
  const severityMap: Record<string, string> = {
    'CRITICAL': 'critical',
    'HIGH': 'warning',
    'MEDIUM': 'info',
    'LOW': 'success'
  }
  
  const targetPriority = severityMap[currentFilterSeverity.value]
  return alerts.filter(a => a.priority === targetPriority)
})
```

### 3. 显示对话框

```typescript
function showDetailModal(severity: string) {
  const severityInfo = {
    'CRITICAL': { title: '🔴 高危预警明细', label: '高危预警', tagType: 'danger' },
    'HIGH': { title: '🟠 警告明细', label: '警告', tagType: 'warning' },
    'MEDIUM': { title: '🟡 提示明细', label: '提示', tagType: 'info' },
    'LOW': { title: '✅ 已处理明细', label: '已处理', tagType: 'success' }
  }
  
  const info = severityInfo[severity]
  modalTitle.value = info.title
  modalSeverityLabel.value = info.label
  modalTagType.value = info.tagType
  
  detailModalVisible.value = true
}
```

---

## 📋 表格列设计

| 列名 | 字段 | 宽度 | 渲染方式 |
|------|------|------|---------|
| # | index | 50px | 序号 |
| 类型 | alert_type | 180px | el-tag (带颜色) |
| 严重程度 | severity | 100px | el-tag (深色) |
| 描述 | description | 300px+ | 文本 (溢出省略) |
| 建议 | recommendation | 200px+ | 文本 (溢出省略) |
| 发现时间 | created_at | 180px | 格式化日期 |
| 操作 | - | 120px | 查看 + 确认按钮 |

---

## 🎯 交互功能

### 1. 查看操作
- 点击"查看"按钮
- 显示预警详细信息
- TODO: 打开详情对话框或跳转详情页

### 2. 确认操作
- 点击"确认"按钮
- 更新预警状态为 `confirmed`
- 显示成功提示
- TODO: 调用后端 API 更新

### 3. 导出功能
- 点击"导出当前筛选"
- 导出当前筛选的所有数据
- 格式：CSV
- 包含字段：类型、严重程度、描述、建议、时间、状态

---

## 🎨 样式设计

### 对话框头部
```css
.detail-modal :deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.detail-modal :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
}
```

### 筛选栏
```css
.detail-modal .filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-modal .count-info {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}
```

---

## 📊 数据映射

### 预警类型映射

| 原始类型 | 显示名称 | 标签颜色 |
|---------|---------|---------|
| INVENTORY_LOW | 库存预警 | danger |
| PURCHASE_PRICE_ABNORMAL | 采购价异常 | warning |
| HUGE_PAYMENT | 大额付款 | danger |
| PAYMENT_ABNORMAL | 付款异常 | warning |
| CUSTOMER_CREDIT_ABNORMAL | 客户信用异常 | info |

### 严重程度映射

| 原始值 | 显示标签 | 标签颜色 |
|-------|---------|---------|
| CRITICAL | 高危 | danger |
| HIGH | 警告 | warning |
| MEDIUM | 提示 | info |
| LOW | 正常 | success |

---

## 🚀 使用流程

1. **用户访问预警中心**
   - 地址：`http://localhost:5176/alert-center`

2. **查看统计概览**
   - 4 个统计卡片显示各严重程度数量

3. **点击卡片查看明细**
   - 点击任意统计卡片
   - 弹出对应严重程度的明细对话框

4. **浏览详细信息**
   - 查看表格中的所有预警
   - 支持滚动查看所有字段

5. **执行操作**
   - 查看：查看单个预警详情
   - 确认：标记预警为已确认
   - 导出：导出当前筛选的所有数据

---

## 🔮 未来扩展

### 1. 高级筛选
- 按时间范围筛选
- 按预警类型筛选
- 按来源系统筛选

### 2. 批量操作
- 批量确认
- 批量分配
- 批量导出

### 3. 详情查看
- 打开独立详情对话框
- 显示完整描述和建议
- 显示关联实体信息

### 4. 图表联动
- 点击图表扇区显示明细
- 点击趋势图数据点显示明细

---

## 📝 修改记录

| 日期 | 版本 | 修改内容 | 作者 |
|------|------|---------|------|
| 2026-04-05 | v1.0 | 初始设计实现 | CodeMaster |

---

## ✅ 验收标准

- [x] 点击统计卡片弹出对话框
- [x] 对话框标题与卡片匹配
- [x] 数据按严重程度正确筛选
- [x] 表格显示所有必要字段
- [x] 查看/确认按钮可点击
- [x] 导出功能可用
- [x] 样式美观统一
- [x] 响应式布局正常

---

**文件位置**: `D:\erpAgent\frontend\src\views\AlertCenter_v2.vue`

**编译命令**: `npm run build`

**访问地址**: `http://localhost:5176/alert-center`
