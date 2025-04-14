"""
Command handlers for the TLDW Discord bot.
"""
import discord
from discord.ext import commands

from tldw.utils.url_utils import is_valid_url, determine_content_type, ContentType
from tldw.utils.cache_utils import get_from_cache, add_to_cache
from tldw.services.content_service import (
    extract_youtube_transcript,
    extract_twitter_content,
    extract_web_content
)
from tldw.services.gemini_service import generate_summary_with_gemini

def help_command() -> str:
    """Return information about the bot's commands.
    
    Returns:
        A string containing help information.
    """
    help_text = """
    **TLDW Bot Help**
    
    This bot generates summaries of YouTube videos, web pages, and Twitter threads.
    
    **Commands:**
    
    `/help` - Show this help message
    `/tldw [url]` - Generate a summary of a YouTube video
    `/tldr [url]` - Generate a summary of a web page or Twitter thread
    
    If no URL is provided, the bot will search for a URL in the previous messages.
    
    **Examples:**
    
    `/tldw https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    `/tldr https://twitter.com/username/status/1234567890`
    """
    return help_text

async def handle_tldw_command(ctx, url: str = None) -> None:
    """Handle the TLDW command to summarize YouTube videos.
    
    Args:
        ctx: The Discord context.
        url: The URL of the YouTube video to summarize.
    """
    # If no URL is provided, search for a YouTube URL in previous messages
    if not url:
        await ctx.send("No URL provided. Searching for a YouTube URL in previous messages...")
        # This is a placeholder for future implementation
        await ctx.send("Feature not yet implemented: searching for URLs in previous messages.")
        return
    
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
    
    # Send a message to indicate that the bot is working
    await ctx.send(f"Generating summary for YouTube video: {url}...")
    
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
        await ctx.send(f"An error occurred: {str(e)}")

async def handle_tldr_command(ctx, url: str = None) -> None:
    """Handle the TLDR command to summarize web pages and Twitter threads.
    
    Args:
        ctx: The Discord context.
        url: The URL of the web page or Twitter thread to summarize.
    """
    # This is a placeholder for future implementation
    await ctx.send("The TLDR command is not yet implemented.")
