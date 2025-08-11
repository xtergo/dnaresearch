import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import datetime

client = TestClient(app)

def test_health_endpoint_status():
    """Test health endpoint returns 200 status"""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_response_format():
    """Test health endpoint response format"""
    response = client.get("/health")
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"

def test_health_timestamp_format():
    """Test timestamp is in ISO format"""
    response = client.get("/health")
    data = response.json()
    
    # Should be able to parse ISO timestamp
    timestamp = data["timestamp"]
    assert timestamp.endswith("Z")
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))