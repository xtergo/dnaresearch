"""Tests for enhanced webhook functionality"""

import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEnhancedWebhooks:
    """Test enhanced webhook functionality"""

    def test_enhanced_webhook_sequencing_complete(self):
        """Test enhanced sequencing complete webhook"""
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": "enhanced_sample_001",
            "run_id": "enhanced_run_001",
            "file_urls": [
                "https://partner.com/files/enhanced_sample_001_R1.fastq.gz",
                "https://partner.com/files/enhanced_sample_001_R2.fastq.gz",
            ],
            "metadata": {"instrument": "NovaSeq X", "run_date": "2025-01-11T10:00:00Z"},
        }

        response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["received", "processing", "completed"]
        assert data["partner_id"] == "illumina"
        assert data["event_type"] == "sequencing_complete"
        assert "event_id" in data
        assert "timestamp" in data
        assert "retry_count" in data

    def test_enhanced_webhook_with_signature(self):
        """Test enhanced webhook with valid signature"""
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": "enhanced_sample_002",
        }

        # Create valid signature for enhanced handler
        payload = json.dumps(webhook_data, sort_keys=True)
        secret = "illumina_webhook_secret_key_2025"
        signature = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        response = client.post(
            "/webhooks/sequencing/illumina",
            json=webhook_data,
            headers={"X-Signature": f"sha256={signature}"},
        )
        assert response.status_code == 200

    def test_enhanced_webhook_invalid_partner(self):
        """Test webhook with invalid partner"""
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": "invalid_partner_sample",
        }

        response = client.post(
            "/webhooks/sequencing/invalid_partner", json=webhook_data
        )
        assert response.status_code == 400
        assert "Unknown partner" in response.json()["detail"]

    def test_enhanced_webhook_unsupported_event(self):
        """Test webhook with unsupported event type"""
        webhook_data = {
            "event_type": "unsupported_event",
            "sample_id": "unsupported_sample",
        }

        response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
        assert response.status_code == 400
        assert "Unsupported event type" in response.json()["detail"]

    def test_enhanced_webhook_qc_complete(self):
        """Test enhanced QC complete webhook"""
        webhook_data = {
            "event_type": "qc_complete",
            "sample_id": "enhanced_qc_sample",
            "qc_metrics": {"passed": True, "quality_score": 42.5, "coverage": "35x"},
        }

        response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
        assert response.status_code == 200

        data = response.json()
        assert data["event_type"] == "qc_complete"

    def test_enhanced_webhook_analysis_complete(self):
        """Test enhanced analysis complete webhook"""
        webhook_data = {
            "event_type": "analysis_complete",
            "sample_id": "enhanced_analysis_sample",
            "analysis_results": {
                "variant_count": 5678,
                "analysis_type": "exome",
                "reference": "GRCh38",
            },
        }

        response = client.post("/webhooks/sequencing/oxford", json=webhook_data)
        assert response.status_code == 200

        data = response.json()
        assert data["event_type"] == "analysis_complete"

    def test_get_enhanced_webhook_event(self):
        """Test getting enhanced webhook event details"""
        # Create an event first
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": "enhanced_event_test",
        }

        create_response = client.post(
            "/webhooks/sequencing/illumina", json=webhook_data
        )
        event_id = create_response.json()["event_id"]

        # Get the enhanced event
        response = client.get(f"/webhooks/events/{event_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == event_id
        assert data["partner_id"] == "illumina"
        assert data["event_type"] == "sequencing_complete"
        assert "retry_count" in data
        assert "max_retries" in data
        assert "processed_at" in data

    def test_get_enhanced_partner_events(self):
        """Test getting enhanced partner events"""
        # Create multiple events
        for i in range(3):
            webhook_data = {
                "event_type": "sequencing_complete",
                "sample_id": f"enhanced_partner_test_{i}",
            }
            client.post("/webhooks/sequencing/illumina", json=webhook_data)

        # Get partner events
        response = client.get("/webhooks/partners/illumina/events")
        assert response.status_code == 200

        data = response.json()
        assert data["partner_id"] == "illumina"
        assert data["count"] >= 3
        assert "partner_info" in data
        assert data["partner_info"]["name"] == "Illumina Inc."
        assert data["partner_info"]["active"] is True

    def test_webhook_statistics(self):
        """Test webhook statistics endpoint"""
        response = client.get("/webhooks/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_events" in data
        assert "status_distribution" in data
        assert "partner_distribution" in data
        assert "active_partners" in data
        assert "queue_size" in data

    def test_list_webhook_partners(self):
        """Test listing webhook partners"""
        response = client.get("/webhooks/partners")
        assert response.status_code == 200

        data = response.json()
        assert "partners" in data
        assert "count" in data
        assert "active_count" in data

        # Check partner structure
        partners = data["partners"]
        assert len(partners) >= 3  # illumina, oxford, pacbio

        illumina_partner = next((p for p in partners if p["id"] == "illumina"), None)
        assert illumina_partner is not None
        assert illumina_partner["name"] == "Illumina Inc."
        assert illumina_partner["active"] is True
        assert "supported_events" in illumina_partner
        assert "webhook_url" in illumina_partner

    def test_list_webhook_events(self):
        """Test listing webhook events"""
        response = client.get("/webhooks/events")
        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "count" in data
        assert "total_events" in data

    def test_list_webhook_events_with_filters(self):
        """Test listing webhook events with filters"""
        # Test status filter
        response = client.get("/webhooks/events?status=completed")
        assert response.status_code == 200

        # Test partner filter
        response = client.get("/webhooks/events?partner=illumina")
        assert response.status_code == 200

        # Test limit
        response = client.get("/webhooks/events?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) <= 5

    def test_list_webhook_events_invalid_status(self):
        """Test listing webhook events with invalid status"""
        response = client.get("/webhooks/events?status=invalid_status")
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_enhanced_webhook_processing_details(self):
        """Test that enhanced webhook processing includes detailed information"""
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": "processing_details_test",
            "run_id": "detailed_run_001",
            "file_urls": ["file1.fastq", "file2.fastq"],
            "metadata": {"instrument": "NovaSeq X Plus"},
        }

        create_response = client.post(
            "/webhooks/sequencing/illumina", json=webhook_data
        )
        event_id = create_response.json()["event_id"]

        # Get the processed event
        response = client.get(f"/webhooks/events/{event_id}")
        data = response.json()

        # Check enhanced processing details
        event_data = data["data"]
        assert "processed_files" in event_data
        assert "file_count" in event_data
        assert "processing_completed_at" in event_data
        assert "next_step" in event_data
        assert event_data["next_step"] == "quality_control"

    def test_enhanced_qc_processing_details(self):
        """Test enhanced QC processing details"""
        webhook_data = {
            "event_type": "qc_complete",
            "sample_id": "qc_details_test",
            "qc_metrics": {"passed": True, "quality_score": 38.5, "coverage": "32x"},
        }

        create_response = client.post(
            "/webhooks/sequencing/illumina", json=webhook_data
        )
        event_id = create_response.json()["event_id"]

        # Get the processed event
        response = client.get(f"/webhooks/events/{event_id}")
        data = response.json()

        # Check enhanced QC processing
        event_data = data["data"]
        assert "qc_passed" in event_data
        assert "quality_assessment" in event_data
        assert event_data["quality_assessment"]["recommendation"] == "proceed"
        assert event_data["next_step"] == "variant_calling"

    def test_enhanced_analysis_processing_details(self):
        """Test enhanced analysis processing details"""
        webhook_data = {
            "event_type": "analysis_complete",
            "sample_id": "analysis_details_test",
            "analysis_results": {
                "variant_count": 2500,
                "analysis_type": "targeted",
                "reference": "GRCh38",
            },
        }

        create_response = client.post("/webhooks/sequencing/oxford", json=webhook_data)
        event_id = create_response.json()["event_id"]

        # Get the processed event
        response = client.get(f"/webhooks/events/{event_id}")
        data = response.json()

        # Check enhanced analysis processing
        event_data = data["data"]
        assert "variants_found" in event_data
        assert "analysis_summary" in event_data
        assert event_data["analysis_summary"]["analysis_quality"] == "high"
        assert event_data["next_step"] == "report_generation"

    def test_webhook_partner_event_type_validation(self):
        """Test that partners only accept supported event types"""
        # Illumina supports sequencing_complete and qc_complete
        webhook_data = {
            "event_type": "analysis_complete",  # Not supported by Illumina
            "sample_id": "validation_test",
        }

        response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
        assert response.status_code == 400
        assert "not supported by illumina" in response.json()["detail"]

    def test_webhook_signature_validation_enhanced(self):
        """Test enhanced signature validation"""
        webhook_data = {
            "event_type": "sequencing_complete",
            "sample_id": "signature_test",
        }

        # Test with wrong secret
        payload = json.dumps(webhook_data, sort_keys=True)
        wrong_secret = "wrong_secret"
        signature = hmac.new(
            wrong_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        response = client.post(
            "/webhooks/sequencing/illumina",
            json=webhook_data,
            headers={"X-Signature": f"sha256={signature}"},
        )
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]
