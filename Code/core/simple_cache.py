"""
Simple Cache - FYP Version
Dictionary-based caching for data and computation results.
Tracks cache hits for thesis metrics (40 lines).
"""
from typing import Any, Optional, Dict
import time

class SimpleCache:
    """Simple dictionary-based cache with TTL and metrics tracking."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        if time.time() - entry['timestamp'] > self._ttl:
            # Expired
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry['value']
    
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp."""
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        print(f"🗑️ Cache cleared. Stats: {self._hits} hits, {self._misses} misses")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for thesis metrics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'total_requests': total,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self._cache),
            'ttl_seconds': self._ttl
        }
    
    def invalidate(self, key: str):
        """Invalidate specific cache entry."""
        if key in self._cache:
            del self._cache[key]
            print(f"🔄 Cache invalidated: {key}")
