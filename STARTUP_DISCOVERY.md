# Automatic Startup Discovery

The AI Investment Scout DAO now includes automatic startup discovery functionality that can search for startups from various sources and automatically process them through the agent pipeline.

## Features

- **Automatic Discovery**: Periodically searches for new startups from configured sources
- **Multiple Sources**: Supports demo data, Product Hunt, and Crunchbase (with API keys)
- **Auto-Processing**: Automatically generates investment memos for discovered startups
- **Manual Trigger**: API endpoint to manually trigger discovery
- **Configurable**: Control search frequency, sources, and behavior via environment variables

## Configuration

Add these variables to your `.env` file:

```bash
# IMPORTANT: Set to false to use REAL startup data
DEMO_MODE=false

# Enable automatic startup discovery
AUTO_SEARCH_STARTUPS=true

# How often to search (in hours, default: 24)
SEARCH_INTERVAL_HOURS=24

# Sources to search (comma-separated)
# Options: demo, producthunt, crunchbase, ycombinator
# Use producthunt and crunchbase for REAL data (requires DEMO_MODE=false)
STARTUP_SEARCH_SOURCES=producthunt,crunchbase

# Optional: Product Hunt API token (for better rate limits)
# Get from: https://api.producthunt.com/v2/oauth/applications
PRODUCT_HUNT_API_TOKEN=your-product-hunt-token-here

# Optional: Crunchbase API key (REQUIRED for Crunchbase source)
# Get from: https://data.crunchbase.com/
CRUNCHBASE_API_KEY=your-crunchbase-api-key-here
```

### Getting Real Startup Data

To search for **REAL startups** (not demo data):

1. **Set DEMO_MODE=false** in your `.env` file
2. **Choose real sources**: Use `producthunt` and/or `crunchbase` in `STARTUP_SEARCH_SOURCES`
3. **Get API keys** (optional but recommended):
   - Product Hunt: Get token from https://api.producthunt.com/v2/oauth/applications
   - Crunchbase: Get API key from https://data.crunchbase.com/
4. **Restart backend** after changing `.env`

## How It Works

### Automatic Mode

When `AUTO_SEARCH_STARTUPS=true`:

1. **On Backend Startup**: A background task starts automatically
2. **Periodic Search**: Every `SEARCH_INTERVAL_HOURS` hours, the system:
   - Searches configured sources for new startups
   - Processes each discovered startup through the agent
   - Generates investment memos automatically
   - Submits proposals to the DAO

3. **Logging**: All discovery and processing activities are logged

### Manual Mode

You can manually trigger discovery via the API:

```bash
# Discover startups and auto-process them
curl -X POST http://localhost:8000/discover-startups \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["demo"],
    "limit_per_source": 5,
    "auto_process": true
  }'

# Just discover (don't process)
curl -X POST http://localhost:8000/discover-startups \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["demo"],
    "limit_per_source": 5,
    "auto_process": false
  }'
```

### Check Status

```bash
# Check discovery status
curl http://localhost:8000/discover-startups/status

# Response:
{
  "auto_search_enabled": true,
  "search_interval_hours": 24,
  "background_task_running": true
}
```

## Startup Sources

### Demo Source (`demo`)
- **No API key required**
- Generates realistic sample startup data
- Perfect for testing and development
- Always available

### Product Hunt (`producthunt`)
- **Currently simulated** (real API integration coming soon)
- In demo mode, uses simulated Product Hunt data
- In production, will integrate with Product Hunt API

### Crunchbase (`crunchbase`)
- **Requires API key**: `CRUNCHBASE_API_KEY`
- Real startup data from Crunchbase
- Get API key from: https://data.crunchbase.com/
- Falls back to simulation if API key not provided

## Example Workflow

1. **Set up environment**:
   ```bash
   AUTO_SEARCH_STARTUPS=true
   SEARCH_INTERVAL_HOURS=24
   STARTUP_SEARCH_SOURCES=demo
   ```

2. **Start backend**:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

3. **Watch logs**:
   ```
   INFO: Starting automatic startup discovery background task...
   INFO: Running scheduled startup discovery...
   INFO: Discovered 5 unique startups from 1 sources
   INFO: Processing startup: AIFlow
   INFO: Successfully processed startup: AIFlow
   ...
   INFO: Discovery cycle complete: 5 discovered, 5 processed
   ```

4. **Check frontend**: New proposals should appear automatically!

## API Endpoints

### `POST /discover-startups`
Manually trigger startup discovery.

**Request Body**:
```json
{
  "sources": ["demo", "producthunt"],
  "limit_per_source": 5,
  "auto_process": true
}
```

**Response**:
```json
{
  "status": "started",
  "message": "Startup discovery and processing started in background",
  "sources": ["demo", "producthunt"],
  "limit_per_source": 5
}
```

### `GET /discover-startups/status`
Get status of automatic discovery.

**Response**:
```json
{
  "auto_search_enabled": true,
  "search_interval_hours": 24,
  "background_task_running": true
}
```

## Troubleshooting

### Discovery Not Running

1. **Check environment variable**:
   ```bash
   echo $AUTO_SEARCH_STARTUPS
   # Should be "true"
   ```

2. **Check backend logs**:
   - Look for "Starting automatic startup discovery background task..."
   - If not present, `AUTO_SEARCH_STARTUPS` might be false

3. **Restart backend** after changing `.env`:
   ```bash
   # Stop backend (Ctrl+C)
   # Restart:
   uvicorn backend.app.main:app --reload
   ```

### No Startups Found

1. **Check sources**: Verify `STARTUP_SEARCH_SOURCES` includes valid sources
2. **Check logs**: Look for error messages about API failures
3. **Try demo source**: Set `STARTUP_SEARCH_SOURCES=demo` for guaranteed results

### Processing Failures

1. **Check agent path**: Ensure `spoon_agent/main.py` exists
2. **Check dependencies**: Agent needs OpenAI API key if `DEMO_MODE=false`
3. **Check logs**: Look for specific error messages in processing

## Production Considerations

- **API Costs**: Each startup processed costs OpenAI API credits
- **Rate Limits**: Be mindful of API rate limits for external sources
- **Storage**: Each processed startup creates a proposal in the database
- **Performance**: Processing multiple startups can take time

## Future Enhancements

- Real Product Hunt API integration
- More startup sources (AngelList, Y Combinator, etc.)
- Filtering criteria (sector, stage, funding amount)
- Deduplication against existing proposals
- Webhook notifications for new discoveries

