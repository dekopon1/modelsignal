# OWNER ACTIONS

Actions that require your identity/credentials/authorization. Everything else runs autonomously.

## Required to go live on a real domain
1. **Domain**: purchase (suggestions: `modelsignal.dev`, `modelsignal.io` — verify availability/trademark first). Then add a CNAME record for the GitHub Pages URL (documented in OPERATIONS.md once repo is live). Cost: ~$10–15/yr.

## Required to charge money
2. **Stripe account** → create, then set `STRIPE_PUBLISHABLE_KEY` + create two Products/Prices ($15/mo Pro, $49/mo Team) and put the Price IDs into `site/config/payments.json`. Checkout buttons are already wired and will switch from waitlist-mode to live-mode automatically.

## Required to send email
3. **Resend (or similar) API key** → enables weekly digest sending + alert emails. Until then the newsletter is generated weekly as RSS + archive page (fully functional, just not emailed).
4. **Formspree (or similar) form ID** → enables newsletter/waitlist signup capture on the static site. Until then, signup buttons link to the RSS feed and a mailto contact.

## Required for full app tier (accounts, watchlists, saved alerts)
5. **Supabase project** (free tier OK) → database + auth. Schema provided in `docs/APP_SCHEMA.sql` (created during build). Until then, the paid-tier UX is stubbed honestly ("coming soon") and the public database + RSS + calculators are live.

## Optional
6. Confirm/reject product name before domain purchase (see DECISIONS.md D5).
7. Approve launch posts (drafts in marketing/LAUNCH_PLAN.md) — posting through your personal accounts needs your explicit OK per ground rules.
8. **Analytics**: the site ships with zero tracking (privacy policy promises this). If you want conversion metrics, create a Plausible/GoatCounter account and put the script URL in `site/config.json` → `analytics_script`; the generator will wire it in. Alternatively enable GitHub's traffic insights (free, repo-level, no code).
