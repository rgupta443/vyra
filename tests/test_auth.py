"""
Basic tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that health endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_auth_me_requires_authentication():
    """Test that /me endpoint requires authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_register_endpoint_exists():
    """Test that register endpoint exists and validates input."""
    # Test with invalid email
    response = client.post("/api/v1/auth/register", json={
        "email": "invalid-email",
        "password": "testpass"
    })
    assert response.status_code == 422  # Validation error
    
    # Test with missing fields
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422


def test_login_endpoint_exists():
    """Test that login endpoint exists and validates input."""
    # Test with invalid email
    response = client.post("/api/v1/auth/login", json={
        "email": "invalid-email",
        "password": "testpass"
    })
    assert response.status_code == 422  # Validation error


def test_session_endpoints_exist():
    """Test that session-based endpoints exist."""
    response = client.post("/api/v1/auth/session/register", json={
        "email": "invalid-email",
        "password": "testpass"
    })
    assert response.status_code == 422  # Validation error
    
    response = client.post("/api/v1/auth/session/login", json={
        "email": "invalid-email", 
        "password": "testpass"
    })
    assert response.status_code == 422  # Validation error


def test_logout_endpoint():
    """Test that logout endpoint works."""
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data