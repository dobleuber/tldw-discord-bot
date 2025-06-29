"""
Message utilities for searching URLs in previous messages.
"""
import os
import re
from typing import Optional
from dotenv import load_dotenv

from .url_utils import is_valid_url

# Load environment variables
load_dotenv()

# Get message history limit from environment
MESSAGE_HISTORY_LIMIT = int(os.getenv("MESSAGE_HISTORY_LIMIT", "5"))

def extract_urls_from_text(text: str) -> list[str]:
    """Extract all URLs from a text string.
    
    Args:
        text: The text to search for URLs.
        
    Returns:
        A list of valid URLs found in the text.
    """
    # Pattern to match URLs (http, https, www, or domain.tld format)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.[a-zA-Z]{2,6}[^\s<>"{}|\\^`\[\]]*'
    
    # Find all potential URLs
    potential_urls = re.findall(url_pattern, text)
    
    # Filter to only valid URLs
    valid_urls = []
    for url in potential_urls:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                test_url = f'https://{url}'
            else:
                test_url = f'https://{url}'
        else:
            test_url = url
            
        if is_valid_url(test_url):
            valid_urls.append(test_url)
    
    return valid_urls

async def find_url_in_recent_messages(ctx, limit: Optional[int] = None) -> Optional[str]:
    """Search for URLs in recent messages in the channel.
    
    Args:
        ctx: The Discord context (either legacy command context or wrapped interaction).
        limit: Maximum number of messages to search. Defaults to MESSAGE_HISTORY_LIMIT.
        
    Returns:
        The most recent URL found, or None if no URLs were found.
    """
    if limit is None:
        limit = MESSAGE_HISTORY_LIMIT
    
    try:
        print(f"Searching for URLs in last {limit} messages...")
        print(f"Channel: {ctx.channel.id if ctx.channel else 'None'}")
        print(f"Channel type: {type(ctx.channel) if ctx.channel else 'None'}")
        
        # Check if we have permission to read message history
        if hasattr(ctx.channel, 'permissions_for'):
            # For guild channels, check permissions
            if hasattr(ctx, 'interaction'):
                # For slash commands, use the bot's permissions
                bot_member = ctx.channel.guild.me if ctx.channel.guild else None
                if bot_member:
                    perms = ctx.channel.permissions_for(bot_member)
                    print(f"Bot permissions - read_message_history: {perms.read_message_history}")
                    if not perms.read_message_history:
                        print("Bot does not have read_message_history permission")
                        return None
        
        # Get recent messages from the channel
        message_count = 0
        found_urls_count = 0
        
        async for message in ctx.channel.history(limit=limit + 2):  # Get a couple extra to account for command message
            message_count += 1
            
            # Skip the command message itself (for legacy commands)
            if hasattr(ctx, 'message') and message.id == ctx.message.id:
                continue
                
            # Skip empty messages or bot messages
            if not message.content.strip() or message.author.bot:
                continue
            
            print(f"Checking message: '{message.content[:100]}...'")
            
            # Extract URLs from message content
            urls = extract_urls_from_text(message.content)
            if urls:
                found_urls_count += 1
                print(f"Found URL: {urls[0]}")
                # Return the first (most recent) URL found
                return urls[0]
        
        print(f"Searched {message_count} messages, found {found_urls_count} URLs")
        return None
    except discord.errors.Forbidden as e:
        print(f"Permission error: {e}")
        print("Bot needs 'Read Message History' permission in this channel")
        return None
    except Exception as e:
        print(f"Error searching for URLs in recent messages: {e}")
        import traceback
        traceback.print_exc()
        return None