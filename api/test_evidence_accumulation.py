from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_add_evidence_success():
    """Test adding evidence to a theory"""
    request_data = {
        "theory_version": "1.0.0",
        "family_id": "family-001",
        "bayes_factor": 2.5,
        "evidence_type": "segregation",
        "weight": 1.5,
        "source": "clinical_study",
    }

    response = client.post("/theories/test-theory/evidence", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "evidence_added"
    assert result["theory_id"] == "test-theory"
    assert result["version"] == "1.0.0"
    assert result["evidence_count"] == 1
    assert result["families_analyzed"] == 1
    assert "accumulated_bf" in result
    assert "posterior" in result
    assert "support_class" in result


def test_multiple_evidence_accumulation():
    """Test accumulating evidence from multiple families"""
    # Add first evidence
    response1 = client.post(
        "/theories/multi-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-001",
            "bayes_factor": 2.0,
            "evidence_type": "execution",
            "weight": 1.0,
            "source": "theory_execution",
        },
    )
    assert response1.status_code == 200

    # Add second evidence
    response2 = client.post(
        "/theories/multi-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-002",
            "bayes_factor": 3.0,
            "evidence_type": "segregation",
            "weight": 1.2,
            "source": "clinical_study",
        },
    )
    assert response2.status_code == 200

    result = response2.json()
    assert result["evidence_count"] == 2
    assert result["families_analyzed"] == 2
    assert result["accumulated_bf"] > 2.0  # Should be higher than individual BFs


def test_get_posterior():
    """Test getting theory posterior"""
    # Add some evidence first
    client.post(
        "/theories/posterior-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-001",
            "bayes_factor": 5.0,
            "evidence_type": "execution",
            "weight": 1.0,
            "source": "theory_execution",
        },
    )

    response = client.get(
        "/theories/posterior-theory/posterior?theory_version=1.0.0&prior=0.1"
    )
    assert response.status_code == 200

    result = response.json()
    assert result["theory_id"] == "posterior-theory"
    assert result["version"] == "1.0.0"
    assert result["prior"] == 0.1
    assert result["evidence_count"] == 1
    assert result["families_analyzed"] == 1
    assert result["accumulated_bf"] > 1.0
    assert result["posterior"] > result["prior"]
    assert result["support_class"] in ["insufficient", "weak", "moderate", "strong"]


def test_get_evidence_trail():
    """Test getting evidence audit trail"""
    # Add evidence
    client.post(
        "/theories/trail-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-001",
            "bayes_factor": 2.5,
            "evidence_type": "segregation",
            "weight": 1.5,
            "source": "clinical_study",
        },
    )

    response = client.get("/theories/trail-theory/evidence?theory_version=1.0.0")
    assert response.status_code == 200

    result = response.json()
    assert result["theory_id"] == "trail-theory"
    assert result["version"] == "1.0.0"
    assert len(result["evidence_trail"]) == 1

    evidence = result["evidence_trail"][0]
    assert evidence["family_id"] == "family-001"
    assert evidence["bayes_factor"] == 2.5
    assert evidence["evidence_type"] == "segregation"
    assert evidence["weight"] == 1.5
    assert evidence["source"] == "clinical_study"
    assert "timestamp" in evidence


def test_support_classification():
    """Test evidence support classification"""
    # Add weak evidence
    response1 = client.post(
        "/theories/classification-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-001",
            "bayes_factor": 1.5,
            "evidence_type": "execution",
            "weight": 1.0,
            "source": "theory_execution",
        },
    )
    result1 = response1.json()
    assert result1["support_class"] in ["insufficient", "weak"]

    # Add strong evidence
    response2 = client.post(
        "/theories/classification-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-002",
            "bayes_factor": 8.0,
            "evidence_type": "segregation",
            "weight": 1.0,
            "source": "clinical_study",
        },
    )
    result2 = response2.json()
    assert result2["support_class"] in ["moderate", "strong"]
    assert result2["accumulated_bf"] > result1["accumulated_bf"]


def test_theory_execution_auto_evidence():
    """Test that theory execution automatically adds evidence"""
    theory = {
        "id": "auto-evidence-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    vcf_data = "#VCFV4.2\n22\t51150000\t.\tA\tT\t60\tPASS"

    # Execute theory
    exec_response = client.post(
        "/theories/auto-evidence-theory/execute",
        json={"theory": theory, "vcf_data": vcf_data, "family_id": "auto-family"},
    )
    assert exec_response.status_code == 200

    # Check that evidence was automatically added
    evidence_response = client.get(
        "/theories/auto-evidence-theory/evidence?theory_version=1.0.0"
    )
    assert evidence_response.status_code == 200

    result = evidence_response.json()
    assert len(result["evidence_trail"]) == 1

    evidence = result["evidence_trail"][0]
    assert evidence["family_id"] == "auto-family"
    assert evidence["evidence_type"] == "execution"
    assert evidence["source"] == "theory_execution"


def test_empty_evidence():
    """Test getting posterior with no evidence"""
    response = client.get(
        "/theories/empty-theory/posterior?theory_version=1.0.0&prior=0.1"
    )
    assert response.status_code == 200

    result = response.json()
    assert result["theory_id"] == "empty-theory"
    assert result["evidence_count"] == 0
    assert result["families_analyzed"] == 0
    assert result["accumulated_bf"] == 1.0
    assert result["posterior"] == result["prior"]
    assert result["support_class"] == "insufficient"


def test_shrinkage_factor():
    """Test shrinkage factor for small sample sizes"""
    # Add single evidence (should have shrinkage)
    response = client.post(
        "/theories/shrinkage-theory/evidence",
        json={
            "theory_version": "1.0.0",
            "family_id": "family-001",
            "bayes_factor": 10.0,
            "evidence_type": "execution",
            "weight": 1.0,
            "source": "theory_execution",
        },
    )

    result = response.json()
    # With shrinkage, accumulated BF should be less than raw BF
    assert result["accumulated_bf"] < 10.0
    assert result["accumulated_bf"] > 1.0
