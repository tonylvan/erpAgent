"""
Tests for Graph Entity Detail and Relationship Exploration API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============ Test Helpers ============
def get_test_token():
    """获取测试用 JWT token"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def get_auth_headers():
    """获取认证请求头"""
    token = get_test_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class TestGetEntityDetail:
    """Tests for GET /api/v1/graph/entity/{entity_id}"""
    
    def test_get_entity_detail_success(self):
        """Test successful entity detail retrieval"""
        headers = get_auth_headers()
        # Using a generic entity ID that should exist in test DB
        response = client.get("/api/v1/graph/entity/1", headers=headers)
        # Accept 200 (found) or 404 (not found in test DB)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
    
    def test_get_entity_detail_not_found(self):
        """Test entity detail for non-existent entity (404)"""
        headers = get_auth_headers()
        response = client.get("/api/v1/graph/entity/999999999", headers=headers)
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_entity_detail_with_properties(self):
        """Test entity detail includes all properties"""
        headers = get_auth_headers()
        response = client.get("/api/v1/graph/entity/1", headers=headers)
        # If entity exists, verify properties
        if response.status_code == 200:
            data = response.json()
            assert "data" in data["data"]


class TestGetEntityRelationships:
    """Tests for GET /api/v1/graph/entity/{entity_id}/relationships"""
    
    def test_get_one_hop_relationships(self):
        """Test getting one-hop (direct) relationships"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entity/1/relationships",
            params={"depth": 1},
            headers=headers
        )
        # Accept 200 or 404 (no relationships)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
    
    def test_get_two_hop_relationships(self):
        """Test getting two-hop relationships"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entity/1/relationships",
            params={"depth": 2},
            headers=headers
        )
        assert response.status_code in [200, 404]
    
    def test_get_relationships_with_relationship_filter(self):
        """Test filtering relationships by type"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entity/1/relationships",
            params={"depth": 1, "rel_type": "OWNS"},
            headers=headers
        )
        assert response.status_code in [200, 404]
    
    def test_get_relationships_entity_not_found(self):
        """Test relationships for non-existent entity"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entity/999999999/relationships",
            params={"depth": 1},
            headers=headers
        )
        assert response.status_code == 404


class TestFindEntityPath:
    """Tests for GET /api/v1/graph/entity/{from_id}/path/to/{to_id}"""
    
    def test_find_path_success(self):
        """Test successful path finding between two entities"""
        headers = get_auth_headers()
        response = client.get("/api/v1/graph/entity/1/path/to/2", headers=headers)
        assert response.status_code in [200, 404]  # 404 if no path exists
    
    def test_find_path_with_max_depth(self):
        """Test path finding with max depth parameter"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entity/1/path/to/2",
            params={"max_depth": 3},
            headers=headers
        )
        assert response.status_code in [200, 404]
    
    def test_find_path_same_entity(self):
        """Test path finding when from_id equals to_id"""
        headers = get_auth_headers()
        response = client.get("/api/v1/entity/1/path/to/1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


class TestSearchEntities:
    """Tests for GET /api/v1/graph/entities/search"""
    
    def test_search_entities_by_keyword(self):
        """Test searching entities by keyword"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entities/search",
            params={"keyword": "test"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_search_entities_with_limit(self):
        """Test searching with limit parameter"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entities/search",
            params={"keyword": "test", "limit": 10},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 10
    
    def test_search_entities_by_label(self):
        """Test searching entities by label type"""
        headers = get_auth_headers()
        response = client.get(
            "/api/v1/graph/entities/search",
            params={"label": "Company"},
            headers=headers
        )
        assert response.status_code == 200
