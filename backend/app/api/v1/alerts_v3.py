from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models.alert import Alert as DBAlert, AlertLevel, AlertStatus

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

# ==================== Database Endpoints ====================

@router.get('/stats', response_model=AlertStats)
async def get_alert_stats(db: Session = Depends(get_db)):
    """Get alert statistics grouped by severity level"""
    from sqlalchemy import func
    
    # Query counts by level
    critical = db.query(func.count(DBAlert.id)).filter(DBAlert.level == AlertLevel.CRITICAL).scalar() or 0
    high = db.query(func.count(DBAlert.id)).filter(DBAlert.level == AlertLevel.HIGH).scalar() or 0
    medium = db.query(func.count(DBAlert.id)).filter(DBAlert.level == AlertLevel.MEDIUM).scalar() or 0
    low = db.query(func.count(DBAlert.id)).filter(DBAlert.level == AlertLevel.LOW).scalar() or 0
    
    return AlertStats(
        critical=critical,
        high=high,
        medium=medium,
        low=low,
        total=critical + high + medium + low
    )

@router.get('/', response_model=List[Alert])
async def get_alerts(
    level: Optional[str] = Query(None, description='Filter by level (comma-separated)'),
    status: Optional[str] = Query(None, description='Filter by status (comma-separated)'),
    search: Optional[str] = Query(None, description='Search keyword in title'),
    page: int = Query(1, ge=1, description='Page number'),
    size: int = Query(20, ge=1, le=100, description='Page size'),
    db: Session = Depends(get_db)
):
    """Get alert list with filters and pagination"""
    from sqlalchemy import or_
    
    # Build query
    query = db.query(DBAlert)
    
    # Apply level filter
    if level:
        levels = [l.strip().upper() for l in level.split(',')]
        level_enums = [getattr(AlertLevel, l) for l in levels if hasattr(AlertLevel, l)]
        if level_enums:
            query = query.filter(DBAlert.level.in_(level_enums))
    
    # Apply status filter
    if status:
        statuses = [s.strip().upper() for s in status.split(',')]
        status_enums = [getattr(AlertStatus, s) for s in statuses if hasattr(AlertStatus, s)]
        if status_enums:
            query = query.filter(DBAlert.status.in_(status_enums))
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                DBAlert.title.ilike(search_pattern),
                DBAlert.description.ilike(search_pattern)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    alerts = query.order_by(DBAlert.created_at.desc()).offset(offset).limit(size).all()
    
    logger.info(f'Get alerts: level={level}, status={status}, search={search}, page={page}, size={size}, total={total}')
    
    return [
        Alert(
            id=alert.id,
            title=alert.title,
            level=alert.level.value,
            status=alert.status.value,
            business_module=alert.business_module,
            description=alert.description,
            created_at=alert.created_at.isoformat() if alert.created_at else None
        )
        for alert in alerts
    ]

@router.get('/{alert_id}')
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get alert detail by ID"""
    alert = db.query(DBAlert).filter(DBAlert.id == alert_id).first()
    
    if not alert:
        logger.warning(f'Alert {alert_id} not found')
        raise HTTPException(status_code=404, detail='Alert not found')
    
    return Alert(
        id=alert.id,
        title=alert.title,
        level=alert.level.value,
        status=alert.status.value,
        business_module=alert.business_module,
        description=alert.description,
        created_at=alert.created_at.isoformat() if alert.created_at else None
    )

@router.post('/{alert_id}/acknowledge')
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge a single alert"""
    from datetime import datetime
    
    alert = db.query(DBAlert).filter(DBAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail='Alert not found')
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    
    logger.info(f'Alert {alert_id} acknowledged')
    return {'success': True, 'message': 'Alert acknowledged'}

@router.post('/batch-acknowledge')
async def batch_acknowledge(request: AcknowledgeRequest, db: Session = Depends(get_db)):
    """Batch acknowledge multiple alerts"""
    from datetime import datetime
    
    count = db.query(DBAlert).filter(DBAlert.id.in_(request.ids)).update(
        {
            DBAlert.status: AlertStatus.ACKNOWLEDGED,
            DBAlert.acknowledged_at: datetime.utcnow()
        },
        synchronize_session=False
    )
    db.commit()
    
    logger.info(f'Batch acknowledge: {count} alerts acknowledged')
    return {'success': True, 'acknowledged_count': count}

@router.post('/export')
async def export_alerts(request: ExportRequest, db: Session = Depends(get_db)):
    """Export alerts to CSV format"""
    # Get all alerts (with optional filters)
    query = db.query(DBAlert)
    
    if request.filters:
        if 'level' in request.filters:
            levels = request.filters['level']
            level_enums = [getattr(AlertLevel, l.upper()) for l in levels if hasattr(AlertLevel, l.upper())]
            if level_enums:
                query = query.filter(DBAlert.level.in_(level_enums))
        
        if 'status' in request.filters:
            statuses = request.filters['status']
            status_enums = [getattr(AlertStatus, s.upper()) for s in statuses if hasattr(AlertStatus, s.upper())]
            if status_enums:
                query = query.filter(DBAlert.status.in_(status_enums))
    
    alerts = query.all()
    
    # In production, this would generate a CSV file
    # For now, return JSON data
    return {
        'success': True,
        'message': f'Exported {len(alerts)} alerts',
        'data': [
            {
                'id': alert.id,
                'title': alert.title,
                'level': alert.level.value,
                'status': alert.status.value,
                'business_module': alert.business_module,
                'created_at': alert.created_at.isoformat() if alert.created_at else None
            }
            for alert in alerts
        ]
    }
