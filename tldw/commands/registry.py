"""
Command registry system for automatic command discovery and registration.
"""

import importlib
import pkgutil
from typing import Dict, List, Type
import discord
from discord.ext import commands

from .base import BaseCommand, command_handler


class CommandRegistry:
    """
    Registry for managing and auto-discovering bot commands.
    
    Automatically discovers command classes and registers them with the Discord bot.
    """
    
    def __init__(self):
        self._commands: Dict[str, BaseCommand] = {}
        self._handlers: Dict[str, tuple] = {}
    
    def register_command(self, command_class: Type[BaseCommand]) -> None:
        """
        Register a command class with the registry.
        
        Args:
            command_class: The command class to register
        """
        command_instance = command_class()
        command_name = command_instance.name
        
        self._commands[command_name] = command_instance
        
        # Create handlers using the decorator
        legacy_handler, slash_handler = command_handler(command_class)
        self._handlers[command_name] = (legacy_handler, slash_handler)
        
        print(f"Registered command: {command_name}")
    
    def get_command(self, name: str) -> BaseCommand:
        """Get a command instance by name."""
        return self._commands.get(name)
    
    def get_handlers(self, name: str) -> tuple:
        """Get the legacy and slash handlers for a command."""
        return self._handlers.get(name, (None, None))
    
    def get_all_commands(self) -> Dict[str, BaseCommand]:
        """Get all registered commands."""
        return self._commands.copy()
    
    def auto_discover_commands(self, package_name: str = "tldw.commands") -> None:
        """
        Automatically discover and register commands from the commands package.
        
        Args:
            package_name: The package to search for command modules
        """
        try:
            package = importlib.import_module(package_name)
            
            # Iterate through all modules in the package
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                if modname in ['__init__', 'base', 'registry']:
                    continue  # Skip infrastructure modules
                
                # Import the module
                module_name = f"{package_name}.{modname}"
                try:
                    module = importlib.import_module(module_name)
                    
                    # Look for command classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # Check if it's a command class (subclass of BaseCommand but not BaseCommand itself)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseCommand) and 
                            attr is not BaseCommand):
                            
                            self.register_command(attr)
                            
                except ImportError as e:
                    print(f"Failed to import command module {module_name}: {e}")
                    
        except ImportError as e:
            print(f"Failed to import commands package {package_name}: {e}")
    
    def register_with_bot(self, bot: commands.Bot) -> None:
        """
        Register all discovered commands with the Discord bot.
        
        Args:
            bot: The Discord bot instance
        """
        for command_name, (legacy_handler, slash_handler) in self._handlers.items():
            command_instance = self._commands[command_name]
            
            # Register legacy command
            if legacy_handler:
                legacy_cmd = commands.Command(
                    name=command_name,
                    callback=legacy_handler,
                    help=command_instance.description
                )
                bot.add_command(legacy_cmd)
            
            # Register slash command - this needs to be done in the bot setup
            # We'll provide the handlers for manual registration
            print(f"Command {command_name} ready for registration")
    
    def register_slash_commands(self, bot: commands.Bot) -> None:
        """
        Register slash commands with the bot's command tree.
        
        This method provides the slash command handlers for manual registration
        since slash commands need specific parameter definitions.
        
        Args:
            bot: The Discord bot instance
        """
        # This will be implemented by each command module
        # as they need specific parameter definitions
        pass