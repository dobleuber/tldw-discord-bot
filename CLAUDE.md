# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TLDW (Too Long; Didn't Watch) is a Discord bot that generates AI-powered summaries of YouTube videos, web pages, and Twitter threads using Google Gemini AI. Built with Python 3.11+ and discord.py.

## Development Commands

```bash
# Install dependencies
uv pip install -e .

# Run locally
uv run start
# or
uv run python main.py

# Run tests
uv run test                    # unittest with verbose output
uv run cov                     # pytest with coverage

# Or run tests directly
uv run python -m unittest tests.py -v
uv run pytest -v

# Docker deployment (recommended)
docker-compose up -d
docker-compose logs -f tldw-bot
docker-compose down
```

## Kubernetes Deployment

```bash
# Build and push image
docker build -t your-registry/tldw-discord-bot:latest .
docker push your-registry/tldw-discord-bot:latest

# Create secrets
kubectl create secret generic tldw-secrets \
  --from-literal=discord-token="YOUR_DISCORD_TOKEN" \
  --from-literal=google-api-key="YOUR_GOOGLE_API_KEY" \
  --from-literal=redis-password="YOUR_REDIS_PASSWORD" \
  --namespace=tldw-bot

# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -k k8s/

# Check deployment
kubectl get all -n tldw-bot
kubectl logs -n tldw-bot deployment/tldw-bot -f

# Scale (bot should stay at 1 replica)
kubectl scale deployment tldw-bot --replicas=1 -n tldw-bot

# Update image
kubectl set image deployment/tldw-bot tldw-bot=your-registry/tldw-discord-bot:new-tag -n tldw-bot

# Cleanup
kubectl delete namespace tldw-bot
```

## Architecture

### Core Structure
- `main.py` - Entry point
- `tldw/bot.py` - Discord bot setup and command registration (both slash and legacy)
- `tldw/commands.py` - Command handlers and business logic
- `tldw/services/` - External service integrations (Gemini AI, content extraction)
- `tldw/utils/` - Utilities (caching, URL validation)

### Multi-Tier Caching Strategy
The bot uses a sophisticated fallback caching system:
1. **Primary**: Redis cache (production)
2. **Fallback 1**: Persistent file-based cache
3. **Fallback 2**: In-memory cache
4. **Fallback 3**: Dummy cache (no-op)

### Command Pattern
Both slash commands and legacy text commands are supported through a wrapper pattern in `bot.py`. The `ContextWrapper` class bridges Discord interactions to the command handlers.

## Key Technologies

- **Discord**: discord.py with both legacy commands and modern slash commands
- **AI**: Google Gemini AI (gemini-2.0-flash model) via `google-generativeai`
- **Content Extraction**: Microsoft MarkItDown library
- **Caching**: Redis with multiple fallback mechanisms
- **Testing**: pytest with async support

## Environment Variables

Required in `.env` file:
- `DISCORD_TOKEN` - Discord bot authentication
- `GOOGLE_API_KEY` - Google Gemini AI access
- `REDIS_HOST` - Redis server (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `CACHE_EXPIRATION_HOURS` - Cache TTL (default: 24)
- `MESSAGE_HISTORY_LIMIT` - Number of previous messages to search for URLs (default: 5)

## Current Implementation Status

**Fully Implemented:**
- YouTube video transcript extraction and summarization (`/tldw`)
- Web page and Twitter thread summarization (`/tldr`)
- Conversation topic analysis and summarization (`/summary`)
- Redis caching with comprehensive fallbacks
- Docker deployment with Redis container
- Both slash and legacy command support
- Automatic URL detection in previous messages (searches last 5 messages by default)
- Rate limiting for summary command (per user and per channel)
- Intelligent topic identification using Gemini AI with fallbacks

## Development Notes

- The bot automatically syncs slash commands with Discord on startup
- All caching implementations follow a consistent interface in `utils/cache_utils.py`
- Content type detection is handled by `utils/url_utils.py` with regex patterns
- Error handling is comprehensive with graceful degradation
- Testing covers both unit tests and integration tests with real services