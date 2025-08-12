"""Enhanced GDPR Compliance Tests - Privacy Impact Assessment and Data Processing Agreements"""

from datetime import datetime, timedelta

import pytest
from gdpr_compliance import (
    BreachSeverity,
    BreachStatus,
    GDPRComplianceManager,
    PIAStatus,
    RiskLevel,
)


class TestEnhancedGDPRCompliance:
    def setup_method(self):
        """Set up test fixtures"""
        self.gdpr_manager = GDPRComplianceManager()

    def test_enhanced_privacy_assessment_creation(self):
        """Test comprehensive privacy impact assessment creation"""
        # Test with genetic data (high risk)
        pia = self.gdpr_manager.create_privacy_assessment(
            purpose="Whole genome sequencing analysis",
            data_categories=["genetic_data", "health_data", "personal_identifiers"],
            processing_activities=["variant_calling", "pathogenicity_assessment"],
        )

        assert pia.pia_id.startswith("pia_")
        assert pia.purpose == "Whole genome sequencing analysis"
        assert pia.risk_level == RiskLevel.HIGH
        assert pia.status == PIAStatus.DRAFT
        assert "genetic_data" in pia.data_categories
        assert "variant_calling" in pia.processing_activities
        assert len(pia.mitigation_measures) >= 7  # High risk gets more measures
        assert "Pseudonymization of personal data" in pia.mitigation_measures

    def test_risk_level_assessment(self):
        """Test automatic risk level assessment based on data categories"""
        # Very high risk - biometric data
        pia_very_high = self.gdpr_manager.create_privacy_assessment(
            purpose="Biometric analysis",
            data_categories=["biometric_data", "personal_identifiers"],
        )
        assert pia_very_high.risk_level == RiskLevel.VERY_HIGH

        # High risk - genetic data
        pia_high = self.gdpr_manager.create_privacy_assessment(
            purpose="Genetic analysis", data_categories=["genetic_data"]
        )
        assert pia_high.risk_level == RiskLevel.HIGH

        # Medium risk - general personal data
        pia_medium = self.gdpr_manager.create_privacy_assessment(
            purpose="General analysis", data_categories=["personal_data"]
        )
        assert pia_medium.risk_level == RiskLevel.MEDIUM

    def test_data_processing_agreement_creation(self):
        """Test data processing agreement creation"""
        dpa = self.gdpr_manager.create_data_processing_agreement(
            partner_name="Illumina Sequencing",
            purpose="Whole genome sequencing",
            data_categories=["genetic_samples", "sequencing_data"],
            retention_period="7 years",
        )

        assert dpa.dpa_id.startswith("dpa_")
        assert dpa.partner_name == "Illumina Sequencing"
        assert dpa.purpose == "Whole genome sequencing"
        assert "genetic_samples" in dpa.data_categories
        assert dpa.retention_period == "7 years"
        assert dpa.status == "active"
        assert len(dpa.security_measures) >= 6
        assert "End-to-end encryption (AES-256)" in dpa.security_measures

        # Check expiry date is ~3 years from now
        expiry = datetime.fromisoformat(dpa.expiry_date.replace("Z", "+00:00"))
        expected_expiry = datetime.utcnow().replace(tzinfo=expiry.tzinfo) + timedelta(
            days=1095
        )
        assert abs((expiry - expected_expiry).days) <= 1

    def test_enhanced_breach_reporting(self):
        """Test enhanced breach reporting with tracking"""
        breach = self.gdpr_manager.report_breach(
            description="Unauthorized database access",
            affected_count=250,
            severity="high",
            data_categories=["genetic_data", "personal_identifiers"],
        )

        assert breach.breach_id.startswith("breach_")
        assert breach.severity == BreachSeverity.HIGH
        assert breach.affected_count == 250
        assert "genetic_data" in breach.data_categories
        assert breach.status == BreachStatus.REPORTED
        assert len(breach.containment_measures) >= 4
        assert "Immediate system isolation" in breach.containment_measures

        # Check notification deadline is 72 hours
        deadline = datetime.fromisoformat(
            breach.notification_deadline.replace("Z", "+00:00")
        )
        expected_deadline = datetime.utcnow().replace(
            tzinfo=deadline.tzinfo
        ) + timedelta(hours=72)
        assert (
            abs((deadline - expected_deadline).total_seconds()) <= 60
        )  # Within 1 minute

    def test_breach_status_updates(self):
        """Test breach status update functionality"""
        # Create a breach
        breach = self.gdpr_manager.report_breach(
            description="Test breach", affected_count=10, severity="medium"
        )

        # Update status to investigating
        success = self.gdpr_manager.update_breach_status(
            breach.breach_id, "investigating"
        )
        assert success
        assert (
            self.gdpr_manager.breaches[breach.breach_id].status
            == BreachStatus.INVESTIGATING
        )

        # Update with regulatory notification
        success = self.gdpr_manager.update_breach_status(
            breach.breach_id, "resolved", notify_regulatory=True
        )
        assert success
        updated_breach = self.gdpr_manager.breaches[breach.breach_id]
        assert updated_breach.status == BreachStatus.REGULATORY_NOTIFIED
        assert updated_breach.regulatory_notified is True

        # Test invalid breach ID
        success = self.gdpr_manager.update_breach_status("invalid_id", "resolved")
        assert not success

    def test_comprehensive_compliance_status(self):
        """Test enhanced compliance status calculation"""
        # Create test data
        self.gdpr_manager.create_privacy_assessment("Test purpose 1")
        self.gdpr_manager.create_privacy_assessment("Test purpose 2")
        self.gdpr_manager.create_data_processing_agreement(
            "Partner 1", "Purpose 1", ["data1"], "5 years"
        )
        breach = self.gdpr_manager.report_breach("Test breach", 5, "low")
        self.gdpr_manager.update_breach_status(breach.breach_id, "resolved")

        status = self.gdpr_manager.get_compliance_status()

        # Check structure
        assert "compliance_score" in status
        assert "privacy_assessments" in status
        assert "breach_notifications" in status
        assert "data_processing_agreements" in status

        # Check PIA details
        assert status["privacy_assessments"]["total"] >= 3  # Including default
        assert status["privacy_assessments"]["pending_review"] >= 0

        # Check breach details
        assert status["breach_notifications"]["total"] == 1
        assert status["breach_notifications"]["resolved"] == 1
        assert status["breach_notifications"]["overdue"] == 0

        # Check DPA details
        assert status["data_processing_agreements"]["total"] == 1
        assert status["data_processing_agreements"]["active"] == 1

    def test_compliance_report_generation(self):
        """Test comprehensive compliance report generation"""
        # Create some test data
        self.gdpr_manager.create_privacy_assessment(
            "High risk activity",
            data_categories=["genetic_data"],
            processing_activities=["analysis"],
        )
        self.gdpr_manager.report_breach("Critical breach", 100, "critical")

        report = self.gdpr_manager.generate_compliance_report()

        # Check report structure
        assert "report_id" in report
        assert "generated_at" in report
        assert "compliance_status" in report
        assert "risk_summary" in report
        assert "recommendations" in report
        assert "next_review_date" in report

        # Check risk summary
        risk_summary = report["risk_summary"]
        assert "high_risk_activities" in risk_summary
        assert "critical_breaches" in risk_summary
        assert "regulatory_notifications_required" in risk_summary

        # Should have recommendations due to pending PIAs and critical breach
        assert len(report["recommendations"]) > 0

        # Check next review date is ~90 days from now
        next_review = datetime.fromisoformat(
            report["next_review_date"].replace("Z", "+00:00")
        )
        expected_review = datetime.utcnow().replace(
            tzinfo=next_review.tzinfo
        ) + timedelta(days=90)
        assert abs((next_review - expected_review).days) <= 1

    def test_expiring_dpas_tracking(self):
        """Test tracking of expiring data processing agreements"""
        # Create DPA that expires soon
        dpa = self.gdpr_manager.create_data_processing_agreement(
            "Test Partner", "Test Purpose", ["test_data"], "1 year"
        )

        # Manually set expiry to 30 days from now (within 90-day threshold)
        near_expiry = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        self.gdpr_manager.dpas[dpa.dpa_id].expiry_date = near_expiry

        # Check expiring count
        expiring_count = self.gdpr_manager._count_expiring_dpas()
        assert expiring_count >= 1

        status = self.gdpr_manager.get_compliance_status()
        assert status["data_processing_agreements"]["expiring_soon"] >= 1

    def test_overdue_breach_notifications(self):
        """Test detection of overdue breach notifications"""
        # Create breach with past deadline
        breach = self.gdpr_manager.report_breach("Test breach", 10, "high")

        # Manually set deadline to past
        past_deadline = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        self.gdpr_manager.breaches[breach.breach_id].notification_deadline = (
            past_deadline
        )

        status = self.gdpr_manager.get_compliance_status()
        assert status["breach_notifications"]["overdue"] >= 1

    def test_dpa_template_functionality(self):
        """Test DPA template retrieval"""
        template = self.gdpr_manager.get_dpa_template()

        assert template is not None
        assert template.status == "template"
        assert template.partner_name == "Sequencing Partner Template"
        assert len(template.security_measures) >= 4

    def test_list_functionality(self):
        """Test listing functions for all GDPR entities"""
        # Create test data
        self.gdpr_manager.create_privacy_assessment("Test PIA")
        self.gdpr_manager.create_data_processing_agreement(
            "Test Partner", "Test Purpose", ["test_data"], "5 years"
        )
        self.gdpr_manager.report_breach("Test breach", 5, "low")

        # Test listing
        pias = self.gdpr_manager.list_assessments()
        assert len(pias) >= 2  # Including default

        dpas = self.gdpr_manager.list_dpas()
        assert len(dpas) == 1  # Excludes template

        breaches = self.gdpr_manager.list_breaches()
        assert len(breaches) == 1

    def test_default_initialization(self):
        """Test that default PIA and DPA template are properly initialized"""
        # Check default PIA
        default_pia = self.gdpr_manager.assessments.get("pia_genomic_001")
        assert default_pia is not None
        assert default_pia.status == PIAStatus.APPROVED
        assert default_pia.risk_level == RiskLevel.HIGH
        assert "genetic_data" in default_pia.data_categories

        # Check DPA template
        template = self.gdpr_manager.get_dpa_template()
        assert template is not None
        assert template.dpa_id == "dpa_template_001"

    def test_compliance_scoring_edge_cases(self):
        """Test compliance scoring with edge cases"""
        # Test with no additional data (only defaults)
        status = self.gdpr_manager.get_compliance_status()
        assert 0.0 <= status["compliance_score"] <= 1.0

        # Test with all negative scenarios
        manager = GDPRComplianceManager()
        # Create draft PIA (not approved)
        manager.create_privacy_assessment("Draft PIA")
        # Create unresolved breach
        manager.report_breach("Unresolved breach", 10, "high")

        status = manager.get_compliance_status()
        assert status["compliance_score"] < 1.0  # Should be penalized


if __name__ == "__main__":
    pytest.main([__file__])
