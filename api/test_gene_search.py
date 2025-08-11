"""Tests for gene search functionality"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_gene_search_exact_symbol():
    """Test exact gene symbol search"""
    response = client.get("/genes/search?query=BRCA1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["query"] == "BRCA1"
    assert data["count"] >= 1
    assert len(data["results"]) >= 1
    
    # Should find BRCA1 as exact match
    brca1_result = next((r for r in data["results"] if r["symbol"] == "BRCA1"), None)
    assert brca1_result is not None
    assert brca1_result["match_type"] == "exact_symbol"
    assert brca1_result["chromosome"] == "17"


def test_gene_search_exact_alias():
    """Test exact gene alias search"""
    response = client.get("/genes/search?query=PROSAP2")
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] >= 1
    
    # Should find SHANK3 via its alias PROSAP2
    result = data["results"][0]
    assert result["symbol"] == "SHANK3"
    assert "PROSAP2" in result["aliases"]


def test_gene_search_coordinate():
    """Test coordinate-based gene search"""
    response = client.get("/genes/search?query=22:51150000-51180000")
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] >= 1
    
    # Should find SHANK3 in this region
    shank3_result = next((r for r in data["results"] if r["symbol"] == "SHANK3"), None)
    assert shank3_result is not None
    assert shank3_result["match_type"] == "coordinate"


def test_gene_search_partial_match():
    """Test partial/fuzzy gene search"""
    response = client.get("/genes/search?query=autism")
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] >= 1
    
    # Should find genes related to autism
    autism_genes = ["SHANK3", "NRXN1", "SYNGAP1"]
    found_symbols = [r["symbol"] for r in data["results"]]
    assert any(gene in found_symbols for gene in autism_genes)


def test_gene_search_limit():
    """Test search result limiting"""
    response = client.get("/genes/search?query=BR&limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["results"]) <= 2


def test_gene_search_empty_query():
    """Test empty query handling"""
    response = client.get("/genes/search?query=")
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_gene_search_no_matches():
    """Test search with no matches"""
    response = client.get("/genes/search?query=NONEXISTENTGENE123")
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_get_gene_details_success():
    """Test getting gene details by symbol"""
    response = client.get("/genes/BRCA1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["symbol"] == "BRCA1"
    assert data["name"] == "BRCA1 DNA repair associated"
    assert data["chromosome"] == "17"
    assert "43044295" in data["location"]
    assert isinstance(data["aliases"], list)
    assert isinstance(data["pathways"], list)
    assert "dna_repair" in data["pathways"]


def test_get_gene_details_case_insensitive():
    """Test gene details with different case"""
    response = client.get("/genes/brca1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["symbol"] == "BRCA1"


def test_get_gene_details_not_found():
    """Test gene details for non-existent gene"""
    response = client.get("/genes/NONEXISTENT")
    assert response.status_code == 404
    
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_gene_search_performance():
    """Test gene search performance"""
    import time
    
    start_time = time.time()
    response = client.get("/genes/search?query=BRCA")
    end_time = time.time()
    
    assert response.status_code == 200
    # Should complete within 200ms as per requirements
    assert (end_time - start_time) < 0.2


def test_gene_search_autism_genes():
    """Test that autism-related genes are properly indexed"""
    autism_genes = ["SHANK3", "NRXN1", "SYNGAP1"]
    
    for gene in autism_genes:
        response = client.get(f"/genes/search?query={gene}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 1
        
        # Should find exact match
        exact_match = next((r for r in data["results"] if r["symbol"] == gene), None)
        assert exact_match is not None
        assert exact_match["match_type"] == "exact_symbol"


def test_gene_search_cancer_genes():
    """Test that cancer-related genes are properly indexed"""
    cancer_genes = ["BRCA1", "BRCA2"]
    
    for gene in cancer_genes:
        response = client.get(f"/genes/search?query={gene}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 1
        
        # Should find exact match
        exact_match = next((r for r in data["results"] if r["symbol"] == gene), None)
        assert exact_match is not None
        assert "cancer" in exact_match["description"].lower()