"""
Message utilities for searching URLs in previous messages and analyzing conversation history.
"""
import os
import re
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import discord

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

async def fetch_recent_messages(ctx, limit: int = 100, time_filter: Optional[timedelta] = None) -> List[Dict[str, Any]]:
    """Fetch recent messages from a channel for conversation analysis.
    
    Args:
        ctx: The Discord context (either legacy command context or wrapped interaction).
        limit: Maximum number of messages to fetch.
        time_filter: Optional time filter to only get messages within this timeframe.
        
    Returns:
        List of message dictionaries with relevant information.
    """
    messages = []
    cutoff_time = datetime.utcnow() - time_filter if time_filter else None
    
    try:
        # Check permissions first
        if hasattr(ctx.channel, 'permissions_for'):
            if hasattr(ctx, 'interaction'):
                bot_member = ctx.channel.guild.me if ctx.channel.guild else None
                if bot_member:
                    perms = ctx.channel.permissions_for(bot_member)
                    if not perms.read_message_history:
                        print("Bot does not have read_message_history permission")
                        return []
        
        message_count = 0
        async for message in ctx.channel.history(limit=limit + 5):  # Get a few extra to account for filtering
            # Skip if we've reached the limit after filtering
            if len(messages) >= limit:
                break
                
            # Apply time filter
            if cutoff_time and message.created_at.replace(tzinfo=None) < cutoff_time:
                continue
            
            # Skip the command message itself (for legacy commands)
            if hasattr(ctx, 'message') and message.id == ctx.message.id:
                continue
            
            # Filter out low-quality messages
            if not _is_message_relevant_for_analysis(message):
                continue
            
            message_data = {
                'id': message.id,
                'content': message.content,
                'author': {
                    'id': message.author.id,
                    'name': message.author.display_name,
                    'bot': message.author.bot
                },
                'created_at': message.created_at,
                'channel_id': message.channel.id
            }
            messages.append(message_data)
            message_count += 1
        
        print(f"Fetched {len(messages)} relevant messages for analysis")
        return messages
        
    except discord.errors.Forbidden as e:
        print(f"Permission error: {e}")
        print("Bot needs 'Read Message History' permission in this channel")
        return []
    except Exception as e:
        print(f"Error fetching recent messages: {e}")
        import traceback
        traceback.print_exc()
        return []

def _is_message_relevant_for_analysis(message: discord.Message) -> bool:
    """Check if a message is relevant for conversation analysis.
    
    Args:
        message: Discord message object.
        
    Returns:
        True if message should be included in analysis.
    """
    # Skip bot messages
    if message.author.bot:
        return False
    
    # Skip empty or very short messages
    if len(message.content.strip()) < 5:
        return False
    
    # Skip common bot commands
    if message.content.strip().startswith(('/', '!', '.', '-')):
        return False
    
    # Skip messages that are just URLs (already handled by other commands)
    if len(extract_urls_from_text(message.content)) > 0 and len(message.content.strip()) < 100:
        return False
    
    # Skip messages that are mostly emojis or reactions
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
    if re.sub(emoji_pattern, '', message.content).strip() == '':
        return False
    
    return True

def create_message_range_hash(messages: List[Dict[str, Any]]) -> str:
    """Create a hash representing a range of messages for caching purposes.
    
    Args:
        messages: List of message dictionaries.
        
    Returns:
        SHA256 hash of the message range.
    """
    if not messages:
        return hashlib.sha256(b'').hexdigest()
    
    # Create a string representation of the message range
    message_ids = sorted([str(msg['id']) for msg in messages])
    range_string = '|'.join(message_ids)
    
    # Add channel and count info
    if messages:
        channel_id = messages[0]['channel_id']
        range_string += f'|channel:{channel_id}|count:{len(messages)}'
    
    return hashlib.sha256(range_string.encode('utf-8')).hexdigest()[:16]

def filter_messages_by_relevance(messages: List[Dict[str, Any]], min_length: int = 10) -> List[Dict[str, Any]]:
    """Filter messages by relevance for topic analysis.
    
    Args:
        messages: List of message dictionaries.
        min_length: Minimum content length to consider.
        
    Returns:
        Filtered list of relevant messages.
    """
    relevant_messages = []
    
    for message in messages:
        content = message['content'].strip()
        
        # Apply minimum length filter
        if len(content) < min_length:
            continue
        
        # Skip messages that are mostly punctuation or numbers
        alphanumeric_ratio = sum(c.isalnum() for c in content) / len(content) if content else 0
        if alphanumeric_ratio < 0.3:
            continue
        
        relevant_messages.append(message)
    
    return relevant_messages

def get_conversation_stats(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get basic statistics about a conversation.
    
    Args:
        messages: List of message dictionaries.
        
    Returns:
        Dictionary with conversation statistics.
    """
    if not messages:
        return {}
    
    # Count messages per user
    user_counts = {}
    total_chars = 0
    
    for message in messages:
        user_id = message['author']['id']
        user_name = message['author']['name']
        
        if user_id not in user_counts:
            user_counts[user_id] = {'name': user_name, 'count': 0, 'chars': 0}
        
        user_counts[user_id]['count'] += 1
        user_counts[user_id]['chars'] += len(message['content'])
        total_chars += len(message['content'])
    
    # Get time range
    timestamps = [msg['created_at'] for msg in messages]
    time_range = max(timestamps) - min(timestamps) if timestamps else timedelta(0)
    
    # Sort users by activity
    most_active = sorted(user_counts.values(), key=lambda x: x['count'], reverse=True)[:3]
    
    return {
        'total_messages': len(messages),
        'total_characters': total_chars,
        'unique_users': len(user_counts),
        'time_range_hours': time_range.total_seconds() / 3600,
        'most_active_users': most_active,
        'avg_message_length': total_chars / len(messages) if messages else 0
    }