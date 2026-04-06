"""
Test suite for Ticket Comment CRUD API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.database import Base, get_db, engine, SessionLocal
from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment


# Use PostgreSQL for testing (same as production)
# Create test database engine
test_engine = create_engine(
    engine.url.render_as_string(),
    pool_pre_ping=True,
    echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create tables before each test"""
    # Drop all tables and recreate
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session():
    """Create a new database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_ticket(db_session):
    """Create a sample ticket for testing"""
    ticket = Ticket(
        title="Test Ticket",
        description="Test Description",
        status="open",
        priority="medium",
        created_by="user_123"
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


class TestCreateTicketComment:
    """Test POST /api/v1/tickets/{ticket_id}/comments"""
    
    def test_create_comment_success(self, client, sample_ticket):
        """Test creating a comment successfully"""
        response = client.post(
            f"/api/v1/tickets/{sample_ticket.id}/comments",
            json={
                "content": "已联系客户，确认下周三付款",
                "is_internal": True,
                "attachments": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == sample_ticket.id
        assert data["content"] == "已联系客户，确认下周三付款"
        assert data["is_internal"] == True
        assert "id" in data
        assert "created_at" in data
    
    def test_create_comment_with_author(self, client, sample_ticket):
        """Test creating a comment with author information"""
        response = client.post(
            f"/api/v1/tickets/{sample_ticket.id}/comments",
            json={
                "content": "Technical analysis completed",
                "author": "John Doe",
                "author_role": "engineer",
                "is_internal": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["author"] == "John Doe"
        assert data["author_role"] == "engineer"
        assert data["is_internal"] == False
    
    def test_create_comment_ticket_not_found(self, client):
        """Test creating a comment for non-existent ticket"""
        response = client.post(
            "/api/v1/tickets/99999/comments",
            json={
                "content": "This should fail"
            }
        )
        
        assert response.status_code == 404
        assert "Ticket not found" in response.json()["detail"]
    
    def test_create_comment_empty_content(self, client, sample_ticket):
        """Test creating a comment with empty content"""
        response = client.post(
            f"/api/v1/tickets/{sample_ticket.id}/comments",
            json={
                "content": ""
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_comment_missing_content(self, client, sample_ticket):
        """Test creating a comment without content"""
        response = client.post(
            f"/api/v1/tickets/{sample_ticket.id}/comments",
            json={
                "is_internal": True
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestGetTicketComments:
    """Test GET /api/v1/tickets/{ticket_id}/comments"""
    
    def test_get_comments_empty(self, client, sample_ticket):
        """Test getting comments when there are none"""
        response = client.get(f"/api/v1/tickets/{sample_ticket.id}/comments")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["total_pages"] == 1
    
    def test_get_comments_with_data(self, client, sample_ticket, db_session):
        """Test getting comments with existing data"""
        # Create test comments
        for i in range(5):
            comment = TicketComment(
                ticket_id=sample_ticket.id,
                content=f"Comment {i}",
                is_internal=False
            )
            db_session.add(comment)
        db_session.commit()
        
        response = client.get(f"/api/v1/tickets/{sample_ticket.id}/comments")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["size"] == 20
    
    def test_get_comments_pagination(self, client, sample_ticket, db_session):
        """Test comment pagination"""
        # Create 25 comments
        for i in range(25):
            comment = TicketComment(
                ticket_id=sample_ticket.id,
                content=f"Comment {i}",
                is_internal=False
            )
            db_session.add(comment)
        db_session.commit()
        
        # Get first page
        response = client.get(
            f"/api/v1/tickets/{sample_ticket.id}/comments",
            params={"page": 1, "size": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["total_pages"] == 3
        
        # Get second page
        response = client.get(
            f"/api/v1/tickets/{sample_ticket.id}/comments",
            params={"page": 2, "size": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2
    
    def test_get_comments_ticket_not_found(self, client):
        """Test getting comments for non-existent ticket"""
        response = client.get("/api/v1/tickets/99999/comments")
        
        # Should return empty list, not error
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestGetCommentById:
    """Test GET /api/v1/tickets/comments/{comment_id}"""
    
    def test_get_comment_success(self, client, sample_ticket, db_session):
        """Test getting a single comment by ID"""
        comment = TicketComment(
            ticket_id=sample_ticket.id,
            content="Single comment test",
            is_internal=False
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        response = client.get(f"/api/v1/tickets/comments/{comment.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == comment.id
        assert data["content"] == "Single comment test"
    
    def test_get_comment_not_found(self, client):
        """Test getting a non-existent comment"""
        response = client.get("/api/v1/tickets/comments/99999")
        
        assert response.status_code == 404
        assert "Comment not found" in response.json()["detail"]


class TestUpdateTicketComment:
    """Test PUT /api/v1/tickets/comments/{comment_id}"""
    
    def test_update_comment_success(self, client, sample_ticket, db_session):
        """Test updating a comment"""
        comment = TicketComment(
            ticket_id=sample_ticket.id,
            content="Original content",
            is_internal=True
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        response = client.put(
            f"/api/v1/tickets/comments/{comment.id}",
            json={
                "content": "Updated content",
                "is_internal": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_internal"] == False
        assert data["id"] == comment.id
    
    def test_update_comment_partial(self, client, sample_ticket, db_session):
        """Test partially updating a comment"""
        comment = TicketComment(
            ticket_id=sample_ticket.id,
            content="Original content",
            is_internal=True
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        # Only update content
        response = client.put(
            f"/api/v1/tickets/comments/{comment.id}",
            json={
                "content": "New content only"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "New content only"
        assert data["is_internal"] == True  # Unchanged
    
    def test_update_comment_not_found(self, client):
        """Test updating a non-existent comment"""
        response = client.put(
            "/api/v1/tickets/comments/99999",
            json={"content": "Test"}
        )
        
        assert response.status_code == 404
        assert "Comment not found" in response.json()["detail"]
    
    def test_update_comment_empty_content(self, client, sample_ticket, db_session):
        """Test updating with empty content"""
        comment = TicketComment(
            ticket_id=sample_ticket.id,
            content="Original content",
            is_internal=True
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        response = client.put(
            f"/api/v1/tickets/comments/{comment.id}",
            json={"content": ""}
        )
        
        assert response.status_code == 422  # Validation error


class TestDeleteTicketComment:
    """Test DELETE /api/v1/tickets/comments/{comment_id}"""
    
    def test_delete_comment_success(self, client, sample_ticket, db_session):
        """Test deleting a comment"""
        comment = TicketComment(
            ticket_id=sample_ticket.id,
            content="To be deleted",
            is_internal=False
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        response = client.delete(f"/api/v1/tickets/comments/{comment.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Comment deleted"
        assert data["comment_id"] == comment.id
        
        # Verify deletion
        response = client.get(f"/api/v1/tickets/comments/{comment.id}")
        assert response.status_code == 404
    
    def test_delete_comment_not_found(self, client):
        """Test deleting a non-existent comment"""
        response = client.delete("/api/v1/tickets/comments/99999")
        
        assert response.status_code == 404
        assert "Comment not found" in response.json()["detail"]
    
    def test_delete_comment_verification(self, client, sample_ticket, db_session):
        """Test that deleted comment is removed from list"""
        # Create comment
        comment = TicketComment(
            ticket_id=sample_ticket.id,
            content="To be deleted",
            is_internal=False
        )
        db_session.add(comment)
        db_session.commit()
        
        # Delete
        client.delete(f"/api/v1/tickets/comments/{comment.id}")
        
        # Verify it's not in the list
        response = client.get(f"/api/v1/tickets/{sample_ticket.id}/comments")
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
