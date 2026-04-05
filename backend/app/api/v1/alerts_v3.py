from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== Models ====================

class AlertStats(BaseModel):
    """Alert statistics by severity level"""
    critical: int
    high: int
    medium: int
    low: int
    total: int

class Alert(BaseModel):
    """Alert data model"""
    id: int
    title: str
    level: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str  # UNREAD, READ, ACKNOWLEDGED
    created_at: str
    business_module: str
    description: Optional[str] = None

class AcknowledgeRequest(BaseModel):
    """Request body for batch acknowledge"""
    ids: List[int]

class ExportRequest(BaseModel):
    """Request body for export"""
    filters: Optional[dict] = None

# ==================== Mock Data ====================

MOCK_ALERTS = [
    {
        'id': 1,
        'title': 'Critical sales anomaly detected',
        'level': 'CRITICAL',
        'status': 'UNREAD',
        'business_module': 'Sales',
        'description': 'Sales dropped 45% compared to last week',
        'created_at': '2026-04-06T01:00:00'
    },
    {
        'id': 2,
        'title': 'Inventory level critically low',
        'level': 'HIGH',
        'status': 'UNREAD',
        'business_module': 'Warehouse',
        'description': 'Product SKU-1234 below safety stock',
        'created_at': '2026-04-06T00:30:00'
    },
    {
        'id': 3,
        'title': 'Payment overdue for 30 days',
        'level': 'MEDIUM',
        'status': 'READ',
        'business_module': 'Finance',
        'description': 'Customer ABC Corp payment overdue',
        'created_at': '2026-04-05T23:00:00'
    },
    {
        'id': 4,
        'title': 'Unusual login pattern detected',
        'level': 'LOW',
        'status': 'ACKNOWLEDGED',
        'business_module': 'Security',
        'description': 'Multiple failed login attempts from new IP',
        'created_at': '2026-04-05T22:00:00'
    },
    {
        'id': 5,
        'title': 'Production line efficiency below target',
        'level': 'HIGH',
        'status': 'UNREAD',
        'business_module': 'Manufacturing',
        'description': 'Line A efficiency at 72% vs target 85%',
        'created_at': '2026-04-05T20:00:00'
    },
]

# ==================== Endpoints ====================

@router.get('/stats', response_model=AlertStats)
async def get_alert_stats():
    """Get alert statistics grouped by severity level"""
    stats = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for alert in MOCK_ALERTS:
        level = alert['level'].lower()
        if level in stats:
            stats[level] += 1
    
    return AlertStats(
        critical=stats['critical'],
        high=stats['high'],
        medium=stats['medium'],
        low=stats['low'],
        total=len(MOCK_ALERTS)
    )

@router.get('/', response_model=List[Alert])
async def get_alerts(
    level: Optional[str] = Query(None, description='Filter by level (comma-separated)'),
    status: Optional[str] = Query(None, description='Filter by status (comma-separated)'),
    search: Optional[str] = Query(None, description='Search keyword in title'),
    page: int = Query(1, ge=1, description='Page number'),
    size: int = Query(20, ge=1, le=100, description='Page size')
):
    """Get alert list with filters and pagination"""
    result = MOCK_ALERTS.copy()
    
    # Apply level filter
    if level:
        levels = [l.strip().upper() for l in level.split(',')]
        result = [a for a in result if a['level'] in levels]
    
    # Apply status filter
    if status:
        statuses = [s.strip().upper() for s in status.split(',')]
        result = [a for a in result if a['status'] in statuses]
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        result = [a for a in result if search_lower in a['title'].lower() or search_lower in (a.get('description') or '').lower()]
    
    # Pagination
    start = (page - 1) * size
    end = start + size
    paginated = result[start:end]
    
    logger.info(f'Get alerts: level={level}, status={status}, search={search}, page={page}, size={size}, total={len(paginated)}')
    
    return [Alert(**alert) for alert in paginated]

@router.get('/{alert_id}')
async def get_alert(alert_id: int):
    """Get alert detail by ID"""
    for alert in MOCK_ALERTS:
        if alert['id'] == alert_id:
            return alert
    
    logger.warning(f'Alert {alert_id} not found')
    raise HTTPException(status_code=404, detail='Alert not found')

@router.post('/{alert_id}/acknowledge')
async def acknowledge_alert(alert_id: int):
    """Acknowledge a single alert"""
    for alert in MOCK_ALERTS:
        if alert['id'] == alert_id:
            alert['status'] = 'ACKNOWLEDGED'
            logger.info(f'Alert {alert_id} acknowledged')
            return {'success': True, 'message': 'Alert acknowledged'}
    
    raise HTTPException(status_code=404, detail='Alert not found')

@router.post('/batch-acknowledge')
async def batch_acknowledge(request: AcknowledgeRequest):
    """Batch acknowledge multiple alerts"""
    count = 0
    for alert in MOCK_ALERTS:
        if alert['id'] in request.ids:
            alert['status'] = 'ACKNOWLEDGED'
            count += 1
    
    logger.info(f'Batch acknowledge: {count} alerts acknowledged')
    return {'success': True, 'acknowledged_count': count}

@router.post('/export')
async def export_alerts(request: ExportRequest):
    """Export alerts to CSV format"""
    # In production, this would generate a CSV file
    # For now, return mock data
    return {
        'success': True,
        'message': 'Export functionality will be implemented in next iteration',
        'data': MOCK_ALERTS
    }
