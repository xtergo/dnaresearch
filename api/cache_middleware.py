"""Cache middleware for FastAPI"""

import json
from functools import wraps
from fastapi import Request, Response
from cache_manager import CacheManager

cache_manager = CacheManager()

# Cache TTL settings (seconds)
CACHE_SETTINGS = {
    "/genes/search": 3600,      # 1 hour - gene data rarely changes
    "/genes/": 7200,            # 2 hours - individual gene details
    "/theories/": 1800,         # 30 minutes - theory data
    "/health": 60,              # 1 minute - health checks
    "/genomic/stats/": 300,     # 5 minutes - genomic stats
}

def get_cache_ttl(endpoint: str) -> int:
    """Get cache TTL for endpoint"""
    for pattern, ttl in CACHE_SETTINGS.items():
        if pattern in endpoint:
            return ttl
    return 300  # Default 5 minutes

def cache_response(func):
    """Decorator to cache GET responses"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For FastAPI, we need to check if this is a GET request
        # Since we can't access request directly, we'll cache all calls
        # and let the cache manager handle the logic
        
        # Generate a simple cache key from function name and args
        func_name = func.__name__
        cache_key = f"{func_name}_{hash(str(kwargs))}"
        
        # Try to get from cache
        cached_response = cache_manager.get(cache_key)
        if cached_response is not None:
            return cached_response
        
        # Execute function and cache result
        response = func(*args, **kwargs)
        
        # Cache the response
        ttl = get_cache_ttl(func_name)
        cache_manager.set(cache_key, response, ttl)
        
        return response
    
    return wrapper

def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    cache_manager.invalidate_pattern(pattern)