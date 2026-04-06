"""
Ticket Workflow API routes

This module provides workflow operations for tickets including:
- Assign: Assign ticket to a user
- Transfer: Transfer ticket to another agent/department
- Escalate: Escalate ticket to higher priority or management
- Resolve: Mark ticket as resolved
- Close: Close ticket permanently
- Reopen: Reopen a closed ticket
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.ticket import Ticket
from app.auth.jwt import get_current_user

router = APIRouter(tags=["Ticket Workflow"])


class AssignRequest(BaseModel):
    """Request model for ticket assignment"""
    assigned_to: str
    reason: Optional[str] = None


class ResolveRequest(BaseModel):
    """Request model for ticket resolution"""
    solution: str
    resolution_type: Optional[str] = None


class TransferRequest(BaseModel):
    """Request model for ticket transfer"""
    transfer_to: str
    reason: Optional[str] = None


class TicketOperationLog(BaseModel):
    """Model for ticket operation log (in-memory for now)"""
    ticket_id: int
    operation: str
    performed_by: str
    timestamp: datetime
    details: Dict[str, Any]


# In-memory operation log storage (TODO: Replace with database model)
operation_logs: list[TicketOperationLog] = []


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    data: AssignRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a ticket to a user.
    
    Args:
        ticket_id: The ID of the ticket to assign
        data: AssignRequest containing assigned_to user ID and optional reason
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated ticket object
        
    Raises:
        HTTPException: 404 if ticket not found
    """
    # 1. Find ticket (404 if not found)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    # 2. Update assigned_to and status (IN_PROGRESS)
    old_assigned_to = ticket.assigned_to
    ticket.assigned_to = data.assigned_to
    ticket.status = "IN_PROGRESS"
    ticket.updated_at = datetime.now()
    
    # 3. Record operation log
    operation_log = TicketOperationLog(
        ticket_id=ticket_id,
        operation="ASSIGN",
        performed_by=current_user.get("username", "unknown"),
        timestamp=datetime.now(),
        details={
            "from": old_assigned_to,
            "to": data.assigned_to,
            "reason": data.reason,
        }
    )
    operation_logs.append(operation_log)
    
    # Commit changes
    db.commit()
    db.refresh(ticket)
    
    # 4. Return updated ticket
    return ticket.to_dict()


@router.post("/{ticket_id}/transfer")
async def transfer_ticket(
    ticket_id: int,
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Transfer a ticket to another agent or department.
    
    Args:
        ticket_id: The ID of the ticket to transfer
        data: TransferRequest containing transfer_to user ID and optional reason
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated ticket object
        
    Raises:
        HTTPException: 404 if ticket not found
        HTTPException: 400 if ticket is not assigned
    """
    # 1. Find ticket (404 if not found)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    # 2. Verify ticket is assigned (cannot transfer unassigned ticket)
    if not ticket.assigned_to:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket {ticket_id} is not assigned. Please assign it first before transferring."
        )
    
    # 3. Update assigned_to (keep status as IN_PROGRESS)
    old_assigned_to = ticket.assigned_to
    ticket.assigned_to = data.transfer_to
    ticket.status = "IN_PROGRESS"  # Keep status as IN_PROGRESS
    ticket.updated_at = datetime.now()
    
    # 4. Record operation log
    operation_log = TicketOperationLog(
        ticket_id=ticket_id,
        operation="TRANSFER",
        performed_by=current_user.get("username", "unknown"),
        timestamp=datetime.now(),
        details={
            "from": old_assigned_to,
            "to": data.transfer_to,
            "reason": data.reason,
        }
    )
    operation_logs.append(operation_log)
    
    # Commit changes
    db.commit()
    db.refresh(ticket)
    
    # 5. Return updated ticket
    return ticket.to_dict()


@router.post("/{ticket_id}/escalate")
def escalate_ticket(ticket_id: int, escalate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Escalate a ticket to higher priority or management.
    
    Args:
        ticket_id: The ID of the ticket to escalate
        escalate_data: Dictionary containing 'reason' and optionally 'new_priority'
        
    Returns:
        Test response confirming escalation
    """
    # TODO: Implement actual escalation logic
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} escalation endpoint ready",
        "ticket_id": ticket_id,
        "reason": escalate_data.get("reason"),
    }


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    data: ResolveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a ticket as resolved.
    
    Args:
        ticket_id: The ID of the ticket to resolve
        data: ResolveRequest containing solution and optional resolution_type
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated ticket object
        
    Raises:
        HTTPException: 404 if ticket not found
        HTTPException: 400 if ticket status is not IN_PROGRESS
    """
    # 1. Find ticket (404 if not found)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    # 2. Verify ticket status is IN_PROGRESS
    if ticket.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400, 
            detail=f"Ticket {ticket_id} cannot be resolved. Current status: {ticket.status}. Ticket must be IN_PROGRESS to resolve."
        )
    
    # 3. Update status to RESOLVED and record solution
    ticket.status = "RESOLVED"
    ticket.solution = data.solution
    ticket.resolution_type = data.resolution_type
    ticket.resolved_at = datetime.now()
    ticket.resolved_by = current_user.get("username", "unknown")
    ticket.updated_at = datetime.now()
    
    # 4. Record operation log
    operation_log = TicketOperationLog(
        ticket_id=ticket_id,
        operation="RESOLVE",
        performed_by=current_user.get("username", "unknown"),
        timestamp=datetime.now(),
        details={
            "solution": data.solution,
            "resolution_type": data.resolution_type,
        }
    )
    operation_logs.append(operation_log)
    
    # Commit changes
    db.commit()
    db.refresh(ticket)
    
    # 5. Return updated ticket
    return ticket.to_dict()


@router.post("/{ticket_id}/close")
def close_ticket(ticket_id: int, close_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Close a ticket permanently.
    
    Args:
        ticket_id: The ID of the ticket to close
        close_data: Dictionary containing 'closed_by' user ID
        
    Returns:
        Test response confirming closure
    """
    # TODO: Implement actual closure logic
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} closure endpoint ready",
        "ticket_id": ticket_id,
        "closed_by": close_data.get("closed_by"),
    }


@router.post("/{ticket_id}/reopen")
def reopen_ticket(ticket_id: int, reopen_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reopen a closed ticket.
    
    Args:
        ticket_id: The ID of the ticket to reopen
        reopen_data: Dictionary containing 'reason' for reopening
        
    Returns:
        Test response confirming reopening
    """
    # TODO: Implement actual reopening logic
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} reopen endpoint ready",
        "ticket_id": ticket_id,
        "reason": reopen_data.get("reason"),
    }
