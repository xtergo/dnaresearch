from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_fork_theory_success():
    """Test successful theory forking"""
    parent_theory = {
        "id": "parent-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    modifications = {
        "criteria": {"genes": ["SHANK3", "NRXN1"]},
        "evidence_model": {"priors": 0.15, "likelihood_weights": {"variant_hit": 2.5}},
    }

    request_data = {
        "parent_theory": parent_theory,
        "new_theory_id": "child-theory",
        "modifications": modifications,
        "fork_reason": "added_genes",
    }

    response = client.post("/theories/parent-theory/fork", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "theory_forked"
    assert result["new_theory_id"] == "child-theory"
    assert result["new_version"] == "1.0.1"
    assert result["parent_id"] == "parent-theory"
    assert result["parent_version"] == "1.0.0"
    assert "Modified criteria" in result["changes_made"]
    assert "Modified evidence_model" in result["changes_made"]
    assert result["new_theory"]["id"] == "child-theory"
    assert result["new_theory"]["criteria"]["genes"] == ["SHANK3", "NRXN1"]


def test_fork_theory_id_mismatch():
    """Test fork fails with parent theory ID mismatch"""
    parent_theory = {
        "id": "wrong-id",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    request_data = {
        "parent_theory": parent_theory,
        "new_theory_id": "child-theory",
        "modifications": {},
        "fork_reason": "test",
    }

    response = client.post("/theories/correct-id/fork", json=request_data)
    assert response.status_code == 400
    assert "Parent theory ID mismatch" in response.json()["detail"]


def test_fork_theory_invalid_parent():
    """Test fork fails with invalid parent theory"""
    invalid_parent = {
        "id": "invalid-parent",
        "version": "1.0.0",
        # Missing required fields
    }

    request_data = {
        "parent_theory": invalid_parent,
        "new_theory_id": "child-theory",
        "modifications": {},
        "fork_reason": "test",
    }

    response = client.post("/theories/invalid-parent/fork", json=request_data)
    assert response.status_code == 400


def test_get_theory_lineage():
    """Test getting theory lineage"""
    # First fork a theory
    parent_theory = {
        "id": "lineage-parent",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    fork_response = client.post(
        "/theories/lineage-parent/fork",
        json={
            "parent_theory": parent_theory,
            "new_theory_id": "lineage-child",
            "modifications": {"criteria": {"genes": ["SHANK3", "NRXN1"]}},
            "fork_reason": "added_gene",
        },
    )
    assert fork_response.status_code == 200

    # Get lineage for child
    lineage_response = client.get("/theories/lineage-child/lineage?version=1.0.1")
    assert lineage_response.status_code == 200

    result = lineage_response.json()
    assert result["theory_id"] == "lineage-child"
    assert result["version"] == "1.0.1"
    assert result["parent_id"] == "lineage-parent"
    assert result["parent_version"] == "1.0.0"
    assert result["fork_reason"] == "added_gene"
    assert result["is_root"] is False
    assert "created_at" in result


def test_get_theory_lineage_root():
    """Test getting lineage for root theory (no parent)"""
    response = client.get("/theories/root-theory/lineage?version=1.0.0")
    assert response.status_code == 200

    result = response.json()
    assert result["theory_id"] == "root-theory"
    assert result["version"] == "1.0.0"
    assert result["lineage"] is None
    assert result["is_root"] is True


def test_get_theory_children():
    """Test getting theory children"""
    parent_theory = {
        "id": "children-parent",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    # Fork first child
    client.post(
        "/theories/children-parent/fork",
        json={
            "parent_theory": parent_theory,
            "new_theory_id": "child-1",
            "modifications": {"criteria": {"genes": ["SHANK3", "NRXN1"]}},
            "fork_reason": "added_nrxn1",
        },
    )

    # Fork second child
    client.post(
        "/theories/children-parent/fork",
        json={
            "parent_theory": parent_theory,
            "new_theory_id": "child-2",
            "modifications": {
                "evidence_model": {
                    "priors": 0.2,
                    "likelihood_weights": {"variant_hit": 2.0},
                }
            },
            "fork_reason": "increased_prior",
        },
    )

    # Get children
    response = client.get("/theories/children-parent/children?version=1.0.0")
    assert response.status_code == 200

    result = response.json()
    assert result["parent_id"] == "children-parent"
    assert result["parent_version"] == "1.0.0"
    assert len(result["children"]) == 2

    child_ids = [child["theory_id"] for child in result["children"]]
    assert "child-1" in child_ids
    assert "child-2" in child_ids


def test_get_theory_ancestry():
    """Test getting theory ancestry chain"""
    # Create simple parent -> child chain
    parent_theory = {
        "id": "ancestry-parent",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    # Fork child from parent
    child_response = client.post(
        "/theories/ancestry-parent/fork",
        json={
            "parent_theory": parent_theory,
            "new_theory_id": "ancestry-child",
            "modifications": {
                "evidence_model": {
                    "priors": 0.2,
                    "likelihood_weights": {"variant_hit": 2.0},
                }
            },
            "fork_reason": "increased_prior",
        },
    )
    if child_response.status_code != 200:
        print(f"Error: {child_response.json()}")
    assert child_response.status_code == 200
    child_version = child_response.json()["new_version"]

    # Get ancestry for child
    response = client.get(f"/theories/ancestry-child/ancestry?version={child_version}")
    assert response.status_code == 200

    result = response.json()
    assert result["theory_id"] == "ancestry-child"
    assert result["version"] == child_version
    assert len(result["ancestry"]) == 1

    # Check ancestry (child -> parent)
    ancestry = result["ancestry"]
    assert ancestry[0]["theory_id"] == "ancestry-child"
    assert ancestry[0]["parent_id"] == "ancestry-parent"


def test_fork_with_new_fields():
    """Test forking with completely new fields"""
    parent_theory = {
        "id": "new-fields-parent",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    modifications = {
        "description": "Enhanced theory with pathway analysis",
        "criteria": {
            "genes": ["SHANK3"],
            "pathways": ["synaptic_transmission"],
        },
    }

    response = client.post(
        "/theories/new-fields-parent/fork",
        json={
            "parent_theory": parent_theory,
            "new_theory_id": "enhanced-theory",
            "modifications": modifications,
            "fork_reason": "added_pathways",
        },
    )
    assert response.status_code == 200

    result = response.json()
    assert "Added description" in result["changes_made"]
    assert "Modified criteria" in result["changes_made"]
    assert (
        result["new_theory"]["description"] == "Enhanced theory with pathway analysis"
    )


def test_version_increment():
    """Test version incrementation in forks"""
    parent_theory = {
        "id": "version-test",
        "version": "2.1.5",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}},
    }

    response = client.post(
        "/theories/version-test/fork",
        json={
            "parent_theory": parent_theory,
            "new_theory_id": "version-child",
            "modifications": {"criteria": {"genes": ["SHANK3", "NRXN1"]}},
            "fork_reason": "version_test",
        },
    )
    assert response.status_code == 200

    result = response.json()
    assert result["new_version"] == "2.1.6"  # Patch version incremented
