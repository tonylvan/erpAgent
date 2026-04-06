"""
Tests for Ticket Comment CRUD API routes
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateComment:
    """Tests for POST /api/v1/tickets/{ticket_id}/comments"""
    
    def test_create_comment_success(self):
        """Test successful comment creation"""
        response = client.post(
            "/api/v1/tickets/1/comments",
            json={
                "content": "已联系客户，确认下周三付款",
                "is_internal": True,
                "attachments": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "已联系客户，确认下周三付款"
        assert data["is_internal"] == True
        assert data["ticket_id"] == 1
        assert "id" in data
        assert "created_at" in data
    
    def test_create_comment_with_author(self):
        """Test comment creation with author information"""
        response = client.post(
            "/api/v1/tickets/1/comments",
            json={
                "content": "内部备注：客户要求延期",
                "author": "张三",
                "author_role": "客服专员",
                "is_internal": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["author"] == "张三"
        assert data["author_role"] == "客服专员"
    
    def test_create_comment_ticket_not_found(self):
        """Test comment creation for non-existent ticket (404)"""
        response = client.post(
            "/api/v1/tickets/99999/comments",
            json={
                "content": "测试评论",
                "is_internal": False
            }
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_create_comment_empty_content(self):
        """Test comment creation with empty content (422)"""
        response = client.post(
            "/api/v1/tickets/1/comments",
            json={
                "content": "",
                "is_internal": False
            }
        )
        assert response.status_code == 422


class TestGetComments:
    """Tests for GET /api/v1/tickets/{ticket_id}/comments"""
    
    def test_get_comments_list(self):
        """Test getting comments list for a ticket"""
        response = client.get("/api/v1/tickets/1/comments")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["items"], list)
    
    def test_get_comments_with_pagination(self):
        """Test getting comments with pagination parameters"""
        response = client.get(
            "/api/v1/tickets/1/comments",
            params={"page": 1, "size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
    
    def test_get_comments_ticket_not_found(self):
        """Test getting comments for non-existent ticket"""
        response = client.get("/api/v1/tickets/99999/comments")
        assert response.status_code == 200  # Should return empty list, not 404


class TestGetSingleComment:
    """Tests for GET /api/v1/tickets/comments/{comment_id}"""
    
    def test_get_comment_by_id(self):
        """Test getting a single comment by ID"""
        # First create a comment
        create_response = client.post(
            "/api/v1/tickets/1/comments",
            json={"content": "测试评论", "is_internal": False}
        )
        if create_response.status_code == 200:
            comment_id = create_response.json()["id"]
            
            # Then get it
            response = client.get(f"/api/v1/tickets/comments/{comment_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == comment_id
            assert data["content"] == "测试评论"
    
    def test_get_comment_not_found(self):
        """Test getting non-existent comment (404)"""
        response = client.get("/api/v1/tickets/comments/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestUpdateComment:
    """Tests for PUT /api/v1/tickets/comments/{comment_id}"""
    
    def test_update_comment_success(self):
        """Test successful comment update"""
        # First create a comment
        create_response = client.post(
            "/api/v1/tickets/1/comments",
            json={"content": "原始评论", "is_internal": True}
        )
        if create_response.status_code == 200:
            comment_id = create_response.json()["id"]
            
            # Update it
            response = client.put(
                f"/api/v1/tickets/comments/{comment_id}",
                json={"content": "更新后的评论", "is_internal": False}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "更新后的评论"
            assert data["is_internal"] == False
            assert "updated_at" in data
    
    def test_update_comment_not_found(self):
        """Test updating non-existent comment (404)"""
        response = client.put(
            "/api/v1/tickets/comments/99999",
            json={"content": "更新内容"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_update_comment_partial(self):
        """Test partial update (only content)"""
        create_response = client.post(
            "/api/v1/tickets/1/comments",
            json={"content": "原始评论", "is_internal": True}
        )
        if create_response.status_code == 200:
            comment_id = create_response.json()["id"]
            
            # Update only content
            response = client.put(
                f"/api/v1/tickets/comments/{comment_id}",
                json={"content": "仅更新内容"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "仅更新内容"


class TestDeleteComment:
    """Tests for DELETE /api/v1/tickets/comments/{comment_id}"""
    
    def test_delete_comment_success(self):
        """Test successful comment deletion"""
        # First create a comment
        create_response = client.post(
            "/api/v1/tickets/1/comments",
            json={"content": "待删除的评论", "is_internal": True}
        )
        if create_response.status_code == 200:
            comment_id = create_response.json()["id"]
            
            # Delete it
            response = client.delete(f"/api/v1/tickets/comments/{comment_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Comment deleted"
            assert data["comment_id"] == comment_id
            
            # Verify it's deleted
            get_response = client.get(f"/api/v1/tickets/comments/{comment_id}")
            assert get_response.status_code == 404
    
    def test_delete_comment_not_found(self):
        """Test deleting non-existent comment (404)"""
        response = client.delete("/api/v1/tickets/comments/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
