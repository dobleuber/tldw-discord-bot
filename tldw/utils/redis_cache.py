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

# Summary-specific cache functions
def get_summary_from_cache(channel_id: str, message_hash: str) -> Optional[Any]:
    """Get a conversation summary from the cache.
    
    Args:
        channel_id: Discord channel ID.
        message_hash: Hash of the message range.
        
    Returns:
        Cached summary data if it exists, None otherwise.
    """
    cache_key = f"summary:{channel_id}:{message_hash}"
    return cache.get(cache_key)

def add_summary_to_cache(channel_id: str, message_hash: str, summary_data: Any, ttl_hours: int = 2) -> None:
    """Add a conversation summary to the cache with shorter TTL.
    
    Args:
        channel_id: Discord channel ID.
        message_hash: Hash of the message range.
        summary_data: Summary data to cache.
        ttl_hours: Time to live in hours (default 2 hours for summaries).
    """
    cache_key = f"summary:{channel_id}:{message_hash}"
    
    # Create a custom cache instance with shorter TTL for summaries
    if hasattr(cache, 'redis'):
        ttl_seconds = ttl_hours * 3600
        if isinstance(summary_data, (dict, list, tuple)):
            value = json.dumps(summary_data)
        else:
            value = summary_data
        cache.redis.setex(cache_key, ttl_seconds, value)
    else:
        # Fallback for non-Redis cache
        cache.set(cache_key, summary_data)

def get_recent_summary_keys(channel_id: str, limit: int = 10) -> list[str]:
    """Get recent summary cache keys for a channel.
    
    Args:
        channel_id: Discord channel ID.
        limit: Maximum number of keys to return.
        
    Returns:
        List of recent summary cache keys.
    """
    if hasattr(cache, 'redis'):
        pattern = f"summary:{channel_id}:*"
        keys = cache.redis.keys(pattern)
        return sorted(keys, reverse=True)[:limit]
    return []

def cleanup_old_summaries(channel_id: str, keep_count: int = 5) -> None:
    """Clean up old summary cache entries for a channel.
    
    Args:
        channel_id: Discord channel ID.
        keep_count: Number of recent summaries to keep.
    """
    if hasattr(cache, 'redis'):
        recent_keys = get_recent_summary_keys(channel_id, keep_count * 2)
        if len(recent_keys) > keep_count:
            keys_to_delete = recent_keys[keep_count:]
            if keys_to_delete:
                cache.redis.delete(*keys_to_delete)

# Rate limiting cache functions
def get_rate_limit_key(user_id: str, command: str) -> str:
    """Generate a rate limit cache key.
    
    Args:
        user_id: Discord user ID.
        command: Command name.
        
    Returns:
        Rate limit cache key.
    """
    return f"rate_limit:{command}:{user_id}"

def check_rate_limit(user_id: str, command: str, limit_minutes: int = 5) -> bool:
    """Check if a user is rate limited for a command.
    
    Args:
        user_id: Discord user ID.
        command: Command name.
        limit_minutes: Rate limit window in minutes.
        
    Returns:
        True if user can execute command, False if rate limited.
    """
    rate_key = get_rate_limit_key(user_id, command)
    
    if hasattr(cache, 'redis'):
        # Check if key exists
        if cache.redis.exists(rate_key):
            return False
        
        # Set rate limit with TTL
        cache.redis.setex(rate_key, limit_minutes * 60, "1")
        return True
    else:
        # For non-Redis cache, always allow (no rate limiting)
        return True

def get_channel_rate_limit_key(channel_id: str, command: str) -> str:
    """Generate a channel rate limit cache key.
    
    Args:
        channel_id: Discord channel ID.
        command: Command name.
        
    Returns:
        Channel rate limit cache key.
    """
    return f"rate_limit:channel:{command}:{channel_id}"

def check_channel_rate_limit(channel_id: str, command: str, limit_minutes: int = 2) -> bool:
    """Check if a channel is rate limited for a command.
    
    Args:
        channel_id: Discord channel ID.
        command: Command name.
        limit_minutes: Rate limit window in minutes.
        
    Returns:
        True if channel can execute command, False if rate limited.
    """
    rate_key = get_channel_rate_limit_key(channel_id, command)
    
    if hasattr(cache, 'redis'):
        # Check if key exists
        if cache.redis.exists(rate_key):
            return False
        
        # Set rate limit with TTL
        cache.redis.setex(rate_key, limit_minutes * 60, "1")
        return True
    else:
        # For non-Redis cache, always allow (no rate limiting)
        return True
