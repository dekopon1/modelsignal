# SCORECARD — ModelSignal

Last updated: 2026-08-23 (MVP deployed and operating autonomously; two production monitor cycles completed)

| Dimension | Score (1–5) | Evidence / reasoning |
|---|---|---|
| Strength of evidence for customer pain | 4 | Cursor 2025 pricing backlash (simonwillison.net + HN); Copilot "premium requests" surprise-billing complaints on HN (story 44181097); Anthropic weekly rate-limit launch friction; DeepSeek price-rise warning made HN Aug 2026. Recurring, financially-material events. |
| Existing competition | — | Generic monitors (Distill $15–80/mo, Visualping) = detection without interpretation. Artificial Analysis ($417/mo/seat) = enterprise AI data, no change alerts. Static price tables (OpenRouter/LiteLLM/extractum) = snapshots. No direct competitor found at prosumer price for *explained* AI/dev-vendor changes. |
| Differentiation | 3 | Structured change records with old→new values, plain-English explanation, impact calculator, source-linked evidence, public history pages. Defensibility is the accumulated verified dataset + SEO surface, not tech. |
| Estimated willingness to pay | 2.5 | Adjacent proof only (Distill $15–80/mo; AA $417/seat). Our own price unproven until first checkout — gated on owner Stripe account. |
| Difficulty of customer acquisition | 3 | Organic-favorable: high-intent low-competition queries ("[vendor] pricing history"), every change → page/RSS/newsletter item. But SEO lag means first traffic depends on launch posts; no paid budget authorized. |
| Autonomous operability / owner burden | 4 | GitHub Actions cron + git-stored snapshots + Pages deploys = fully autonomous loop. Owner needed only for: domain, email service key, Stripe key, verification promotions (<1h/wk). |
| Technical difficulty | 3 | Fetch/snapshot/diff is solved; risk concentrated in extraction robustness and avoiding noise. Mitigated via deterministic parsers, markdown-friendly sources, confidence labels. JS-only pages deferred (Playwright later if justified). |
| Recurring-use potential | 3.5 | Monitoring/alerts are inherently recurring; public site visits are episodic but SEO-compounding. |
| **Overall** | **Go** | Pain is documented and frequent; wedge is narrow and buildable solo; costs ~$0 while owner actions are pending. |

## Strongest evidence it will work
Adjacent paid products bracket our price point from both sides (Distill $15–80 generic monitoring; AA $417/seat AI data), the pain events are real, recurring, and public — and as of today the product demonstrably works end-to-end at $0 operating cost: 12 official sources polled autonomously every 6h, structured diffs with honest detected/verified labels, 407 live-extracted model rates in a public calculator, and a site that grows a citable change history automatically.

## Strongest evidence it will fail
No direct willingness-to-pay proof for this exact product yet (checkout is waitlist-mode pending owner Stripe account); free alternatives may suffice for most devs; and the moat depends on extraction coverage we've run for only one day — noise rate and source stability are unproven over time.

## Kill/pivot criteria (decided now, honestly applied)
- After launch exposure (HN Show + 2 subreddits): if organic signup intent < ~20 emails or < 1 meaningful "would pay" conversation per 1,000 visitors → treat as weak demand; pivot toward free-tools/data-API angle or stop.
- If pipeline produces >50% false-positive/noise alerts over 30 days despite tuning → core promise broken; stop rather than ship junk.
