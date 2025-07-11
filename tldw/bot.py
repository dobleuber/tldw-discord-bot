"""
Main Discord bot implementation for TLDW.

Refactored to use the modular command system with automatic command discovery.
"""

import os
import signal
import sys
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from .commands import registry
from .commands.base import DeferredContextWrapper
from .health import start_health_server, stop_health_server
from .logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

# Get the Discord token
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in the .env file")

# Create a bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    logger.info(f"{bot.user.name} has connected to Discord!")
    
    # Start health check server
    start_health_server()
    
    # Auto-discover and register commands
    registry.auto_discover_commands()
    
    # Register slash commands manually (since they need specific parameter definitions)
    await register_slash_commands()
    
    # Sync commands with Discord
    try:
        logger.info("Syncing commands with Discord...")
        await bot.tree.sync()
        logger.info("Commands synced successfully!")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")


async def register_slash_commands():
    """Register slash commands with specific parameter definitions."""
    
    # Info command (no parameters)
    @bot.tree.command(name="info", description="Get information about the bot")
    async def info_slash(interaction: discord.Interaction):
        """Slash command handler for the info command."""
        command = registry.get_command("info")
        if command:
            await interaction.response.defer()
            ctx_wrapper = DeferredContextWrapper(interaction)
            await command.execute_with_error_handling(ctx_wrapper)
    
    # TLDW command (optional URL parameter)
    @bot.tree.command(name="tldw", description="Generate a summary of a YouTube video")
    async def tldw_slash(interaction: discord.Interaction, url: str = None):
        """Slash command handler for the TLDW command."""
        command = registry.get_command("tldw")
        if command:
            await interaction.response.defer()
            ctx_wrapper = DeferredContextWrapper(interaction)
            await command.execute_with_error_handling(ctx_wrapper, url)
    
    # TLDR command (optional URL parameter)
    @bot.tree.command(name="tldr", description="Generate a summary of a web page or Twitter thread")
    async def tldr_slash(interaction: discord.Interaction, url: str = None):
        """Slash command handler for the TLDR command."""
        command = registry.get_command("tldr")
        if command:
            await interaction.response.defer()
            ctx_wrapper = DeferredContextWrapper(interaction)
            await command.execute_with_error_handling(ctx_wrapper, url)
    
    # Summary command (optional count and time_filter parameters)
    @bot.tree.command(name="summary", description="Generate a topic-based summary of recent conversation")
    async def summary_slash(interaction: discord.Interaction, count: int = 100, time_filter: str = None):
        """Slash command handler for the summary command."""
        command = registry.get_command("summary")
        if command:
            await interaction.response.defer()
            ctx_wrapper = DeferredContextWrapper(interaction)
            await command.execute_with_error_handling(ctx_wrapper, count, time_filter)


def register_legacy_commands():
    """Register legacy commands dynamically."""
    
    # Info command
    @bot.command(name="info")
    async def info_legacy(ctx):
        """Legacy command handler for the info command."""
        command = registry.get_command("info")
        if command:
            await command.execute_with_error_handling(ctx)
    
    # TLDW command
    @bot.command(name="tldw")
    async def tldw_legacy(ctx, url: str = None):
        """Legacy command handler for the TLDW command."""
        command = registry.get_command("tldw")
        if command:
            await command.execute_with_error_handling(ctx, url)
    
    # TLDR command
    @bot.command(name="tldr")
    async def tldr_legacy(ctx, url: str = None):
        """Legacy command handler for the TLDR command."""
        command = registry.get_command("tldr")
        if command:
            await command.execute_with_error_handling(ctx, url)
    
    # Summary command
    @bot.command(name="summary")
    async def summary_legacy(ctx, count: int = 100, time_filter: str = None):
        """Legacy command handler for the summary command."""
        command = registry.get_command("summary")
        if command:
            await command.execute_with_error_handling(ctx, count, time_filter)


# Register legacy commands at module level
register_legacy_commands()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    stop_health_server()
    sys.exit(0)


def run_bot():
    """Run the Discord bot."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        logger.info("Starting TLDW Discord bot...")
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        stop_health_server()


if __name__ == "__main__":
    run_bot()