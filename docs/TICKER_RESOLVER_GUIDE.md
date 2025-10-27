# Dynamic Ticker Resolver - User Guide

## Quick Start

The system now automatically recognizes company names and resolves them to ticker symbols.

### Supported Query Formats

```python
# All of these work now:
"What's the price of Apple?"          → AAPL
"Analyze Facebook sentiment"          → META
"Compare Microsoft and Google"        → MSFT, GOOGL
"Tesla vs Amazon"                     → TSLA, AMZN
"How is AAPL doing?"                  → AAPL
"Johnson & Johnson risks"             → JNJ
```

## How It Works

**Three-Layer Resolution:**

1. **Cache** (instant): Checks local cache first
2. **yfinance** (fast): Validates ticker symbols
3. **LLM** (smart): Uses AI to understand aliases

**Example:**
```
User: "What about Facebook?"
  ↓
Cache: "facebook" → META (instant)
  ↓
Result: META
```

## Initial Setup

### First-Time Initialization

```bash
# Activate environment
source .venv/bin/activate

# Initialize cache with S&P 500 companies
python -m backend.scripts.init_ticker_cache
```

This downloads and caches 24+ major companies.

## No Setup Required!

The system works out-of-the-box. On first query:
- Unknown companies are resolved via LLM
- Results are cached for future use
- Cache grows automatically with usage

## Usage Examples

### Python API

```python
from backend.services.ticker_resolver import ticker_resolver

# Resolve a company name
ticker = await ticker_resolver.resolve("Apple")
print(ticker)  # Output: "AAPL"

# Resolve with aliases
ticker = await ticker_resolver.resolve("Facebook")
print(ticker)  # Output: "META"

# Handles abbreviations
ticker = await ticker_resolver.resolve("J&J")
print(ticker)  # Output: "JNJ" (via LLM)
```

### In Queries (Automatic)

Just use natural language:

```python
from backend.agents.graph import run_research_query

# All of these work automatically:
await run_research_query(session_id, "Analyze Apple")
await run_research_query(session_id, "Facebook vs Google")
await run_research_query(session_id, "What's Tesla doing?")
```

## Maintenance

### View Cache

```bash
# Show cached companies
cat backend/data/ticker_cache.json

# Count cached entries
jq '.metadata.total_entries' backend/data/ticker_cache.json
```

### Update Cache

```bash
# Re-initialize with latest data
python -m backend.scripts.init_ticker_cache
```

### Clear Cache

```bash
# Delete cache (rebuilds automatically)
rm backend/data/ticker_cache.json
```

## Performance

- **Cache hit:** <1ms
- **yfinance query:** 200-500ms
- **LLM resolution:** 1-2s

After warmup, 95%+ queries are cache hits (<1ms).

## Cost

- **Cache lookup:** Free
- **yfinance:** Free
- **LLM:** ~$0.0001 per new company

**Monthly cost:** <$0.10 (for 1000 new companies)

## Troubleshooting

### Company Not Recognized

**Problem:** System returns `None` for a company

**Solution:**
1. Check spelling
2. Try official name ("Meta Platforms" vs "Facebook")
3. Use ticker directly ("META" instead of "Facebook")

### Cache Issues

**Problem:** Old/stale data in cache

**Solution:**
```bash
# Cache entries expire after 90 days
# Force refresh:
rm backend/data/ticker_cache.json
python -m backend.scripts.init_ticker_cache
```

### LLM Not Working

**Problem:** LLM resolution fails

**Check:**
```python
# Ensure OpenAI API key is set
echo $OPENAI_API_KEY

# Check settings
from backend.config.settings import settings
print(settings.openai_api_key)
```

## Advanced Features

### Disable LLM (Cost Saving)

If you want to disable LLM and rely only on cache + yfinance:

```python
# In backend/services/ticker_resolver.py
ticker_resolver = TickerResolver(
    enable_llm=False  # Disable LLM
)
```

### Adjust TTL

Change cache expiration time:

```python
ticker_resolver = TickerResolver(
    ttl_days=180  # 6 months instead of 90 days
)
```

### Custom Cache Location

```python
ticker_resolver = TickerResolver(
    cache_path="/custom/path/ticker_cache.json"
)
```

## API Reference

### TickerResolver.resolve()

```python
async def resolve(company_name: str) -> Optional[str]:
    """
    Resolve company name to ticker symbol.

    Args:
        company_name: Company name, alias, or ticker

    Returns:
        Ticker symbol (e.g., "AAPL") or None
    """
```

**Examples:**
```python
await ticker_resolver.resolve("Apple")      # → "AAPL"
await ticker_resolver.resolve("Facebook")   # → "META"
await ticker_resolver.resolve("MSFT")       # → "MSFT"
await ticker_resolver.resolve("Unknown")    # → None
```

### TickerResolver.add_sp500_companies()

```python
def add_sp500_companies(sp500_data: Dict[str, str]):
    """
    Bulk add companies to cache.

    Args:
        sp500_data: {company_name: ticker}
    """
```

**Example:**
```python
companies = {
    "Apple Inc.": "AAPL",
    "Microsoft Corporation": "MSFT"
}
ticker_resolver.add_sp500_companies(companies)
```

## FAQ

### Q: How many companies are supported?

**A:** Unlimited. System starts with 24 cached companies and learns new ones dynamically via LLM.

### Q: What happens if a company is delisted?

**A:** Cache entries expire after 90 days. On expiry, ticker is re-validated. Invalid tickers are removed.

### Q: Can I add my own companies?

**A:** Yes! Either:
1. Let the system learn them (query once, it caches)
2. Manually add to `ticker_cache.json`
3. Use `add_sp500_companies()` to bulk import

### Q: Does it work offline?

**A:** Partially. Cache lookups work offline. New company queries require internet (yfinance/LLM).

### Q: What about international companies?

**A:** Currently optimized for US companies. International tickers may work via LLM but are not in initial cache.

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review cache: `backend/data/ticker_cache.json`
- Test directly:
  ```bash
  python -c "
  from backend.services.ticker_resolver import ticker_resolver
  import asyncio
  result = asyncio.run(ticker_resolver.resolve('YourCompany'))
  print(result)
  "
  ```

---

**Last Updated:** October 26, 2025
**Feature Version:** 1.0
**Status:** Production Ready ✅
