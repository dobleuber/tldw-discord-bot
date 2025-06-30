"""
Topic analysis service for identifying and summarizing conversation themes using Gemini AI.
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai

def setup_gemini():
    """Configure the Gemini AI API.
    
    Raises:
        ValueError: If the GOOGLE_API_KEY environment variable is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in the .env file")
    genai.configure(api_key=api_key)

async def identify_conversation_topics(messages: List[Dict[str, Any]], max_topics: int = 5) -> List[Dict[str, Any]]:
    """Identify main topics from a list of messages using Gemini AI.
    
    Args:
        messages: List of message dictionaries.
        max_topics: Maximum number of topics to identify.
        
    Returns:
        List of topic dictionaries with metadata.
    """
    if not messages:
        return []
    
    # Prepare messages for analysis
    conversation_text = _prepare_messages_for_analysis(messages)
    
    if len(conversation_text.strip()) < 50:
        return []
    
    try:
        setup_gemini()
        model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-preview-04-17")
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""Analyze the following Discord conversation and identify the main topics discussed.

IMPORTANT INSTRUCTIONS:
1. Identify between 1-{max_topics} main topics
2. Each topic must have at least 3 related messages
3. Provide topic names that are concise (2-4 words)
4. Return ONLY a valid JSON array, no other text
5. Include message counts and key participants for each topic

FORMAT: Return only this JSON structure:
[
    {{
        "name": "Topic Name",
        "description": "Brief description of what was discussed",
        "message_count": number_of_related_messages,
        "key_users": ["user1", "user2"],
        "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
]

CONVERSATION:
{conversation_text}

RESPOND WITH JSON ONLY:"""

        response = await model.generate_content_async(prompt)
        
        # Parse the JSON response
        topics = _parse_topics_response(response.text)
        
        # Validate and enhance topics with message references
        validated_topics = _validate_and_enhance_topics(topics, messages)
        
        return validated_topics
        
    except Exception as e:
        print(f"Error identifying topics: {e}")
        # Fallback to keyword-based analysis
        return _fallback_topic_identification(messages, max_topics)

async def summarize_topic_messages(topic: Dict[str, Any], related_messages: List[Dict[str, Any]]) -> str:
    """Generate a summary for a specific topic based on related messages.
    
    Args:
        topic: Topic dictionary with metadata.
        related_messages: Messages related to this topic.
        
    Returns:
        Summary text for the topic.
    """
    if not related_messages:
        return "No messages found for this topic."
    
    try:
        setup_gemini()
        model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-preview-04-17")
        model = genai.GenerativeModel(model_name)
        
        # Prepare messages for summarization
        messages_text = _prepare_messages_for_analysis(related_messages)
        
        prompt = f"""Summarize the following messages about "{topic['name']}" from a Discord conversation.

INSTRUCTIONS:
1. Create a concise summary (2-4 sentences)
2. Focus on key points, decisions, or conclusions
3. Mention specific details or examples if relevant
4. Use a conversational tone
5. Do not repeat the topic name unnecessarily

TOPIC: {topic['name']}
DESCRIPTION: {topic['description']}

MESSAGES:
{messages_text}

SUMMARY:"""

        response = await model.generate_content_async(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Error summarizing topic {topic['name']}: {e}")
        # Fallback to simple summary
        return _create_fallback_summary(topic, related_messages)

def _prepare_messages_for_analysis(messages: List[Dict[str, Any]]) -> str:
    """Prepare messages for AI analysis by formatting them clearly.
    
    Args:
        messages: List of message dictionaries.
        
    Returns:
        Formatted conversation text.
    """
    formatted_messages = []
    
    for msg in messages:
        timestamp = msg['created_at'].strftime("%H:%M") if isinstance(msg['created_at'], datetime) else "00:00"
        author = msg['author']['name']
        content = msg['content']
        
        # Clean up the content
        content = re.sub(r'<@!?\d+>', '@user', content)  # Replace mentions
        content = re.sub(r'<#\d+>', '#channel', content)  # Replace channel refs
        content = re.sub(r'<:.+?:\d+>', ':emoji:', content)  # Replace custom emojis
        
        formatted_messages.append(f"[{timestamp}] {author}: {content}")
    
    return '\n'.join(formatted_messages)

def _parse_topics_response(response_text: str) -> List[Dict[str, Any]]:
    """Parse the Gemini AI response to extract topics.
    
    Args:
        response_text: Raw response from Gemini AI.
        
    Returns:
        List of parsed topic dictionaries.
    """
    try:
        # Clean up the response to extract JSON
        cleaned_response = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_response.startswith('```'):
            cleaned_response = re.sub(r'^```json?\n|```$', '', cleaned_response, flags=re.MULTILINE)
        
        # Try to find JSON array in the response
        json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
        if json_match:
            cleaned_response = json_match.group(0)
        
        topics = json.loads(cleaned_response)
        
        # Validate the structure
        if not isinstance(topics, list):
            return []
        
        validated_topics = []
        for topic in topics:
            if isinstance(topic, dict) and 'name' in topic:
                # Ensure required fields exist
                validated_topic = {
                    'name': topic.get('name', 'Unknown Topic'),
                    'description': topic.get('description', ''),
                    'message_count': topic.get('message_count', 0),
                    'key_users': topic.get('key_users', []),
                    'keywords': topic.get('keywords', [])
                }
                validated_topics.append(validated_topic)
        
        return validated_topics
        
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing topics response: {e}")
        print(f"Raw response: {response_text[:200]}...")
        return []

def _validate_and_enhance_topics(topics: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate topics and enhance them with message references.
    
    Args:
        topics: List of topic dictionaries from AI.
        messages: Original messages for reference.
        
    Returns:
        Enhanced and validated topics.
    """
    validated_topics = []
    
    for topic in topics:
        # Ensure minimum message count
        if topic.get('message_count', 0) < 3:
            continue
        
        # Enhance with actual message analysis
        related_messages = _find_related_messages(topic, messages)
        if len(related_messages) < 3:
            continue
        
        # Update with actual counts
        topic['message_count'] = len(related_messages)
        topic['related_message_ids'] = [msg['id'] for msg in related_messages]
        
        # Get actual participants
        participants = list(set([msg['author']['name'] for msg in related_messages]))
        topic['key_users'] = participants[:3]  # Limit to top 3
        
        validated_topics.append(topic)
    
    return validated_topics

def _find_related_messages(topic: Dict[str, Any], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find messages related to a specific topic using keyword matching.
    
    Args:
        topic: Topic dictionary with keywords.
        messages: List of all messages.
        
    Returns:
        List of messages related to the topic.
    """
    keywords = topic.get('keywords', [])
    topic_name_words = topic.get('name', '').lower().split()
    
    # Combine keywords with topic name words
    all_keywords = keywords + topic_name_words
    all_keywords = [kw.lower() for kw in all_keywords if len(kw) > 2]
    
    if not all_keywords:
        return []
    
    related_messages = []
    
    for message in messages:
        content_lower = message['content'].lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in all_keywords if keyword in content_lower)
        
        # Include message if it has multiple keyword matches or strong single match
        if matches >= 2 or (matches == 1 and len(all_keywords) <= 2):
            related_messages.append(message)
    
    return related_messages

def _fallback_topic_identification(messages: List[Dict[str, Any]], max_topics: int) -> List[Dict[str, Any]]:
    """Fallback topic identification using keyword frequency analysis.
    
    Args:
        messages: List of message dictionaries.
        max_topics: Maximum number of topics to return.
        
    Returns:
        List of topics identified through keyword analysis.
    """
    # Simple keyword frequency analysis
    word_freq = {}
    
    for message in messages:
        words = re.findall(r'\b\w{4,}\b', message['content'].lower())
        for word in words:
            if word not in ['that', 'this', 'with', 'have', 'they', 'were', 'been', 'have']:
                word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top keywords
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_topics * 2]
    
    topics = []
    for i, (keyword, count) in enumerate(top_keywords[:max_topics]):
        if count >= 3:  # Minimum frequency
            topic = {
                'name': keyword.title(),
                'description': f'Discussion about {keyword}',
                'message_count': count,
                'key_users': [],
                'keywords': [keyword]
            }
            topics.append(topic)
    
    return topics

def _create_fallback_summary(topic: Dict[str, Any], related_messages: List[Dict[str, Any]]) -> str:
    """Create a fallback summary when AI summarization fails.
    
    Args:
        topic: Topic dictionary.
        related_messages: Messages related to the topic.
        
    Returns:
        Basic summary text.
    """
    if not related_messages:
        return "No detailed discussion found."
    
    participants = list(set([msg['author']['name'] for msg in related_messages]))
    message_count = len(related_messages)
    
    summary = f"This topic was discussed by {', '.join(participants)} "
    summary += f"across {message_count} messages. "
    
    # Add a snippet from the longest message
    longest_message = max(related_messages, key=lambda m: len(m['content']))
    if len(longest_message['content']) > 50:
        snippet = longest_message['content'][:100] + "..." if len(longest_message['content']) > 100 else longest_message['content']
        summary += f"Key point: \"{snippet}\""
    
    return summary