"""
Help command for TLDW Discord bot.

Provides information about available commands and usage examples.
"""

from .base import BaseCommand


class HelpCommand(BaseCommand):
    """Command to display help information about the bot."""
    
    def get_command_name(self) -> str:
        return "info"
    
    def get_command_description(self) -> str:
        return "Get information about the bot"
    
    async def execute(self, ctx) -> None:
        """
        Display help information about the bot and its commands.
        
        Args:
            ctx: Discord context
        """
        help_text = """
    **TLDW Bot Help**
    
    This bot generates summaries of YouTube videos, web pages, and Twitter threads.
    
    **Commands:**
    
    `/info` - Show this help message
    `/tldw [url]` - Generate a summary of a YouTube video
    `/tldr [url]` - Generate a summary of a web page or Twitter thread
    `/summary [count] [time_filter]` - Generate a topic-based summary of recent conversation
    
    If no URL is provided for tldw/tldr, the bot will search for a URL in the previous messages.
    For summary: count (default 100, max 200) and time_filter (e.g., "1h", "30m") are optional.
    
    **Examples:**
    
    `/tldw https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    `/tldr https://twitter.com/username/status/1234567890`
    `/summary 50` - Summarize last 50 messages by topic
    `/summary 100 2h` - Summarize last 100 messages from the past 2 hours
    """
        await ctx.send(help_text)