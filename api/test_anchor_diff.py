from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_store_genomic_data():
    """Test storing genomic data with anchor+diff compression"""
    vcf_data = """#VCFV4.2
1	12345	.	A	T	60	PASS
1	23456	.	G	C	55	PASS
2	34567	.	C	T	70	PASS"""

    genomic_request = {
        "individual_id": "patient-001",
        "vcf_data": vcf_data,
        "reference_genome": "GRCh38",
    }

    response = client.post("/genomic/store", json=genomic_request)
    assert response.status_code == 200

    data = response.json()
    assert data["individual_id"] == "patient-001"
    assert "anchor_id" in data
    assert data["total_variants"] == 3
    assert data["storage_size_mb"] > 0
    assert data["compression_ratio"] > 0


def test_materialize_sequence():
    """Test materializing genomic sequence from stored data"""
    # First store data
    vcf_data = """#VCFV4.2
1	100	.	A	T	60	PASS
1	200	.	G	C	55	PASS"""

    store_response = client.post(
        "/genomic/store",
        json={
            "individual_id": "patient-002",
            "vcf_data": vcf_data,
            "reference_genome": "GRCh38",
        },
    )
    assert store_response.status_code == 200
    anchor_id = store_response.json()["anchor_id"]

    # Then materialize sequence
    response = client.get(f"/genomic/materialize/patient-002/{anchor_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["individual_id"] == "patient-002"
    assert data["anchor_id"] == anchor_id
    assert "sequence" in data
    assert len(data["sequence"]) == 400  # Mock sequence length
    assert "stats" in data


def test_materialization_stats():
    """Test getting materialization statistics"""
    # Store data first
    store_response = client.post(
        "/genomic/store",
        json={
            "individual_id": "patient-003",
            "vcf_data": "#VCFV4.2\n1\t300\t.\tA\tG\t80\tPASS",
            "reference_genome": "GRCh38",
        },
    )
    anchor_id = store_response.json()["anchor_id"]

    # Get stats
    response = client.get(f"/genomic/stats/patient-003/{anchor_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["individual_id"] == "patient-003"
    assert data["anchor_id"] == anchor_id
    assert data["reference_genome"] == "GRCh38"
    assert data["total_variants"] == 1
    assert data["sequence_length"] == 400
    assert "materialization_efficiency" in data


def test_invalid_anchor_id():
    """Test materialization with invalid anchor ID"""
    response = client.get("/genomic/materialize/patient-999/invalid-anchor")
    assert response.status_code == 404
    assert "error" in response.json()


def test_compression_efficiency():
    """Test that anchor+diff provides compression"""
    large_vcf = "#VCFV4.2\n" + "\n".join(
        [f"1\t{i}\t.\tA\tT\t60\tPASS" for i in range(1000, 1010)]
    )

    response = client.post(
        "/genomic/store",
        json={
            "individual_id": "patient-large",
            "vcf_data": large_vcf,
            "reference_genome": "GRCh38",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["compression_ratio"] < 1.0  # Should be compressed
    assert data["total_variants"] == 10
