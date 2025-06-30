"""
TLDR command for web page and Twitter thread summarization.

Extracts content from web pages and Twitter threads and generates AI-powered summaries.
"""

from .base import BaseCommand
from ..utils.url_utils import is_valid_url, determine_content_type, ContentType
from ..utils.redis_cache import get_from_cache, add_to_cache
from ..utils.message_utils import find_url_in_recent_messages
from ..services.content_service import extract_twitter_content, extract_web_content
from ..services.gemini_service import generate_summary_with_gemini


class TldrCommand(BaseCommand):
    """Command to summarize web pages and Twitter threads."""
    
    def get_command_name(self) -> str:
        return "tldr"
    
    def get_command_description(self) -> str:
        return "Generate a summary of a web page or Twitter thread"
    
    async def execute(self, ctx, url: str = None) -> None:
        """
        Handle the TLDR command to summarize web pages and Twitter threads.
        
        Args:
            ctx: The Discord context.
            url: The URL of the web page or Twitter thread to summarize.
        """
        # If no URL is provided, search for a URL in previous messages
        if not url:
            await ctx.send("No URL provided. Searching for a URL in previous messages...")
            url = await find_url_in_recent_messages(ctx)
            if not url:
                await ctx.send("No URL found in the last 5 messages. Please provide a web page or Twitter URL.")
                return
            else:
                await ctx.send(f"Found URL: {url}")
        
        # Validate the URL
        if not is_valid_url(url):
            await ctx.send(f"Invalid URL: {url}")
            return
        
        # Determine the content type
        try:
            content_type = determine_content_type(url)
        except ValueError:
            await ctx.send(f"Invalid URL: {url}")
            return
        
        # Check if the URL is a YouTube URL (should use tldw instead)
        if content_type == ContentType.YOUTUBE:
            await ctx.send(f"The URL {url} is a YouTube video. Use /tldw for YouTube videos.")
            return
        
        # Check if the summary is already in the cache
        cached_summary = get_from_cache(url)
        if cached_summary:
            content_label = "Twitter thread" if content_type == ContentType.TWITTER else "web page"
            await ctx.send(f"**Summary of {content_label}:**\n{cached_summary}")
            return
        
        try:
            # Extract content based on type
            if content_type == ContentType.TWITTER:
                content = await extract_twitter_content(url)
                content_label = "Twitter thread"
            else:  # ContentType.WEB
                content = await extract_web_content(url)
                content_label = "web page"
            
            if not content:
                await ctx.send(f"Could not extract content from the {content_label}.")
                return
            
            # Generate a summary
            summary = await generate_summary_with_gemini(content)
            if not summary:
                await ctx.send(f"Could not generate a summary for the {content_label}.")
                return
            
            # Add the summary to the cache
            add_to_cache(url, summary)
            
            # Send the summary
            await ctx.send(f"**Summary of {content_label}:**\n{summary}")
        except Exception as e:
            raise  # Let the base class handle error logging and user notification