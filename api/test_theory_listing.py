"""Tests for theory listing functionality"""

from fastapi.testclient import TestClient
from main import app, cache_manager

client = TestClient(app)


def test_list_theories_default():
    """Test default theory listing"""
    response = client.get("/theories")
    assert response.status_code == 200

    data = response.json()
    assert "theories" in data
    assert "total_count" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data

    assert data["total_count"] == 6
    assert len(data["theories"]) == 6
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert data["has_more"] is False


def test_list_theories_filter_by_scope():
    """Test filtering theories by scope"""
    response = client.get("/theories?scope=autism")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 3

    # All returned theories should be autism-related
    for theory in data["theories"]:
        assert theory["scope"] == "autism"


def test_list_theories_filter_by_lifecycle():
    """Test filtering theories by lifecycle"""
    response = client.get("/theories?lifecycle=active")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 4

    # All returned theories should be active
    for theory in data["theories"]:
        assert theory["lifecycle"] == "active"


def test_list_theories_filter_by_author():
    """Test filtering theories by author"""
    response = client.get("/theories?author=dr.smith")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 1
    assert data["theories"][0]["author"] == "dr.smith"
    assert data["theories"][0]["id"] == "autism-theory-1"


def test_list_theories_filter_by_comments():
    """Test filtering theories by comment presence"""
    response = client.get("/theories?has_comments=true")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 4

    # All returned theories should have comments
    for theory in data["theories"]:
        assert theory["has_comments"] is True


def test_list_theories_search():
    """Test searching theories"""
    response = client.get("/theories?search=SHANK3")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 1
    assert "SHANK3" in data["theories"][0]["title"]


def test_list_theories_filter_by_tags():
    """Test filtering theories by tags"""
    response = client.get("/theories?tags=validated")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 2

    # All returned theories should have the 'validated' tag
    for theory in data["theories"]:
        assert "validated" in theory["tags"]


def test_list_theories_multiple_tags():
    """Test filtering by multiple tags"""
    response = client.get("/theories?tags=synaptic,validated")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] >= 1

    # Theories should have at least one of the specified tags
    for theory in data["theories"]:
        assert any(tag in theory["tags"] for tag in ["synaptic", "validated"])


def test_list_theories_sort_by_posterior():
    """Test sorting theories by posterior"""
    response = client.get("/theories?sort_by=posterior&sort_order=desc")
    assert response.status_code == 200

    data = response.json()
    theories = data["theories"]

    # Should be sorted by posterior in descending order
    for i in range(len(theories) - 1):
        assert theories[i]["posterior"] >= theories[i + 1]["posterior"]


def test_list_theories_sort_by_evidence_count():
    """Test sorting theories by evidence count"""
    response = client.get("/theories?sort_by=evidence_count&sort_order=desc")
    assert response.status_code == 200

    data = response.json()
    theories = data["theories"]

    # Should be sorted by evidence count in descending order
    for i in range(len(theories) - 1):
        assert theories[i]["evidence_count"] >= theories[i + 1]["evidence_count"]


def test_list_theories_sort_ascending():
    """Test ascending sort order"""
    response = client.get("/theories?sort_by=posterior&sort_order=asc")
    assert response.status_code == 200

    data = response.json()
    theories = data["theories"]

    # Should be sorted by posterior in ascending order
    for i in range(len(theories) - 1):
        assert theories[i]["posterior"] <= theories[i + 1]["posterior"]


def test_list_theories_pagination():
    """Test theory pagination"""
    # Get first 2 theories
    response1 = client.get("/theories?limit=2&offset=0")
    assert response1.status_code == 200

    data1 = response1.json()
    assert len(data1["theories"]) == 2
    assert data1["has_more"] is True

    # Get next 2 theories
    response2 = client.get("/theories?limit=2&offset=2")
    assert response2.status_code == 200

    data2 = response2.json()
    assert len(data2["theories"]) == 2

    # Should be different theories
    theory_ids_1 = [t["id"] for t in data1["theories"]]
    theory_ids_2 = [t["id"] for t in data2["theories"]]
    assert set(theory_ids_1).isdisjoint(set(theory_ids_2))


def test_list_theories_combined_filters():
    """Test combining multiple filters"""
    response = client.get(
        "/theories?scope=autism&lifecycle=active&sort_by=evidence_count"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 2

    # All theories should match both filters
    for theory in data["theories"]:
        assert theory["scope"] == "autism"
        assert theory["lifecycle"] == "active"


def test_get_theory_stats():
    """Test getting theory statistics"""
    response = client.get("/theories/stats")
    assert response.status_code == 200

    data = response.json()
    assert "total_theories" in data
    assert "active_theories" in data
    assert "scope_distribution" in data
    assert "average_posterior" in data
    assert "support_classes" in data

    assert data["total_theories"] == 6
    assert data["active_theories"] == 4
    assert "autism" in data["scope_distribution"]
    assert data["scope_distribution"]["autism"] == 3
    assert 0 <= data["average_posterior"] <= 1


def test_theory_listing_caching():
    """Test that theory listing is cached"""
    cache_manager.clear()

    # First request - should miss cache
    response1 = client.get("/theories?scope=autism")
    assert response1.status_code == 200

    # Second request - should hit cache
    response2 = client.get("/theories?scope=autism")
    assert response2.status_code == 200

    # Results should be identical
    assert response1.json() == response2.json()

    # Check cache stats
    stats = cache_manager.get_stats()
    assert stats["hits"] >= 1


def test_theory_stats_caching():
    """Test that theory stats are cached"""
    cache_manager.clear()

    # First request
    response1 = client.get("/theories/stats")
    assert response1.status_code == 200

    # Second request - should be cached
    response2 = client.get("/theories/stats")
    assert response2.status_code == 200

    assert response1.json() == response2.json()


def test_theory_listing_response_structure():
    """Test theory listing response structure"""
    response = client.get("/theories?limit=1")
    assert response.status_code == 200

    data = response.json()
    theory = data["theories"][0]

    # Check all required fields are present
    required_fields = [
        "id",
        "version",
        "title",
        "scope",
        "lifecycle",
        "author",
        "created_at",
        "updated_at",
        "evidence_count",
        "posterior",
        "support_class",
        "tags",
        "has_comments",
    ]

    for field in required_fields:
        assert field in theory

    # Check data types
    assert isinstance(theory["id"], str)
    assert isinstance(theory["version"], str)
    assert isinstance(theory["title"], str)
    assert isinstance(theory["evidence_count"], int)
    assert isinstance(theory["posterior"], float)
    assert isinstance(theory["tags"], list)
    assert isinstance(theory["has_comments"], bool)


def test_empty_search_results():
    """Test search with no results"""
    response = client.get("/theories?search=nonexistent_theory")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 0
    assert data["theories"] == []
    assert data["has_more"] is False


def test_invalid_sort_field():
    """Test with invalid sort field falls back to default"""
    response = client.get("/theories?sort_by=invalid_field")
    assert response.status_code == 200

    # Should still return results (falls back to default sorting)
    data = response.json()
    assert data["total_count"] > 0
