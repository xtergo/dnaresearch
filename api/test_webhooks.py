"""Tests for webhook functionality"""

import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_webhook_sequencing_complete():
    """Test sequencing complete webhook"""
    webhook_data = {
        "event_type": "sequencing_complete",
        "sample_id": "sample_001",
        "run_id": "run_20250111_001",
        "file_urls": [
            "https://partner.com/files/sample_001_R1.fastq.gz",
            "https://partner.com/files/sample_001_R2.fastq.gz"
        ],
        "metadata": {
            "instrument": "NovaSeq 6000",
            "run_date": "2025-01-11T10:00:00Z"
        }
    }
    
    response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    assert data["partner_id"] == "illumina"
    assert data["event_type"] == "sequencing_complete"
    assert "event_id" in data
    assert "timestamp" in data


def test_webhook_qc_complete():
    """Test QC complete webhook"""
    webhook_data = {
        "event_type": "qc_complete",
        "sample_id": "sample_002",
        "qc_metrics": {
            "passed": True,
            "quality_score": 35.2,
            "coverage": "30x"
        }
    }
    
    response = client.post("/webhooks/sequencing/oxford", json=webhook_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    assert data["partner_id"] == "oxford"
    assert data["event_type"] == "qc_complete"


def test_webhook_analysis_complete():
    """Test analysis complete webhook"""
    webhook_data = {
        "event_type": "analysis_complete",
        "sample_id": "sample_003",
        "analysis_results": {
            "variant_count": 4567,
            "analysis_type": "whole_genome",
            "reference": "GRCh38"
        }
    }
    
    response = client.post("/webhooks/sequencing/pacbio", json=webhook_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    assert data["partner_id"] == "pacbio"
    assert data["event_type"] == "analysis_complete"


def test_webhook_with_signature():
    """Test webhook with valid signature"""
    webhook_data = {
        "event_type": "sequencing_complete",
        "sample_id": "sample_004"
    }
    
    # Create valid signature
    payload = json.dumps(webhook_data, sort_keys=True)
    secret = "illumina_webhook_secret_key"
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    
    response = client.post(
        "/webhooks/sequencing/illumina",
        json=webhook_data,
        headers={"X-Signature": f"sha256={signature}"}
    )
    assert response.status_code == 200


def test_webhook_invalid_signature():
    """Test webhook with invalid signature"""
    webhook_data = {
        "event_type": "sequencing_complete",
        "sample_id": "sample_005"
    }
    
    response = client.post(
        "/webhooks/sequencing/illumina",
        json=webhook_data,
        headers={"X-Signature": "sha256=invalid_signature"}
    )
    assert response.status_code == 401
    assert "Invalid webhook signature" in response.json()["detail"]


def test_webhook_unknown_partner():
    """Test webhook from unknown partner"""
    webhook_data = {
        "event_type": "sequencing_complete",
        "sample_id": "sample_006"
    }
    
    response = client.post("/webhooks/sequencing/unknown_partner", json=webhook_data)
    assert response.status_code == 200  # Should still process but without signature validation


def test_get_webhook_event():
    """Test getting webhook event details"""
    # First create an event
    webhook_data = {
        "event_type": "sequencing_complete",
        "sample_id": "sample_007"
    }
    
    create_response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
    event_id = create_response.json()["event_id"]
    
    # Get the event
    response = client.get(f"/webhooks/events/{event_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == event_id
    assert data["partner_id"] == "illumina"
    assert data["event_type"] == "sequencing_complete"
    assert data["status"] == "completed"
    assert "data" in data


def test_get_webhook_event_not_found():
    """Test getting non-existent webhook event"""
    response = client.get("/webhooks/events/nonexistent_event")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_partner_events():
    """Test getting all events for a partner"""
    # Create multiple events
    for i in range(3):
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": f"sample_{i+10}"
        }
        client.post("/webhooks/sequencing/illumina", json=webhook_data)
    
    # Get partner events
    response = client.get("/webhooks/partners/illumina/events")
    assert response.status_code == 200
    
    data = response.json()
    assert data["partner_id"] == "illumina"
    assert data["count"] >= 3
    assert len(data["events"]) >= 3
    
    # Check event structure
    event = data["events"][0]
    assert "id" in event
    assert "event_type" in event
    assert "status" in event
    assert "timestamp" in event


def test_get_partner_events_with_limit():
    """Test getting partner events with limit"""
    response = client.get("/webhooks/partners/illumina/events?limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["events"]) <= 2


def test_webhook_event_processing():
    """Test that webhook events are processed correctly"""
    webhook_data = {
        "event_type": "sequencing_complete",
        "sample_id": "sample_processing_test",
        "run_id": "run_test_001",
        "file_urls": ["file1.fastq", "file2.fastq", "file3.fastq"]
    }
    
    create_response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
    event_id = create_response.json()["event_id"]
    
    # Get the processed event
    response = client.get(f"/webhooks/events/{event_id}")
    data = response.json()
    
    # Check that processing occurred
    assert data["data"]["processed_files"] == 3
    assert "processing_started" in data["data"]


def test_webhook_qc_processing():
    """Test QC webhook processing"""
    webhook_data = {
        "event_type": "qc_complete",
        "sample_id": "qc_test_sample",
        "qc_metrics": {
            "passed": True,
            "quality_score": 40.5
        }
    }
    
    create_response = client.post("/webhooks/sequencing/oxford", json=webhook_data)
    event_id = create_response.json()["event_id"]
    
    # Get the processed event
    response = client.get(f"/webhooks/events/{event_id}")
    data = response.json()
    
    # Check QC processing
    assert data["data"]["qc_passed"] is True
    assert "qc_processed" in data["data"]


def test_webhook_analysis_processing():
    """Test analysis webhook processing"""
    webhook_data = {
        "event_type": "analysis_complete",
        "sample_id": "analysis_test_sample",
        "analysis_results": {
            "variant_count": 1234
        }
    }
    
    create_response = client.post("/webhooks/sequencing/pacbio", json=webhook_data)
    event_id = create_response.json()["event_id"]
    
    # Get the processed event
    response = client.get(f"/webhooks/events/{event_id}")
    data = response.json()
    
    # Check analysis processing
    assert data["data"]["variants_found"] == 1234
    assert "analysis_processed" in data["data"]