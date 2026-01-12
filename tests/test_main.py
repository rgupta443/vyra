"""
Basic tests for the main application setup.
"""
import pytest


def test_root_endpoint(client):
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Instagram Content Automation API"
    assert data["status"] == "healthy"


def test_health_endpoint(client):
    """Test the detailed health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "environment" in data


def test_api_endpoints_exist(client):
    """Test that API endpoints are properly registered."""
    # Test auth endpoints
    response = client.post("/api/v1/auth/register")
    assert response.status_code in [200, 422]  # 422 for missing body
    
    # Test user endpoints
    response = client.get("/api/v1/users/profile")
    assert response.status_code in [200, 401]  # 401 for unauthorized
    
    # Test face endpoints
    response = client.get("/api/v1/faces/current")
    assert response.status_code in [200, 401]  # 401 for unauthorized
    
    # Test generation endpoints
    response = client.get("/api/v1/generate/history")
    assert response.status_code in [200, 401]  # 401 for unauthorized
    
    # Test payment endpoints
    response = client.get("/api/v1/payments/plans")
    assert response.status_code in [200, 401]  # 401 for unauthorized