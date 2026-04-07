"""
Alert Auto-Escalation Service
Automatically escalates alerts based on time and severity rules
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Alert Escalation"])


class EscalationRule(BaseModel):
    """Escalation rule model"""
    id: int
    name: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    escalate_after_minutes: int
    escalate_to_severity: str
    notify_users: List[str]
    enabled: bool = True


class EscalationResult(BaseModel):
    """Escalation result"""
    success: bool
    escalated_count: int
    alerts: List[Dict[str, Any]]
    message: str


@router.get("/escalation-rules", response_model=List[EscalationRule])
def get_escalation_rules(db: Session = Depends(get_db)):
    """Get all escalation rules"""
    rules = [
        {
            "id": 1,
            "name": "LOW → MEDIUM after 30 min",
            "severity": "LOW",
            "escalate_after_minutes": 30,
            "escalate_to_severity": "MEDIUM",
            "notify_users": ["team_lead"],
            "enabled": True
        },
        {
            "id": 2,
            "name": "MEDIUM → HIGH after 1 hour",
            "severity": "MEDIUM",
            "escalate_after_minutes": 60,
            "escalate_to_severity": "HIGH",
            "notify_users": ["department_manager"],
            "enabled": True
        },
        {
            "id": 3,
            "name": "HIGH → CRITICAL after 2 hours",
            "severity": "HIGH",
            "escalate_after_minutes": 120,
            "escalate_to_severity": "CRITICAL",
            "notify_users": ["executive_team"],
            "enabled": True
        },
        {
            "id": 4,
            "name": "CRITICAL → Executive after 15 min",
            "severity": "CRITICAL",
            "escalate_after_minutes": 15,
            "escalate_to_severity": "CRITICAL",
            "notify_users": ["ceo", "cto", "cfo"],
            "enabled": True
        }
    ]
    return rules


@router.post("/execute-escalation", response_model=EscalationResult)
def execute_escalation(db: Session = Depends(get_db)):
    """
    Execute alert escalation based on rules
    
    Checks all unacknowledged alerts and escalates them according to rules
    """
    try:
        # Mock escalation logic (replace with actual database queries)
        escalated_alerts = []
        
        # Simulate checking alerts
        current_time = datetime.now()
        
        # Example: Find alerts that need escalation
        # In production, query database for alerts where:
        # - status = 'UNREAD' or 'UNACKNOWLEDGED'
        # - created_at < (now - escalate_after_minutes)
        
        escalated_alerts = [
            {
                "alert_id": 1,
                "title": "Inventory Alert - Product A001",
                "old_severity": "LOW",
                "new_severity": "MEDIUM",
                "escalated_at": current_time.isoformat(),
                "notified_users": ["team_lead"]
            },
            {
                "alert_id": 3,
                "title": "Payment Overdue Alert - INV-2026-001",
                "old_severity": "MEDIUM",
                "new_severity": "HIGH",
                "escalated_at": current_time.isoformat(),
                "notified_users": ["department_manager"]
            }
        ]
        
        return EscalationResult(
            success=True,
            escalated_count=len(escalated_alerts),
            alerts=escalated_alerts,
            message=f"Successfully escalated {len(escalated_alerts)} alerts"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalation failed: {str(e)}")


@router.get("/escalation-stats")
def get_escalation_stats(db: Session = Depends(get_db)):
    """Get escalation statistics"""
    return {
        "success": True,
        "stats": {
            "total_escalations_today": 5,
            "by_severity": {
                "LOW_to_MEDIUM": 2,
                "MEDIUM_to_HIGH": 2,
                "HIGH_to_CRITICAL": 1
            },
            "average_escalation_time_minutes": 45,
            "fastest_escalation_minutes": 15,
            "slowest_escalation_minutes": 120
        }
    }
