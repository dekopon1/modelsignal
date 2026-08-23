# LAUNCH-READINESS REPORT

Audit repair pass of 2026-08-23. Every item below was verified against **live production** (`https://dekopon1.github.io/modelsignal/`) or reproducible commands — not against green CI badges. Overall: **CONDITIONAL GO** — technically launch-ready; scheduled-cron proof pending; zero paid features promised.

| # | Audit item | Verdict | Evidence |
|---|---|---|---|
| 1 | Root-relative internal links (404s on `/modelsignal/`) | ✅ FIXED & VERIFIED LIVE | Single helper `u()` in `pipeline/ssg.py`; every anchor in generator goes through it; `pipeline/tests/test_links.py` (4 tests) fails on any root-relative or dangling link; production crawl following real anchors visited **29 pages, all HTTP 200, 0 broken** (crawl method described in Route Matrix section below) |
| 2 | Synthetic `gpt-test`/example.com record in production | ✅ FIXED & VERIFIED | Purged (record `a4106c6d6c2ca5b3` deleted); guard #1 `monitor.validate_source()` rejects non-https/example/test-shaped sources pre-fetch; guard #2 `build_site_data` re-filters every record against the source registry at build; tests prove both layers block injection. Public feed now shows **exactly 1 record: a genuine OpenRouter price change verified against archived raw snapshots AND live API** |
| 3 | OpenRouter `'str' object has no attribute 'get'` | ✅ FIXED & VERIFIED ×2 | Root cause: parser emitted 1-level records, diff engine expects 2-level. Parser now nests under `"models"`; baseline reset cleanly; regression test `test_audit_fixes.py::test_baseline_then_price_change_then_revert` covers baseline→price change→dedupe→revert; **production monitor ran twice back-to-back: 12/12 sources OK, second run produced zero duplicate/phantom changes** |
| 4 | Failed source → green workflow; stale errors | ✅ FIXED (behavior live next run) | `pipeline/quality_gate.py`: PARTIAL failure → red run + `::error` annotation + summary table; TOTAL failure distinguished explicitly; successful source runs now clear prior error state (`st.pop("last_error")`) so `/status` never lies. Gate unit-tested (5 tests). Note: gate's first *scheduled* appearance is the pending cron run |
| 5 | Broken waitlist form (`forms.gle/placeholder`) | ✅ FIXED & VERIFIED LIVE | All placeholder forms removed. Signup form renders **only if** `site/config.json → forms.newsletter_endpoint` is set (it isn't); pages instead say email capture doesn't exist yet and point to RSS. Verified live copy on /pricing/ and /newsletter/ |
| 6 | Unsupported claims | ✅ FIXED & VERIFIED LIVE | Vendors vs sources separated: stats now show **6 actively monitored** (Anthropic, Gemini, DeepSeek, Mistral, Copilot, OpenRouter), **1 announcements-only (OpenAI)**, Cursor removed entirely from site (no working monitor). Homepage says "polls 12 official sources across 6 vendors"; vendor directory has status column; OpenAI page says "Planned, not active". Pricing page splits **Available now (free)** vs **Planned paid tiers — not purchasable today**; alerts/watchlists/Slack/webhooks/accounts described as planned only; terms/privacy updated to match reality |
| 7 | OWNER_ACTIONS.md referenced missing files | ✅ FIXED | No more `docs/APP_SCHEMA.sql` / `site/config/payments.json`. Real wiring point documented and code-verified: `site/config.json` keys `site_url`, `forms.newsletter_endpoint`, `analytics_script`. Supabase item removed (no app tier exists). Corrections listed at bottom of the file |
| 8 | Name conflict | ⚠️ RENAME RECOMMENDED (owner decides) | **modelsignal.ai exists** — beehiiv newsletter, "Stay on top of AI model releases" (same space/audience); modelsignal.com returns 403. Recommendation + 5 alternatives in DECISIONS.md D9: VendorSignal, PriceRadar, RateLedger, QuotaWatch, APIPriceWatch (domain checks recorded; registrar/trademark verification is yours). Product name unchanged until you pick |
| 9 | Scheduled cron unproven | ⚠️ HONESTLY UNPROVEN | Attempted real proof: temporarily set `*/10 * * * *`, observed two cron ticks (03:30Z, 03:40Z) — **no scheduled run fired within 25 min** (GitHub scheduler lag). Reverted to production cadence `17 */6 * * *` (confirmed in workflow file on main). **Scheduled operation remains UNPROVEN until first native cron run, expected 06:17 UTC.** Verify: `gh run list --repo dekopon1/modelsignal --workflow=monitor --json event,conclusion --jq '.[] \| select(.event=="schedule")'`. Manual dispatches do work (4 successful) |

## Bonus defect found & fixed during repair
- Stale build artifacts accumulated in `site/dist` across builds (could serve dead pages): generator now wipes dist before rebuild.
- Materiality filter missed `prompt_per_mtok`-style fields (would have silently dropped model-price changes): regex fixed + regression-tested.
- Feed JS used root-relative template URLs: base-injected at build.

## Test suite
**32 tests passing** (parsers/diff/materiality/summaries, end-to-end monitor flow, publication guard, quality gate, link integrity, sitemap/feed integrity).

---

# CLICKABLE ROUTE MATRIX (verified live 2026-08-23 ~03:25 UTC)

Base: https://dekopon1.github.io/modelsignal

| Route | Status | What it is |
|---|---|---|
| [/](https://dekopon1.github.io/modelsignal/) | 200 | Homepage w/ honest stats + latest real change |
| [/changes/](https://dekopon1.github.io/modelsignal/changes/) | 200 | Filterable change feed (JS renders embedded evidence data) |
| [/changes/f3c5d5682110d7cc/](https://dekopon1.github.io/modelsignal/changes/f3c5d5682110d7cc/) | 200 | First genuine record: OpenRouter DeepSeek-v4-flash completion $0.18→$0.14/MTok |
| [/vendors/](https://dekopon1.github.io/modelsignal/vendors/) | 200 | Directory with Active vs Announcements-only status |
| [/vendors/anthropic/](https://dekopon1.github.io/modelsignal/vendors/anthropic/) · [/pricing-history/](https://dekopon1.github.io/modelsignal/vendors/anthropic/pricing-history/) | 200 | Active monitor |
| [/vendors/google-gemini/](https://dekopon1.github.io/modelsignal/vendors/google-gemini/) · [/pricing-history/](https://dekopon1.github.io/modelsignal/vendors/google-gemini/pricing-history/) | 200 | Active monitor |
| [/vendors/deepseek/](https://dekopon1.github.io/modelsignal/vendors/deepseek/) · [/pricing-history/](https://dekopon1.github.io/modelsignal/vendors/deepseek/pricing-history/) | 200 | Active monitor |
| [/vendors/mistral/](https://dekopon1.github.io/modelsignal/vendors/mistral/) · [/pricing-history/](https://dekopon1.github.io/modelsignal/vendors/mistral/pricing-history/) | 200 | Active monitor |
| [/vendors/github-copilot/](https://dekopon1.github.io/modelsignal/vendors/github-copilot/) · [/pricing-history/](https://dekopon1.github.io/modelsignal/vendors/github-copilot/pricing-history/) | 200 | Active monitor |
| [/vendors/openrouter/](https://dekopon1.github.io/modelsignal/vendors/openrouter/) · [/pricing-history/](https://dekopon1.github.io/modelsignal/vendors/openrouter/pricing-history/) | 200 | Active monitor |
| [/vendors/openai/](https://dekopon1.github.io/modelsignal/vendors/openai/) | 200 | Labeled announcements-only, "Planned, not active" |
| [/calculators/llm-cost/](https://dekopon1.github.io/modelsignal/calculators/llm-cost/) | 200 | Calculator over 514 live-extracted rates |
| [/pricing/](https://dekopon1.github.io/modelsignal/pricing/) | 200 | Free-now vs planned-only; no fake checkout |
| [/methodology/](https://dekopon1.github.io/modelsignal/methodology/) · [/faq/](https://dekopon1.github.io/modelsignal/faq/) · [/about/](https://dekopon1.github.io/modelsignal/about/) · [/status/](https://dekopon1.github.io/modelsignal/status/) · [/newsletter/](https://dekopon1.github.io/modelsignal/newsletter/) · [/blog/](https://dekopon1.github.io/modelsignal/blog/) | 200 | Informational set |
| [/privacy/](https://dekopon1.github.io/modelsignal/privacy/) · [/terms/](https://dekopon1.github.io/modelsignal/terms/) | 200 | Legal matching actual behavior |
| [/feed.xml](https://dekopon1.github.io/modelsignal/feed.xml) · [/sitemap.xml](https://dekopon1.github.io/modelsignal/sitemap.xml) · [/robots.txt](https://dekopon1.github.io/modelsignal/robots.txt) | 200 | Machine surfaces |

Crawl method: followed every `<a href>` from the homepage breadth-first (29 unique pages), flagged any root-relative href as broken, then separately validated runtime-generated JS targets. Result: PASS.

---

# WHAT THE PRODUCT CAN ACTUALLY DO TODAY

1. **Autonomously poll 12 official sources every 6h** (pending cron proof above; manual runs proven): Anthropic pricing/rate-limits/release-notes (.md endpoints), Gemini pricing/changelog, DeepSeek pricing, Mistral models, Copilot plans/premium-requests docs, OpenRouter public models API, OpenAI news RSS, GitHub changelog RSS.
2. **Detect and publish material changes** with old value, new value, section context, plain-English summary, effective date when literally stated, confidence label, and links to source + archived raw snapshot. Demonstrated on a real 22% price drop within hours of deployment.
3. **Corroborate** detected changes against same-vendor official announcements (token-overlap within time window) → upgrades detected→verified.
4. **Publish a free public database**: change feed, per-vendor history pages, RSS, sitemap — growing automatically.
5. **LLM cost calculator**: monthly cost estimates from 514 published rates extracted verbatim from official sources, auto-updating when those sources change.
6. **Weekly digest generation** (markdown archive + site page), idempotent per ISO week.
7. **Honest ops**: per-source health page, quality-gated CI, git-backed immutable snapshot evidence, zero dependencies, $0/month infra.
8. Refuse to do: collect emails (no endpoint), take payments (no Stripe), promise personalized impact math (accounts layer unbuilt), list vendors it cannot actually monitor.

It cannot yet do: scheduled-run-proven monitoring (hours away), email/webhook/Slack delivery, accounts, watchlists, exports, personalized impact models, JS-rendered vendor pages (Cursor/Windsurf/OpenAI-pricing) — all labeled planned, several gated on your actions.

---

# 7-DAY VALIDATION PLAN (before building billing/accounts)

Goal: **real conversations + signup intent**, not traffic vanity. Billing stays disabled regardless until Day-7 review.

**Day 0–1 (today+tomorrow) — make intent measurable**
- [ ] Owner: pick name/domain (DECISIONS.md D9) → I migrate site_url + canonical.
- [ ] Owner: create free Formspree (or similar) form → paste endpoint into `site/config.json` → signup form appears automatically. This is the validation instrument: one field, double-opt-in if possible.
- [ ] Confirm first native cron run succeeded (~06:17Z). If GitHub scheduler keeps lagging, switch trigger to a self-rescheduling workflow (workflow_dispatch → schedule next run via API) — still zero-owner.

**Day 1–2 — seed evidence, quietly**
- [ ] Publish digest edition #1 linking the real OpenRouter drop ("first catch").
- [ ] Post the blog piece + repo publicly announce nothing yet; submit sitemap to Google Search Console (owner account).

**Day 2–3 — first exposure batch (founder voice, transparent)**
- [ ] One subreddit only (r/ChatGPTCoding or r/cursor): lead with the calculator + the caught price drop; mention database; zero pricing talk.
- [ ] One X/Bluesky post with the change-page screenshot.
- Measure: outbound clicks (referrer logs), form submissions, repo stars.

**Day 3–5 — second exposure batch**
- [ ] Show HN (only after domain live + ≥3 days of clean monitoring).
- [ ] Indie Hackers build-log post incl. scorecard honesty.
- [ ] Direct outreach: 10 DMs/emails to builders who publicly complained about Cursor/Copilot billing (reply to their public posts helpfully first; never spam — max 10, personalized).

**Day 6–7 — interviews & decision**
- [ ] Convert any form signup into a 15-min call (target: ≥3).
- [ ] Ask: last time a vendor change surprised them? what did it cost? would they pay $15/mo for earlier warning with impact math? (Mom-test style, no pitching.)
- [ ] Score against SCORECARD kill criteria:
  - **Proceed signals:** ≥20 qualified signups OR ≥3 "would pay today" statements OR 1 person asks to pay early.
  - **Weak:** <8 signups and no pay-intent after genuine HN-level exposure → pivot toward free tools/data-API angle or stop.
  - Either way: write findings into research/MARKET_VALIDATION.md before touching Stripe.

Explicitly deferred until Day-7 verdict: Stripe, Resend, accounts/database, watchlists, Slack/webhooks.
