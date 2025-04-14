"""
Main Discord bot implementation for TLDW.
"""
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from tldw.commands import help_command, handle_tldw_command, handle_tldr_command

# Load environment variables
load_dotenv()

# Get the Discord token
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in the .env file")

# Create a bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f"{bot.user.name} has connected to Discord!")
    
    # Sync commands with Discord
    try:
        print("Syncing commands with Discord...")
        await bot.tree.sync()
        print("Commands synced successfully!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Legacy command
@bot.command(name="info")
async def info(ctx):
    """Command handler for the information command."""
    await ctx.send(help_command())

# Slash command
@bot.tree.command(name="info", description="Get information about the bot")
async def info_slash(interaction: discord.Interaction):
    """Slash command handler for the information command."""
    await interaction.response.send_message(help_command())

# Legacy command
@bot.command(name="tldw")
async def tldw(ctx, url: str = None):
    """Command handler for the TLDW command."""
    await handle_tldw_command(ctx, url)

# Slash command
@bot.tree.command(name="tldw", description="Generate a summary of a YouTube video")
async def tldw_slash(interaction: discord.Interaction, url: str = None):
    """Slash command handler for the TLDW command."""
    # Create a wrapper for the ctx object that the handler expects
    class ContextWrapper:
        def __init__(self, interaction):
            self.interaction = interaction
            self.author = interaction.user
            self.channel = interaction.channel
        
        async def send(self, content):
            await self.interaction.response.send_message(content)
    
    ctx_wrapper = ContextWrapper(interaction)
    await handle_tldw_command(ctx_wrapper, url)

# Legacy command
@bot.command(name="tldr")
async def tldr(ctx, url: str = None):
    """Command handler for the TLDR command."""
    await handle_tldr_command(ctx, url)

# Slash command
@bot.tree.command(name="tldr", description="Generate a summary of a web page or Twitter thread")
async def tldr_slash(interaction: discord.Interaction, url: str = None):
    """Slash command handler for the TLDR command."""
    # Create a wrapper for the ctx object that the handler expects
    class ContextWrapper:
        def __init__(self, interaction):
            self.interaction = interaction
            self.author = interaction.user
            self.channel = interaction.channel
        
        async def send(self, content):
            await self.interaction.response.send_message(content)
    
    ctx_wrapper = ContextWrapper(interaction)
    await handle_tldr_command(ctx_wrapper, url)

def run_bot():
    """Run the Discord bot."""
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
