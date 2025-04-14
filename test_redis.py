"""
Test script to verify Redis connection and cache functionality.
"""
import asyncio
from tldw.utils.redis_cache import add_to_cache, get_from_cache, clear_cache

async def test_redis_cache():
    """Test the basic functionality of the Redis cache."""
    print("Testing Redis cache...")
    
    # Clear the cache
    clear_cache()
    print("Cache cleared.")
    
    # Add a value to the cache
    test_key = "test_key"
    test_value = "This is a test value"
    add_to_cache(test_key, test_value)
    print(f"Value added to cache: {test_key} -> {test_value}")
    
    # Retrieve the value from the cache
    retrieved_value = get_from_cache(test_key)
    print(f"Value retrieved from cache: {retrieved_value}")
    
    # Verify that the retrieved value is correct
    if retrieved_value == test_value:
        print("✅ Test successful: The retrieved value matches the original value.")
    else:
        print("❌ Test failed: The retrieved value does not match the original value.")
        print(f"  Original value: {test_value}")
        print(f"  Retrieved value: {retrieved_value}")
    
    # Test with a non-existent key
    non_existent_key = "non_existent_key"
    non_existent_value = get_from_cache(non_existent_key)
    print(f"Value for non-existent key: {non_existent_value}")
    
    if non_existent_value is None:
        print("✅ Test successful: The non-existent key returns None.")
    else:
        print("❌ Test failed: The non-existent key does not return None.")
        print(f"  Retrieved value: {non_existent_value}")
    
    # Test with a structured value (dictionary)
    dict_key = "dict_key"
    dict_value = {"name": "TLDW Bot", "version": "1.0", "features": ["YouTube", "Twitter", "Web"]}
    add_to_cache(dict_key, dict_value)
    print(f"Dictionary added to cache: {dict_key} -> {dict_value}")
    
    # Retrieve the dictionary
    retrieved_dict = get_from_cache(dict_key)
    print(f"Dictionary retrieved from cache: {retrieved_dict}")
    
    # Verify that the retrieved dictionary is correct
    if retrieved_dict == dict_value:
        print("✅ Test successful: The retrieved dictionary matches the original.")
    else:
        print("❌ Test failed: The retrieved dictionary does not match the original.")
        print(f"  Original dictionary: {dict_value}")
        print(f"  Retrieved dictionary: {retrieved_dict}")
    
    print("Cache tests completed.")

if __name__ == "__main__":
    asyncio.run(test_redis_cache())
