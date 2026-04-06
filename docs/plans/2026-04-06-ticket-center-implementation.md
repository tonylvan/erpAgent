# 工单中心 v3.0 实施计划

**创建时间**: 2026-04-06 23:07  
**设计版本**: v3.0  
**设计文档**: `D:\erpAgent\docs\工单中心产品设计 v3.0.md`

---

## 📋 开发策略

**采用方案 A: 分阶段渐进式开发**（推荐）

### Phase 1: 核心工作流 (Week 1-2)
- ✅ 工单分配/转派/升级 API
- ✅ 工单评论功能
- ✅ 工单详情页组件
- ✅ 基础通知

### Phase 2: 智能派单 (Week 3-4)
- ⏳ 派单规则引擎
- ⏳ 规则配置页面
- ⏳ 自动分配逻辑

### Phase 3: 集成联动 (Week 5-6)
- ⏳ 预警中心集成
- ⏳ 智能问数集成
- ⏳ 一键生成工单

---

## 🎯 Phase 1 详细任务分解

### Task 1.1: 后端 API - 工单工作流
**文件**: `backend/app/api/v1/tickets.py`  
**内容**:
- POST `/api/v1/tickets/{id}/assign` - 分配工单
- POST `/api/v1/tickets/{id}/transfer` - 转派工单
- POST `/api/v1/tickets/{id}/escalate` - 升级工单
- POST `/api/v1/tickets/{id}/resolve` - 解决工单
- POST `/api/v1/tickets/{id}/close` - 关闭工单

**测试**: `backend/tests/test_ticket_workflow.py` (15 个测试用例)

---

### Task 1.2: 后端 API - 工单评论
**文件**: `backend/app/models/ticket_comment.py` + `backend/app/api/v1/ticket_comments.py`  
**内容**:
- 评论模型（ticket_comments 表）
- GET `/api/v1/tickets/{id}/comments` - 获取评论列表
- POST `/api/v1/tickets/{id}/comments` - 添加评论
- PUT `/api/v1/tickets/{id}/comments/{comment_id}` - 编辑评论
- DELETE `/api/v1/tickets/{id}/comments/{comment_id}` - 删除评论

**测试**: `backend/tests/test_ticket_comments.py` (10 个测试用例)

---

### Task 1.3: 后端服务 - 通知服务
**文件**: `backend/app/services/notification_service.py`  
**内容**:
- 站内通知（数据库存储）
- 邮件通知（SMTP）
- 微信通知（企业微信 webhook）
- 通知模板管理

**测试**: `backend/tests/test_notifications.py` (8 个测试用例)

---

### Task 1.4: 前端组件 - 工单详情页
**文件**: `frontend/src/views/TicketDetail.vue`  
**内容**:
- 工单基本信息展示
- 工作流操作按钮（分配/转派/升级/解决/关闭）
- 评论区域（列表 + 输入框）
- 操作日志时间线
- 关联预警/问题链接

**测试**: `frontend/tests/unit/TicketDetail.test.js` (12 个测试用例)

---

### Task 1.5: 前端组件 - 工单列表增强
**文件**: `frontend/src/views/TicketCenter.vue` (更新)  
**内容**:
- 快速操作菜单（右键菜单）
- 批量操作工具栏
- 高级筛选器（按状态/优先级/负责人）
- 工单统计卡片（更新为 6 个）

**测试**: `frontend/tests/unit/TicketCenter.test.js` (8 个测试用例)

---

### Task 1.6: 数据库迁移
**文件**: `backend/alembic/versions/xxxx_add_ticket_workflow.py`  
**内容**:
- 创建 `ticket_comments` 表
- 创建 `ticket_notifications` 表
- 创建 `ticket_workflow_logs` 表
- 添加外键约束和索引

---

### Task 1.7: SLA 时效管理
**文件**: `backend/app/services/sla_service.py`  
**内容**:
- SLA 规则配置（按优先级）
- 时效计算（响应时间/解决时间）
- 超时预警（提前 30 分钟通知）
- SLA 达成率统计

**测试**: `backend/tests/test_sla_service.py` (10 个测试用例)

---

## 📊 验收标准

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 后端 API 测试 | >30 个 | ⏳ - | ⏳ 待完成 |
| 前端组件测试 | >20 个 | ⏳ - | ⏳ 待完成 |
| 测试覆盖率 | >75% | ⏳ - | ⏳ 待完成 |
| 测试通过率 | 100% | ⏳ - | ⏳ 待完成 |
| API P99 延迟 | <200ms | ⏳ - | ⏳ 待完成 |

---

## 🚀 执行模式

**Subagent 驱动**（推荐）

每个任务由独立 subagent 完成：
- Subagent 1: Task 1.1 + 1.2（后端 API）
- Subagent 2: Task 1.3 + 1.7（服务层）
- Subagent 3: Task 1.4 + 1.5（前端组件）
- Subagent 4: Task 1.6（数据库迁移）

---

## 📝 下一步

1. ✅ 创建实施计划（当前）
2. ⏳ 开始 Task 1.1: 工单工作流 API
3. ⏳ 开始 Task 1.2: 工单评论 API
4. ⏳ 开始 Task 1.3: 通知服务
5. ⏳ 开始 Task 1.4: 工单详情页
6. ⏳ 开始 Task 1.5: 工单列表增强
7. ⏳ 开始 Task 1.6: 数据库迁移
8. ⏳ 开始 Task 1.7: SLA 服务

---

**准备就绪，等待开始执行！** 🚀
