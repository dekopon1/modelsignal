# OPERATIONS

## What runs automatically (zero human involvement)

| Process | Mechanism | Frequency | Notes |
|---|---|---|---|
| Source monitoring | `.github/workflows/monitor.yml` cron | every 6h | 12 official sources; per-source failures recorded in `data/state.json` and surfaced on `/status` — never silently dropped |
| Change detection → publication | same workflow | every 6h | deterministic diffs + materiality filter; idempotent (no duplicate records) |
| Verification | `pipeline/verify.py` | every run | corroborates against official announcements; upgrades `detected`→`verified` |
| Site rebuild + deploy | same workflow (chained) | after every monitor run | GITHUB_TOKEN pushes don't trigger workflows, so deploy is invoked directly in-workflow |
| Weekly digest generation | `pipeline/newsletter.py` | weekly (inside monitor run) | writes `marketing/digests/YYYY-Wnn.md` + `/newsletter` page content; idempotent per ISO week |
| RSS feed / sitemap / robots | `pipeline/ssg.py` | every deploy | derived from real change data |
| Evidence trail | git | every run | raw gzipped snapshots + parsed records committed; every published change links its snapshot |
| Backups | git itself | every run | full history on GitHub |

## What still requires a human (< 1h/week)

1. **Weekly skim (≈10 min):** glance at `/status` + the digest. If a source has been failing >48h, check whether the vendor moved the page (update URL in `pipeline/sources.json`).
2. **Verification promotions (≈5 min/day at most):** `detected` items are published with the `detected` label. Optionally promote to `verified` after eyeballing the source; the automated corroboration does most of this.
3. **Billing & email** (once wired): Stripe handles payments/cancellations automatically; Resend sends digests. Only exceptions escalate.
4. **Launch posts** (one-time): see `marketing/LAUNCH_PLAN.md` — needs owner approval to post from personal accounts.

## Failure handling (automated)

- **Fetch failure:** 3 retries with backoff → error recorded in state → shown on `/status` → step summary warning in the Actions run. Monitoring of other sources unaffected.
- **Parser breakage (vendor changes HTML):** structured diff returns empty/odd records → change detection simply finds nothing until fixed; site keeps serving last known-good data. The `/status` page + digest absence make this visible.
- **Whole-workflow failure:** run shows red on GitHub Actions. (Email/Slack alert on workflow failure requires owner's notification prefs — enable "Send notifications for failed workflows" in GitHub settings, one-time.)
- **False-positive control:** materiality keyword filter + numeric-equality suppression + cosmetic-noise regex; measured via tests. Kill criterion: >50% noise rate over 30 days (see SCORECARD).

## Adding a vendor/source

1. Append entry to `pipeline/sources.json` (pick parser: `markdown_tables`, `html_tables`, `rss`, `json_models`).
2. `python3 pipeline/monitor.py --source <id>` locally → confirms baseline capture.
3. Commit. Next cron run diffs against the baseline automatically.
4. JS-only pages need a Playwright runner (deliberately deferred — see DECISIONS.md).

## Manual runbook

```bash
python3 pipeline/monitor.py            # full poll
python3 pipeline/monitor.py --source anthropic-pricing
python3 pipeline/verify.py             # corroboration pass
python3 pipeline/build_site_data.py    # refresh site JSON
python3 pipeline/newsletter.py --force # regenerate this week's digest
python3 pipeline/ssg.py                # rebuild site into site/dist
python3 -m unittest discover -s pipeline/tests -v
gh workflow run monitor.yml            # force a production cycle
```

## Cost structure

GitHub Actions + Pages on a public repo: **$0/month**. Domain (~$12/yr) + Stripe fees (2.9% + 30¢) + Resend free tier (3k emails/mo) when wired. Gross margin at first paying customer ≈ 97%.
