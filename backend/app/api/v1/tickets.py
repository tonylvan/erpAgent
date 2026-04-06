"""
Ticket Center API routes - v3.0
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.db.database import get_db
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.task import Task, TaskStatus, TaskPriority
from app.services.ticket_workflow import TicketWorkflowService
from app.auth.jwt import get_current_user

router = APIRouter()


@router.get("/stats")
def get_ticket_stats(db: Session = Depends(get_db)):
    """Get ticket statistics by status and priority"""
    from sqlalchemy import func
    
    # Stats by status
    status_stats = db.query(
        Ticket.status,
        func.count(Ticket.id).label("count")
    ).group_by(Ticket.status).all()
    
    # Stats by priority
    priority_stats = db.query(
        Ticket.priority,
        func.count(Ticket.id).label("count")
    ).group_by(Ticket.priority).all()
    
    # Total count
    total = db.query(func.count(Ticket.id)).scalar()
    
    # Open tickets (not closed)
    open_count = db.query(func.count(Ticket.id)).filter(
        Ticket.status != "CLOSED"
    ).scalar()
    
    return {
        "by_status": {item.status: item.count for item in status_stats},
        "by_priority": {item.priority: item.count for item in priority_stats},
        "total": total,
        "open": open_count,
    }


@router.get("/")
def get_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated ticket list"""
    query = db.query(Ticket)
    
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if category:
        query = query.filter(Ticket.category == category)
    
    # Order by created_at desc
    query = query.order_by(Ticket.created_at.desc())
    
    # Pagination
    total = query.count()
    tickets = query.offset((page - 1) * size).limit(size).all()
    
    return [ticket.to_dict() for ticket in tickets]


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get single ticket by ID"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.to_dict()


@router.post("/")
def create_ticket(ticket_data: dict, db: Session = Depends(get_db)):
    """Create a new ticket"""
    ticket = Ticket(**ticket_data)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket.to_dict()


@router.put("/{ticket_id}")
def update_ticket(ticket_id: int, ticket_data: dict, db: Session = Depends(get_db)):
    """Update an existing ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update fields
    for key, value in ticket_data.items():
        if hasattr(ticket, key):
            setattr(ticket, key, value)
    
    db.commit()
    db.refresh(ticket)
    return ticket.to_dict()


@router.post("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int, 
    assign_data: dict, 
    db: Session = Depends(get_db)
):
    """Assign ticket to a user"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.assigned_to = assign_data.get("assigned_to")
    ticket.status = "IN_PROGRESS"
    db.commit()
    db.refresh(ticket)
    return ticket.to_dict()


@router.post("/{ticket_id}/transfer")
def transfer_ticket(
    ticket_id: int,
    transfer_data: dict,
    db: Session = Depends(get_db)
):
    """Transfer ticket to another user"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Verify ticket is assigned
    if not ticket.assigned_to:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket {ticket_id} is not assigned. Please assign it first before transferring."
        )
    
    old_assignee = ticket.assigned_to
    ticket.assigned_to = transfer_data.get("transfer_to")
    ticket.status = "IN_PROGRESS"
    
    db.commit()
    db.refresh(ticket)
    return {
        **ticket.to_dict(),
        "message": f"Ticket transferred from {old_assignee} to {transfer_data.get('transfer_to')}",
        "reason": transfer_data.get("reason")
    }


@router.post("/{ticket_id}/escalate")
def escalate_ticket(
    ticket_id: int,
    escalate_data: dict,
    db: Session = Depends(get_db)
):
    """Escalate ticket priority"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    old_priority = ticket.priority
    priority_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "URGENT": 3}
    
    current_level = priority_order.get(old_priority, 1)
    if current_level >= 3:
        raise HTTPException(status_code=400, detail="Ticket already at highest priority")
    
    # Escalate one level
    new_priority = list(priority_order.keys())[current_level + 1]
    ticket.priority = new_priority
    
    db.commit()
    db.refresh(ticket)
    return {
        **ticket.to_dict(),
        "message": f"Priority escalated from {old_priority} to {new_priority}",
        "reason": escalate_data.get("reason")
    }


@router.post("/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: int,
    resolve_data: dict,
    db: Session = Depends(get_db)
):
    """Resolve a ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Verify ticket status is IN_PROGRESS
    if ticket.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail=f"Ticket {ticket_id} cannot be resolved. Current status: {ticket.status}. Ticket must be IN_PROGRESS to resolve."
        )
    
    ticket.status = "RESOLVED"
    ticket.resolved_at = datetime.now()
    ticket.resolved_by = resolve_data.get("resolved_by", "system")
    ticket.solution = resolve_data.get("solution")
    ticket.resolution_type = resolve_data.get("resolution_type")
    ticket.resolution_notes = resolve_data.get("resolution_notes")
    
    db.commit()
    db.refresh(ticket)
    return ticket.to_dict()


@router.post("/{ticket_id}/close")
def close_ticket(ticket_id: int, close_data: dict, db: Session = Depends(get_db)):
    """Close a ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = "CLOSED"
    ticket.closed_at = datetime.now()
    ticket.closed_by = close_data.get("closed_by", "system")
    ticket.closing_notes = close_data.get("closing_notes")
    
    db.commit()
    db.refresh(ticket)
    return ticket.to_dict()


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete a ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    db.delete(ticket)
    db.commit()
    return {"message": "Ticket deleted"}


# Note: Comment APIs moved to ticket_comments.py
