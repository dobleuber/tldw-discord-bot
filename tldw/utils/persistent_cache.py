"""
Persistent cache utilities for storing generated summaries.
"""
import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any

# Cache directory
CACHE_DIR = os.environ.get("CACHE_DIR", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "summary_cache.pkl")
CACHE_EXPIRATION = timedelta(hours=24)

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

class PersistentCache:
    """A persistent cache that stores data in a file."""
    
    def __init__(self, cache_file: str = CACHE_FILE, expiration: timedelta = CACHE_EXPIRATION):
        """Initialize the persistent cache.
        
        Args:
            cache_file: Path to the cache file.
            expiration: Time after which cache entries expire.
        """
        self.cache_file = cache_file
        self.expiration = expiration
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load the cache from the cache file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
            except (pickle.PickleError, EOFError, FileNotFoundError):
                # If there's an error loading the cache, start with an empty cache
                self.cache = {}
    
    def _save_cache(self) -> None:
        """Save the cache to the cache file."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except (pickle.PickleError, FileNotFoundError):
            # If there's an error saving the cache, log it but continue
            print(f"Error saving cache to {self.cache_file}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache if it exists and is not expired.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached value if it exists and is not expired, None otherwise.
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.expiration:
                return value
            # Remove expired entry
            self.remove(key)
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Add a value to the cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
        """
        self.cache[key] = (value, datetime.now())
        self._save_cache()
    
    def remove(self, key: str) -> None:
        """Remove a key from the cache.
        
        Args:
            key: The cache key to remove.
        """
        if key in self.cache:
            del self.cache[key]
            self._save_cache()
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.cache.clear()
        self._save_cache()
    
    def remove_expired_entries(self) -> None:
        """Remove expired entries from the cache."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.expiration
        ]
        for key in expired_keys:
            self.remove(key)

# Create a global cache instance
cache = PersistentCache()

# Compatibility functions for the existing API
def get_from_cache(key: str) -> Optional[Any]:
    """Get a value from the cache if it exists and is not expired."""
    return cache.get(key)

def add_to_cache(key: str, value: Any) -> None:
    """Add a value to the cache."""
    cache.set(key, value)

def clear_cache() -> None:
    """Clear all entries from the cache."""
    cache.clear()

def remove_expired_entries() -> None:
    """Remove expired entries from the cache."""
    cache.remove_expired_entries()
