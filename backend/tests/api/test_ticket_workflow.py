"""
Tests for Ticket Workflow API routes
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_assign_ticket_success():
    """Test successful ticket assignment"""
    # First, we need to create a ticket or use an existing one
    # For now, we'll test with a mock ticket ID
    response = client.post(
        "/api/v1/tickets/1/assign",
        json={"assigned_to": "user_123", "reason": "专业匹配"}
    )
    # Should return 200 with updated ticket
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["assigned_to"] == "user_123"
    assert "id" in data
    assert "updated_at" in data


def test_assign_ticket_not_found():
    """Test assignment of non-existent ticket (404)"""
    response = client.post(
        "/api/v1/tickets/99999/assign",
        json={"assigned_to": "user_123", "reason": "测试"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_assign_ticket_duplicate():
    """Test re-assigning an already assigned ticket"""
    # First assignment
    response1 = client.post(
        "/api/v1/tickets/1/assign",
        json={"assigned_to": "user_123", "reason": "初次分配"}
    )
    assert response1.status_code == 200
    
    # Second assignment (should still succeed but update the assignment)
    response2 = client.post(
        "/api/v1/tickets/1/assign",
        json={"assigned_to": "user_456", "reason": "重新分配"}
    )
    assert response2.status_code == 200
    data = response2.json()
    assert data["assigned_to"] == "user_456"
    assert data["status"] == "IN_PROGRESS"
