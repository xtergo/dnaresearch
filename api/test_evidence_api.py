from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEvidenceAccumulationAPI:
    """Test evidence accumulation API endpoints"""

    def test_add_theory_evidence_success(self):
        """Test successful evidence addition"""
        evidence_data = {
            "theory_version": "1.0.0",
            "family_id": "family-001",
            "bayes_factor": 2.5,
            "evidence_type": "variant_segregation",
            "weight": 1.0,
            "source": "vcf_analysis",
        }

        response = client.post("/theories/test-theory/evidence", json=evidence_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "evidence_added"
        assert data["theory_id"] == "test-theory"
        assert data["theory_version"] == "1.0.0"
        assert data["family_id"] == "family-001"
        assert data["bayes_factor"] == 2.5
        assert data["evidence_type"] == "variant_segregation"
        assert data["weight"] == 1.0
        assert data["source"] == "vcf_analysis"
        assert "timestamp" in data

    def test_add_theory_evidence_minimal(self):
        """Test evidence addition with minimal required fields"""
        evidence_data = {
            "theory_version": "1.0.0",
            "family_id": "family-002",
            "bayes_factor": 1.8,
        }

        response = client.post("/theories/test-theory-2/evidence", json=evidence_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "evidence_added"
        assert data["theory_id"] == "test-theory-2"
        assert data["evidence_type"] == "execution"  # default
        assert data["weight"] == 1.0  # default
        assert data["source"] == "manual_entry"  # default

    def test_add_theory_evidence_invalid_bayes_factor(self):
        """Test evidence addition with invalid Bayes factor"""
        evidence_data = {
            "theory_version": "1.0.0",
            "family_id": "family-003",
            "bayes_factor": -1.0,  # Invalid: must be positive
        }

        response = client.post("/theories/test-theory/evidence", json=evidence_data)

        assert response.status_code == 400
        assert "Bayes factor must be positive" in response.json()["detail"]

    def test_add_theory_evidence_zero_bayes_factor(self):
        """Test evidence addition with zero Bayes factor"""
        evidence_data = {
            "theory_version": "1.0.0",
            "family_id": "family-004",
            "bayes_factor": 0.0,  # Invalid: must be positive
        }

        response = client.post("/theories/test-theory/evidence", json=evidence_data)

        assert response.status_code == 400
        assert "Bayes factor must be positive" in response.json()["detail"]

    def test_get_theory_evidence_empty(self):
        """Test getting evidence for theory with no evidence"""
        response = client.get("/theories/empty-theory/evidence?theory_version=1.0.0")

        assert response.status_code == 200
        data = response.json()
        assert data["theory_id"] == "empty-theory"
        assert data["theory_version"] == "1.0.0"
        assert data["evidence_trail"] == []
        assert data["evidence_count"] == 0

    def test_get_theory_evidence_with_data(self):
        """Test getting evidence for theory with accumulated evidence"""
        # First add some evidence
        evidence_data = {
            "theory_version": "1.0.0",
            "family_id": "family-005",
            "bayes_factor": 3.2,
            "evidence_type": "pathway_analysis",
            "weight": 1.5,
            "source": "literature_review",
        }

        client.post("/theories/evidence-theory/evidence", json=evidence_data)

        # Now get the evidence
        response = client.get("/theories/evidence-theory/evidence?theory_version=1.0.0")

        assert response.status_code == 200
        data = response.json()
        assert data["theory_id"] == "evidence-theory"
        assert data["theory_version"] == "1.0.0"
        assert data["evidence_count"] == 1
        assert len(data["evidence_trail"]) == 1

        evidence = data["evidence_trail"][0]
        assert evidence["family_id"] == "family-005"
        assert evidence["bayes_factor"] == 3.2
        assert evidence["evidence_type"] == "pathway_analysis"
        assert evidence["weight"] == 1.5
        assert evidence["source"] == "literature_review"
        assert "timestamp" in evidence

    def test_get_theory_posterior_no_evidence(self):
        """Test posterior calculation with no evidence"""
        response = client.get(
            "/theories/no-evidence-theory/posterior?theory_version=1.0.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theory_id"] == "no-evidence-theory"
        assert data["version"] == "1.0.0"
        assert data["prior"] == 0.1  # default
        assert data["accumulated_bf"] == 1.0
        assert data["posterior"] == 0.1  # same as prior
        assert data["support_class"] == "insufficient"
        assert data["evidence_count"] == 0
        assert data["families_analyzed"] == 0

    def test_get_theory_posterior_with_evidence(self):
        """Test posterior calculation with accumulated evidence"""
        # Add multiple pieces of evidence
        evidence_list = [
            {
                "theory_version": "1.0.0",
                "family_id": "family-006",
                "bayes_factor": 2.0,
                "evidence_type": "variant_hit",
            },
            {
                "theory_version": "1.0.0",
                "family_id": "family-007",
                "bayes_factor": 3.0,
                "evidence_type": "segregation",
            },
        ]

        for evidence in evidence_list:
            client.post("/theories/posterior-theory/evidence", json=evidence)

        # Get posterior
        response = client.get(
            "/theories/posterior-theory/posterior?theory_version=1.0.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theory_id"] == "posterior-theory"
        assert data["version"] == "1.0.0"
        assert data["prior"] == 0.1
        assert data["accumulated_bf"] > 1.0  # Should be accumulated
        assert data["posterior"] > 0.1  # Should be higher than prior
        assert data["evidence_count"] >= 2
        assert data["families_analyzed"] >= 2
        assert data["support_class"] in ["weak", "moderate", "strong", "insufficient"]

    def test_get_theory_posterior_custom_prior(self):
        """Test posterior calculation with custom prior"""
        # Add evidence first
        evidence_data = {
            "theory_version": "1.0.0",
            "family_id": "family-008",
            "bayes_factor": 5.0,
        }

        client.post("/theories/custom-prior-theory/evidence", json=evidence_data)

        # Get posterior with custom prior
        response = client.get(
            "/theories/custom-prior-theory/posterior?theory_version=1.0.0&prior=0.2"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prior"] == 0.2
        assert data["posterior"] > 0.2  # Should be higher than custom prior

    def test_get_evidence_stats_empty(self):
        """Test evidence statistics for theory with no evidence"""
        response = client.get(
            "/theories/stats-empty-theory/evidence/stats?theory_version=1.0.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theory_id"] == "stats-empty-theory"
        assert data["theory_version"] == "1.0.0"
        assert data["total_evidence"] == 0
        assert data["unique_families"] == 0
        assert data["evidence_types"] == {}
        assert data["bayes_factor_range"] == {}
        assert data["weight_distribution"] == {}

    def test_get_evidence_stats_with_data(self):
        """Test evidence statistics with accumulated evidence"""
        # Add diverse evidence
        evidence_list = [
            {
                "theory_version": "1.0.0",
                "family_id": "family-009",
                "bayes_factor": 2.5,
                "evidence_type": "variant_hit",
                "weight": 1.0,
            },
            {
                "theory_version": "1.0.0",
                "family_id": "family-010",
                "bayes_factor": 4.0,
                "evidence_type": "variant_hit",
                "weight": 1.5,
            },
            {
                "theory_version": "1.0.0",
                "family_id": "family-011",
                "bayes_factor": 1.8,
                "evidence_type": "pathway_analysis",
                "weight": 0.8,
            },
        ]

        for evidence in evidence_list:
            client.post("/theories/stats-theory/evidence", json=evidence)

        # Get statistics
        response = client.get(
            "/theories/stats-theory/evidence/stats?theory_version=1.0.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theory_id"] == "stats-theory"
        assert data["theory_version"] == "1.0.0"
        assert data["total_evidence"] == 3
        assert data["unique_families"] == 3

        # Check evidence type distribution
        assert data["evidence_types"]["variant_hit"] == 2
        assert data["evidence_types"]["pathway_analysis"] == 1

        # Check Bayes factor statistics
        bf_stats = data["bayes_factor_range"]
        assert bf_stats["min"] == 1.8
        assert bf_stats["max"] == 4.0
        assert bf_stats["mean"] == (2.5 + 4.0 + 1.8) / 3
        assert bf_stats["median"] == 2.5

        # Check weight statistics
        weight_stats = data["weight_distribution"]
        assert weight_stats["mean"] == (1.0 + 1.5 + 0.8) / 3
        assert weight_stats["total_weight"] == 3.3

    def test_evidence_api_integration_workflow(self):
        """Test complete evidence accumulation workflow"""
        theory_id = "integration-theory"
        theory_version = "1.0.0"

        # 1. Start with no evidence
        response = client.get(
            f"/theories/{theory_id}/evidence?theory_version={theory_version}"
        )
        assert response.json()["evidence_count"] == 0

        # 2. Add first piece of evidence
        evidence1 = {
            "theory_version": theory_version,
            "family_id": "family-integration-1",
            "bayes_factor": 2.0,
            "evidence_type": "variant_segregation",
        }

        response = client.post(f"/theories/{theory_id}/evidence", json=evidence1)
        assert response.status_code == 200

        # 3. Check evidence was added
        response = client.get(
            f"/theories/{theory_id}/evidence?theory_version={theory_version}"
        )
        assert response.json()["evidence_count"] == 1

        # 4. Check posterior updated
        response = client.get(
            f"/theories/{theory_id}/posterior?theory_version={theory_version}"
        )
        data = response.json()
        assert data["evidence_count"] == 1
        assert data["families_analyzed"] == 1
        assert data["accumulated_bf"] >= 1.0

        # 5. Add second piece of evidence from different family
        evidence2 = {
            "theory_version": theory_version,
            "family_id": "family-integration-2",
            "bayes_factor": 3.5,
            "evidence_type": "pathway_analysis",
        }

        response = client.post(f"/theories/{theory_id}/evidence", json=evidence2)
        assert response.status_code == 200

        # 6. Check final state
        response = client.get(
            f"/theories/{theory_id}/posterior?theory_version={theory_version}"
        )
        final_data = response.json()
        assert final_data["evidence_count"] == 2
        assert final_data["families_analyzed"] == 2
        assert final_data["accumulated_bf"] > data["accumulated_bf"]  # Should be higher
        assert final_data["posterior"] > data["posterior"]  # Should be higher

        # 7. Check statistics
        response = client.get(
            f"/theories/{theory_id}/evidence/stats?theory_version={theory_version}"
        )
        stats = response.json()
        assert stats["total_evidence"] == 2
        assert stats["unique_families"] == 2
        assert "variant_segregation" in stats["evidence_types"]
        assert "pathway_analysis" in stats["evidence_types"]

    def test_evidence_caching_behavior(self):
        """Test that evidence endpoints properly use caching"""
        theory_id = "cache-theory"
        theory_version = "1.0.0"

        # Add evidence
        evidence_data = {
            "theory_version": theory_version,
            "family_id": "cache-family",
            "bayes_factor": 2.8,
        }

        client.post(f"/theories/{theory_id}/evidence", json=evidence_data)

        # First call should populate cache
        response1 = client.get(
            f"/theories/{theory_id}/evidence?theory_version={theory_version}"
        )
        data1 = response1.json()

        # Second call should use cache (same data)
        response2 = client.get(
            f"/theories/{theory_id}/evidence?theory_version={theory_version}"
        )
        data2 = response2.json()

        assert data1 == data2
        assert response1.status_code == response2.status_code == 200

    def test_multiple_evidence_types_classification(self):
        """Test support classification with multiple evidence types"""
        theory_id = "classification-theory"
        theory_version = "1.0.0"

        # Add evidence that should result in strong support
        strong_evidence = [
            {
                "theory_version": theory_version,
                "family_id": "fam1",
                "bayes_factor": 5.0,
            },
            {
                "theory_version": theory_version,
                "family_id": "fam2",
                "bayes_factor": 4.0,
            },
            {
                "theory_version": theory_version,
                "family_id": "fam3",
                "bayes_factor": 3.0,
            },
        ]

        for evidence in strong_evidence:
            client.post(f"/theories/{theory_id}/evidence", json=evidence)

        # Check classification
        response = client.get(
            f"/theories/{theory_id}/posterior?theory_version={theory_version}"
        )
        data = response.json()

        # With accumulated BF of 5*4*3 = 60, should be strong support
        assert data["accumulated_bf"] >= 10.0  # Strong threshold
        assert data["support_class"] == "strong"
