# 🧠 智能问数 SmartQuery v3.0 实施计划

**创建时间**: 2026-04-06 23:30  
**版本**: v1.0  
**状态**: 🟡 准备启动  

---

## 📋 项目概述

### 产品定位
- **名称**: GSD 智能问数 SmartQuery v3.0
- **核心能力**: NL2Cypher + 风险预测 + 异常检测 + 知识问答
- **目标用户**: 财务经理、业务分析师、风控专员、高管
- **技术底座**: Neo4j 知识图谱 + LLM + 机器学习

### 四大核心功能

| 模块 | 功能 | 优先级 | 预计工时 |
|------|------|--------|---------|
| **数据查询** | NL2Cypher 引擎，自然语言查询 Neo4j 数据 | P0 | 2 周 |
| **风险预测** | 现金流/付款/库存/AR 风险预测 | P0 | 2 周 |
| **异常检测** | 虚假交易/关联交易/时序异常检测 | P1 | 2 周 |
| **知识问答** | RAG 架构，业务/领域/通识知识问答 | P1 | 2 周 |

---

## 🎯 Phase 1: NL2Cypher 引擎开发 (Week 1-2)

### 目标
实现自然语言到 Cypher 查询的自动转换，支持基础数据查询。

### 子任务

#### 1.1 意图识别模块
- **文件**: `backend/app/services/nl2cypher/intent_classifier.py`
- **功能**: 识别用户查询意图（实体查询/关系查询/统计查询/对比查询/排名查询）
- **技术**: sklearn + 规则匹配
- **测试**: `tests/services/test_intent_classifier.py`

#### 1.2 实体提取模块
- **文件**: `backend/app/services/nl2cypher/ner_extractor.py`
- **功能**: 提取查询中的实体（客户/供应商/产品/订单/时间等）
- **技术**: spaCy + 自定义 NER 模型
- **测试**: `tests/services/test_ner_extractor.py`

#### 1.3 关系映射模块
- **文件**: `backend/app/services/nl2cypher/relation_mapper.py`
- **功能**: 将实体映射到 Neo4j 关系类型
- **技术**: 规则引擎 + 知识图谱 schema
- **测试**: `tests/services/test_relation_mapper.py`

#### 1.4 Cypher 生成模块
- **文件**: `backend/app/services/nl2cypher/query_generator.py`
- **功能**: 根据意图、实体、关系生成 Cypher 查询
- **技术**: 模板引擎 + 查询构建器
- **测试**: `tests/services/test_query_generator.py`

#### 1.5 API 接口开发
- **文件**: `backend/app/api/v1/smart_query.py`
- **端点**: 
  - `POST /api/v1/smart-query/query` - 自然语言查询
  - `GET /api/v1/smart-query/schema` - 获取图谱 schema
- **测试**: `tests/api/test_smart_query_api.py`

#### 1.6 前端组件开发
- **文件**: `frontend/src/views/smart-query/QueryPanel.vue`
- **功能**: 
  - 对话式输入框
  - 查询结果展示（表格 + 图表）
  - 历史查询记录
- **测试**: `tests/frontend/smart-query/query-panel.spec.ts`

### 交付物
- ✅ NL2Cypher 引擎（支持 5 种查询类型）
- ✅ 后端 API 接口
- ✅ 前端查询面板
- ✅ 单元测试覆盖率 > 80%

---

## 📈 Phase 2: 风险预测模块 (Week 3-4)

### 目标
实现多维度风险预测功能，支持现金流、付款、库存等风险预测。

### 子任务

#### 2.1 现金流预测模型
- **文件**: `backend/app/services/prediction/cash_flow_predictor.py`
- **算法**: Prophet + LSTM
- **数据源**: 历史现金流 + 应收应付 + 销售数据
- **输出**: 未来 30/60/90 天现金流缺口预测
- **测试**: `tests/services/test_cash_flow_predictor.py`

#### 2.2 付款风险预测模型
- **文件**: `backend/app/services/prediction/payment_risk_predictor.py`
- **算法**: XGBoost + 生存分析
- **数据源**: 客户信用 + 交易历史 + AR 账龄
- **输出**: 客户违约概率 + 逾期风险评分
- **测试**: `tests/services/test_payment_risk_predictor.py`

#### 2.3 库存风险预测模型
- **文件**: `backend/app/services/prediction/inventory_risk_predictor.py`
- **算法**: 需求预测 + 安全库存模型
- **数据源**: 销售数据 + 库存数据 + 采购周期
- **输出**: 缺货/积压风险预警
- **测试**: `tests/services/test_inventory_risk_predictor.py`

#### 2.4 预测 API 开发
- **文件**: `backend/app/api/v1/smart_query.py` (扩展)
- **端点**: 
  - `POST /api/v1/smart-query/predict` - 风险预测
  - `GET /api/v1/smart-query/prediction/{id}` - 获取预测结果
- **测试**: `tests/api/test_prediction_api.py`

#### 2.5 前端预测面板
- **文件**: `frontend/src/views/smart-query/PredictionPanel.vue`
- **功能**: 
  - 风险类型选择
  - 时间范围设置
  - 预测结果可视化（仪表盘 + 趋势图）
  - 风险因素分析
- **测试**: `tests/frontend/smart-query/prediction-panel.spec.ts`

### 交付物
- ✅ 3 个风险预测模型
- ✅ 预测 API 接口
- ✅ 前端预测面板
- ✅ 模型评估报告

---

## 🚨 Phase 3: 异常检测模块 (Week 5-6)

### 目标
实现交易异常检测功能，发现虚假交易、关联交易等问题。

### 子任务

#### 3.1 虚假交易检测
- **文件**: `backend/app/services/detection/fraud_detector.py`
- **算法**: 交易网络分析 + 循环检测
- **功能**: 检测循环交易、关联交易
- **测试**: `tests/services/test_fraud_detector.py`

#### 3.2 先卖后租检测
- **文件**: `backend/app/services/detection/sale_leaseback_detector.py`
- **算法**: 资产流向追踪 + 时序分析
- **功能**: 检测资产出售后短期内租回
- **测试**: `tests/services/test_sale_leaseback_detector.py`

#### 3.3 老鼠仓检测
- **文件**: `backend/app/services/detection/insider_trading_detector.py`
- **算法**: 关联关系挖掘 + 时序异常
- **功能**: 检测内部人员提前交易
- **测试**: `tests/services/test_insider_trading_detector.py`

#### 3.4 时序异常检测
- **文件**: `backend/app/services/detection/time_series_anomaly.py`
- **算法**: Isolation Forest + Z-score
- **功能**: 价格异常、频率异常检测
- **测试**: `tests/services/test_time_series_anomaly.py`

#### 3.5 检测 API 开发
- **文件**: `backend/app/api/v1/smart_query.py` (扩展)
- **端点**: 
  - `POST /api/v1/smart-query/detect` - 异常检测
  - `GET /api/v1/smart-query/alerts` - 获取告警列表
- **测试**: `tests/api/test_detection_api.py`

#### 3.6 前端检测面板
- **文件**: `frontend/src/views/smart-query/DetectionPanel.vue`
- **功能**: 
  - 检测类型选择
  - 时间范围设置
  - 异常结果可视化（网络图 + 时间轴）
  - 告警详情展示
- **测试**: `tests/frontend/smart-query/detection-panel.spec.ts`

### 交付物
- ✅ 4 个异常检测模型
- ✅ 检测 API 接口
- ✅ 前端检测面板
- ✅ 异常检测报告

---

## 📚 Phase 4: 知识问答模块 (Week 7-8)

### 目标
实现 RAG 架构的知识问答系统，支持业务/领域/通识知识问答。

### 子任务

#### 4.1 知识库构建
- **文件**: `backend/app/services/knowledge/knowledge_base.py`
- **数据源**: 
  - ERP 业务流程文档
  - 财务规则/税务法规
  - 行业标准/外部研报
- **技术**: 文档解析 + 向量化
- **测试**: `tests/services/test_knowledge_base.py`

#### 4.2 向量检索引擎
- **文件**: `backend/app/services/knowledge/vector_search.py`
- **技术**: FAISS/Chroma + Embedding 模型
- **功能**: 语义检索 + 相似度排序
- **测试**: `tests/services/test_vector_search.py`

#### 4.3 RAG 生成引擎
- **文件**: `backend/app/services/knowledge/rag_engine.py`
- **技术**: LLM + 上下文组装
- **功能**: 基于检索结果生成答案
- **测试**: `tests/services/test_rag_engine.py`

#### 4.4 问答 API 开发
- **文件**: `backend/app/api/v1/smart_query.py` (扩展)
- **端点**: 
  - `POST /api/v1/smart-query/ask` - 知识问答
  - `GET /api/v1/smart-query/knowledge/{id}` - 获取知识详情
- **测试**: `tests/api/test_qa_api.py`

#### 4.5 前端问答面板
- **文件**: `frontend/src/views/smart-query/QAPanel.vue`
- **功能**: 
  - 对话式界面
  - 知识卡片展示
  - 相关推荐问题
  - 答案来源引用
- **测试**: `tests/frontend/smart-query/qa-panel.spec.ts`

### 交付物
- ✅ 知识库（包含企业文档 + 外部知识）
- ✅ RAG 引擎
- ✅ 问答 API 接口
- ✅ 前端问答面板

---

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI
- **数据库**: Neo4j (知识图谱) + PostgreSQL (业务数据)
- **ML 框架**: scikit-learn + XGBoost + Prophet
- **向量检索**: FAISS/Chroma
- **Embedding**: local-ollama (qwen2.5:7b)

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus
- **图表**: ECharts + D3.js
- **状态管理**: Pinia

### 部署架构
```
┌─────────────────┐
│   Frontend      │  (Nginx, port 80)
│   (Vue 3)       │
└────────┬────────┘
         │
┌────────┴────────┐
│   API Gateway   │  (FastAPI, port 8000)
│   (SmartQuery)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───┴───┐ ┌──┴───┐
│Neo4j  │ │PostgreSQL│
│(Graph)│ │(RDBMS) │
└───────┘ └───────┘
```

---

## 📊 成功指标

| 指标 | 目标值 | 测量方式 |
|------|--------|---------|
| **查询准确率** | > 85% | NL2Cypher 转换成功率 |
| **预测准确率** | > 80% | 风险预测模型 AUC |
| **响应时间** | < 3s | API P95 延迟 |
| **用户满意度** | > 4.5/5 | 用户反馈评分 |
| **测试覆盖率** | > 80% | pytest/vitest 覆盖率报告 |

---

## 🚀 下一步行动

### 立即执行（Phase 1.1）
1. ✅ 创建 NL2Cypher 引擎基础结构
2. ✅ 实现意图识别模块
3. ✅ 编写单元测试
4. ✅ 开发 API 接口

### 本周目标
- 完成 Phase 1.1-1.3（意图识别 + 实体提取 + 关系映射）
- 前端 QueryPanel 基础框架
- 端到端测试通过

---

**📝 备注**: 
- 每个子任务都需要先写测试（TDD 原则）
- 使用 subagent 驱动开发模式
- 每日提交代码到 Git
- 每周进行进度回顾

---

**状态**: 🟡 准备启动 Brainstorming 阶段
