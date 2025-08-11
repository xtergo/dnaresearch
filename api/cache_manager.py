"""Redis cache manager for response caching"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional


class CacheManager:
    """Redis-like cache manager for API responses"""

    def __init__(self):
        # In-memory cache for development (Redis in production)
        self.cache = {}
        self.expiry = {}
        self.key_mapping = {}  # Maps original keys to hashed keys
        self.hit_count = 0
        self.miss_count = 0

    def _generate_key(self, endpoint: str, params: dict = None) -> str:
        """Generate cache key from endpoint and parameters"""
        key_data = {"endpoint": endpoint}
        if params:
            key_data["params"] = params

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, endpoint: str, params: dict = None) -> Optional[Any]:
        """Get cached response"""
        key = self._generate_key(endpoint, params)

        # Check if key exists and not expired
        if key in self.cache:
            if key in self.expiry and datetime.utcnow() > self.expiry[key]:
                # Expired, remove from cache
                del self.cache[key]
                del self.expiry[key]
                self.miss_count += 1
                return None

            self.hit_count += 1
            return self.cache[key]

        self.miss_count += 1
        return None

    def set(
        self, endpoint: str, data: Any, ttl_seconds: int = 300, params: dict = None
    ):
        """Set cached response with TTL"""
        key = self._generate_key(endpoint, params)
        self.cache[key] = data
        self.key_mapping[endpoint] = key  # Store mapping for pattern matching

        if ttl_seconds > 0:
            self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    def delete(self, endpoint: str, params: dict = None):
        """Delete cached response"""
        key = self._generate_key(endpoint, params)
        if key in self.cache:
            del self.cache[key]
        if key in self.expiry:
            del self.expiry[key]

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.expiry.clear()
        self.key_mapping.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_ratio = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_ratio": round(hit_ratio, 3),
            "cached_items": len(self.cache),
        }

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        keys_to_delete = []
        original_keys_to_delete = []

        # Find original keys that match pattern
        for original_key, hashed_key in list(self.key_mapping.items()):
            if pattern in original_key:
                keys_to_delete.append(hashed_key)
                original_keys_to_delete.append(original_key)

        # Delete from cache
        for key in keys_to_delete:
            if key in self.cache:
                del self.cache[key]
            if key in self.expiry:
                del self.expiry[key]

        # Delete from key mapping
        for key in original_keys_to_delete:
            if key in self.key_mapping:
                del self.key_mapping[key]
