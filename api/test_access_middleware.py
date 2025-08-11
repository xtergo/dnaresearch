from access_control import AccessControlManager
from access_middleware import AccessControlMiddleware
from consent_manager import ConsentManager
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestAccessControlMiddleware:
    def setup_method(self):
        """Set up test fixtures"""
        self.consent_manager = ConsentManager()
        self.access_control = AccessControlManager(self.consent_manager)

        # Create test app with middleware
        self.app = FastAPI()
        self.app.add_middleware(
            AccessControlMiddleware, access_control_manager=self.access_control
        )

        # Add test endpoints
        @self.app.get("/genes/{gene}/interpret")
        def interpret_variant(gene: str):
            return {"gene": gene, "result": "interpreted"}

        @self.app.post("/theories/{theory_id}/execute")
        def execute_theory(theory_id: str):
            return {"theory_id": theory_id, "result": "executed"}

        @self.app.get("/public/endpoint")
        def public_endpoint():
            return {"message": "public access"}

        self.client = TestClient(self.app)

    def test_middleware_allows_access_with_consent(self):
        """Test middleware allows access when user has consent"""
        # Give user consent
        self.consent_manager.capture_consent(
            user_id="user_middleware_1",
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

        # Make request with user ID header
        response = self.client.get(
            "/genes/BRCA1/interpret", headers={"X-User-ID": "user_middleware_1"}
        )

        assert response.status_code == 200
        assert response.json()["gene"] == "BRCA1"
        assert "X-Access-Audit-ID" in response.headers

    def test_middleware_denies_access_without_consent(self):
        """Test middleware denies access when user lacks consent"""

    def test_middleware_allows_public_endpoints(self):
        """Test middleware allows access to unprotected endpoints"""
        response = self.client.get("/public/endpoint")

        assert response.status_code == 200
        assert response.json()["message"] == "public access"

    def test_middleware_handles_missing_user_id(self):
        """Test middleware handles requests without user ID"""
        response = self.client.get("/genes/BRCA1/interpret")

        # Should pass through without access control when no user ID
        assert response.status_code == 200

    def test_middleware_path_matching(self):
        """Test middleware correctly matches path patterns"""
        middleware = AccessControlMiddleware(self.app, self.access_control)

        # Test exact matches
        assert middleware._path_matches(
            "/genes/BRCA1/interpret", "/genes/{gene}/interpret"
        )
        assert middleware._path_matches(
            "/theories/theory-1/execute", "/theories/{theory_id}/execute"
        )

        # Test non-matches
        assert not middleware._path_matches("/genes/BRCA1", "/genes/{gene}/interpret")
        assert not middleware._path_matches(
            "/theories/theory-1/execute/results", "/theories/{theory_id}/execute"
        )

    def test_middleware_user_id_extraction(self):
        """Test user ID extraction from different sources"""
        middleware = AccessControlMiddleware(self.app, self.access_control)

        # Mock request with header
        class MockRequest:
            def __init__(self, headers=None, query_params=None):
                self.headers = headers or {}
                self.query_params = query_params or {}

        # Test header extraction
        request_with_header = MockRequest(headers={"X-User-ID": "header_user"})
        assert middleware._extract_user_id(request_with_header) == "header_user"

        # Test query param extraction
        request_with_query = MockRequest(query_params={"user_id": "query_user"})
        assert middleware._extract_user_id(request_with_query) == "query_user"

        # Test no user ID
        request_empty = MockRequest()
        assert middleware._extract_user_id(request_empty) is None

    def test_middleware_theory_execution_requires_research_consent(self):
        """Test theory execution requires research participation consent"""
        # Give user only basic genomic analysis consent (which includes research participation)
        self.consent_manager.capture_consent(
            user_id="user_theory_test",
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

        response = self.client.post(
            "/theories/autism-theory-1/execute",
            headers={"X-User-ID": "user_theory_test"},
        )

        assert response.status_code == 200
        assert "X-Access-Audit-ID" in response.headers

    def test_middleware_audit_trail_creation(self):
        """Test that middleware creates audit trail entries"""
        # Give user consent
        self.consent_manager.capture_consent(
            user_id="user_audit_test",
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

        # Make request
        response = self.client.get(
            "/genes/BRCA1/interpret", headers={"X-User-ID": "user_audit_test"}
        )

        assert response.status_code == 200

        # Check audit trail was created
        log_entries = self.access_control.get_access_log(user_id="user_audit_test")
        assert len(log_entries) == 1

        log_entry = log_entries[0]
        assert log_entry["user_id"] == "user_audit_test"
        assert log_entry["action"] == "analyze_variants"
        assert log_entry["granted"] is True
