"""
Redis cache utilities for storing generated summaries.
"""
import os
import json
import redis
from datetime import timedelta
from typing import Optional, Any

# Redis configuration
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
CACHE_EXPIRATION = int(os.environ.get("CACHE_EXPIRATION_HOURS", "24")) * 3600  # Convert hours to seconds

class RedisCache:
    """A cache that uses Redis for storage."""
    
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, 
                 db: int = REDIS_DB, password: Optional[str] = REDIS_PASSWORD,
                 expiration: int = CACHE_EXPIRATION):
        """Initialize the Redis cache.
        
        Args:
            host: Redis host.
            port: Redis port.
            db: Redis database number.
            password: Redis password, if required.
            expiration: Time in seconds after which cache entries expire.
        """
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Automatically decode responses to strings
        )
        self.expiration = expiration
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache if it exists.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached value if it exists, None otherwise.
        """
        value = self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If it's not JSON, return as is
                return value
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Add a value to the cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
        """
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        self.redis.setex(key, self.expiration, value)
    
    def remove(self, key: str) -> None:
        """Remove a key from the cache.
        
        Args:
            key: The cache key to remove.
        """
        self.redis.delete(key)
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.redis.flushdb()

# Create a global cache instance
try:
    cache = RedisCache()
except redis.exceptions.ConnectionError:
    # Fallback to a dummy cache if Redis is not available
    print("Warning: Could not connect to Redis. Using a dummy cache instead.")
    
    class DummyCache:
        """A dummy cache that doesn't actually cache anything."""
        def get(self, key: str) -> None:
            return None
        
        def set(self, key: str, value: Any) -> None:
            pass
        
        def remove(self, key: str) -> None:
            pass
        
        def clear(self) -> None:
            pass
    
    cache = DummyCache()

# Compatibility functions for the existing API
def get_from_cache(key: str) -> Optional[Any]:
    """Get a value from the cache if it exists."""
    return cache.get(key)

def add_to_cache(key: str, value: Any) -> None:
    """Add a value to the cache."""
    cache.set(key, value)

def clear_cache() -> None:
    """Clear all entries from the cache."""
    cache.clear()
