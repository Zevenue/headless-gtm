# Firecrawl SDK Reference

## Auth

```
FIRECRAWL_API_KEY=<key>  # in .env file
```

## SDK setup

```bash
pip install firecrawl-py python-dotenv
```

```python
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
```

## Endpoints used by this skill

### /map - Discover site URLs (1 credit)

```python
result = app.map("https://example.com", limit=200)
# Returns LinkResult objects - normalize:
urls = [str(u.url) if hasattr(u, 'url') else str(u) for u in result]
```

- Returns up to `limit` URLs found on the site
- 1 credit regardless of how many URLs found
- May return `links` attribute or raw list depending on SDK version

### /scrape - Fetch single page (1 credit)

```python
page = app.scrape(
    "https://example.com/about",
    formats=["markdown"],           # or ["markdown", "screenshot"]
    only_main_content=False,
    wait_for=1500,                  # ms to wait for JS rendering
)
content = page.markdown             # or page.get("markdown", "")
screenshot = page.screenshot        # base64 or URL (if requested)
```

- 1 credit per page
- Handles JS rendering natively (no extra cost)
- Handles moderate anti-bot (~80% success rate)
- `wait_for` helps with JS-heavy sites
- `screenshot` format option: same credit, 0 extra cost

### /extract - Structured field extraction (1 credit)

```python
result = app.extract(
    ["https://example.com"],
    prompt="Extract GTM-relevant company information.",
    schema={
        "founder": "string",
        "headcount_clues": "string",
        # ...
    },
)
```

- 1 credit per extraction
- LLM-driven: pass a schema and get structured JSON back
- Best for quick field pulls without full page scraping

## DO NOT use these patterns

These are old API methods that will fail with current SDK:

| Wrong | Right |
|-------|-------|
| `app.map_url()` | `app.map()` |
| `app.scrape_url()` | `app.scrape()` |
| `V1FirecrawlApp` | `FirecrawlApp` |
| `params={}` wrapper | Direct keyword args |

## Response handling

Map response may return:
- `response.links` (attribute) - list of LinkResult objects
- `response` itself as a list
- Always normalize: `[str(u.url) if hasattr(u, 'url') else str(u) for u in raw]`

Scrape response may return:
- `response.markdown` (attribute)
- `response["markdown"]` (dict)
- Always try attribute first, then dict access

## Rate limits

- No explicit rate limit documented, but add 1-2s pause between scrape calls in batch mode
- Map calls are lightweight - no pause needed
