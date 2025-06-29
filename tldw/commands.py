"""
Command handlers for the TLDW Discord bot.
"""
import discord
from discord.ext import commands
from datetime import datetime

from tldw.utils.url_utils import is_valid_url, determine_content_type, ContentType
from tldw.utils.redis_cache import (
    get_from_cache, add_to_cache, get_summary_from_cache, add_summary_to_cache,
    check_rate_limit, check_channel_rate_limit, cleanup_old_summaries
)
from tldw.utils.message_utils import (
    find_url_in_recent_messages, fetch_recent_messages, create_message_range_hash,
    filter_messages_by_relevance, get_conversation_stats
)
from tldw.services.content_service import (
    extract_youtube_transcript,
    extract_twitter_content,
    extract_web_content
)
from tldw.services.gemini_service import generate_summary_with_gemini
from tldw.services.topic_analysis_service import identify_conversation_topics, summarize_topic_messages

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
    `/summary [count] [time_filter]` - Generate a topic-based summary of recent conversation
    
    If no URL is provided for tldw/tldr, the bot will search for a URL in the previous messages.
    For summary: count (default 100, max 200) and time_filter (e.g., "1h", "30m") are optional.
    
    **Examples:**
    
    `/tldw https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    `/tldr https://twitter.com/username/status/1234567890`
    `/summary 50` - Summarize last 50 messages by topic
    `/summary 100 2h` - Summarize last 100 messages from the past 2 hours
    """
    return help_text

async def handle_tldw_command(ctx, url: str = None) -> None:
    """Handle the TLDW command to summarize YouTube videos.
    
    Args:
        ctx: The Discord context.
        url: The URL of the YouTube video to summarize.
    """
    # If no URL is provided, search for a URL in previous messages
    if not url:
        await ctx.send("No URL provided. Searching for a URL in previous messages...")
        url = await find_url_in_recent_messages(ctx)
        if not url:
            await ctx.send("No URL found in the last 5 messages. Please provide a YouTube URL.")
            return
        else:
            await ctx.send(f"Found URL: {url}")
    
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
    # If no URL is provided, search for a URL in previous messages
    if not url:
        await ctx.send("No URL provided. Searching for a URL in previous messages...")
        url = await find_url_in_recent_messages(ctx)
        if not url:
            await ctx.send("No URL found in the last 5 messages. Please provide a web page or Twitter URL.")
            return
        else:
            await ctx.send(f"Found URL: {url}")
    
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
    
    # Check if the URL is a YouTube URL (should use tldw instead)
    if content_type == ContentType.YOUTUBE:
        await ctx.send(f"The URL {url} is a YouTube video. Use /tldw for YouTube videos.")
        return
    
    # Check if the summary is already in the cache
    cached_summary = get_from_cache(url)
    if cached_summary:
        content_label = "Twitter thread" if content_type == ContentType.TWITTER else "web page"
        await ctx.send(f"**Summary of {content_label}:**\n{cached_summary}")
        return
    
    try:
        # Extract content based on type
        if content_type == ContentType.TWITTER:
            content = await extract_twitter_content(url)
            content_label = "Twitter thread"
        else:  # ContentType.WEB
            content = await extract_web_content(url)
            content_label = "web page"
        
        if not content:
            await ctx.send(f"Could not extract content from the {content_label}.")
            return
        
        # Generate a summary
        summary = await generate_summary_with_gemini(content)
        if not summary:
            await ctx.send(f"Could not generate a summary for the {content_label}.")
            return
        
        # Add the summary to the cache
        add_to_cache(url, summary)
        
        # Send the summary
        await ctx.send(f"**Summary of {content_label}:**\n{summary}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

async def handle_summary_command(ctx, count: int = 100, time_filter: str = None) -> None:
    """Handle the summary command to analyze and summarize recent conversation by topics.
    
    Args:
        ctx: The Discord context.
        count: Number of messages to analyze (default 100, max 200).
        time_filter: Time filter string like "1h", "30m", "2h" (optional).
    """
    # Rate limiting checks
    user_id = str(ctx.author.id)
    channel_id = str(ctx.channel.id)
    
    # Check user rate limit (5 minutes)
    if not check_rate_limit(user_id, "summary", 5):
        await ctx.send("⏱️ You can only use the summary command once every 5 minutes. Please wait before trying again.")
        return
    
    # Check channel rate limit (2 minutes)
    if not check_channel_rate_limit(channel_id, "summary", 2):
        await ctx.send("⏱️ The summary command was used recently in this channel. Please wait before using it again.")
        return
    
    # Validate and limit message count
    if count < 10:
        count = 10
    elif count > 200:
        count = 200
    
    # Parse time filter
    time_delta = None
    if time_filter:
        time_delta = _parse_time_filter(time_filter)
        if not time_delta:
            await ctx.send("❌ Invalid time filter. Use format like '1h', '30m', '2h' (hours or minutes).")
            return
    
    await ctx.send(f"🔍 Analyzing last {count} messages{f' from the past {time_filter}' if time_filter else ''}...")
    
    try:
        # Fetch recent messages
        messages = await fetch_recent_messages(ctx, limit=count, time_filter=time_delta)
        
        if not messages:
            await ctx.send("❌ No messages found to analyze. Make sure the bot has permission to read message history.")
            return
        
        if len(messages) < 10:
            await ctx.send(f"❌ Only found {len(messages)} messages. Need at least 10 messages for meaningful analysis.")
            return
        
        # Filter messages for relevance
        relevant_messages = filter_messages_by_relevance(messages, min_length=10)
        
        if len(relevant_messages) < 5:
            await ctx.send("❌ Not enough substantial messages found for topic analysis.")
            return
        
        # Create message hash for caching
        message_hash = create_message_range_hash(relevant_messages)
        
        # Check cache first
        cached_summary = get_summary_from_cache(channel_id, message_hash)
        if cached_summary:
            await _send_summary_response(ctx, cached_summary, from_cache=True)
            return
        
        await ctx.send(f"🤖 Analyzing {len(relevant_messages)} relevant messages for topics...")
        
        # Identify topics using AI
        topics = await identify_conversation_topics(relevant_messages, max_topics=5)
        
        if not topics:
            await ctx.send("❌ Could not identify clear topics in the conversation. The discussion might be too fragmented.")
            return
        
        await ctx.send(f"📝 Found {len(topics)} topics. Generating summaries...")
        
        # Generate summaries for each topic
        topic_summaries = []
        for topic in topics:
            # Find messages related to this topic
            related_messages = _find_messages_for_topic(topic, relevant_messages)
            
            if len(related_messages) >= 3:  # Minimum threshold
                summary = await summarize_topic_messages(topic, related_messages)
                topic_summaries.append({
                    'topic': topic,
                    'summary': summary,
                    'message_count': len(related_messages)
                })
        
        if not topic_summaries:
            await ctx.send("❌ Could not generate meaningful summaries for the identified topics.")
            return
        
        # Get conversation statistics
        stats = get_conversation_stats(relevant_messages)
        
        # Prepare final summary data
        summary_data = {
            'topics': topic_summaries,
            'stats': stats,
            'metadata': {
                'total_messages_analyzed': len(relevant_messages),
                'total_messages_fetched': len(messages),
                'time_filter': time_filter,
                'generated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Cache the summary
        add_summary_to_cache(channel_id, message_hash, summary_data)
        
        # Clean up old summaries for this channel
        cleanup_old_summaries(channel_id, keep_count=5)
        
        # Send the response
        await _send_summary_response(ctx, summary_data, from_cache=False)
        
    except Exception as e:
        print(f"Error in summary command: {e}")
        import traceback
        traceback.print_exc()
        await ctx.send(f"❌ An error occurred while generating the summary: {str(e)}")

def _parse_time_filter(time_str: str):
    """Parse time filter string like '1h', '30m', '2h' into timedelta.
    
    Args:
        time_str: Time string to parse.
        
    Returns:
        timedelta object or None if invalid.
    """
    import re
    from datetime import timedelta
    
    # Match patterns like "1h", "30m", "2h30m"
    pattern = r'^(\d+)([hm])$'
    match = re.match(pattern, time_str.lower())
    
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 'h':
        return timedelta(hours=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    
    return None

def _find_messages_for_topic(topic: dict, messages: list) -> list:
    """Find messages related to a specific topic.
    
    Args:
        topic: Topic dictionary with keywords.
        messages: List of all messages.
        
    Returns:
        List of messages related to the topic.
    """
    if 'related_message_ids' in topic:
        # Use pre-identified message IDs
        related_ids = set(topic['related_message_ids'])
        return [msg for msg in messages if msg['id'] in related_ids]
    
    # Fallback to keyword matching
    keywords = topic.get('keywords', [])
    topic_name_words = topic.get('name', '').lower().split()
    
    all_keywords = keywords + topic_name_words
    all_keywords = [kw.lower() for kw in all_keywords if len(kw) > 2]
    
    if not all_keywords:
        return []
    
    related_messages = []
    for message in messages:
        content_lower = message['content'].lower()
        matches = sum(1 for keyword in all_keywords if keyword in content_lower)
        
        if matches >= 1:  # More lenient matching for summary generation
            related_messages.append(message)
    
    return related_messages

async def _send_summary_response(ctx, summary_data: dict, from_cache: bool = False) -> None:
    """Send formatted summary response to Discord.
    
    Args:
        ctx: Discord context.
        summary_data: Summary data dictionary.
        from_cache: Whether this data came from cache.
    """
    topics = summary_data.get('topics', [])
    stats = summary_data.get('stats', {})
    metadata = summary_data.get('metadata', {})
    
    # Build the response
    cache_indicator = "📄 *(from cache)* " if from_cache else ""
    
    response = f"📊 **Conversation Summary** {cache_indicator}\n\n"
    
    # Add statistics
    total_messages = metadata.get('total_messages_analyzed', stats.get('total_messages', 0))
    unique_users = stats.get('unique_users', 0)
    time_range = stats.get('time_range_hours', 0)
    
    response += f"📈 **Overview:** {total_messages} messages from {unique_users} users"
    if time_range > 0:
        if time_range < 1:
            response += f" (over {int(time_range * 60)} minutes)\n\n"
        else:
            response += f" (over {time_range:.1f} hours)\n\n"
    else:
        response += "\n\n"
    
    # Add topic summaries with emojis
    topic_emojis = ["🤖", "💬", "🎯", "📚", "⚡", "🔧", "💡", "🎮"]
    
    for i, topic_data in enumerate(topics):
        topic = topic_data['topic']
        summary = topic_data['summary']
        message_count = topic_data['message_count']
        
        emoji = topic_emojis[i % len(topic_emojis)]
        
        response += f"{emoji} **{topic['name']}** ({message_count} messages)\n"
        response += f"{summary}\n\n"
    
    # Add most active users if available
    if stats.get('most_active_users'):
        response += "👥 **Most Active:** "
        active_users = stats['most_active_users'][:3]
        user_mentions = [f"{user['name']} ({user['count']})" for user in active_users]
        response += ", ".join(user_mentions) + "\n"
    
    # Split long responses
    if len(response) > 2000:
        # Send in chunks
        parts = _split_response(response, 2000)
        for part in parts:
            await ctx.send(part)
    else:
        await ctx.send(response)

def _split_response(text: str, max_length: int) -> list:
    """Split a long response into smaller chunks.
    
    Args:
        text: Text to split.
        max_length: Maximum length per chunk.
        
    Returns:
        List of text chunks.
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current = ""
    
    for line in text.split('\n'):
        if len(current + line + '\n') > max_length:
            if current:
                parts.append(current.strip())
                current = line + '\n'
            else:
                # Single line too long, force split
                parts.append(line[:max_length-3] + "...")
                current = ""
        else:
            current += line + '\n'
    
    if current:
        parts.append(current.strip())
    
    return parts
