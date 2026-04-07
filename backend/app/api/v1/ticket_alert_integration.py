"""
Ticket-Alert Integration API
Link alerts to tickets and vice versa
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Ticket-Alert Integration"])


class LinkAlertToTicket(BaseModel):
    """Request to link alert to ticket"""
    alert_id: int
    ticket_id: int
    relationship_type: str = "related_to"  # related_to, caused_by, resolved_by


class LinkResponse(BaseModel):
    """Link response"""
    success: bool
    link_id: int
    alert_id: int
    ticket_id: int
    relationship_type: str
    created_at: str
    message: str


class TicketAlertLink(BaseModel):
    """Ticket-Alert link model"""
    id: int
    alert_id: int
    alert_title: str
    alert_severity: str
    ticket_id: int
    ticket_title: str
    ticket_status: str
    relationship_type: str
    created_at: str


@router.post("/link-alert-to-ticket", response_model=LinkResponse)
def link_alert_to_ticket(
    link_data: LinkAlertToTicket,
    db: Session = Depends(get_db)
):
    """
    Link an alert to a ticket
    
    Creates a relationship between an alert and a ticket
    """
    try:
        # Mock link creation (replace with actual database operations)
        link_id = 1  # In production, get from database
        
        return LinkResponse(
            success=True,
            link_id=link_id,
            alert_id=link_data.alert_id,
            ticket_id=link_data.ticket_id,
            relationship_type=link_data.relationship_type,
            created_at=datetime.now().isoformat(),
            message=f"Successfully linked alert {link_data.alert_id} to ticket {link_data.ticket_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link: {str(e)}")


@router.get("/ticket/{ticket_id}/alerts")
def get_ticket_alerts(ticket_id: int, db: Session = Depends(get_db)):
    """Get all alerts linked to a ticket"""
    # Mock data
    alerts = [
        {
            "id": 1,
            "title": "Inventory Alert - Product A001",
            "severity": "MEDIUM",
            "status": "UNREAD",
            "created_at": datetime.now().isoformat(),
            "relationship_type": "caused_by"
        },
        {
            "id": 2,
            "title": "Payment Overdue Alert - INV-2026-001",
            "severity": "HIGH",
            "status": "READ",
            "created_at": datetime.now().isoformat(),
            "relationship_type": "related_to"
        }
    ]
    
    return {
        "success": True,
        "ticket_id": ticket_id,
        "alerts": alerts,
        "count": len(alerts)
    }


@router.get("/alert/{alert_id}/tickets")
def get_alert_tickets(alert_id: int, db: Session = Depends(get_db)):
    """Get all tickets linked to an alert"""
    # Mock data
    tickets = [
        {
            "id": 1,
            "title": "Follow up: Inventory Alert - Product A001",
            "status": "OPEN",
            "priority": "HIGH",
            "created_at": datetime.now().isoformat(),
            "relationship_type": "resolved_by"
        }
    ]
    
    return {
        "success": True,
        "alert_id": alert_id,
        "tickets": tickets,
        "count": len(tickets)
    }


@router.delete("/link/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    """Remove a ticket-alert link"""
    # Mock deletion
    return {
        "success": True,
        "link_id": link_id,
        "message": f"Successfully removed link {link_id}"
    }


@router.post("/auto-create-ticket-from-alert")
def auto_create_ticket_from_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Automatically create a ticket from an alert
    
    Useful for high-severity alerts that need immediate attention
    """
    try:
        # Mock ticket creation
        ticket = {
            "id": 100,
            "title": f"Auto-created from Alert #{alert_id}",
            "description": "This ticket was automatically created from a high-severity alert",
            "status": "OPEN",
            "priority": "HIGH",
            "created_from_alert_id": alert_id,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "ticket": ticket,
            "message": f"Successfully created ticket from alert {alert_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")
