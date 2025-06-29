# TLDW - Too Long; Didn't Watch

A Discord bot that generates summaries of YouTube videos, web pages, and Twitter threads using Google Gemini AI.

## Features

- **TLDW Command**: Extracts and summarizes YouTube video transcripts
- **TLDR Command**: Summarizes web pages and Twitter threads
- **Summary Command**: Analyzes recent conversation and generates topic-based summaries
- **Adaptive Command Behavior**: Searches for links in previous messages if none is provided
- **Multi-tier Caching System**: Redis cache with fallbacks, optimized TTL per command type
- **Intelligent Rate Limiting**: Per-user and per-channel limits to prevent abuse

## Technology Stack

- Python 3.11+
- [discord.py](https://discordpy.readthedocs.io) for Discord integration
- Google Gemini AI for generating summaries
- Microsoft MarkitDown library for content extraction
- Redis caching with multi-tier fallback system

## Project Structure

- `main.py`: Main implementation of the Discord bot
- `.env.example`: Template for environment variables
- `tests.py`: Unit tests for the bot functionality
- `pyproject.toml`: Project configuration and dependencies

## Setup and Installation

### Method 1: Local Execution

1. Clone this repository
2. Create and activate a virtual environment (Python 3.11+ required):
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies with uv:
   ```bash
   uv pip install -e .
   ```
4. Copy `.env.example` to `.env` and fill in the required environment variables:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `GOOGLE_API_KEY`: Your Google API key for Gemini AI
   - `MESSAGE_HISTORY_LIMIT`: Number of messages to search for URLs (optional, default: 5)
5. Run the bot:
   ```bash
   uv run start
   # or
   python main.py
   ```

### Method 2: Docker Execution (recommended)

1. Clone this repository
2. Create a `.env` file based on the `.env.example` file and add your tokens
3. Build and run the containers with Docker Compose:

```bash
docker-compose up -d
```

This will start the bot and a Redis server for caching in separate containers.

To view the bot logs:

```bash
docker-compose logs -f tldw-bot
```

To stop the containers:

```bash
docker-compose down
```

## Usage

Once the bot is running and added to your Discord server, you can use the following commands:

### Core Commands

- `/tldw [url]` - Generate a summary of a YouTube video
- `/tldr [url]` - Generate a summary of a web page or Twitter thread  
- `/summary [count] [time_filter]` - Analyze recent conversation and generate topic-based summaries
- `/info` - Display help information

### Summary Command Examples

- `/summary` - Analyze last 100 messages by topic
- `/summary 50` - Analyze last 50 messages by topic
- `/summary 100 2h` - Analyze last 100 messages from the past 2 hours
- `/summary 150 30m` - Analyze last 150 messages from the past 30 minutes

### Notes

- If you don't provide a URL for `/tldw` or `/tldr`, the bot will search for the last message with a relevant link in the channel
- The `/summary` command uses AI to identify conversation topics and provides structured summaries
- Rate limits apply: 1 summary per user every 5 minutes, 1 per channel every 2 minutes

## Development

This project uses Test-Driven Development (TDD). To run the tests:

```bash
# Using project scripts (recommended)
uv run test                    # unittest with verbose output
uv run cov                     # pytest with coverage

# Or run directly with uv
uv run python -m unittest tests.py -v
uv run pytest -v

# Start the bot for development
uv run start                   # or uv run python main.py
```

## Implementation Notes

- Microsoft MarkitDown library is used for extracting content from different sources
- The bot implements a caching system to avoid processing the same content repeatedly
- The bot adapts to user behavior by searching for links in previous messages
