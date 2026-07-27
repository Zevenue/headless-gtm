# Firecrawl Cost Guide

## Credit pricing by plan

| Plan | Credits/mo | Price | Per credit |
|------|-----------|-------|------------|
| Free | 500 | $0 | $0 |
| Hobby | 3,000 | $19/mo | $0.006 |
| Standard | 100,000 | $99/mo | $0.001 |
| Growth | 1,000,000 | $399/mo | $0.0004 |

## Credits per operation

| Operation | Credits |
|-----------|---------|
| `/map` (discover URLs) | 1 |
| `/scrape` (one page) | 1 |
| `/scrape` with screenshot | 1 (same cost) |
| `/extract` (structured) | 1 |

## Credits per domain by mode

| Mode | Pages | Credits | Cost (Standard) | Cost (Growth) |
|------|-------|---------|-----------------|---------------|
| Minimal | 2 | 3 | $0.003 | $0.001 |
| Standard | 4-7 | 5-8 | $0.005-0.008 | $0.002-0.003 |
| Deep | 4-10 | 5-11 | $0.005-0.011 | $0.002-0.004 |
| Extract | 1 | 1 | $0.001 | $0.0004 |

Formula: 1 (map) + N (scrapes) = total credits

## Batch cost estimates

| Batch size | Mode | Credits | Standard | Growth |
|-----------|------|---------|----------|--------|
| 100 | Standard | 500-800 | $0.50-0.80 | $0.20-0.32 |
| 100 | Minimal | 300 | $0.30 | $0.12 |
| 500 | Standard | 2,500-4,000 | $2.50-4.00 | $1.00-1.60 |
| 1,000 | Standard | 5,000-8,000 | $5.00-8.00 | $2.00-3.20 |
| 2,000 | Minimal | 6,000 | $6.00 | $2.40 |
| 2,000 | Standard | 10,000-16,000 | $10.00-16.00 | $4.00-6.40 |

## Cost guard thresholds

| Trigger | Action |
|---------|--------|
| Single domain > 10 credits | Warn before proceeding |
| Batch > 50 domains | Show estimated total, ask confirmation |
| Batch > 500 domains | Suggest minimal mode, require confirmation |
| Estimated batch > $10 | Hard stop, require user approval |

## Screenshot logo extraction cost

- Screenshot format on `/scrape`: 0 extra credits (same call)
- Claude Code vision (Max plan): $0 extra (built-in capability)
- Total additional cost for logo extraction: $0

## Cost optimization tips

- Use `/map` once per domain, never repeat
- Use minimal mode for initial qualification batches
- Use standard mode for shortlisted prospects
- Use deep mode only for high-value targets
- Use extract mode when you only need specific fields
- For 2K+ domains: consider minimal mode to stay under credit limits
