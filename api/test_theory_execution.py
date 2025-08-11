from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_theory_execution_success():
    """Test successful theory execution with valid data"""
    theory = {
        "id": "test-autism-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"], "pathways": ["synaptic_transmission"]},
        "evidence_model": {
            "priors": 0.1,
            "likelihood_weights": {"variant_hit": 2.0, "pathway": 1.0},
        },
    }

    vcf_data = """#VCFV4.2
22	51150000	.	A	T	60	PASS"""

    request_data = {
        "theory": theory,
        "vcf_data": vcf_data,
        "family_id": "test-family-001",
    }

    response = client.post("/theories/test-autism-theory/execute", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["theory_id"] == "test-autism-theory"
    assert result["version"] == "1.0.0"
    assert "bayes_factor" in result
    assert "posterior" in result
    assert result["support_class"] in ["insufficient", "weak", "moderate", "strong"]
    assert result["execution_time_ms"] > 0
    assert "diagnostics" in result
    assert "artifact_hash" in result


def test_theory_execution_gene_hit():
    """Test theory execution with variant hitting target gene"""
    theory = {
        "id": "shank3-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 3.0}},
    }

    # VCF with variant in SHANK3 region
    vcf_data = """#VCFV4.2
22	51150000	.	A	T	60	PASS"""

    request_data = {"theory": theory, "vcf_data": vcf_data, "family_id": "family-001"}

    response = client.post("/theories/shank3-theory/execute", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["diagnostics"]["matching_genes"] > 0
    assert result["bayes_factor"] > 1.0  # Should be elevated due to gene hit


def test_theory_execution_no_variants():
    """Test theory execution with no variants"""
    theory = {
        "id": "empty-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    vcf_data = "#VCFV4.2"  # Empty VCF

    request_data = {"theory": theory, "vcf_data": vcf_data, "family_id": "empty-family"}

    response = client.post("/theories/empty-theory/execute", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["diagnostics"]["variants_analyzed"] == 0
    assert result["diagnostics"]["matching_genes"] == 0


def test_theory_execution_id_mismatch():
    """Test theory execution fails with ID mismatch"""
    theory = {
        "id": "wrong-id",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    vcf_data = "#VCFV4.2"

    request_data = {"theory": theory, "vcf_data": vcf_data, "family_id": "test-family"}

    response = client.post("/theories/correct-id/execute", json=request_data)
    assert response.status_code == 400
    assert "Theory ID mismatch" in response.json()["detail"]


def test_theory_execution_invalid_theory():
    """Test theory execution fails with invalid theory"""
    invalid_theory = {
        "id": "invalid-theory",
        "version": "1.0.0",
        # Missing required fields
    }

    vcf_data = "#VCFV4.2"

    request_data = {
        "theory": invalid_theory,
        "vcf_data": vcf_data,
        "family_id": "test-family",
    }

    response = client.post("/theories/invalid-theory/execute", json=request_data)
    assert response.status_code == 400


def test_theory_execution_support_classification():
    """Test support classification based on Bayes factors"""
    theory = {
        "id": "classification-test",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3", "NRXN1", "SYNGAP1"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 5.0}},
    }

    # Multiple variants in target genes for higher Bayes factor
    vcf_data = """#VCFV4.2
22	51150000	.	A	T	60	PASS
2	50200000	.	G	C	70	PASS
6	33450000	.	T	A	80	PASS"""

    request_data = {
        "theory": theory,
        "vcf_data": vcf_data,
        "family_id": "multi-variant-family",
    }

    response = client.post("/theories/classification-test/execute", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["diagnostics"]["variants_analyzed"] == 3
    assert result["diagnostics"]["matching_genes"] == 3
    assert result["bayes_factor"] > 1.0
    # With multiple gene hits, should get moderate or strong support
    assert result["support_class"] in ["moderate", "strong"]


def test_theory_execution_performance():
    """Test theory execution completes within time limits"""
    theory = {
        "id": "performance-test",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    vcf_data = "#VCFV4.2\n22\t51150000\t.\tA\tT\t60\tPASS"

    request_data = {"theory": theory, "vcf_data": vcf_data, "family_id": "perf-test"}

    response = client.post("/theories/performance-test/execute", json=request_data)
    assert response.status_code == 200

    result = response.json()
    # Should complete well under 30 second limit
    assert result["execution_time_ms"] < 30000
    assert result["execution_time_ms"] > 0


def test_theory_execution_artifact_hash():
    """Test artifact hash generation for reproducibility"""
    theory = {
        "id": "hash-test",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    vcf_data = "#VCFV4.2\n22\t51150000\t.\tA\tT\t60\tPASS"

    request_data = {"theory": theory, "vcf_data": vcf_data, "family_id": "hash-family"}

    # Execute twice with same data
    response1 = client.post("/theories/hash-test/execute", json=request_data)
    response2 = client.post("/theories/hash-test/execute", json=request_data)

    assert response1.status_code == 200
    assert response2.status_code == 200

    result1 = response1.json()
    result2 = response2.json()

    # Artifact hashes should be different due to timestamp
    assert "artifact_hash" in result1
    assert "artifact_hash" in result2
    assert len(result1["artifact_hash"]) == 64  # SHA256 hex length
    assert len(result2["artifact_hash"]) == 64
