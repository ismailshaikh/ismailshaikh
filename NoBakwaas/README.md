# NoBakwaas Design Trend Finder

On-demand (not scheduled) research tool for new t-shirt/hoodie design
ideas - trending memes, fashion, anime, and general design signal, all
from FREE sources.

## How it's meant to be used

**One command, same pattern as FakiraMusafir** - no n8n, no scheduler:
```bash
cd NoBakwaas
pip install -r requirements.txt
python main.py
```
This researches trends from the free sources below AND pushes a fresh
report into your Notion page. Or just ask Claude in chat: "design
trends do" - it runs this same pipeline live.

Flags:
```bash
python main.py --top 15        # more items per category
python main.py --no-notion     # just save design_trends.json locally, skip Notion
```

## One-time setup - Notion

1. Go to **notion.so/my-integrations** -> "New integration" -> name it
   (e.g. "NoBakwaas Trends") -> copy the **Internal Integration Token**
   (starts with `secret_` or `ntn_`)
2. Open your target Notion page in the browser -> "..." menu (top
   right) -> **Connections** -> add the integration you just created
3. Copy the **page ID** from the page's URL - it's the 32-character
   string right before any `?` in the URL, e.g.
   `notion.so/My-Page-3e7e55f3de1c812d903bf4d2a3a07523` -> ID is
   `3e7e55f3de1c812d903bf4d2a3a07523`
4. Add both as environment variables (same way you added the Pexels/
   Pixabay/YouTube keys for FakiraMusafir - session settings -> Edit ->
   Environment Variables, or in a local `.env` file, never paste real
   values into `.env.example`):
   - `NOTION_API_KEY`
   - `NOTION_PAGE_ID`

That's it - every `python main.py` run appends a fresh, timestamped
trend report to that page.

## Sources (all free, no API key needed)

| Category | Source | Notes |
|---|---|---|
| Trending memes | Reddit (r/IndianDankMemes, r/india, r/bakchodi) | public `.json` endpoints, no auth |
| Trending fashion / general design ideas | Google Trends India (pytrends) | rising queries around streetwear/tshirt/hoodie keywords |
| Trending anime | MyAnimeList current season (Jikan API) | `api.jikan.moe`, free and official-adjacent |
| Trending dialogues | *(no reliable free API)* | check manually, see below |

## Manual-check only (no free scriptable API)

- **Redbubble / Teepublic "Trending"** - browse `redbubble.com/shop/trending`
  and `teepublic.com` by hand. This is the single best signal for what
  design *themes* are actually selling on print-on-demand right now.
- **Twitter/X Trends for India** - check the app's Trends tab.
- **Instagram Reels trending audio** - browse Explore/Reels by hand;
  a viral audio/dialogue is a strong signal for a print line.
- **Direct competitors** - Bewakoof, The Souled Store, Redwolf, Bonkers
  Corner "New Arrivals"/"Bestsellers" - fastest read on what's working
  in the Indian streetwear market specifically.

## Notes

- Google Trends' unofficial API rate-limits fast (HTTP 429) - the
  script waits 8s between keyword lookups. If you still get 429s,
  wait a few minutes and retry.
- Reddit's public JSON endpoints may be blocked from some sandboxed
  cloud environments (network policy, not a code bug) - runs fine
  from a normal machine with open internet.
- This tool only finds and researches trends. Turning a trend into an
  actual print design still happens in Canva - see Ismail's own
  preference: Claude's role here is research/strategy, not proposing
  individual graphics.
