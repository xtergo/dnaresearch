"""Tests for GDPR Compliance Manager"""

from gdpr_compliance import (
    BreachSeverity,
    BreachStatus,
    GDPRComplianceManager,
    PIAStatus,
    RiskLevel,
)


class TestGDPRComplianceManager:
    def setup_method(self):
        """Set up test fixtures"""
        self.gdpr_manager = GDPRComplianceManager()

    def test_init_creates_default_assessment(self):
        """Test that initialization creates default genomic PIA"""
        assessments = self.gdpr_manager.list_assessments()
        assert len(assessments) == 1
        assert assessments[0].pia_id == "pia_genomic_001"
        assert assessments[0].purpose == "Genomic research and variant analysis"
        assert assessments[0].risk_level == RiskLevel.HIGH
        assert assessments[0].status == PIAStatus.APPROVED

    def test_create_privacy_assessment_genomic(self):
        """Test creating genomic privacy assessment"""
        purpose = "Genomic data analysis for research"
        assessment = self.gdpr_manager.create_privacy_assessment(purpose)

        assert assessment.pia_id == "pia_002"
        assert assessment.purpose == purpose
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.status == PIAStatus.DRAFT
        assert assessment.created_at.endswith("Z")

    def test_create_privacy_assessment_non_genomic(self):
        """Test creating non-genomic privacy assessment"""
        purpose = "User account management"
        assessment = self.gdpr_manager.create_privacy_assessment(purpose)

        assert assessment.risk_level == RiskLevel.MEDIUM
        assert assessment.status == PIAStatus.DRAFT

    def test_report_breach_low_severity(self):
        """Test reporting low severity breach"""
        breach = self.gdpr_manager.report_breach("Minor data exposure", 5, "low")

        assert breach.breach_id == "breach_001"
        assert breach.severity == BreachSeverity.LOW
        assert breach.affected_count == 5
        assert breach.status == BreachStatus.REPORTED

    def test_report_breach_high_severity(self):
        """Test reporting high severity breach"""
        breach = self.gdpr_manager.report_breach("Major genomic data leak", 100, "high")

        assert breach.severity == BreachSeverity.HIGH
        assert breach.affected_count == 100

    def test_get_compliance_status_initial(self):
        """Test getting initial compliance status"""
        status = self.gdpr_manager.get_compliance_status()

        assert "compliance_score" in status
        assert status["privacy_assessments"]["total"] == 1
        assert status["privacy_assessments"]["approved"] == 1
        assert status["breach_notifications"]["total"] == 0
        assert status["compliance_score"] == 1.0  # Perfect initial score

    def test_get_compliance_status_with_breach(self):
        """Test compliance status after breach"""
        self.gdpr_manager.report_breach("Test breach", 10, "low")
        status = self.gdpr_manager.get_compliance_status()

        assert status["breach_notifications"]["total"] == 1
        assert status["breach_notifications"]["resolved"] == 0
        # Score should be 0.6 (PIA: 1/1 approved) + 0.0 (breach: 0/1 resolved) = 0.6
        assert status["compliance_score"] == 0.6

    def test_list_assessments(self):
        """Test listing all assessments"""
        self.gdpr_manager.create_privacy_assessment("Test purpose")
        assessments = self.gdpr_manager.list_assessments()

        assert len(assessments) == 2
        assert all(hasattr(a, "pia_id") for a in assessments)

    def test_list_breaches(self):
        """Test listing all breaches"""
        self.gdpr_manager.report_breach("Breach 1", 5, "low")
        self.gdpr_manager.report_breach("Breach 2", 10, "high")
        breaches = self.gdpr_manager.list_breaches()

        assert len(breaches) == 2
        assert all(hasattr(b, "breach_id") for b in breaches)

    def test_multiple_assessments_compliance_score(self):
        """Test compliance score with multiple assessments"""
        # Create draft assessment (not approved)
        self.gdpr_manager.create_privacy_assessment("Draft assessment")
        status = self.gdpr_manager.get_compliance_status()

        # Should have 1 approved out of 2 total = 0.5 * 0.6 + 0.4 (no breaches) = 0.7
        assert status["privacy_assessments"]["total"] == 2
        assert status["privacy_assessments"]["approved"] == 1
        assert status["compliance_score"] == 0.7
