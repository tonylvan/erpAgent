# Alert Center v2.0 - Product Design Document

**Version**: 2.0  
**Date**: 2026-04-06  
**Status**: Ready for Development

---

## 1. Product Overview

### 1.1 Purpose
Alert Center is the core monitoring module of GSD Platform, providing real-time risk warning, anomaly detection, and decision support for enterprises.

### 1.2 Target Users
- **Business Operations** - Daily business health monitoring
- **Risk Management** - Identify and handle potential risks
- **Executives** - View key metrics and trends
- **Data Analysts** - Deep dive into anomaly root causes

---

## 2. Functional Requirements

### 2.1 P0 - Core Features (Must Have)

#### 2.1.1 Real-time Alert Monitoring
- 4 alert statistic cards (Critical/Warning/Info/Processed)
- Auto-refresh every 30 seconds
- Color-coded alert levels

#### 2.1.2 Alert List
- Table view with all alerts
- Filter by level/status/time
- Search by title/content
- Pagination support

#### 2.1.3 Alert Details
- Click statistic cards to view details by level
- Modal dialog with full information
- CSV export support

#### 2.1.4 Alert Handling
- Acknowledge alerts (mark as read)
- Batch acknowledge
- Assign to specific personnel

### 2.2 P1 - Enhanced Features (Important)

#### 2.2.1 Trend Analysis
- 7-day/30-day alert trends
- Breakdown by level
- Year-over-year/Month-over-month comparison

#### 2.2.2 Distribution Analysis
- By business module
- By severity
- Pie chart/Bar chart

### 2.3 P2 - Advanced Features (Optional)

#### 2.3.1 Correlation Analysis
- Link to knowledge graph nodes
- Root cause analysis
- Impact assessment

#### 2.3.2 Notifications
- Email notifications
- WeChat Work/DingTalk push
- SMS for critical alerts

---

## 3. UI/UX Design

### 3.1 Layout

```
┌─────────────────────────────────────────────┐
│  Top Navigation [Alert | Query | Graph]     │
├─────────────────────────────────────────────┤
│  Statistics Cards (4 cards horizontal)       │
│  [Critical] [Warning] [Info] [Processed]    │
├─────────────────────────────────────────────┤
│  Trend Chart | Distribution (toggle)         │
├─────────────────────────────────────────────┤
│  Filter Toolbar                              │
│  [Search] [Level] [Status] [Date Range]     │
├─────────────────────────────────────────────┤
│  Alert List (Table)                          │
│  ┌───┬────┬────┬────┬────┬────┬────┐       │
│  │✓ │Level│Title│Time │Status│Action│      │
│  ├───┼────┼────┼────┼────┼────┼────┤       │
│  │  │🔴  |... │... │... │View │      │
│  └───┴────┴────┴────┴────┴────┴────┘       │
├─────────────────────────────────────────────┤
│  Pagination [1/10] [<] [1] [2] [3] [...] [>]│
└─────────────────────────────────────────────┘
```

### 3.2 Color Scheme

| Level | Primary | Gradient | Icon |
|-------|---------|----------|------|
| CRITICAL | #ff4d4f | #ff4d4f → #ff7875 | 🔴 |
| HIGH | #fa8c16 | #fa8c16 → #ffc53d | 🟠 |
| MEDIUM | #fadb14 | #fadb14 → #fff566 | 🟡 |
| LOW | #52c41a | #52c41a → #73d13d | 🟢 |

### 3.3 Interactions

1. **Card Click**
   - Hover: Card lifts + shadow deepens
   - Click: Open detail modal
   - Animation: 300ms ease-in-out

2. **Table Actions**
   - Row Hover: Background highlight
   - Acknowledge button: Green → Gray after click
   - Batch actions: Show toolbar when selected

3. **Filters**
   - Real-time search (type-as-you-go)
   - Multi-select dropdowns
   - Date range picker

---

## 4. Technical Architecture

### 4.1 Frontend Stack
- **Framework**: Vue 3 + TypeScript
- **UI Library**: Element Plus
- **Charts**: ECharts 5.x
- **State**: Pinia (optional)
- **Router**: Vue Router 4.x

### 4.2 Backend Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL + Neo4j
- **Cache**: Redis
- **Scheduler**: APScheduler

### 4.3 API Endpoints

```
# Alert Statistics
GET /api/v1/alerts/stats

# Alert List
GET /api/v1/alerts
  ?level=CRITICAL,HIGH
  &status=UNREAD,READ
  &search=keyword
  &page=1
  &size=20

# Alert Detail
GET /api/v1/alerts/{id}

# Acknowledge Alert
POST /api/v1/alerts/{id}/acknowledge

# Batch Acknowledge
POST /api/v1/alerts/batch-acknowledge
  { "ids": [1,2,3] }

# Export CSV
POST /api/v1/alerts/export
  { "filters": {...} }

# Alert Trend
GET /api/v1/alerts/trend
  ?days=7
  &granularity=day

# Alert Distribution
GET /api/v1/alerts/distribution
  ?dimension=business_module
```

---

## 5. Development Tasks

### Phase 1: Core Features (2 days)

#### Agent 1: Frontend Infrastructure
- [ ] Create AlertCenter_v3.vue component
- [ ] Implement top navigation
- [ ] Implement 4 statistic cards
- [ ] Implement alert list table
- [ ] Implement pagination

#### Agent 2: Backend API
- [ ] Create alerts_v3.py routes
- [ ] Implement GET /alerts/stats
- [ ] Implement GET /alerts (with filters)
- [ ] Implement POST /alerts/{id}/acknowledge
- [ ] Integrate PostgreSQL queries

#### Agent 3: Database
- [ ] Design alerts table schema
- [ ] Create database migration scripts
- [ ] Write sample data insertion scripts
- [ ] Optimize query performance (indexes)

### Phase 2: Charts & Analytics (1 day)

#### Agent 4: Data Visualization
- [ ] Implement trend chart (ECharts)
- [ ] Implement distribution chart (pie/bar)
- [ ] Implement chart linkage
- [ ] Add data refresh functionality

### Phase 3: Enhanced Features (1 day)

#### Agent 5: Interaction Optimization
- [ ] Implement detail modal
- [ ] Implement CSV export
- [ ] Implement batch operations
- [ ] Implement search/filter

#### Agent 6: Testing & Optimization
- [ ] Write unit tests
- [ ] Performance test (1000+ records)
- [ ] Bug fixes
- [ ] Optimize load time

---

## 6. Acceptance Criteria

### 6.1 Functional
- [ ] 4 statistic cards display correctly
- [ ] Click card shows corresponding level details
- [ ] Alert list displays correctly (paginated)
- [ ] Filter functionality works
- [ ] Acknowledge functionality works
- [ ] CSV export works

### 6.2 Performance
- [ ] First screen load < 2 seconds
- [ ] API response < 500ms
- [ ] Smooth display with 1000+ records
- [ ] Memory usage < 200MB

### 6.3 UI/UX
- [ ] Colors match design spec
- [ ] Smooth animations (60fps)
- [ ] Responsive layout (1920x1080, 1366x768)
- [ ] No console errors

### 6.4 Code Quality
- [ ] All comments in English
- [ ] Complete TypeScript types
- [ ] No ESLint warnings
- [ ] Git commit conventions

---

## 7. Development Workflow

```
Product Review → Tech Design → DB Design → Backend API
                ↓
            Frontend Components
                ↓
            Integration Test
                ↓
            Performance Optimization
                ↓
            User Acceptance
                ↓
            Deployment
```

---

## 8. Notes & Guidelines

### 8.1 Coding Standards
1. ✅ **All comments must be in English**
2. ✅ File encoding: UTF-8 (no BOM)
3. ✅ Use ESLint + Prettier
4. ✅ Git push before any file deletion

### 8.2 PowerShell Anti-Garbage
1. ✅ Use `chcp 65001` for UTF-8
2. ✅ PowerShell Profile configured
3. ✅ File writes use `-Encoding UTF8`
4. ✅ Avoid Chinese filenames

### 8.3 Security Requirements
1. ✅ JWT authentication required for APIs
2. ✅ Prevent SQL injection (parameterized queries)
3. ✅ Prevent XSS (escape user input)
4. ✅ Log sensitive operations

---

## 9. File Structure

```
D:\erpAgent\
├── frontend\
│   └── src\
│       ├── views\
│       │   └── AlertCenter_v3.vue      # New alert center
│       └── router\
│           └── index.js                # Updated routes
├── backend\
│   └── app\
│       └── api\
│           └── v1\
│               └── alerts_v3.py        # New alert routes
└── docs\
    └── alert-center-v2-design.md       # This document
```

---

**Status**: Ready for development  
**Next Step**: Assign agents to implement each phase
