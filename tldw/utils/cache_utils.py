"""
Cache utilities for storing generated summaries.
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

# Cache for storing generated summaries
summary_cache: Dict[str, Tuple[str, datetime]] = {}
CACHE_EXPIRATION = timedelta(hours=24)

def get_from_cache(key: str) -> Optional[str]:
    """Get a summary from the cache if it exists and is not expired.
    
    Args:
        key: The cache key (usually the URL).
        
    Returns:
        The cached summary if it exists and is not expired, None otherwise.
    """
    if key in summary_cache:
        summary, timestamp = summary_cache[key]
        if datetime.now() - timestamp < CACHE_EXPIRATION:
            return summary
        # Remove expired entry
        del summary_cache[key]
    return None

def add_to_cache(key: str, summary: str) -> None:
    """Add a summary to the cache.
    
    Args:
        key: The cache key (usually the URL).
        summary: The summary to cache.
    """
    summary_cache[key] = (summary, datetime.now())

def clear_cache() -> None:
    """Clear all entries from the cache."""
    summary_cache.clear()

def remove_expired_entries() -> None:
    """Remove expired entries from the cache."""
    now = datetime.now()
    expired_keys = [
        key for key, (_, timestamp) in summary_cache.items()
        if now - timestamp >= CACHE_EXPIRATION
    ]
    for key in expired_keys:
        del summary_cache[key]
