# DECISIONS LOG

## D1 — Proceed, narrowed wedge (2026-08-22)
Evidence in research/MARKET_VALIDATION.md. ICP: indie AI devs & small AI startups (2–20 eng). Initial vendor set chosen for demand + source fetchability: OpenAI, Anthropic, Google Gemini, DeepSeek, Mistral, xAI, OpenRouter, Cursor, GitHub Copilot, Windsurf. Expand only from verified sources.

## D2 — Stack: Python-stdlib pipeline + custom static-site generator + GitHub Pages + Actions cron
Why not Next.js/Supabase/Stripe-now: no owner credentials exist for any paid/hosting service; gh CLI is the only live deploy path. A zero-dependency Python pipeline + stdlib SSG eliminates npm supply-chain/build fragility on CI, costs $0, and git itself is the snapshot store (free versioned history). Trade-off: no dynamic app yet; accounts/billing scaffolded behind config and documented in OWNER_ACTIONS.md. Reversible: site generator is isolated; data is plain JSON.

## D3 — Deterministic extraction only; LLM interpretation deferred
No LLM API key exists; more importantly, hallucinated pricing is an existential trust risk. Summaries are template-generated from extracted fields only. Confidence states: `detected` (single-source diff) / `verified` (corroborated by official announcement source) / `inferred` (never auto-published).

## D4 — Pricing hypothesis: Free / Pro $15 / Team $49
Between Distill's $15 starter and AA's enterprise pricing; dev-tool subscription norms are $10–39/user/mo. Treat as hypothesis pending first checkout.

## D5 — Product name: "ModelSignal" provisional
Domain purchase requires owner action; check conflicts before purchase. Alternates if taken: SignalStack? (check), PricePulse (likely taken), TokenTally, VendorSignal. Listed in OWNER_ACTIONS.md.

## D6 — Verification model
`detected` changes publish to public feed only after passing a materiality filter (pricing/limit/model fields, not cosmetic). Cross-corroboration with official announcement feeds promotes to `verified`. Unverifiable significant changes stay `detected` and are labeled as such everywhere.
