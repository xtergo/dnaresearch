"""Enhanced GDPR API Tests - Testing new endpoints for comprehensive compliance"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEnhancedGDPRAPI:
    def test_enhanced_privacy_assessment_creation(self):
        """Test enhanced privacy assessment creation API"""
        response = client.post(
            "/gdpr/privacy-assessment",
            json={
                "purpose": "Genomic variant analysis for rare disease research",
                "data_categories": [
                    "genetic_data",
                    "health_data",
                    "personal_identifiers",
                ],
                "processing_activities": [
                    "variant_calling",
                    "pathogenicity_assessment",
                    "report_generation",
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "pia_id" in data
        assert data["purpose"] == "Genomic variant analysis for rare disease research"
        assert data["data_categories"] == [
            "genetic_data",
            "health_data",
            "personal_identifiers",
        ]
        assert data["processing_activities"] == [
            "variant_calling",
            "pathogenicity_assessment",
            "report_generation",
        ]
        assert data["risk_level"] == "high"  # Should be high due to genetic_data
        assert data["status"] == "draft"
        assert "mitigation_measures" in data
        assert len(data["mitigation_measures"]) >= 7  # High risk gets more measures

    def test_privacy_assessment_minimal_data(self):
        """Test privacy assessment creation with minimal data"""
        response = client.post(
            "/gdpr/privacy-assessment", json={"purpose": "Basic data analysis"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["purpose"] == "Basic data analysis"
        assert data["data_categories"] == ["personal_data"]  # Default
        assert data["processing_activities"] == ["data_analysis"]  # Default
        assert data["risk_level"] == "medium"  # Default for non-genetic data

    def test_enhanced_breach_notification(self):
        """Test enhanced breach notification API"""
        response = client.post(
            "/gdpr/breach-notification",
            json={
                "description": "Unauthorized access to genomic database",
                "affected_count": 150,
                "severity": "high",
                "data_categories": ["genetic_data", "personal_identifiers"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "breach_id" in data
        assert data["description"] == "Unauthorized access to genomic database"
        assert data["affected_count"] == 150
        assert data["severity"] == "high"
        assert data["data_categories"] == ["genetic_data", "personal_identifiers"]
        assert data["status"] == "reported"
        assert "containment_measures" in data
        assert "notification_deadline" in data
        assert len(data["containment_measures"]) >= 4

    def test_data_processing_agreement_creation(self):
        """Test data processing agreement creation API"""
        response = client.post(
            "/gdpr/data-processing-agreement",
            json={
                "partner_name": "Illumina Sequencing Services",
                "purpose": "Whole genome sequencing for rare disease analysis",
                "data_categories": [
                    "genetic_samples",
                    "sequencing_data",
                    "quality_metrics",
                ],
                "retention_period": "7 years post-analysis completion",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "dpa_id" in data
        assert data["partner_name"] == "Illumina Sequencing Services"
        assert data["purpose"] == "Whole genome sequencing for rare disease analysis"
        assert data["data_categories"] == [
            "genetic_samples",
            "sequencing_data",
            "quality_metrics",
        ]
        assert data["retention_period"] == "7 years post-analysis completion"
        assert data["status"] == "active"
        assert "security_measures" in data
        assert len(data["security_measures"]) >= 6
        assert "signed_date" in data
        assert "expiry_date" in data

    def test_compliance_report_generation(self):
        """Test compliance report generation API"""
        response = client.get("/gdpr/compliance-report")

        assert response.status_code == 200
        data = response.json()

        # Check report structure
        assert "report_id" in data
        assert "generated_at" in data
        assert "compliance_status" in data
        assert "risk_summary" in data
        assert "recommendations" in data
        assert "next_review_date" in data

        # Check compliance status structure
        compliance_status = data["compliance_status"]
        assert "compliance_score" in compliance_status
        assert "privacy_assessments" in compliance_status
        assert "breach_notifications" in compliance_status
        assert "data_processing_agreements" in compliance_status

        # Check risk summary structure
        risk_summary = data["risk_summary"]
        assert "high_risk_activities" in risk_summary
        assert "critical_breaches" in risk_summary
        assert "regulatory_notifications_required" in risk_summary

        # Recommendations should be a list
        assert isinstance(data["recommendations"], list)

    def test_list_privacy_assessments(self):
        """Test listing privacy assessments API"""
        response = client.get("/gdpr/privacy-assessments")

        assert response.status_code == 200
        data = response.json()

        assert "assessments" in data
        assert "count" in data
        assert isinstance(data["assessments"], list)
        assert data["count"] >= 1  # Should have at least the default PIA

        # Check assessment structure
        if data["assessments"]:
            assessment = data["assessments"][0]
            assert "pia_id" in assessment
            assert "purpose" in assessment
            assert "risk_level" in assessment
            assert "status" in assessment
            assert "created_at" in assessment
            assert "updated_at" in assessment

    def test_list_data_processing_agreements(self):
        """Test listing data processing agreements API"""
        response = client.get("/gdpr/data-processing-agreements")

        assert response.status_code == 200
        data = response.json()

        assert "agreements" in data
        assert "count" in data
        assert isinstance(data["agreements"], list)

        # Check agreement structure if any exist
        if data["agreements"]:
            agreement = data["agreements"][0]
            assert "dpa_id" in agreement
            assert "partner_name" in agreement
            assert "purpose" in agreement
            assert "status" in agreement
            assert "signed_date" in agreement
            assert "expiry_date" in agreement

    def test_breach_status_update(self):
        """Test breach status update API"""
        # First create a breach
        create_response = client.post(
            "/gdpr/breach-notification",
            json={
                "description": "Test breach for status update",
                "affected_count": 10,
                "severity": "medium",
            },
        )
        assert create_response.status_code == 200
        breach_id = create_response.json()["breach_id"]

        # Update the breach status
        update_response = client.put(
            f"/gdpr/breach/{breach_id}/status",
            json={"status": "resolved", "notify_regulatory": True},
        )

        assert update_response.status_code == 200
        data = update_response.json()

        assert data["status"] == "updated"
        assert data["breach_id"] == breach_id
        assert data["new_status"] == "resolved"
        assert data["regulatory_notified"] is True

    def test_breach_status_update_invalid_id(self):
        """Test breach status update with invalid breach ID"""
        response = client.put(
            "/gdpr/breach/invalid_breach_id/status", json={"status": "resolved"}
        )

        assert response.status_code == 404
        assert "Breach not found" in response.json()["detail"]

    def test_compliance_status_endpoint(self):
        """Test the existing compliance status endpoint still works"""
        response = client.get("/gdpr/compliance")

        assert response.status_code == 200
        data = response.json()

        assert "compliance_score" in data
        assert "privacy_assessments" in data
        assert "breach_notifications" in data
        assert "data_processing_agreements" in data
        assert "last_updated" in data

    def test_api_error_handling(self):
        """Test API error handling for invalid requests"""
        # Test missing required fields in privacy assessment
        response = client.post("/gdpr/privacy-assessment", json={})
        assert response.status_code == 422  # Validation error

        # Test missing required fields in DPA
        response = client.post(
            "/gdpr/data-processing-agreement",
            json={
                "partner_name": "Test Partner"
                # Missing other required fields
            },
        )
        assert response.status_code == 422  # Validation error

        # Test invalid severity in breach notification
        response = client.post(
            "/gdpr/breach-notification",
            json={
                "description": "Test breach",
                "affected_count": 10,
                "severity": "invalid_severity",
            },
        )
        assert response.status_code == 500  # Should fail during processing

    def test_comprehensive_workflow(self):
        """Test a comprehensive GDPR compliance workflow"""
        # 1. Create a privacy assessment
        pia_response = client.post(
            "/gdpr/privacy-assessment",
            json={
                "purpose": "Comprehensive genomic analysis workflow",
                "data_categories": ["genetic_data", "health_data"],
                "processing_activities": ["sequencing", "analysis", "reporting"],
            },
        )
        assert pia_response.status_code == 200
        # pia_id = pia_response.json()["pia_id"]  # Not used in this test

        # 2. Create a data processing agreement
        dpa_response = client.post(
            "/gdpr/data-processing-agreement",
            json={
                "partner_name": "Genomics Lab Inc",
                "purpose": "Genomic sequencing services",
                "data_categories": ["genetic_samples", "sequencing_data"],
                "retention_period": "5 years",
            },
        )
        assert dpa_response.status_code == 200
        # dpa_id = dpa_response.json()["dpa_id"]  # Not used in this test

        # 3. Report a breach
        breach_response = client.post(
            "/gdpr/breach-notification",
            json={
                "description": "Minor data exposure incident",
                "affected_count": 5,
                "severity": "low",
                "data_categories": ["personal_identifiers"],
            },
        )
        assert breach_response.status_code == 200
        breach_id = breach_response.json()["breach_id"]

        # 4. Update breach status
        status_response = client.put(
            f"/gdpr/breach/{breach_id}/status", json={"status": "resolved"}
        )
        assert status_response.status_code == 200

        # 5. Generate compliance report
        report_response = client.get("/gdpr/compliance-report")
        assert report_response.status_code == 200
        report = report_response.json()

        # Verify the workflow is reflected in the report
        assert report["compliance_status"]["privacy_assessments"]["total"] >= 2
        assert report["compliance_status"]["data_processing_agreements"]["total"] >= 1
        assert report["compliance_status"]["breach_notifications"]["total"] >= 1
        assert report["compliance_status"]["breach_notifications"]["resolved"] >= 1

    def test_data_validation_edge_cases(self):
        """Test edge cases in data validation"""
        # Test very high affected count in breach
        response = client.post(
            "/gdpr/breach-notification",
            json={
                "description": "Major security incident",
                "affected_count": 1000000,
                "severity": "critical",
                "data_categories": [
                    "genetic_data",
                    "health_data",
                    "personal_identifiers",
                ],
            },
        )
        assert response.status_code == 200

        # Test empty data categories (should use defaults)
        response = client.post(
            "/gdpr/privacy-assessment",
            json={
                "purpose": "Test with empty categories",
                "data_categories": [],
                "processing_activities": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data_categories"]) >= 1  # Should have defaults
        assert len(data["processing_activities"]) >= 1  # Should have defaults


if __name__ == "__main__":
    pytest.main([__file__])
