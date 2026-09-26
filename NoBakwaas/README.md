# NoBakwaas Design Trend Finder

On-demand (not scheduled) research tool for new t-shirt/hoodie design
ideas - trending memes, fashion, anime, and general design signal, all
from FREE sources.

## How it's meant to be used

**Just ask Claude in chat**: "design trends do" / "NoBakwaas trend research karo".
Claude re-runs the same free lookups live and gives you a fresh set of
ideas (and updates the linked Notion page) - no schedule, no cron,
only when you ask.

You can also run it yourself:
```bash
cd NoBakwaas
pip install -r requirements.txt
python design_trend_finder.py --top 10
```
Saves results to `design_trends.json` and prints a summary.

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
