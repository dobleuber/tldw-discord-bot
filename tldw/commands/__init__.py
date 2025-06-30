"""
Command system for TLDW Discord bot.

This module provides a modular command architecture with automatic registration
and consistent patterns for all bot commands.
"""

from .base import BaseCommand
from .registry import CommandRegistry

# Import command classes to ensure they're available for auto-discovery
from .help_command import HelpCommand
from .tldw_command import TldwCommand
from .tldr_command import TldrCommand
from .summary_command import SummaryCommand

# Global command registry instance
registry = CommandRegistry()

# Export commonly used classes and functions
__all__ = [
    'BaseCommand',
    'CommandRegistry', 
    'registry',
    'HelpCommand',
    'TldwCommand', 
    'TldrCommand',
    'SummaryCommand'
]