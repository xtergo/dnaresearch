"""
Integration Tests for Consent API Endpoints

Tests for the consent management REST API endpoints.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestConsentAPI:
    """Test consent API endpoints"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_user_id = "api_test_user_123"
        self.test_user_data = {
            "full_name": "Jane Smith",
            "date_of_birth": "1985-05-15",
            "email": "jane.smith@example.com",
        }
        self.test_signature = "abc123def456789012345678901234567890fedcba"

    def test_list_consent_forms(self):
        """Test listing consent forms"""
        response = client.get("/consent/forms")

        assert response.status_code == 200
        data = response.json()

        assert "forms" in data
        assert len(data["forms"]) >= 2

        # Check genomic analysis form exists
        genomic_form = next(
            (f for f in data["forms"] if f["form_id"] == "genomic_analysis_v1"), None
        )
        assert genomic_form is not None
        assert genomic_form["title"] == "Genomic Data Analysis Consent"
        assert "genomic_analysis" in genomic_form["consent_types"]
        assert "full_name" in genomic_form["required_fields"]

    def test_get_consent_form(self):
        """Test getting specific consent form"""
        response = client.get("/consent/forms/genomic_analysis_v1")

        assert response.status_code == 200
        data = response.json()

        assert data["form_id"] == "genomic_analysis_v1"
        assert data["version"] == "1.0.0"
        assert data["title"] == "Genomic Data Analysis Consent"
        assert "consent_text" in data
        assert len(data["consent_text"]) > 0
        assert "genomic_analysis" in data["consent_types"]

    def test_get_nonexistent_consent_form(self):
        """Test getting nonexistent consent form"""
        response = client.get("/consent/forms/nonexistent_form")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_capture_consent(self):
        """Test capturing user consent"""
        consent_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": self.test_user_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }

        response = client.post("/consent/capture", json=consent_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "consent_captured"
        assert data["user_id"] == self.test_user_id
        assert "consent_id" in data
        assert "genomic_analysis" in data["consent_types"]
        assert "granted_at" in data
        assert "expires_at" in data

    def test_capture_consent_missing_field(self):
        """Test capturing consent with missing required field"""
        incomplete_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": self.test_user_id,
            "user_data": {"full_name": "Jane Smith"},  # Missing required fields
            "digital_signature": self.test_signature,
        }

        response = client.post("/consent/capture", json=incomplete_data)

        assert response.status_code == 400
        assert "missing" in response.json()["detail"]

    def test_capture_consent_invalid_form(self):
        """Test capturing consent with invalid form"""
        invalid_data = {
            "form_id": "invalid_form_id",
            "user_id": self.test_user_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }

        response = client.post("/consent/capture", json=invalid_data)

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_check_consent_valid(self):
        """Test checking valid consent"""
        # First capture consent
        consent_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": self.test_user_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }
        client.post("/consent/capture", json=consent_data)

        # Check consent
        response = client.get(
            f"/consent/check/{self.test_user_id}?consent_type=genomic_analysis"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == self.test_user_id
        assert data["consent_type"] == "genomic_analysis"
        assert data["has_consent"] is True
        assert "checked_at" in data

    def test_check_consent_invalid(self):
        """Test checking consent for user without consent"""
        response = client.get(
            "/consent/check/nonexistent_user?consent_type=genomic_analysis"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "nonexistent_user"
        assert data["has_consent"] is False

    def test_check_consent_invalid_type(self):
        """Test checking consent with invalid consent type"""
        response = client.get(
            f"/consent/check/{self.test_user_id}?consent_type=invalid_type"
        )

        assert response.status_code == 400
        assert "Invalid consent type" in response.json()["detail"]

    def test_withdraw_consent(self):
        """Test withdrawing consent"""
        # First capture consent
        consent_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": self.test_user_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }
        client.post("/consent/capture", json=consent_data)

        # Withdraw consent
        withdraw_data = {
            "user_id": self.test_user_id,
            "consent_type": "genomic_analysis",
            "reason": "API test withdrawal",
        }

        response = client.post("/consent/withdraw", json=withdraw_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "consent_withdrawn"
        assert data["user_id"] == self.test_user_id
        assert data["consent_type"] == "genomic_analysis"
        assert "withdrawn_at" in data

        # Verify consent is no longer valid
        check_response = client.get(
            f"/consent/check/{self.test_user_id}?consent_type=genomic_analysis"
        )
        assert check_response.json()["has_consent"] is False

    def test_withdraw_nonexistent_consent(self):
        """Test withdrawing consent that doesn't exist"""
        withdraw_data = {
            "user_id": "nonexistent_user",
            "consent_type": "genomic_analysis",
            "reason": "Test",
        }

        response = client.post("/consent/withdraw", json=withdraw_data)

        assert response.status_code == 404
        assert "No active consent found" in response.json()["detail"]

    def test_withdraw_consent_invalid_type(self):
        """Test withdrawing consent with invalid type"""
        withdraw_data = {
            "user_id": self.test_user_id,
            "consent_type": "invalid_type",
            "reason": "Test",
        }

        response = client.post("/consent/withdraw", json=withdraw_data)

        assert response.status_code == 400
        assert "Invalid consent type" in response.json()["detail"]

    def test_get_user_consents(self):
        """Test getting user consents"""
        # Use unique user ID for this test
        user_consents_id = f"{self.test_user_id}_user_consents"

        # Capture multiple consents
        genomic_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": user_consents_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }
        client.post("/consent/capture", json=genomic_data)

        sharing_data = {
            "form_id": "data_sharing_v1",
            "user_id": user_consents_id,
            "user_data": {"full_name": "Jane Smith", "email": "jane@example.com"},
            "digital_signature": self.test_signature,
        }
        client.post("/consent/capture", json=sharing_data)

        # Get user consents
        response = client.get(f"/consent/users/{user_consents_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == user_consents_id
        assert "consents" in data
        assert len(data["consents"]) >= 2

        consent_types = [c["consent_type"] for c in data["consents"]]
        assert "genomic_analysis" in consent_types
        assert "data_sharing" in consent_types

        # Check consent structure
        first_consent = data["consents"][0]
        assert "consent_id" in first_consent
        assert "status" in first_consent
        assert "granted_at" in first_consent
        assert first_consent["status"] == "active"

    def test_get_consent_audit_trail(self):
        """Test getting consent audit trail"""
        # Use unique user ID for this test
        audit_user_id = f"{self.test_user_id}_audit_trail"

        # Capture consent
        consent_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": audit_user_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }
        client.post("/consent/capture", json=consent_data)

        # Withdraw consent
        withdraw_data = {
            "user_id": audit_user_id,
            "consent_type": "genomic_analysis",
            "reason": "Audit trail test",
        }
        client.post("/consent/withdraw", json=withdraw_data)

        # Get audit trail
        response = client.get(f"/consent/audit/{audit_user_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == audit_user_id
        assert "audit_trail" in data
        assert len(data["audit_trail"]) >= 2

        # Check for grant and withdrawal actions
        actions = [entry["action"] for entry in data["audit_trail"]]
        assert "granted" in actions
        assert "withdrawn" in actions

        # Check audit entry structure
        grant_entry = next(e for e in data["audit_trail"] if e["action"] == "granted")
        assert "consent_id" in grant_entry
        assert "timestamp" in grant_entry
        assert "ip_address" in grant_entry
        assert grant_entry["consent_type"] in [
            "genomic_analysis",
            "research_participation",
        ]  # Form creates multiple types

        withdraw_entry = next(
            e for e in data["audit_trail"] if e["action"] == "withdrawn"
        )
        assert withdraw_entry["reason"] == "Audit trail test"

    def test_get_consent_stats(self):
        """Test getting consent statistics"""
        # Capture some consents to ensure stats exist
        consent_data = {
            "form_id": "genomic_analysis_v1",
            "user_id": f"{self.test_user_id}_stats",
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }
        client.post("/consent/capture", json=consent_data)

        response = client.get("/consent/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_consents" in data
        assert "by_status" in data
        assert "by_type" in data
        assert "active_users" in data

        assert data["total_consents"] >= 1
        assert "active" in data["by_status"]
        assert "genomic_analysis" in data["by_type"]
        assert data["active_users"] >= 1

    def test_consent_workflow_integration(self):
        """Test complete consent workflow"""
        user_id = f"{self.test_user_id}_workflow"

        # 1. List available forms
        forms_response = client.get("/consent/forms")
        assert forms_response.status_code == 200
        forms = forms_response.json()["forms"]
        genomic_form = next(f for f in forms if f["form_id"] == "genomic_analysis_v1")

        # 2. Get detailed form
        form_response = client.get(f"/consent/forms/{genomic_form['form_id']}")
        assert form_response.status_code == 200

        # 3. Capture consent
        consent_data = {
            "form_id": genomic_form["form_id"],
            "user_id": user_id,
            "user_data": self.test_user_data,
            "digital_signature": self.test_signature,
        }
        capture_response = client.post("/consent/capture", json=consent_data)
        assert capture_response.status_code == 200

        # 4. Check consent is valid
        check_response = client.get(
            f"/consent/check/{user_id}?consent_type=genomic_analysis"
        )
        assert check_response.status_code == 200
        assert check_response.json()["has_consent"] is True

        # 5. Get user consents
        user_consents_response = client.get(f"/consent/users/{user_id}")
        assert user_consents_response.status_code == 200
        consents = user_consents_response.json()["consents"]
        assert len(consents) >= 1

        # 6. Get audit trail
        audit_response = client.get(f"/consent/audit/{user_id}")
        assert audit_response.status_code == 200
        audit_trail = audit_response.json()["audit_trail"]
        assert len(audit_trail) >= 1

        # 7. Withdraw consent
        withdraw_data = {
            "user_id": user_id,
            "consent_type": "genomic_analysis",
            "reason": "Workflow test complete",
        }
        withdraw_response = client.post("/consent/withdraw", json=withdraw_data)
        assert withdraw_response.status_code == 200

        # 8. Verify consent is withdrawn
        final_check_response = client.get(
            f"/consent/check/{user_id}?consent_type=genomic_analysis"
        )
        assert final_check_response.status_code == 200
        assert final_check_response.json()["has_consent"] is False

        # 9. Verify audit trail includes withdrawal
        final_audit_response = client.get(f"/consent/audit/{user_id}")
        assert final_audit_response.status_code == 200
        final_audit_trail = final_audit_response.json()["audit_trail"]
        actions = [entry["action"] for entry in final_audit_trail]
        assert "granted" in actions
        assert "withdrawn" in actions

    def test_data_sharing_consent_workflow(self):
        """Test data sharing consent workflow"""
        user_id = f"{self.test_user_id}_sharing"

        # Capture data sharing consent
        consent_data = {
            "form_id": "data_sharing_v1",
            "user_id": user_id,
            "user_data": {"full_name": "Jane Smith", "email": "jane@example.com"},
            "digital_signature": self.test_signature,
        }

        response = client.post("/consent/capture", json=consent_data)
        assert response.status_code == 200

        # Check data sharing consent
        check_response = client.get(
            f"/consent/check/{user_id}?consent_type=data_sharing"
        )
        assert check_response.status_code == 200
        assert check_response.json()["has_consent"] is True

        # Verify genomic analysis consent is not granted
        genomic_check = client.get(
            f"/consent/check/{user_id}?consent_type=genomic_analysis"
        )
        assert genomic_check.status_code == 200
        assert genomic_check.json()["has_consent"] is False
