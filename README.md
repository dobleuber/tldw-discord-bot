# TLDW - Too Long; Didn't Watch

A Discord bot that generates summaries of YouTube videos, web pages, and Twitter threads using Google Gemini AI.

## Features

- **TLDW Command**: Extracts and summarizes YouTube video transcripts
- **TLDR Command**: Summarizes web pages and Twitter threads
- **Adaptive Command Behavior**: Searches for links in previous messages if none is provided
- **Caching System**: Stores previously generated summaries with 24-hour expiration

## Technology Stack

- Python 3.11+
- [discord.py](https://discordpy.readthedocs.io) for Discord integration
- Google Gemini AI for generating summaries
- Microsoft MarkitDown library for content extraction
- In-memory cache with 24-hour expiration

## Project Structure

- `main.py`: Main implementation of the Discord bot
- `.env.example`: Template for environment variables
- `tests.py`: Unit tests for the bot functionality
- `pyproject.toml`: Project configuration and dependencies

## Running the Bot

### Method 1: Local Execution

To run the bot locally, follow these steps:

1. Clone this repository
2. Create a `.env` file based on the `.env.example` file and add your tokens
3. Install dependencies with `pip install -e .`
4. Run the bot with `python main.py`

### Method 2: Docker Execution (recommended)

To run the bot with Docker, follow these steps:

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

## Setup and Installation

1. Clone the repository
2. Set up a virtual environment (Python 3.11+ required)
3. Install dependencies with uv:
   ```bash
   uv pip install -e .
   ```
4. Copy `.env.example` to `.env` and fill in the required environment variables:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `GOOGLE_API_KEY`: Your Google API key for Gemini AI
5. Run the bot:
   ```bash
   python main.py
   ```

## Usage

Once the bot is running and added to your Discord server, you can use the following commands:

- `/tldw [url]`: Generate a summary of a YouTube video
- `/tldr [url]`: Generate a summary of a web page or Twitter thread
- `/info`: Display help information

If you don't provide a URL, the bot will search for the last message with a relevant link.

## Development

This project uses Test-Driven Development (TDD). To run the tests:

```bash
uv run python -m unittest tests.py
```

## Implementation Notes

- Microsoft MarkitDown library is used for extracting content from different sources
- The bot implements a caching system to avoid processing the same content repeatedly
- The bot adapts to user behavior by searching for links in previous messages
