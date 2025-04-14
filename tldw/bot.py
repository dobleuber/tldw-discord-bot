"""
Main Discord bot implementation for TLDW.
"""
import os
import discord
from discord.ext import commands
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

@bot.command(name="help")
async def help(ctx):
    """Command handler for the help command."""
    await ctx.send(help_command())

@bot.command(name="tldw")
async def tldw(ctx, url: str = None):
    """Command handler for the TLDW command."""
    await handle_tldw_command(ctx, url)

@bot.command(name="tldr")
async def tldr(ctx, url: str = None):
    """Command handler for the TLDR command."""
    await handle_tldr_command(ctx, url)

def run_bot():
    """Run the Discord bot."""
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
