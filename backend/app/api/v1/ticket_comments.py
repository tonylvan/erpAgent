"""
Ticket Comment CRUD API routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.db.database import get_db
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.ticket_comment import (
    TicketComment,
    TicketCommentBase,
    TicketCommentUpdate,
    TicketCommentResponse
)

router = APIRouter(prefix="/tickets")


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse)
def create_ticket_comment(
    ticket_id: int,
    comment_data: TicketCommentBase,
    db: Session = Depends(get_db)
):
    """
    Add a comment to a ticket
    
    - **ticket_id**: The ID of the ticket to comment on
    - **content**: Comment content (required, 1-10000 characters)
    - **author**: Optional author name
    - **author_role**: Optional author role
    - **is_internal**: Whether this is an internal comment (default: True)
    - **attachments**: Optional list of attachments
    """
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Create comment
    comment = TicketComment(
        ticket_id=ticket_id,
        content=comment_data.content,
        author=comment_data.author,
        author_role=comment_data.author_role,
        is_internal=comment_data.is_internal,
        attachments=comment_data.attachments if comment_data.attachments else []
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


@router.get("/{ticket_id}/comments")
def get_ticket_comments(
    ticket_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated comments list for a ticket
    
    - **ticket_id**: The ID of the ticket
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    
    Returns:
    - **items**: List of comments
    - **total**: Total number of comments
    - **page**: Current page number
    - **size**: Page size
    - **total_pages**: Total number of pages
    """
    # Query comments for this ticket
    query = db.query(TicketComment).filter(
        TicketComment.ticket_id == ticket_id
    )
    
    # Order by created_at desc (newest first)
    query = query.order_by(TicketComment.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Paginate
    comments = query.offset((page - 1) * size).limit(size).all()
    
    # Calculate total pages
    total_pages = (total + size - 1) // size if total > 0 else 1
    
    return {
        "items": [comment.to_dict() for comment in comments],
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages
    }


@router.get("/comments/{comment_id}", response_model=TicketCommentResponse)
def get_comment_by_id(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single comment by ID
    
    - **comment_id**: The ID of the comment to retrieve
    """
    comment = db.query(TicketComment).filter(
        TicketComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return comment


@router.put("/comments/{comment_id}", response_model=TicketCommentResponse)
def update_ticket_comment(
    comment_id: int,
    comment_data: TicketCommentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing comment
    
    - **comment_id**: The ID of the comment to update
    - **content**: Optional new content
    - **is_internal**: Optional update to internal flag
    - **attachments**: Optional update to attachments
    
    Only provided fields will be updated.
    """
    comment = db.query(TicketComment).filter(
        TicketComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Update provided fields
    update_data = comment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(comment, field) and value is not None:
            setattr(comment, field, value)
    
    db.commit()
    db.refresh(comment)
    
    return comment


@router.delete("/comments/{comment_id}")
def delete_ticket_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a comment
    
    - **comment_id**: The ID of the comment to delete
    """
    comment = db.query(TicketComment).filter(
        TicketComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(comment)
    db.commit()
    
    return {
        "message": "Comment deleted",
        "comment_id": comment_id
    }
