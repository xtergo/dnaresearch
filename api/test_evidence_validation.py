import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import datetime

client = TestClient(app)

def test_valid_variant_hit_evidence():
    """Test validation passes for valid variant_hit evidence"""
    variant_evidence = {
        "type": "variant_hit",
        "weight": 2.5,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "gene": "SHANK3",
            "variant": "c.3679C>T",
            "impact": "high"
        },
        "source": "clinical_lab",
        "confidence": 0.9
    }
    
    response = client.post("/evidence/validate", json=variant_evidence)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    assert data["evidence"]["type"] == "variant_hit"

def test_valid_segregation_evidence():
    """Test validation passes for valid segregation evidence"""
    segregation_evidence = {
        "type": "segregation",
        "weight": 1.8,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "family_id": "FAM001",
            "affected_carriers": 3,
            "unaffected_carriers": 1,
            "segregation_score": 0.75
        },
        "source": "family_study",
        "confidence": 0.85
    }
    
    response = client.post("/evidence/validate", json=segregation_evidence)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    assert data["evidence"]["type"] == "segregation"

def test_valid_pathway_evidence():
    """Test validation passes for valid pathway evidence"""
    pathway_evidence = {
        "type": "pathway",
        "weight": 1.2,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "pathway_name": "synaptic_transmission",
            "genes_in_pathway": ["SHANK3", "NRXN1", "NLGN4X"],
            "enrichment_score": 2.3
        },
        "source": "pathway_db",
        "confidence": 0.7
    }
    
    response = client.post("/evidence/validate", json=pathway_evidence)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    assert data["evidence"]["type"] == "pathway"

def test_invalid_evidence_missing_required():
    """Test validation fails for evidence missing required fields"""
    invalid_evidence = {
        "type": "variant_hit",
        "weight": 2.5
        # Missing timestamp and data
    }
    
    response = client.post("/evidence/validate", json=invalid_evidence)
    assert response.status_code == 400
    assert "validation failed" in response.json()["detail"].lower()

def test_invalid_evidence_type():
    """Test validation fails for invalid evidence type"""
    invalid_evidence = {
        "type": "invalid_type",
        "weight": 1.0,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {"test": "data"}
    }
    
    response = client.post("/evidence/validate", json=invalid_evidence)
    assert response.status_code == 400

def test_invalid_weight_range():
    """Test validation fails for weight outside valid range"""
    invalid_evidence = {
        "type": "variant_hit",
        "weight": 15.0,  # Above maximum of 10
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "gene": "SHANK3",
            "variant": "c.3679C>T",
            "impact": "high"
        }
    }
    
    response = client.post("/evidence/validate", json=invalid_evidence)
    assert response.status_code == 400