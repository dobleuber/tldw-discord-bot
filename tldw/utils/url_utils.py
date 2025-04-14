"""
URL validation and content type detection utilities.
"""
import re
from enum import Enum, auto

# Content type definitions
class ContentType(Enum):
    """Enum for different types of content."""
    YOUTUBE = auto()
    TWITTER = auto()
    WEB = auto()

def is_valid_url(url: str) -> bool:
    """Verify if a string is a valid URL.
    
    Args:
        url: The URL to validate.
        
    Returns:
        True if the URL is valid, False otherwise.
    """
    if not url:
        return False
    # Simple pattern to validate URLs
    pattern = r'^(https?://)?(www\.)?[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+(:\d+)?(\/\S*)?$'
    return bool(re.match(pattern, url))

def determine_content_type(url: str) -> ContentType:
    """Determine the type of content based on the URL.
    
    Args:
        url: The URL to analyze.
        
    Returns:
        The ContentType of the URL.
    """
    if not is_valid_url(url):
        raise ValueError("Invalid URL")
    
    # Check for YouTube URLs
    if any(domain in url.lower() for domain in ["youtube.com", "youtu.be"]):
        return ContentType.YOUTUBE
    
    # Check for Twitter URLs
    if any(domain in url.lower() for domain in ["twitter.com", "x.com"]):
        return ContentType.TWITTER
    
    # Default to web content
    return ContentType.WEB
