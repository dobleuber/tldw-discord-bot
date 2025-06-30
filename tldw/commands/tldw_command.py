"""
TLDW command for YouTube video summarization.

Extracts YouTube video transcripts and generates AI-powered summaries.
"""

from .base import BaseCommand
from ..utils.url_utils import is_valid_url, determine_content_type, ContentType
from ..utils.redis_cache import get_from_cache, add_to_cache
from ..utils.message_utils import find_url_in_recent_messages
from ..services.content_service import extract_youtube_transcript
from ..services.gemini_service import generate_summary_with_gemini


class TldwCommand(BaseCommand):
    """Command to summarize YouTube videos."""
    
    def get_command_name(self) -> str:
        return "tldw"
    
    def get_command_description(self) -> str:
        return "Generate a summary of a YouTube video"
    
    async def execute(self, ctx, url: str = None) -> None:
        """
        Handle the TLDW command to summarize YouTube videos.
        
        Args:
            ctx: The Discord context.
            url: The URL of the YouTube video to summarize.
        """
        # If no URL is provided, search for a URL in previous messages
        if not url:
            await ctx.send("No URL provided. Searching for a URL in previous messages...")
            url = await find_url_in_recent_messages(ctx)
            if not url:
                await ctx.send("No URL found in the last 5 messages. Please provide a YouTube URL.")
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
        
        # Check if the URL is a YouTube URL
        if content_type != ContentType.YOUTUBE:
            await ctx.send(f"The URL {url} is not a YouTube video. Use /tldr for web pages and Twitter threads.")
            return
        
        # Check if the summary is already in the cache
        cached_summary = get_from_cache(url)
        if cached_summary:
            await ctx.send(f"**Summary of YouTube video:**\n{cached_summary}")
            return
        
        try:
            # Extract the transcript
            transcript = await extract_youtube_transcript(url)
            if not transcript:
                await ctx.send("Could not extract transcript from the YouTube video.")
                return
            
            # Generate a summary
            summary = await generate_summary_with_gemini(transcript)
            if not summary:
                await ctx.send("Could not generate a summary for the transcript.")
                return
            
            # Add the summary to the cache
            add_to_cache(url, summary)
            
            # Send the summary
            await ctx.send(f"**Summary of YouTube video:**\n{summary}")
        except Exception as e:
            raise  # Let the base class handle error logging and user notification