# ELYNE System - Organic Content Trend Pipeline

On-demand (not scheduled, no n8n) tool for ELYNE's own organic social
media content - finds what's trending in India + real small-business/
marketing pain points, then turns them into trend-jacked marketing-tip
Reel scripts via Claude Pro.

Same architecture as `FakiraMusafir/` and `NoBakwaas/` in this repo:
one Python command, results pushed to Notion, everything free.

## How it's meant to be used

```bash
cd ELYNE
pip install -r requirements.txt
python main.py
```
This researches trends from the free sources below AND pushes a fresh
report to your Notion page. Or ask Claude in chat: "ELYNE trending
topics do" - it runs this same pipeline live.

Flags:
```bash
python main.py --top 20        # more items per category
python main.py --no-notion     # just save elyne_trends.json locally
```

## Daily workflow - turning a trend into a post

1. Run `python main.py` (or ask Claude), pick one trending topic or
   pain point from the results (or from `topics.csv` for an evergreen,
   non-trend-dependent idea).
2. Open `prompts/claude_pro_content_prompt.txt`, replace `{TOPIC}`,
   paste into Claude Pro.
3. Copy the script/caption/hashtags it gives you, post it.

## Sources (all free, no API key needed)

| Category | Source | Notes |
|---|---|---|
| Marketing/small-business rising queries | Google Trends India (pytrends) | rising queries around GMB, WhatsApp marketing, Instagram Reels, etc. |
| Business pain points | Reddit (r/smallbusiness, r/marketing, r/IndianStartups) | public `.json` endpoints, no auth - what business owners are actually asking |

Google Trends' general daily "Trending Now" list (`pytrends.trending_searches()`)
was tried and dropped - it reliably 404s (Google changed the endpoint,
pytrends hasn't caught up). For general trend-jacking, check Twitter/X
Trends or Instagram Explore by hand instead.

## Manual-check only (no free scriptable API)

- **Instagram Reels trending audio** - browse Explore/Reels by hand
- **LinkedIn** - browse feed for what marketing content is getting engagement right now
- **Twitter/X Trends for India** - check the app's Trends tab

## One-time setup - Notion

1. Go to **notion.so/my-integrations** -> "New integration" -> name it
   (e.g. "ELYNE Trends") -> copy the **Internal Integration Token**
2. Open your target Notion page -> "..." menu -> **Connections** ->
   add the integration
3. Copy the **page ID** from the page's URL (32-char string before
   any `?`)
4. Add both as environment variables (same way as the other keys in
   this repo - session settings -> Edit -> Environment Variables, or
   a local `.env` file; never paste real values into `.env.example`):
   - `NOTION_API_KEY`
   - `NOTION_PAGE_ID`

You can reuse the SAME Notion page/integration as NoBakwaas if you
want everything in one place, or create a separate ELYNE-only page -
either works, just point `NOTION_PAGE_ID` at whichever you choose.

## Notes

- Google Trends' unofficial API rate-limits fast (HTTP 429) - the
  script waits 8s between keyword lookups.
- Reddit's public JSON endpoints may be blocked from some sandboxed
  cloud environments (network policy, not a code bug) - runs fine
  from a normal machine with open internet.
- This is content strategy/research only. The actual Reel filming,
  editing, and posting is manual - matches how NoBakwaas's design
  work stays manual too.
