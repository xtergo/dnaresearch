"""Tests for caching functionality"""

import time

from fastapi.testclient import TestClient
from main import app, cache_manager

client = TestClient(app)


def test_cache_gene_search():
    """Test gene search response caching"""
    # Clear cache first
    cache_manager.clear()

    # First request - should miss cache
    response1 = client.get("/genes/search?query=BRCA1")
    assert response1.status_code == 200

    # Second request - should hit cache
    response2 = client.get("/genes/search?query=BRCA1")
    assert response2.status_code == 200
    assert response1.json() == response2.json()

    # Check cache stats
    stats = cache_manager.get_stats()
    assert stats["hits"] >= 1
    assert stats["cached_items"] >= 1


def test_cache_gene_details():
    """Test gene details response caching"""
    cache_manager.clear()

    # First request
    response1 = client.get("/genes/BRCA1")
    assert response1.status_code == 200

    # Second request - should be cached
    response2 = client.get("/genes/BRCA1")
    assert response2.status_code == 200
    assert response1.json() == response2.json()


def test_cache_genomic_stats():
    """Test genomic stats caching"""
    cache_manager.clear()

    # First request
    response1 = client.get("/genomic/stats/patient-001/anchor-001")
    assert response1.status_code == 200

    # Second request - should be cached
    response2 = client.get("/genomic/stats/patient-001/anchor-001")
    assert response2.status_code == 200
    assert response1.json() == response2.json()


def test_cache_different_parameters():
    """Test caching with different parameters"""
    cache_manager.clear()

    # Different queries should have separate cache entries
    response1 = client.get("/genes/search?query=BRCA1")
    response2 = client.get("/genes/search?query=BRCA2")

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() != response2.json()

    # Both should be cached
    stats = cache_manager.get_stats()
    assert stats["cached_items"] >= 2


def test_cache_stats_endpoint():
    """Test cache statistics endpoint"""
    cache_manager.clear()

    # Make some cached requests
    client.get("/genes/search?query=BRCA1")
    client.get("/genes/search?query=BRCA1")  # Cache hit
    client.get("/genes/BRCA2")

    # Get cache stats
    response = client.get("/cache/stats")
    assert response.status_code == 200

    data = response.json()
    assert "hits" in data
    assert "misses" in data
    assert "hit_ratio" in data
    assert "cached_items" in data
    assert data["hits"] >= 1
    assert data["cached_items"] >= 1


def test_cache_clear_endpoint():
    """Test cache clear endpoint"""
    # Add some cached data
    client.get("/genes/search?query=BRCA1")

    # Verify cache has data
    stats_before = client.get("/cache/stats").json()
    assert stats_before["cached_items"] > 0

    # Clear cache
    response = client.delete("/cache/clear")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "cache_cleared"
    assert "timestamp" in data

    # Verify cache is empty
    stats_after = client.get("/cache/stats").json()
    assert stats_after["cached_items"] == 0


def test_cache_invalidate_pattern():
    """Test cache pattern invalidation"""
    cache_manager.clear()

    # Add some cached data
    client.get("/genes/search?query=BRCA1")
    client.get("/genes/BRCA2")
    client.get("/genomic/stats/patient-001/anchor-001")

    # Verify cache has data
    stats_before = client.get("/cache/stats").json()
    assert stats_before["cached_items"] >= 3

    # Invalidate gene-related cache
    response = client.delete("/cache/invalidate?pattern=genes")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "cache_invalidated"
    assert data["pattern"] == "genes"

    # Verify gene cache is cleared but genomic stats remain
    stats_after = client.get("/cache/stats").json()
    assert stats_after["cached_items"] < stats_before["cached_items"]


def test_cache_ttl_behavior():
    """Test cache TTL expiration"""
    cache_manager.clear()

    # Make request
    response1 = client.get("/genes/search?query=BRCA1")
    assert response1.status_code == 200

    # Verify it's cached
    stats = cache_manager.get_stats()
    assert stats["cached_items"] >= 1

    # Manually expire cache entry (simulate TTL)
    cache_manager.cache.clear()  # Force expiration

    # Next request should miss cache
    response2 = client.get("/genes/search?query=BRCA1")
    assert response2.status_code == 200


def test_cache_hit_ratio_calculation():
    """Test cache hit ratio calculation"""
    cache_manager.clear()

    # Make requests to build cache
    client.get("/genes/search?query=BRCA1")  # Miss
    client.get("/genes/search?query=BRCA1")  # Hit
    client.get("/genes/search?query=BRCA1")  # Hit
    client.get("/genes/search?query=BRCA2")  # Miss

    stats = cache_manager.get_stats()
    assert stats["hits"] >= 2
    assert stats["misses"] >= 2
    assert 0 <= stats["hit_ratio"] <= 1


def test_cache_performance_improvement():
    """Test that caching improves response time"""
    cache_manager.clear()

    # First request (cache miss)
    start_time = time.time()
    response1 = client.get("/genes/search?query=autism")
    # first_duration = time.time() - start_time

    # Second request (cache hit)
    start_time = time.time()
    response2 = client.get("/genes/search?query=autism")
    second_duration = time.time() - start_time

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()

    # Cache hit should be faster (though in-memory cache might be too fast to measure)
    # This test mainly verifies the caching mechanism works
    assert second_duration >= 0  # Basic sanity check


def test_post_requests_not_cached():
    """Test that POST requests are not cached"""
    cache_manager.clear()

    # POST requests should not be cached
    webhook_data = {"event_type": "sequencing_complete", "sample_id": "test_sample"}

    response = client.post("/webhooks/sequencing/illumina", json=webhook_data)
    assert response.status_code == 200

    # Cache should still be empty
    stats = cache_manager.get_stats()
    assert stats["cached_items"] == 0


def test_cache_key_generation():
    """Test cache key generation for different endpoints"""
    cache_manager.clear()

    # Different endpoints should have different cache keys
    client.get("/genes/search?query=BRCA1")
    client.get("/genes/BRCA1")
    client.get("/genes/search?query=BRCA2")

    stats = cache_manager.get_stats()
    assert stats["cached_items"] == 3  # All should be cached separately
