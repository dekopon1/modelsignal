# STATUS

Current phase: **Phase 10 — Deployed & operating autonomously** (Phases 1–9 complete)

## Live
- Site: https://dekopon1.github.io/modelsignal/ — verified 200 on all key routes (/, /changes/, /vendors/*, /calculators/llm-cost/, /pricing/, /status/, /feed.xml, /sitemap.xml, /robots.txt)
- Repo: https://github.com/dekopon1/modelsignal (public)
- Monitor loop: GitHub Actions cron every 6h → fetch 12 official sources → snapshot to git → deterministic diff → materiality filter → verify → digest → commit → site rebuild + Pages deploy. **Two full production cycles ran successfully**; idempotency confirmed (no phantom changes between runs).

## Completed
- Market validation with live sources; SCORECARD + go/no-go decision (GO, narrowed wedge)
- Pipeline: parsers (markdown/HTML tables incl. rowspan matrices/RSS/OpenRouter JSON), diffing, materiality filter, corroboration engine, newsletter generator — zero dependencies
- Baselines captured for all 12 sources on day one; no fabricated history anywhere
- Static site: 31+ pages generated from real data; LLM cost calculator with 407 live-extracted model rates
- Tests: 18 passing (unit + end-to-end simulated price change, idempotency, noise filtering, failure handling)
- Fixed in production: GITHUB_TOKEN anti-recursion (deploys chained into monitor workflow), RSS CDATA parsing, rowspan field offsets

## Current blocker
None technical. Owner-gated: domain purchase, Stripe keys, email endpoint (see OWNER_ACTIONS.md). Until then checkout is waitlist-mode and email signup falls back to RSS — both handled honestly in the UI.

## Next actions
1. Owner: domain + Stripe + Resend/Formspree wiring (OWNER_ACTIONS.md) — unblocks first dollar
2. Execute LAUNCH_PLAN.md channel sequence (needs owner OK for personal-account posts)
3. After ~2 weeks of monitoring data: review noise rate vs SCORECARD kill criteria; add sources from demonstrated demand (Playwright runner for JS-only pages if justified)
