# import pytest  # Unused import
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_valid_theory_validation():
    """Test validation passes for valid theory JSON"""
    valid_theory = {
        "id": "test-theory-1",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {
            "genes": ["SHANK3", "NRXN1"],
            "pathways": ["synaptic_transmission"],
            "phenotypes": ["autism_spectrum_disorder"],
        },
        "evidence_model": {
            "priors": 0.1,
            "likelihood_weights": {
                "variant_hit": 2.0,
                "segregation": 1.5,
                "pathway": 1.0,
            },
        },
    }

    response = client.post("/theories/validate", json=valid_theory)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    assert data["theory"]["id"] == "test-theory-1"


def test_invalid_theory_missing_required():
    """Test validation fails for theory missing required fields"""
    invalid_theory = {
        "id": "incomplete-theory",
        "version": "1.0.0",
        # Missing scope, criteria, evidence_model
    }

    response = client.post("/theories/validate", json=invalid_theory)
    assert response.status_code == 400
    assert "validation failed" in response.json()["detail"].lower()


def test_invalid_version_format():
    """Test validation fails for invalid semantic version"""
    invalid_theory = {
        "id": "bad-version-theory",
        "version": "1.0",  # Invalid semver format
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {}},
    }

    response = client.post("/theories/validate", json=invalid_theory)
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"].lower()


def test_invalid_scope_enum():
    """Test validation fails for invalid scope value"""
    invalid_theory = {
        "id": "bad-scope-theory",
        "version": "1.0.0",
        "scope": "invalid_scope",  # Not in enum
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {}},
    }

    response = client.post("/theories/validate", json=invalid_theory)
    assert response.status_code == 400
