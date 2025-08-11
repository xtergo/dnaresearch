"""
Tests for Consent Management System

Comprehensive tests for GDPR-compliant consent capture and management.
"""

from datetime import datetime, timedelta

import pytest
from consent_manager import ConsentManager, ConsentStatus, ConsentType


class TestConsentManager:
    """Test consent management functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.consent_manager = ConsentManager()
        self.test_user_id = "test_user_123"
        self.test_ip = "192.168.1.100"
        self.test_user_agent = "Mozilla/5.0 Test Browser"
        self.test_signature = "a1b2c3d4e5f6789012345678901234567890abcdef"

        self.test_user_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-01",
            "email": "john.doe@example.com",
        }

    def test_capture_genomic_consent(self):
        """Test capturing genomic analysis consent"""
        consent = self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        assert consent.user_id == self.test_user_id
        assert consent.consent_type == ConsentType.GENOMIC_ANALYSIS
        assert consent.status == ConsentStatus.ACTIVE
        assert consent.ip_address == self.test_ip
        assert consent.digital_signature == self.test_signature
        assert consent.expires_at is not None

    def test_capture_data_sharing_consent(self):
        """Test capturing data sharing consent"""
        consent = self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="data_sharing_v1",
            user_data={"full_name": "John Doe", "email": "john@example.com"},
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        assert consent.consent_type == ConsentType.DATA_SHARING
        assert consent.status == ConsentStatus.ACTIVE

    def test_capture_consent_missing_required_field(self):
        """Test consent capture with missing required field"""
        incomplete_data = {"full_name": "John Doe"}  # Missing email

        with pytest.raises(ValueError, match="Required field 'date_of_birth' missing"):
            self.consent_manager.capture_consent(
                user_id=self.test_user_id,
                form_id="genomic_analysis_v1",
                user_data=incomplete_data,
                ip_address=self.test_ip,
                user_agent=self.test_user_agent,
                digital_signature=self.test_signature,
            )

    def test_capture_consent_invalid_form(self):
        """Test consent capture with invalid form ID"""
        with pytest.raises(ValueError, match="Consent form 'invalid_form' not found"):
            self.consent_manager.capture_consent(
                user_id=self.test_user_id,
                form_id="invalid_form",
                user_data=self.test_user_data,
                ip_address=self.test_ip,
                user_agent=self.test_user_agent,
                digital_signature=self.test_signature,
            )

    def test_check_valid_consent(self):
        """Test checking valid consent"""
        # First capture consent
        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        # Check consent
        has_consent = self.consent_manager.check_consent(
            user_id=self.test_user_id, consent_type=ConsentType.GENOMIC_ANALYSIS
        )

        assert has_consent is True

    def test_check_invalid_consent(self):
        """Test checking consent that doesn't exist"""
        has_consent = self.consent_manager.check_consent(
            user_id="nonexistent_user", consent_type=ConsentType.GENOMIC_ANALYSIS
        )

        assert has_consent is False

    def test_withdraw_consent(self):
        """Test withdrawing consent"""
        # First capture consent
        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        # Withdraw consent
        success = self.consent_manager.withdraw_consent(
            user_id=self.test_user_id,
            consent_type=ConsentType.GENOMIC_ANALYSIS,
            reason="Changed mind",
        )

        assert success is True

        # Check consent is no longer valid
        has_consent = self.consent_manager.check_consent(
            user_id=self.test_user_id, consent_type=ConsentType.GENOMIC_ANALYSIS
        )

        assert has_consent is False

    def test_withdraw_nonexistent_consent(self):
        """Test withdrawing consent that doesn't exist"""
        success = self.consent_manager.withdraw_consent(
            user_id="nonexistent_user", consent_type=ConsentType.GENOMIC_ANALYSIS
        )

        assert success is False

    def test_get_user_consents(self):
        """Test getting all user consents"""
        # Capture multiple consents
        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="data_sharing_v1",
            user_data={"full_name": "John Doe", "email": "john@example.com"},
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        consents = self.consent_manager.get_user_consents(self.test_user_id)

        assert len(consents) >= 2  # At least genomic_analysis and data_sharing
        consent_types = [c.consent_type for c in consents]
        assert ConsentType.GENOMIC_ANALYSIS in consent_types
        assert ConsentType.DATA_SHARING in consent_types

    def test_get_consent_audit_trail(self):
        """Test getting consent audit trail"""
        # Capture consent
        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        # Withdraw consent
        self.consent_manager.withdraw_consent(
            user_id=self.test_user_id,
            consent_type=ConsentType.GENOMIC_ANALYSIS,
            reason="Test withdrawal",
        )

        # Get audit trail
        audit_trail = self.consent_manager.get_consent_audit_trail(self.test_user_id)

        assert len(audit_trail) >= 2  # At least grant and withdrawal

        # Check grant action
        grant_action = next(a for a in audit_trail if a["action"] == "granted")
        assert grant_action["consent_type"] == "genomic_analysis"
        assert grant_action["ip_address"] == self.test_ip

        # Check withdrawal action
        withdraw_action = next(a for a in audit_trail if a["action"] == "withdrawn")
        assert withdraw_action["consent_type"] == "genomic_analysis"
        assert withdraw_action["reason"] == "Test withdrawal"

    def test_get_consent_form(self):
        """Test getting consent form"""
        form = self.consent_manager.get_consent_form("genomic_analysis_v1")

        assert form is not None
        assert form.form_id == "genomic_analysis_v1"
        assert form.title == "Genomic Data Analysis Consent"
        assert ConsentType.GENOMIC_ANALYSIS in form.consent_types
        assert "full_name" in form.required_fields

    def test_get_nonexistent_consent_form(self):
        """Test getting nonexistent consent form"""
        form = self.consent_manager.get_consent_form("nonexistent_form")
        assert form is None

    def test_list_consent_forms(self):
        """Test listing all consent forms"""
        forms = self.consent_manager.list_consent_forms()

        assert len(forms) >= 2  # At least genomic and data sharing forms
        form_ids = [f.form_id for f in forms]
        assert "genomic_analysis_v1" in form_ids
        assert "data_sharing_v1" in form_ids

    def test_consent_expiration(self):
        """Test consent expiration handling"""
        # Create a consent manager with expired consent
        consent = self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        # Manually set expiration to past date
        consent.expires_at = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"

        # Check consent should return False and mark as expired
        has_consent = self.consent_manager.check_consent(
            user_id=self.test_user_id, consent_type=ConsentType.GENOMIC_ANALYSIS
        )

        assert has_consent is False
        assert consent.status == ConsentStatus.EXPIRED

    def test_get_consent_stats(self):
        """Test getting consent statistics"""
        # Capture some consents
        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        self.consent_manager.capture_consent(
            user_id="user_456",
            form_id="data_sharing_v1",
            user_data={"full_name": "Jane Doe", "email": "jane@example.com"},
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        stats = self.consent_manager.get_consent_stats()

        assert stats["total_consents"] >= 2
        assert "active" in stats["by_status"]
        assert "genomic_analysis" in stats["by_type"]
        assert stats["active_users"] >= 2

    def test_digital_signature_validation(self):
        """Test digital signature validation"""
        consent_text = "I consent to genomic analysis"
        user_data = {"name": "John Doe"}

        # Create a valid signature (simplified)
        import hashlib
        import json

        signature_data = f"{consent_text}{json.dumps(user_data, sort_keys=True)}"
        valid_signature = hashlib.sha256(signature_data.encode("utf-8")).hexdigest()

        # Test valid signature
        is_valid = self.consent_manager.validate_digital_signature(
            consent_text, valid_signature, user_data
        )
        assert is_valid is True

        # Test invalid signature
        is_valid = self.consent_manager.validate_digital_signature(
            consent_text, "invalid_signature", user_data
        )
        assert is_valid is False

    def test_consent_id_generation(self):
        """Test consent ID generation"""
        consent1 = self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        consent2 = self.consent_manager.capture_consent(
            user_id="different_user",
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        # Consent IDs should be unique
        assert consent1.consent_id != consent2.consent_id
        assert consent1.consent_id.startswith("consent_")
        assert consent2.consent_id.startswith("consent_")

    def test_multiple_consent_types_single_form(self):
        """Test capturing multiple consent types from single form"""
        self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",  # This form has multiple consent types
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        # Check that both consent types are active
        has_genomic = self.consent_manager.check_consent(
            user_id=self.test_user_id, consent_type=ConsentType.GENOMIC_ANALYSIS
        )

        has_research = self.consent_manager.check_consent(
            user_id=self.test_user_id, consent_type=ConsentType.RESEARCH_PARTICIPATION
        )

        assert has_genomic is True
        assert has_research is True

    def test_consent_metadata_storage(self):
        """Test that consent metadata is properly stored"""
        consent = self.consent_manager.capture_consent(
            user_id=self.test_user_id,
            form_id="genomic_analysis_v1",
            user_data=self.test_user_data,
            ip_address=self.test_ip,
            user_agent=self.test_user_agent,
            digital_signature=self.test_signature,
        )

        assert consent.metadata["form_id"] == "genomic_analysis_v1"
        assert consent.metadata["form_version"] == "1.0.0"
        assert consent.metadata["user_data"] == self.test_user_data
        assert consent.user_agent == self.test_user_agent
        assert consent.ip_address == self.test_ip
