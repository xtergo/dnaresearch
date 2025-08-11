# import pytest  # Unused import
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_swagger_ui_available():
    """Test Swagger UI is accessible at /docs"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_json_available():
    """Test OpenAPI JSON schema is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_interactive_functionality():
    """Test that OpenAPI schema contains interactive elements"""
    response = client.get("/openapi.json")
    data = response.json()

    # Check that endpoints are documented
    assert "/health" in data["paths"]
    assert "/genes/search" in data["paths"]

    # Check that health endpoint has proper documentation
    health_endpoint = data["paths"]["/health"]["get"]
    assert "summary" in health_endpoint
    assert "responses" in health_endpoint
