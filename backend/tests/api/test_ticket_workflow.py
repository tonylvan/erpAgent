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


def test_resolve_ticket_success():
    """Test successful ticket resolution"""
    # First assign the ticket to put it in IN_PROGRESS state
    assign_response = client.post(
        "/api/v1/tickets/1/assign",
        json={"assigned_to": "user_123", "reason": "测试分配"}
    )
    assert assign_response.status_code == 200
    
    # Now resolve the ticket
    response = client.post(
        "/api/v1/tickets/1/resolve",
        json={
            "solution": "已与客户沟通，制定还款计划",
            "resolution_type": "negotiated"
        }
    )
    # Should return 200 with updated ticket
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_by"] is not None
    assert "resolved_at" in data
    assert data["resolved_at"] is not None


def test_resolve_ticket_not_found():
    """Test resolution of non-existent ticket (404)"""
    response = client.post(
        "/api/v1/tickets/99999/resolve",
        json={
            "solution": "测试解决方案",
            "resolution_type": "fixed"
        }
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_resolve_ticket_invalid_status():
    """Test resolution of ticket not in IN_PROGRESS state"""
    # First, assign and resolve ticket 1 to put it in RESOLVED state
    assign_response = client.post(
        "/api/v1/tickets/1/assign",
        json={"assigned_to": "user_test", "reason": "测试"}
    )
    assert assign_response.status_code == 200
    
    resolve_response = client.post(
        "/api/v1/tickets/1/resolve",
        json={"solution": "测试解决", "resolution_type": "fixed"}
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "RESOLVED"
    
    # Now try to resolve it again (should fail because it's already RESOLVED)
    response = client.post(
        "/api/v1/tickets/1/resolve",
        json={
            "solution": "再次解决",
            "resolution_type": "fixed"
        }
    )
    # Should return 400 Bad Request because ticket is not IN_PROGRESS
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_transfer_ticket_success():
    """Test successful ticket transfer"""
    # First assign the ticket
    assign_response = client.post(
        "/api/v1/tickets/1/assign",
        json={"assigned_to": "user_123", "reason": "初次分配"}
    )
    assert assign_response.status_code == 200
    print(f"Assign response: {assign_response.json()}")
    
    # Then transfer to another user
    response = client.post(
        "/api/v1/tickets/1/transfer",
        json={"transfer_to": "user_456", "reason": "非本部门职责"}
    )
    print(f"Transfer response status: {response.status_code}")
    print(f"Transfer response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_to"] == "user_456"
    assert data["status"] == "IN_PROGRESS"
    assert "id" in data


def test_transfer_ticket_not_found():
    """Test transfer of non-existent ticket (404)"""
    response = client.post(
        "/api/v1/tickets/99999/transfer",
        json={"transfer_to": "user_456", "reason": "测试"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_transfer_ticket_not_assigned():
    """Test transfer of unassigned ticket (should fail)"""
    # Create a new ticket that is not assigned
    create_response = client.post(
        "/api/v1/tickets",
        json={
            "title": "Test ticket for transfer",
            "description": "Testing transfer of unassigned ticket",
            "priority": "LOW",
            "category": "IT",
            "created_by": "user_000"
        }
    )
    if create_response.status_code == 200:
        ticket_id = create_response.json()["id"]
        
        # Try to transfer unassigned ticket
        response = client.post(
            f"/api/v1/tickets/{ticket_id}/transfer",
            json={"transfer_to": "user_456", "reason": "测试"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
