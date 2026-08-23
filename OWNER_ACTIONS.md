# OWNER ACTIONS — prioritized

Only actions that require **your** identity, credentials, money, or accounts. Everything else is automated (see OPERATIONS.md). All configuration happens in **one file**: `site/config.json` — the generator reads it on every build.

## Priority 1 — before telling anyone about this product
1. **Domain (recommended, ~$12/yr).** The site currently lives at `https://dekopon1.github.io/modelsignal/`. A bare domain looks credible and SEO URLs stop changing later.
   - Before buying: see DECISIONS.md D9 for the name-conflict research and rename recommendation.
   - After buying: set `"site_url"` in `site/config.json` to the new domain, add a CNAME file + DNS record per GitHub Pages docs (I will do the repo side once you own it).

## Priority 2 — first dollar (only after validation signals; see 7-DAY PLAN)
2. **Stripe payment links.** Paid tiers are intentionally NOT purchasable today. When validation justifies billing:
   - Create Stripe Payment Links for Pro/Team → put URLs in `site/config.json` under a new `payments` key → I wire the checkout UI and flip copy from "planned" to "available".
   - No credentials need to be shared with me; you paste link URLs into config and push.

## Priority 3 — email
3. **Email capture endpoint** (Formspree/Resend form or similar, free tiers OK):
   - Put the POST URL in `site/config.json` → `forms.newsletter_endpoint`.
   - Until set, the site deliberately shows NO signup form (it refuses to collect addresses it cannot store) — RSS works instead.
4. **Email sending key** (Resend or similar) if/when weekly digest should arrive by email rather than RSS.

## Priority 4 — optional
5. **Analytics** (privacy-friendly): create Plausible/GoatCounter account → put script URL in `site/config.json` → `analytics_script`. Or use GitHub's built-in repo traffic insights (free, zero code).
6. **Approve launch posts** (drafts in `marketing/LAUNCH_PLAN.md`) — posting through your personal accounts needs your explicit OK per ground rules.
7. Enable "Send notifications for failed workflows" in your GitHub notification settings so degraded monitor runs reach your inbox.

## Removed / corrected from previous version of this file
- ~~`docs/APP_SCHEMA.sql`~~ — never existed; there is no database yet. Accounts/watchlists are planned features, not partially built.
- ~~`site/config/payments.json`~~ — wrong path; real wiring point is `site/config.json`.
- Supabase item removed: no app tier exists today; it would be created fresh when paid alerting is actually built.
