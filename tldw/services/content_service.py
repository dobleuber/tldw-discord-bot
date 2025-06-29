"""
Content extraction services for different types of content.
"""
from markitdown import MarkItDown

async def extract_youtube_transcript(url: str) -> str:
    """Extract the transcript from a YouTube video.
    
    Args:
        url: The URL of the YouTube video.
        
    Returns:
        The transcript of the video as a string.
    """
    markitdown = MarkItDown()
    result = markitdown.convert(url)
    return result.text_content

async def extract_twitter_content(url: str) -> str:
    """Extract content from a Twitter thread.
    
    Args:
        url: The URL of the Twitter thread.
        
    Returns:
        The content of the Twitter thread as a string.
    """
    markitdown = MarkItDown()
    result = markitdown.convert(url)
    return result.text_content

async def extract_web_content(url: str) -> str:
    """Extract content from a web page.
    
    Args:
        url: The URL of the web page.
        
    Returns:
        The content of the web page as a string.
    """
    markitdown = MarkItDown()
    result = markitdown.convert(url)
    return result.text_content
