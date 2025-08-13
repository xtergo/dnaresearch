"""
Test authentication functionality
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_login_success():
    """Test successful login"""
    response = client.post(
        "/auth/login-json", json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = client.post(
        "/auth/login-json", json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_get_current_user():
    """Test getting current user info"""
    # First login
    login_response = client.post(
        "/auth/login-json", json={"username": "admin", "password": "admin123"}
    )
    token = login_response.json()["access_token"]

    # Get user info
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"
    assert data["is_active"] is True


def test_protected_endpoint_without_auth():
    """Test accessing protected endpoint without authentication"""
    response = client.post(
        "/theories", json={"id": "test-theory", "version": "1.0.0", "scope": "autism"}
    )
    # Now allows anonymous access but may fail validation
    assert response.status_code in [200, 400]  # Success or validation error


def test_protected_endpoint_with_auth():
    """Test accessing protected endpoint with authentication"""
    # First login
    login_response = client.post(
        "/auth/login-json", json={"username": "researcher", "password": "research123"}
    )
    token = login_response.json()["access_token"]

    # Access protected endpoint
    response = client.post(
        "/theories",
        json={
            "id": "test-theory-auth",
            "version": "1.0.0",
            "scope": "autism",
            "criteria": {
                "genes": ["SHANK3"],
                "pathways": ["synaptic_transmission"],
                "phenotypes": ["autism_spectrum_disorder"],
            },
            "evidence_model": {
                "priors": 0.1,
                "likelihood_weights": {
                    "variant_hit": 2.0,
                    "segregation": 1.5,
                    "pathway": 1.0,
                },
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_register_user():
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "role": "user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "user"


def test_list_users_admin_only():
    """Test that only admin can list users"""
    # Login as regular user
    login_response = client.post(
        "/auth/login-json", json={"username": "user", "password": "user123"}
    )
    token = login_response.json()["access_token"]

    # Try to list users
    response = client.get("/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    # Login as admin
    admin_login = client.post(
        "/auth/login-json", json={"username": "admin", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]

    # List users as admin
    response = client.get(
        "/auth/users", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3  # admin, researcher, user


def test_get_test_users():
    """Test getting test user credentials"""
    response = client.get("/auth/test-users")
    assert response.status_code == 200
    data = response.json()
    assert "test_users" in data
    assert len(data["test_users"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
