"""
Base command class and common utilities for TLDW Discord bot commands.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import discord
from discord.ext import commands

from ..utils.redis_cache import check_rate_limit, check_channel_rate_limit


class BaseCommand(ABC):
    """
    Abstract base class for all TLDW Discord bot commands.
    
    Provides common functionality like rate limiting, error handling,
    and standardized command registration.
    """
    
    def __init__(self):
        """Initialize the command with default settings."""
        self._name = self.get_command_name()
        self._description = self.get_command_description()
        self._rate_limit_user = self.get_user_rate_limit_minutes()
        self._rate_limit_channel = self.get_channel_rate_limit_minutes()
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return self._name
    
    @property 
    def description(self) -> str:
        """Get the command description."""
        return self._description
    
    @abstractmethod
    def get_command_name(self) -> str:
        """Return the command name (e.g., 'tldw', 'summary')."""
        pass
    
    @abstractmethod
    def get_command_description(self) -> str:
        """Return a brief description for the slash command."""
        pass
    
    @abstractmethod
    async def execute(self, ctx, *args, **kwargs) -> None:
        """
        Execute the command logic.
        
        Args:
            ctx: Discord context (command context or wrapped interaction)
            *args: Positional arguments for the command
            **kwargs: Keyword arguments for the command
        """
        pass
    
    def get_user_rate_limit_minutes(self) -> Optional[int]:
        """
        Get the rate limit for users in minutes.
        
        Returns:
            Number of minutes, or None for no rate limiting.
        """
        return None
    
    def get_channel_rate_limit_minutes(self) -> Optional[int]:
        """
        Get the rate limit for channels in minutes.
        
        Returns:
            Number of minutes, or None for no rate limiting.
        """
        return None
    
    async def check_rate_limits(self, ctx) -> bool:
        """
        Check if the command can be executed based on rate limits.
        
        Args:
            ctx: Discord context
            
        Returns:
            True if command can be executed, False if rate limited
        """
        user_id = str(ctx.author.id)
        channel_id = str(ctx.channel.id)
        
        # Check user rate limit
        if self._rate_limit_user:
            if not check_rate_limit(user_id, self._name, self._rate_limit_user):
                await ctx.send(f"⏱️ You can only use the {self._name} command once every {self._rate_limit_user} minutes. Please wait before trying again.")
                return False
        
        # Check channel rate limit  
        if self._rate_limit_channel:
            if not check_channel_rate_limit(channel_id, self._name, self._rate_limit_channel):
                await ctx.send(f"⏱️ The {self._name} command was used recently in this channel. Please wait before using it again.")
                return False
        
        return True
    
    async def handle_error(self, ctx, error: Exception) -> None:
        """
        Handle errors that occur during command execution.
        
        Args:
            ctx: Discord context
            error: The exception that occurred
        """
        print(f"Error in {self._name} command: {error}")
        import traceback
        traceback.print_exc()
        await ctx.send(f"❌ An error occurred while executing the {self._name} command: {str(error)}")
    
    async def execute_with_error_handling(self, ctx, *args, **kwargs) -> None:
        """
        Execute the command with built-in error handling and rate limiting.
        
        Args:
            ctx: Discord context
            *args: Positional arguments for the command
            **kwargs: Keyword arguments for the command
        """
        try:
            # Check rate limits first
            if not await self.check_rate_limits(ctx):
                return
            
            # Execute the command
            await self.execute(ctx, *args, **kwargs)
            
        except Exception as error:
            await self.handle_error(ctx, error)


class DeferredContextWrapper:
    """Wrapper for deferred Discord interactions compatible with legacy command handlers."""
    
    def __init__(self, interaction):
        self.interaction = interaction
        self.author = interaction.user
        self.channel = interaction.channel
    
    async def send(self, content):
        try:
            await self.interaction.followup.send(content)
        except discord.errors.NotFound:
            # If interaction expired, try to send to channel directly
            if self.interaction.channel:
                await self.interaction.channel.send(content)


def command_handler(command_class):
    """
    Decorator to create both legacy and slash command handlers for a command class.
    
    Args:
        command_class: The command class to create handlers for
        
    Returns:
        A tuple of (legacy_handler, slash_handler) functions
    """
    command_instance = command_class()
    
    async def legacy_handler(ctx, *args, **kwargs):
        """Legacy command handler."""
        await command_instance.execute_with_error_handling(ctx, *args, **kwargs)
    
    async def slash_handler(interaction: discord.Interaction, *args, **kwargs):
        """Slash command handler with deferred response."""
        await interaction.response.defer()
        ctx_wrapper = DeferredContextWrapper(interaction)
        await command_instance.execute_with_error_handling(ctx_wrapper, *args, **kwargs)
    
    return legacy_handler, slash_handler