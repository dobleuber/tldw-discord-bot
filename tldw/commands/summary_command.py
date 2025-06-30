"""
Summary command for conversation analysis and topic-based summarization.

Analyzes recent conversation messages and generates AI-powered topic summaries.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .base import BaseCommand
from ..utils.redis_cache import (
    get_summary_from_cache, add_summary_to_cache, cleanup_old_summaries
)
from ..utils.message_utils import (
    fetch_recent_messages, create_message_range_hash,
    filter_messages_by_relevance, get_conversation_stats
)
from ..services.topic_analysis_service import identify_conversation_topics, summarize_topic_messages


class SummaryCommand(BaseCommand):
    """Command to analyze conversation and generate topic-based summaries."""
    
    def get_command_name(self) -> str:
        return "summary"
    
    def get_command_description(self) -> str:
        return "Generate a topic-based summary of recent conversation"
    
    def get_user_rate_limit_minutes(self) -> int:
        return 5  # 5 minutes between uses per user
    
    def get_channel_rate_limit_minutes(self) -> int:
        return 2  # 2 minutes between uses per channel
    
    async def execute(self, ctx, count: int = 100, time_filter: str = None) -> None:
        """
        Handle the summary command to analyze and summarize recent conversation by topics.
        
        Args:
            ctx: The Discord context.
            count: Number of messages to analyze (default 100, max 200).
            time_filter: Time filter string like "1h", "30m", "2h" (optional).
        """
        channel_id = str(ctx.channel.id)
        
        # Validate and limit message count
        if count < 10:
            count = 10
        elif count > 200:
            count = 200
        
        # Parse time filter
        time_delta = None
        if time_filter:
            time_delta = self._parse_time_filter(time_filter)
            if not time_delta:
                await ctx.send("❌ Invalid time filter. Use format like '1h', '30m', '2h' (hours or minutes).")
                return
        
        await ctx.send(f"🔍 Analyzing last {count} messages{f' from the past {time_filter}' if time_filter else ''}...")
        
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
            await self._send_summary_response(ctx, cached_summary, from_cache=True)
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
            related_messages = self._find_messages_for_topic(topic, relevant_messages)
            
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
        await self._send_summary_response(ctx, summary_data, from_cache=False)
    
    def _parse_time_filter(self, time_str: str) -> timedelta:
        """
        Parse time filter string like '1h', '30m', '2h' into timedelta.
        
        Args:
            time_str: Time string to parse.
            
        Returns:
            timedelta object or None if invalid.
        """
        # Match patterns like "1h", "30m"
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
    
    def _find_messages_for_topic(self, topic: dict, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find messages related to a specific topic.
        
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
    
    async def _send_summary_response(self, ctx, summary_data: dict, from_cache: bool = False) -> None:
        """
        Send formatted summary response to Discord.
        
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
            parts = self._split_response(response, 2000)
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)
    
    def _split_response(self, text: str, max_length: int) -> List[str]:
        """
        Split a long response into smaller chunks.
        
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