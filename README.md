# ModelSignal

We watch what AI & developer-tool vendors change — prices, limits, quotas, model availability, plan entitlements — and explain what changed, who is affected, and (where published rates allow) what it costs you. Every fact links to an official source.

**Live site:** https://dekopon1.github.io/modelsignal/ · **Feed:** `/feed.xml`

## Why

Generic page-monitors stop at "this page changed". Price-table sites have no memory. This project records structured change history: old value → new value → plain-English summary → impact estimate → source link, with honest `detected` vs `verified` confidence labels.

## Architecture (deliberately boring)

```
GitHub Actions cron (every 6h)
  └─ pipeline/monitor.py     fetch 12 official sources → normalize → snapshot (git) → parse
                             → field-level diff → materiality filter → change objects
  └─ pipeline/verify.py      corroborate against official announcements → detected|verified
  └─ pipeline/build_site_data.py   JSON for the site
  └─ pipeline/newsletter.py  weekly digest (markdown archive + site JSON)
  └─ commit data/            → triggers deploy.yml
       └─ pipeline/ssg.py    zero-dependency static site generator → GitHub Pages
```

- **Zero runtime dependencies** — Python stdlib only. Nothing to break on CI.
- **Snapshots live in git** — immutable evidence trail.
- **No hallucinated facts** — summaries are template-generated from extracted fields; estimates are labeled; `inferred` values are never auto-published.

## Monitored sources (initial set)

Anthropic (pricing / rate limits / release notes), Google Gemini (pricing / changelog), DeepSeek pricing, Mistral models, GitHub Copilot (plans / premium requests), OpenRouter models API, OpenAI news RSS, GitHub changelog RSS. Live health: `/status` on the site. JS-only pages (e.g. cursor.com/pricing) are documented in `pipeline/sources.json` `_notes` and excluded until a browser runner is justified.

## Tests

```
python3 pipeline/tests/test_pipeline.py        # parsers, diff, materiality, summaries
python3 pipeline/tests/test_monitor_flow.py    # end-to-end: baseline → price change → dedupe → noise filter
python3 -m unittest discover -s pipeline/tests
```

## Operations

See `OPERATIONS.md`. Owner-only actions (domain, Stripe, email keys): `OWNER_ACTIONS.md`.

## Repo layout

- `research/MARKET_VALIDATION.md` — demand & competition evidence
- `SCORECARD.md` — honest business scorecard with kill criteria
- `marketing/LAUNCH_PLAN.md`, `marketing/digests/`
- `site/config.json` — domain/payment/form wiring points
