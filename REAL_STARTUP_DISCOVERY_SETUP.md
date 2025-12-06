# Real Startup Discovery Setup Guide

This guide will help you configure the app to search for **REAL startups** from actual APIs instead of demo data.

## Quick Start

### Step 1: Enable Real Data Mode

In your `.env` file, set:

```bash
DEMO_MODE=false
```

**This is critical!** Without this, the app will use simulated data even if you have API keys.

### Step 2: Choose Your Data Sources

Set which sources to use:

```bash
STARTUP_SEARCH_SOURCES=producthunt,crunchbase
```

Available sources:
- `producthunt` - Real Product Hunt data (works without API key, better with token)
- `crunchbase` - Real Crunchbase data (requires API key)
- `ycombinator` - Placeholder (uses demo data)
- `demo` - Demo data (always available)

### Step 3: Get API Keys (Optional but Recommended)

#### Product Hunt API Token (Optional)

1. Go to https://api.producthunt.com/v2/oauth/applications
2. Create an application
3. Get your access token
4. Add to `.env`:
   ```bash
   PRODUCT_HUNT_API_TOKEN=your-token-here
   ```

**Note**: Product Hunt API works without a token but has stricter rate limits.

#### Crunchbase API Key (Required for Crunchbase source)

1. Go to https://data.crunchbase.com/
2. Sign up for an account
3. Get your API key from the dashboard
4. Add to `.env`:
   ```bash
   CRUNCHBASE_API_KEY=your-api-key-here
   ```

### Step 4: Enable Automatic Discovery

```bash
AUTO_SEARCH_STARTUPS=true
SEARCH_INTERVAL_HOURS=24  # Search every 24 hours
```

### Step 5: Restart Backend

After updating `.env`, restart your backend:

```bash
# Stop current backend (Ctrl+C)
uvicorn backend.app.main:app --reload
```

## Example `.env` Configuration

```bash
# ===========================================
# Enable Real Data (NOT DEMO MODE)
# ===========================================
DEMO_MODE=false

# ===========================================
# Startup Discovery Configuration
# ===========================================
AUTO_SEARCH_STARTUPS=true
SEARCH_INTERVAL_HOURS=24
STARTUP_SEARCH_SOURCES=producthunt,crunchbase

# ===========================================
# API Keys for Real Data
# ===========================================
PRODUCT_HUNT_API_TOKEN=ph_token_xxxxxxxxxxxxx
CRUNCHBASE_API_KEY=your-crunchbase-api-key-here

# ===========================================
# Other Required Settings
# ===========================================
OPENAI_API_KEY=sk-your-openai-key  # Required for processing startups
BACKEND_URL=http://localhost:8000
```

## Testing Real Startup Discovery

### Manual Test

```bash
curl -X POST http://localhost:8000/discover-startups \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["producthunt"],
    "limit_per_source": 5,
    "auto_process": false
  }'
```

This will discover startups without processing them, so you can verify the data is real.

### Check Logs

Look for these log messages:

```
INFO: Successfully fetched 5 startups from Product Hunt
INFO: Successfully fetched 5 startups from Crunchbase
```

If you see "Simulating" messages, check that `DEMO_MODE=false`.

## What Data You'll Get

### From Product Hunt:
- Real product names and descriptions
- Actual vote counts and engagement metrics
- Real categories/topics
- Website URLs
- Maker (founder) information

### From Crunchbase:
- Real company names and descriptions
- Actual funding amounts and rounds
- Funding dates
- Company categories
- Founded dates

## Troubleshooting

### Still Getting Demo Data?

1. **Check DEMO_MODE**: Must be `false` (not `False` or `FALSE`)
2. **Check logs**: Look for "DEMO_MODE: Simulating" messages
3. **Restart backend**: Changes to `.env` require restart
4. **Verify API keys**: Check they're set correctly in `.env`

### API Errors?

**Product Hunt:**
- Works without token but may hit rate limits
- Get token for better reliability
- Check: https://api.producthunt.com/v2/oauth/applications

**Crunchbase:**
- Requires valid API key
- Check your API key is correct
- Verify account is active at https://data.crunchbase.com/
- Check API limits/quota

### No Startups Found?

1. **Check sources**: Verify `STARTUP_SEARCH_SOURCES` includes valid sources
2. **Check API keys**: Crunchbase requires API key
3. **Check logs**: Look for error messages
4. **Try Product Hunt first**: It works without API key

## Rate Limits

- **Product Hunt**: 
  - Without token: ~100 requests/hour
  - With token: Higher limits (varies by plan)
  
- **Crunchbase**: 
  - Varies by subscription plan
  - Check your plan limits at https://data.crunchbase.com/

## Next Steps

Once real startup discovery is working:

1. **Monitor costs**: Each startup processed uses OpenAI API credits
2. **Adjust frequency**: Change `SEARCH_INTERVAL_HOURS` based on your needs
3. **Filter sources**: Use only sources you have API access for
4. **Check proposals**: Real startups will appear in your frontend automatically!

## Support

If you encounter issues:
1. Check backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test API keys independently (curl commands)
4. Ensure `DEMO_MODE=false` is set

