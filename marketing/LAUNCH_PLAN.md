# LAUNCH PLAN

Product: ModelSignal — explained change monitoring for AI & dev-tool vendors.
Live site: https://dekopon1.github.io/modelsignal/ (custom domain pending owner purchase — see OWNER_ACTIONS.md).

## Positioning statement

"AI vendors change prices, limits and models constantly. ModelSignal records every change, explains it, and tells you what it costs you — with a link to the official source. Free database; alerts from $15/mo."

Founder-transparent everywhere: we say we built it, never shill as neutral users.

## Channels (in order of execution)

### 1. Show HN (owner posts; draft below)
Title: `Show HN: I built a recorder for AI vendor pricing/limit changes, with sources`
Angle: the Cursor/Copilot/Anthropic-rate-limit pattern → what generic monitors miss → honest detected-vs-verified labels → free public DB.
Timing: Tue–Thu, 8–10am ET. First hour: answer every comment with specifics.
Risk control: if data coverage questions arise, point at `/status` (honest health) rather than overclaiming.

### 2. Reddit (owner posts, one subreddit per day max)
- r/cursor + r/ChatGPTCoding: "I got tired of finding out about pricing changes from my bill — I built something that records them"
- r/LocalLLaMA: angle on OpenRouter model-price drift + calculator
- r/github Copilot discussions: premium-request allowance history
Read each sub's self-promo rules first; lead with the free utility (calculator/history), not the paid tier.

### 3. Indie Hackers
Milestone post: "Bootstrapped to a live product in one session — here's the full scorecard including what's unproven." Radical transparency is the hook.

### 4. Product Hunt
Only after custom domain is live (PH penalizes github.io links). Prepare gallery images from real product screenshots.

### 5. SEO (compounding, starts immediately)
- Every verified change → indexable page (already automatic).
- Target queries: "[vendor] pricing history", "[vendor] rate limits", "did [vendor] change pricing", "[model] deprecated".
- Sitemap submitted via robots.txt; request indexing for top 10 pages once domain is final (URLs change with domain — don't waste the quota twice).
- After domain migration: 301s via Pages redirect? GitHub Pages doesn't do 301s → publish a rel=canonical note and accept re-crawl; keep github.io up during transition.

### 6. Newsletter swap / dev newsletters
Pitch "This Week in AI Pricing & Limits" archive to curators (e.g., console.dev, TLDR) once ≥4 editions exist.

## Content pieces grounded in our own captured evidence
1. "Every AI API pricing change since we started recording" (living page — /changes/)
2. "The hidden complexity of coding-agent billing: premium requests, AI credits, flex allotments" — uses our extracted Copilot tables
3. "Gemini publishes price steps in advance — here's how to catch them" — uses the "$0.375 through Dec 31, 2026 / $0.75 starting Jan 1, 2027" extraction as proof-of-value
4. "detected vs verified: why we refuse to publish inferred prices"

## Free tools (funnel into monitoring)
1. LLM cost calculator (LIVE at /calculators/llm-cost/, 407 models, auto-updating rates)
2. Vendor change RSS feeds per vendor (trivial add — feed.xml already exists globally)
3. Planned: Slack/Discord bot posting verified changes (needs owner server for demo)

## Launch-week success metrics (honest bar)
- ≥200 uniques on launch day (GitHub Pages can't measure this precisely without analytics owner approval — use HN/Reddit referral counts + repo stars/forks as proxy)
- ≥15 newsletter/waitlist emails
- ≥3 conversations mentioning willingness to pay
- If ~zero intent after genuine exposure → revisit SCORECARD kill criteria

## Owner approvals needed before posting
See OWNER_ACTIONS.md item 7 — drafts ready; will not post from personal accounts without explicit OK.
