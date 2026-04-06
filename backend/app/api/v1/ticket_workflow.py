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
from app.auth.jwt import get_current_user, UserInfo

router = APIRouter(tags=["Ticket Workflow"])


class AssignRequest(BaseModel):
    """Request model for ticket assignment"""
    assigned_to: str
    reason: Optional[str] = None


class ResolveRequest(BaseModel):
    """Request model for ticket resolution"""
    solution: str
    resolution_type: Optional[str] = None


class CloseRequest(BaseModel):
    """Request model for ticket closure"""
    close_reason: str
    satisfaction: Optional[str] = "satisfied"  # satisfied/unsatisfied


class TransferRequest(BaseModel):
    """Request model for ticket transfer"""
    transfer_to: str
    reason: Optional[str] = None


class ReopenRequest(BaseModel):
    """Request model for ticket reopening"""
    reopen_reason: str


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
    current_user: UserInfo = Depends(get_current_user)
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
    current_user: UserInfo = Depends(get_current_user)
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
    current_user: UserInfo = Depends(get_current_user)
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
async def close_ticket(
    ticket_id: int,
    data: CloseRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Close a ticket permanently (creator confirmation).
    
    Args:
        ticket_id: The ID of the ticket to close
        data: CloseRequest containing close_reason and optional satisfaction
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated ticket object
        
    Raises:
        HTTPException: 404 if ticket not found
        HTTPException: 400 if ticket status is not RESOLVED
    """
    # 1. Find ticket (404 if not found)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    # 2. Verify ticket status is RESOLVED
    if ticket.status != "RESOLVED":
        raise HTTPException(
            status_code=400,
            detail=f"Ticket {ticket_id} cannot be closed. Current status: {ticket.status}. Ticket must be RESOLVED to close."
        )
    
    # 3. Update status to CLOSED and record close_reason and satisfaction
    ticket.status = "CLOSED"
    ticket.close_reason = data.close_reason
    ticket.satisfaction = data.satisfaction
    ticket.closed_at = datetime.now()
    ticket.closed_by = current_user.get("username", "unknown")
    ticket.updated_at = datetime.now()
    
    # 4. Record operation log
    operation_log = TicketOperationLog(
        ticket_id=ticket_id,
        operation="CLOSE",
        performed_by=current_user.get("username", "unknown"),
        timestamp=datetime.now(),
        details={
            "close_reason": data.close_reason,
            "satisfaction": data.satisfaction,
        }
    )
    operation_logs.append(operation_log)
    
    # Commit changes
    db.commit()
    db.refresh(ticket)
    
    # 5. Return updated ticket
    return ticket.to_dict()


@router.post("/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: int,
    data: ReopenRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Reopen a closed ticket.
    
    Args:
        ticket_id: The ID of the ticket to reopen
        data: ReopenRequest containing reopen_reason
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated ticket object
        
    Raises:
        HTTPException: 404 if ticket not found
        HTTPException: 400 if ticket status is not CLOSED
    """
    # 1. Find ticket (404 if not found)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    # 2. Verify ticket status is CLOSED
    if ticket.status != "CLOSED":
        raise HTTPException(
            status_code=400,
            detail=f"Ticket {ticket_id} cannot be reopened. Current status: {ticket.status}. Ticket must be CLOSED to reopen."
        )
    
    # 3. Update status to OPEN and record reopen reason
    ticket.status = "OPEN"
    ticket.reopen_reason = data.reopen_reason
    ticket.reopened_at = datetime.now()
    ticket.reopened_by = current_user.username
    ticket.updated_at = datetime.now()
    
    # 4. Record operation log
    operation_log = TicketOperationLog(
        ticket_id=ticket_id,
        operation="REOPEN",
        performed_by=current_user.username,
        timestamp=datetime.now(),
        details={
            "reopen_reason": data.reopen_reason,
        }
    )
    operation_logs.append(operation_log)
    
    # Commit changes
    db.commit()
    db.refresh(ticket)
    
    # 5. Return updated ticket
    return ticket.to_dict()
