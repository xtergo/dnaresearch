from datetime import datetime

from access_control import AccessAction, AccessControlManager, AccessRequest
from consent_manager import ConsentManager, ConsentType


class TestAccessControlManager:
    def setup_method(self):
        """Set up test fixtures"""
        self.consent_manager = ConsentManager()
        self.access_control = AccessControlManager(self.consent_manager)

    def test_access_granted_with_valid_consent(self):
        """Test access granted when user has valid consent"""
        # Capture consent first
        self.consent_manager.capture_consent(
            user_id="user_001",
            form_id="genomic_analysis_v1",
            user_data={
                "full_name": "Test User",
                "date_of_birth": "1990-01-01",
                "email": "test@example.com",
            },
            ip_address="192.168.1.1",
            user_agent="test-agent",
            digital_signature="test_signature",
        )

        # Create access request
        request = AccessRequest(
            user_id="user_001",
            action=AccessAction.ANALYZE_VARIANTS,
            resource_id="/genes/BRCA1/interpret",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={"method": "POST"},
        )

        # Check access
        result = self.access_control.check_access(request)

        assert result.granted is True
        assert result.reason == "All required consents valid"
        assert ConsentType.GENOMIC_ANALYSIS in result.consent_types_checked
        assert result.audit_id.startswith("access_")

    def test_access_denied_without_consent(self):
        """Test access denied when user has no consent"""
        request = AccessRequest(
            user_id="user_002",
            action=AccessAction.ANALYZE_VARIANTS,
            resource_id="/genes/BRCA1/interpret",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={"method": "POST"},
        )

        result = self.access_control.check_access(request)

        assert result.granted is False
        assert "Missing consent" in result.reason
        assert "genomic_analysis" in result.reason

    def test_access_denied_for_data_sharing_without_consent(self):
        """Test access denied for data sharing without proper consent"""
        # User has genomic analysis consent but not data sharing
        self.consent_manager.capture_consent(
            user_id="user_003",
            form_id="genomic_analysis_v1",
            user_data={
                "full_name": "Test User",
                "date_of_birth": "1990-01-01",
                "email": "test@example.com",
            },
            ip_address="192.168.1.1",
            user_agent="test-agent",
            digital_signature="test_signature",
        )

        request = AccessRequest(
            user_id="user_003",
            action=AccessAction.SHARE_DATA,
            resource_id="/data/share",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={"method": "POST"},
        )

        result = self.access_control.check_access(request)

        assert result.granted is False
        assert "data_sharing" in result.reason

    def test_theory_execution_requires_multiple_consents(self):
        """Test theory execution requires both genomic analysis and research participation"""
        # Give user only genomic analysis consent
        self.consent_manager.capture_consent(
            user_id="user_004",
            form_id="genomic_analysis_v1",
            user_data={
                "full_name": "Test User",
                "date_of_birth": "1990-01-01",
                "email": "test@example.com",
            },
            ip_address="192.168.1.1",
            user_agent="test-agent",
            digital_signature="test_signature",
        )

        request = AccessRequest(
            user_id="user_004",
            action=AccessAction.EXECUTE_THEORY,
            resource_id="/theories/theory-1/execute",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={"method": "POST"},
        )

        result = self.access_control.check_access(request)

        # Should be granted because genomic_analysis_v1 form includes research_participation
        assert result.granted is True
        assert ConsentType.GENOMIC_ANALYSIS in result.consent_types_checked
        assert ConsentType.RESEARCH_PARTICIPATION in result.consent_types_checked

    def test_access_log_records_attempts(self):
        """Test that access attempts are logged"""
        request = AccessRequest(
            user_id="user_005",
            action=AccessAction.READ_GENOMIC_DATA,
            resource_id="/genomic/data",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={"method": "GET"},
        )

        result = self.access_control.check_access(request)

        # Check log was created
        log_entries = self.access_control.get_access_log()
        assert len(log_entries) == 1

        log_entry = log_entries[0]
        assert log_entry["audit_id"] == result.audit_id
        assert log_entry["user_id"] == "user_005"
        assert log_entry["action"] == "read_genomic_data"
        assert log_entry["granted"] is False  # No consent

    def test_access_log_filtering_by_user(self):
        """Test filtering access log by user"""
        # Create requests for different users
        for i in range(3):
            request = AccessRequest(
                user_id=f"user_{i:03d}",
                action=AccessAction.ANALYZE_VARIANTS,
                resource_id="/genes/test",
                timestamp=datetime.utcnow().isoformat() + "Z",
                ip_address="192.168.1.1",
                metadata={"method": "POST"},
            )
            self.access_control.check_access(request)

        # Get log for specific user
        user_log = self.access_control.get_access_log(user_id="user_001")
        assert len(user_log) == 1
        assert user_log[0]["user_id"] == "user_001"

        # Get all logs
        all_logs = self.access_control.get_access_log()
        assert len(all_logs) == 3

    def test_access_stats_calculation(self):
        """Test access statistics calculation"""
        # Create some access requests
        users_with_consent = ["user_100", "user_101"]
        users_without_consent = ["user_200", "user_201", "user_202"]

        # Give consent to some users
        for user_id in users_with_consent:
            self.consent_manager.capture_consent(
                user_id=user_id,
                form_id="genomic_analysis_v1",
                user_data={
                    "full_name": "Test User",
                    "date_of_birth": "1990-01-01",
                    "email": "test@example.com",
                },
                ip_address="192.168.1.1",
                user_agent="test-agent",
                digital_signature="test_signature",
            )

        # Create access requests
        all_users = users_with_consent + users_without_consent
        for user_id in all_users:
            request = AccessRequest(
                user_id=user_id,
                action=AccessAction.ANALYZE_VARIANTS,
                resource_id="/genes/test",
                timestamp=datetime.utcnow().isoformat() + "Z",
                ip_address="192.168.1.1",
                metadata={"method": "POST"},
            )
            self.access_control.check_access(request)

        # Check stats
        stats = self.access_control.get_access_stats()
        assert stats["total_requests"] == 5
        assert stats["granted_requests"] == 2
        assert stats["denied_requests"] == 3
        assert stats["grant_rate"] == 0.4
        assert stats["unique_users"] == 5
        assert stats["by_action"]["analyze_variants"] == 5

    def test_action_consent_mapping(self):
        """Test that different actions require correct consent types"""
        mappings = self.access_control.action_consent_mapping

        assert ConsentType.GENOMIC_ANALYSIS in mappings[AccessAction.READ_GENOMIC_DATA]
        assert ConsentType.GENOMIC_ANALYSIS in mappings[AccessAction.ANALYZE_VARIANTS]
        assert ConsentType.DATA_SHARING in mappings[AccessAction.SHARE_DATA]
        assert ConsentType.GENOMIC_ANALYSIS in mappings[AccessAction.GENERATE_REPORTS]

        # Theory execution requires both genomic analysis and research participation
        theory_consents = mappings[AccessAction.EXECUTE_THEORY]
        assert ConsentType.GENOMIC_ANALYSIS in theory_consents
        assert ConsentType.RESEARCH_PARTICIPATION in theory_consents

    def test_audit_id_generation(self):
        """Test that unique audit IDs are generated"""
        request1 = AccessRequest(
            user_id="user_audit_1",
            action=AccessAction.ANALYZE_VARIANTS,
            resource_id="/test1",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={},
        )

        request2 = AccessRequest(
            user_id="user_audit_2",
            action=AccessAction.ANALYZE_VARIANTS,
            resource_id="/test2",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="192.168.1.1",
            metadata={},
        )

        result1 = self.access_control.check_access(request1)
        result2 = self.access_control.check_access(request2)

        assert result1.audit_id != result2.audit_id
        assert result1.audit_id.startswith("access_")
        assert result2.audit_id.startswith("access_")

    def test_metadata_logging(self):
        """Test that request metadata is properly logged"""
        request = AccessRequest(
            user_id="user_meta",
            action=AccessAction.GENERATE_REPORTS,
            resource_id="/reports/test",
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address="10.0.0.1",
            metadata={
                "method": "POST",
                "user_agent": "test-browser",
                "custom_field": "test_value",
            },
        )

        self.access_control.check_access(request)

        log_entries = self.access_control.get_access_log(user_id="user_meta")
        assert len(log_entries) == 1

        log_entry = log_entries[0]
        assert log_entry["ip_address"] == "10.0.0.1"
        assert log_entry["metadata"]["method"] == "POST"
        assert log_entry["metadata"]["user_agent"] == "test-browser"
        assert log_entry["metadata"]["custom_field"] == "test_value"
