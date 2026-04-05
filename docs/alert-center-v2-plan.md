# Alert Center v2.0 - Development Plan

**Created**: 2026-04-06 01:30  
**Status**: In Progress

---

## Phase 1: Backend API (Priority 1)

### Task 1.1: Create alerts_v3.py

**File**: `D:\erpAgent\backend\app\api\v1\alerts_v3.py`

**Endpoints**:
- `GET /api/v1/alerts/stats` - Alert statistics
- `GET /api/v1/alerts` - Alert list with filters
- `GET /api/v1/alerts/{id}` - Alert detail
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert
- `POST /api/v1/alerts/batch-acknowledge` - Batch acknowledge

**Implementation**:
```python
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Models
class AlertStats(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    total: int

class Alert(BaseModel):
    id: int
    title: str
    level: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str  # UNREAD, READ, ACKNOWLEDGED
    created_at: datetime
    business_module: str

# Mock data for development
MOCK_ALERTS = [
    {"id": 1, "title": "Sales anomaly detected", "level": "CRITICAL", "status": "UNREAD", "business_module": "Sales", "created_at": "2026-04-06T01:00:00"},
    {"id": 2, "title": "Inventory low", "level": "HIGH", "status": "UNREAD", "business_module": "Warehouse", "created_at": "2026-04-06T00:30:00"},
    {"id": 3, "title": "Payment overdue", "level": "MEDIUM", "status": "READ", "business_module": "Finance", "created_at": "2026-04-05T23:00:00"},
    {"id": 4, "title": "User login anomaly", "level": "LOW", "status": "ACKNOWLEDGED", "business_module": "Security", "created_at": "2026-04-05T22:00:00"},
]

@router.get("/stats", response_model=AlertStats)
async def get_alert_stats():
    """Get alert statistics by level"""
    stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for alert in MOCK_ALERTS:
        level = alert["level"].lower()
        if level in stats:
            stats[level] += 1
    return AlertStats(
        **stats,
        total=len(MOCK_ALERTS)
    )

@router.get("", response_model=List[Alert])
async def get_alerts(
    level: Optional[str] = Query(None, description="Filter by level (comma-separated)"),
    status: Optional[str] = Query(None, description="Filter by status (comma-separated)"),
    search: Optional[str] = Query(None, description="Search keyword"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    """Get alert list with filters"""
    result = MOCK_ALERTS.copy()
    
    # Apply filters
    if level:
        levels = [l.strip().upper() for l in level.split(",")]
        result = [a for a in result if a["level"] in levels]
    
    if status:
        statuses = [s.strip().upper() for s in status.split(",")]
        result = [a for a in result if a["status"] in statuses]
    
    if search:
        search_lower = search.lower()
        result = [a for a in result if search_lower in a["title"].lower()]
    
    # Pagination
    start = (page - 1) * size
    end = start + size
    paginated = result[start:end]
    
    return [Alert(**alert) for alert in paginated]

@router.get("/{alert_id}")
async def get_alert(alert_id: int):
    """Get alert detail by ID"""
    for alert in MOCK_ALERTS:
        if alert["id"] == alert_id:
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Acknowledge a single alert"""
    for alert in MOCK_ALERTS:
        if alert["id"] == alert_id:
            alert["status"] = "ACKNOWLEDGED"
            return {"success": True, "message": "Alert acknowledged"}
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/batch-acknowledge")
async def batch_acknowledge(alert_ids: List[int]):
    """Batch acknowledge alerts"""
    count = 0
    for alert in MOCK_ALERTS:
        if alert["id"] in alert_ids:
            alert["status"] = "ACKNOWLEDGED"
            count += 1
    return {"success": True, "acknowledged_count": count}
```

---

## Phase 2: Frontend Component (Priority 1)

### Task 2.1: Create AlertCenter_v3.vue

**File**: `D:\erpAgent\frontend\src\views\AlertCenter_v3.vue`

**Requirements**:
1. Top navigation (Alert/Query/Graph)
2. 4 statistic cards with colors
3. Alert list table
4. Pagination
5. Detail modal
6. Search/filter

**Key Features**:
- Vue 3 Composition API
- TypeScript
- Element Plus components
- English comments only
- UTF-8 encoding

---

## Phase 3: Integration (Priority 2)

### Task 3.1: Update Router

**File**: `D:\erpAgent\frontend\src\router\index.js`

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import AlertCenter_v3 from '../views/AlertCenter_v3.vue'
import SmartQuery from '../views/SmartQuery.vue'

const routes = [
  {
    path: '/',
    name: 'AlertCenter',
    component: AlertCenter_v3,
    meta: { title: 'Alert Center - GSD Platform' }
  },
  {
    path: '/smart-query',
    name: 'SmartQuery',
    component: SmartQuery,
    meta: { title: 'Smart Query - GSD Platform' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

---

## Execution Order

1. **First**: Create backend API (alerts_v3.py)
2. **Second**: Register route in main.py
3. **Third**: Create frontend component (AlertCenter_v3.vue)
4. **Fourth**: Update router
5. **Fifth**: Test end-to-end

---

## PowerShell Commands (UTF-8 Safe)

All file operations must use UTF-8 encoding:

```powershell
# Set UTF-8 encoding for current session
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Create file with UTF-8 encoding
$Content | Out-File -FilePath "path\to\file.py" -Encoding UTF8

# Or use Python for file creation (more reliable)
python -c "open('file.py', 'w', encoding='utf-8').write(content)"
```

---

**Next Action**: Start implementing Phase 1 (Backend API)
