import unittest
import pytest

class TestHelpCommand(unittest.TestCase):
    """Tests for the help command functionality."""

    def test_help_command_returns_correct_information(self):
        """Test that the help command returns the correct information."""
        from tldw.commands.help_command import HelpCommand
        
        help_cmd = HelpCommand()
        
        # Verify command properties
        self.assertEqual(help_cmd.name, "info")
        self.assertIn("Get information about the bot", help_cmd.description)


class TestUrlValidation(unittest.TestCase):
    """Tests for URL validation."""
    
    def test_valid_urls(self):
        """Test that valid URLs are correctly identified."""
        from tldw.utils.url_utils import is_valid_url
        
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://twitter.com/username/status/1234567890",
            "http://example.org/page",
            "www.example.com"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(is_valid_url(url), f"Valid URL not recognized: {url}")
    
    def test_invalid_urls(self):
        """Test that invalid URLs are correctly identified."""
        from tldw.utils.url_utils import is_valid_url
        
        invalid_urls = [
            "",
            "not a url",
            "http://",
            "www."
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(is_valid_url(url), f"Invalid URL recognized as valid: {url}")


class TestContentTypeDetection(unittest.TestCase):
    """Tests for content type detection based on URLs."""

    def test_youtube_url_detection(self):
        """Test that YouTube URLs are correctly detected."""
        from tldw.utils.url_utils import determine_content_type, ContentType
        
        youtube_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in youtube_urls:
            with self.subTest(url=url):
                self.assertEqual(determine_content_type(url), ContentType.YOUTUBE)
    
    def test_twitter_url_detection(self):
        """Test that Twitter URLs are correctly detected."""
        from tldw.utils.url_utils import determine_content_type, ContentType
        
        twitter_urls = [
            "https://twitter.com/username/status/1234567890",
            "https://x.com/username/status/1234567890",
            "http://twitter.com/username/status/1234567890",
            "www.twitter.com/username/status/1234567890"
        ]
        
        for url in twitter_urls:
            with self.subTest(url=url):
                self.assertEqual(determine_content_type(url), ContentType.TWITTER)
    
    def test_web_url_detection(self):
        """Test that web URLs are correctly detected."""
        from tldw.utils.url_utils import determine_content_type, ContentType
        
        web_urls = [
            "https://example.com",
            "http://example.org/page",
            "www.example.net/article/123",
            "example.io/blog/post"
        ]
        
        for url in web_urls:
            with self.subTest(url=url):
                self.assertEqual(determine_content_type(url), ContentType.WEB)


@pytest.mark.asyncio
class TestTLDWCommand:
    """Tests for the TLDW command functionality."""

    async def test_tldw_command_handler(self):
        """Test that the TLDW command handler processes YouTube URLs correctly."""
        from tldw.commands import handle_tldw_command
        from unittest.mock import AsyncMock, patch, MagicMock
        
        # Create a mock context object
        ctx = AsyncMock()
        
        # Test with a valid YouTube URL
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Mock the dependencies to avoid actual API calls
        with patch('tldw.commands.extract_youtube_transcript', new_callable=AsyncMock) as mock_extract, \
             patch('tldw.commands.generate_summary_with_gemini', new_callable=AsyncMock) as mock_generate, \
             patch('tldw.commands.get_from_cache', return_value=None) as mock_get_cache, \
             patch('tldw.commands.add_to_cache') as mock_add_cache:
            
            # Configure the mocks
            mock_extract.return_value = "Sample transcript"
            mock_generate.return_value = "Sample summary"
            
            # Call the function
            await handle_tldw_command(ctx, test_url)
            
            # Verify that extract_youtube_transcript was called
            mock_extract.assert_called_once_with(test_url)
            
            # Verify that generate_summary_with_gemini was called
            mock_generate.assert_called_once_with("Sample transcript")
            
            # Verify that add_to_cache was called
            mock_add_cache.assert_called_once_with(test_url, "Sample summary")
            
            # Verify that the context's send method was called EXACTLY ONCE with the final summary
            ctx.send.assert_called_once()
            call_args = ctx.send.call_args[0][0]
            assert "Summary" in call_args
            assert "Sample summary" in call_args
        
    async def test_extract_youtube_transcript(self):
        """Test that the YouTube transcript extraction works correctly."""
        from tldw.services.content_service import extract_youtube_transcript
        from unittest.mock import patch
        
        # Test with a valid YouTube URL
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Mock the MarkItDown functionality for testing
        with patch('tldw.services.content_service.MarkItDown') as mock_markitdown:
            # Configure the mock to return a sample transcript
            mock_instance = mock_markitdown.return_value
            mock_result = unittest.mock.MagicMock()
            mock_result.text_content = "Sample YouTube transcript content"
            mock_instance.convert.return_value = mock_result
            
            # Call the function
            transcript = await extract_youtube_transcript(test_url)
            
            # Verify the transcript was extracted correctly
            assert transcript == "Sample YouTube transcript content"
            
            # Verify MarkItDown was called with the correct URL
            mock_instance.convert.assert_called_once_with(test_url)
            
    async def test_generate_summary_with_gemini(self):
        """Test that the summary generation with Gemini AI works correctly."""
        from tldw.services.gemini_service import generate_summary_with_gemini
        from unittest.mock import patch, AsyncMock, MagicMock
        
        # Sample transcript to summarize
        transcript = "This is a sample transcript of a YouTube video that needs to be summarized."
        
        # Mock the list_models function to return our test model
        mock_model_obj = MagicMock()
        mock_model_obj.name = "models/gemini-2.0-flash"
        mock_model_obj.supported_generation_methods = ["generateContent"]
        
        # Mock the Gemini AI functionality for testing
        with patch('tldw.services.gemini_service.genai.list_models', return_value=[mock_model_obj]), \
             patch('tldw.services.gemini_service.genai.GenerativeModel') as mock_genai:
            
            # Configure the mock to return a sample summary
            mock_model = mock_genai.return_value
            mock_response = MagicMock()
            mock_response.text = "This is a sample summary generated by Gemini AI."
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            
            # Call the function
            summary = await generate_summary_with_gemini(transcript)
            
            # Verify the summary was generated correctly
            assert summary == "This is a sample summary generated by Gemini AI."
            
            # Verify Gemini AI was called with the correct prompt
            mock_model.generate_content_async.assert_called_once()
            
            # Verify the model was created with the correct model name
            mock_genai.assert_called_once_with("models/gemini-2.0-flash")


class TestMessageUtils(unittest.TestCase):
    """Tests for message utilities."""
    
    def test_extract_urls_from_text(self):
        """Test URL extraction from text."""
        from tldw.utils.message_utils import extract_urls_from_text
        
        # Test with various URL formats
        text1 = "Check out this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        urls1 = extract_urls_from_text(text1)
        self.assertEqual(len(urls1), 1)
        self.assertIn("youtube.com", urls1[0])
        
        # Test with multiple URLs
        text2 = "Here are some links: https://example.com and www.twitter.com/test"
        urls2 = extract_urls_from_text(text2)
        self.assertEqual(len(urls2), 2)
        
        # Test with no URLs
        text3 = "This is just regular text with no links"
        urls3 = extract_urls_from_text(text3)
        self.assertEqual(len(urls3), 0)
        
    def test_message_history_limit_configuration(self):
        """Test that message history limit is configurable."""
        from tldw.utils.message_utils import MESSAGE_HISTORY_LIMIT
        
        # Should be an integer (default 5 or from environment)
        self.assertIsInstance(MESSAGE_HISTORY_LIMIT, int)
        self.assertGreater(MESSAGE_HISTORY_LIMIT, 0)


class TestSummaryCommand(unittest.TestCase):
    """Tests for summary command functionality."""
    
    def test_parse_time_filter(self):
        """Test time filter parsing function."""
        from tldw.commands.summary_command import SummaryCommand
        from datetime import timedelta
        
        summary_cmd = SummaryCommand()
        
        # Test valid formats
        self.assertEqual(summary_cmd._parse_time_filter("1h"), timedelta(hours=1))
        self.assertEqual(summary_cmd._parse_time_filter("30m"), timedelta(minutes=30))
        self.assertEqual(summary_cmd._parse_time_filter("2h"), timedelta(hours=2))
        
        # Test invalid formats
        self.assertIsNone(summary_cmd._parse_time_filter("invalid"))
        self.assertIsNone(summary_cmd._parse_time_filter("1x"))
        self.assertIsNone(summary_cmd._parse_time_filter(""))
        
    def test_split_response(self):
        """Test response splitting function."""
        from tldw.commands.summary_command import SummaryCommand
        
        summary_cmd = SummaryCommand()
        
        # Test short response (no splitting needed)
        short_text = "This is a short response."
        result = summary_cmd._split_response(short_text, 100)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], short_text)
        
        # Test long response that needs splitting
        long_text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        result = summary_cmd._split_response(long_text, 20)
        self.assertGreater(len(result), 1)
        
    def test_message_range_hash(self):
        """Test message range hash creation."""
        from tldw.utils.message_utils import create_message_range_hash
        from datetime import datetime
        
        # Test with sample messages
        messages = [
            {
                'id': 123456789,
                'content': 'Test message 1',
                'channel_id': 987654321,
                'created_at': datetime.now()
            },
            {
                'id': 123456790,
                'content': 'Test message 2', 
                'channel_id': 987654321,
                'created_at': datetime.now()
            }
        ]
        
        hash1 = create_message_range_hash(messages)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 16)  # Should be 16 characters long
        
        # Same messages should produce same hash
        hash2 = create_message_range_hash(messages)
        self.assertEqual(hash1, hash2)
        
        # Different messages should produce different hash
        different_messages = [
            {
                'id': 999999999,
                'content': 'Different message',
                'channel_id': 987654321,
                'created_at': datetime.now()
            }
        ]
        
        hash3 = create_message_range_hash(different_messages)
        self.assertNotEqual(hash1, hash3)
        
    def test_message_relevance_filtering(self):
        """Test message relevance filtering."""
        from tldw.utils.message_utils import filter_messages_by_relevance
        from datetime import datetime
        
        messages = [
            {
                'content': 'This is a substantial message with good content for analysis',
                'author': {'name': 'User1'},
                'created_at': datetime.now()
            },
            {
                'content': 'Short',  # Too short
                'author': {'name': 'User2'},
                'created_at': datetime.now()
            },
            {
                'content': '!!!!!!!!!!',  # Mostly punctuation
                'author': {'name': 'User3'},
                'created_at': datetime.now()
            },
            {
                'content': 'Another good message that should be included in analysis',
                'author': {'name': 'User4'},
                'created_at': datetime.now()
            }
        ]
        
        filtered = filter_messages_by_relevance(messages, min_length=15)
        
        # Should keep only the substantial messages
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all('good' in msg['content'] or 'substantial' in msg['content'] 
                          for msg in filtered))


class TestTopicAnalysis(unittest.TestCase):
    """Tests for topic analysis functionality."""
    
    def test_fallback_topic_identification(self):
        """Test fallback topic identification using keyword frequency."""
        from tldw.services.topic_analysis_service import _fallback_topic_identification
        from datetime import datetime
        
        messages = [
            {'content': 'Let\'s discuss Python programming and coding best practices', 'author': {'name': 'User1'}, 'created_at': datetime.now()},
            {'content': 'Python is great for data science and machine learning', 'author': {'name': 'User2'}, 'created_at': datetime.now()},
            {'content': 'I love Python programming, it\'s so versatile', 'author': {'name': 'User3'}, 'created_at': datetime.now()},
            {'content': 'Docker containers are useful for deployment', 'author': {'name': 'User4'}, 'created_at': datetime.now()},
            {'content': 'Docker makes development environments consistent', 'author': {'name': 'User5'}, 'created_at': datetime.now()},
            {'content': 'Docker is essential for modern DevOps', 'author': {'name': 'User6'}, 'created_at': datetime.now()},
        ]
        
        topics = _fallback_topic_identification(messages, max_topics=3)
        
        # Should identify topics based on keyword frequency
        self.assertGreater(len(topics), 0)
        self.assertLessEqual(len(topics), 3)
        
        # Should have required fields
        for topic in topics:
            self.assertIn('name', topic)
            self.assertIn('description', topic)
            self.assertIn('message_count', topic)
            self.assertIn('keywords', topic)
        
    def test_prepare_messages_for_analysis(self):
        """Test message preparation for AI analysis."""
        from tldw.services.topic_analysis_service import _prepare_messages_for_analysis
        from datetime import datetime
        
        messages = [
            {
                'content': 'Hello <@!123456789> check out <#987654321> channel',
                'author': {'name': 'TestUser'},
                'created_at': datetime(2024, 1, 1, 12, 0)
            },
            {
                'content': 'Custom emoji test <:custom_emoji:123456>',
                'author': {'name': 'AnotherUser'},
                'created_at': datetime(2024, 1, 1, 12, 5)
            }
        ]
        
        formatted = _prepare_messages_for_analysis(messages)
        
        # Should format properly and clean mentions/emojis
        self.assertIn('[12:00] TestUser:', formatted)
        self.assertIn('@user', formatted)  # Mentions should be replaced
        self.assertIn('#channel', formatted)  # Channel refs should be replaced
        self.assertIn(':emoji:', formatted)  # Custom emojis should be replaced
        # Verify original Discord formatting was replaced
        self.assertNotIn('<@!123456789>', formatted)
        self.assertNotIn('<#987654321>', formatted) 
        self.assertNotIn('<:custom_emoji:123456>', formatted)

if __name__ == "__main__":
    unittest.main()
