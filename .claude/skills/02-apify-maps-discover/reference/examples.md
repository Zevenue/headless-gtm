# Reference · Recipes

Copy-paste commands. All assume `APIFY_API_TOKEN` is exported and you're in the
`apify-maps-discover/` folder.

## 1. Dry-run the cost (no spend)
```bash
python discover.py --search-term "yoga studios" --geo "California" \
  --max-results 2000 --estimate-only
```

## 2. Quick smoke test (cheap, ~25 rows)
```bash
python discover.py --search-term "laundromat" --geo "Toronto, ON" \
  --max-results 25
```

## 3. Single-city prospect list
```bash
python discover.py --search-term "hair salon" --geo "San Diego, CA" \
  --max-results 250 --min-rating 4.0
```

## 4. Full Step-2 deliverable with emails (~2K rows, ~$8)
```bash
python discover.py --search-term "hvac contractor" --geo "California" \
  --max-results 2000 --include-emails --yes
```

## 5. Add review recency (detail-page scrape, extra cost)
```bash
python discover.py --search-term "pilates studio" --geo "Ontario" \
  --max-results 500 --with-review-dates
```

## 6. Two verticals into one folder, then dedup downstream
```bash
python discover.py --search-term "nail salon" --geo "Toronto, ON" --max-results 300 --out runs/beauty
python discover.py --search-term "hair salon" --geo "Toronto, ON" --max-results 300 --out runs/beauty
# → feed runs/beauty/*.json to the multi-source merge / eval step
```

## 7. Multi-city sweep (loop)
```bash
for city in "Toronto, ON" "Mississauga, ON" "Brampton, ON"; do
  python discover.py --search-term "auto repair shop" --geo "$city" \
    --max-results 200 --out runs/auto
done
```

## Output of every run
`runs/<slug>.json`, `runs/<slug>.csv`, `runs/<slug>_meta.json` (row count + spend
estimate + the echoed query). `<slug>` = `apify-<search>-<geo>`.
