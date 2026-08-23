"""Static informational pages for ModelSignal."""
import json, os


def build_all(write, page, CFG, stats, changes, vendors):
    URL = CFG["site_url"].rstrip("/")

    # ---------- pricing ----------
    payments = CFG.get("payments", {})
    live = bool(payments.get("pro_price_id") and payments.get("team_price_id"))
    pro_href = f"https://buy.stripe.com/{payments.get('pro_payment_link', '')}" if live else "#waitlist"
    team_href = f"https://buy.stripe.com/{payments.get('team_payment_link', '')}" if live else "#waitlist"
    mode_note = "" if live else """
    <div class="notice">Checkout is being activated right now — while payment goes live you can join the
    founding-customer list below and we'll honor these prices at launch.</div>"""
    body = f"""
<h1>Pricing</h1>
<p class="sub">The public database is free forever. Paid plans are for people who need to know <i>fast</i> and know <i>what it means</i>.</p>
{mode_note}
<div class="plans">
<div class="plan">
<h3>Free</h3><p class="price">$0</p>
<ul>
<li>Public change feed &amp; vendor history pages</li>
<li>RSS feed of all detected changes</li>
<li>LLM cost calculator</li>
<li>Weekly digest archive</li>
</ul>
<p><a class="ghost" href="/changes/">Use the feed</a></p>
</div>
<div class="plan featured">
<h3>Pro</h3><p class="price">$15<span>/mo</span></p>
<ul>
<li>Watch up to 15 vendor/product combinations</li>
<li>Email alerts on material changes (instant)</li>
<li>Impact estimates tuned to your usage inputs</li>
<li>Full change history &amp; export (CSV/JSON)</li>
<li>Weekly digest by email</li>
</ul>
<p><a class="big" href="{pro_href}">{"Start Pro" if live else "Join the founding list"}</a></p>
</div>
<div class="plan">
<h3>Team</h3><p class="price">$49<span>/mo</span></p>
<ul>
<li>Everything in Pro</li>
<li>Up to 10 teammates, shared watchlists</li>
<li>Slack + webhook notifications</li>
<li>Saved impact models per workload</li>
<li>Priority verification queue</li>
</ul>
<p><a class="ghost" href="{team_href}">{"Start Team" if live else "Join the founding list"}</a></p>
</div>
</div>
<h2 id="waitlist">Founding-customer list</h2>
<p>No spam — one email when checkout opens, and early access to alerts.</p>
<form class="signup" action="{CFG.get("forms", {}).get("newsletter_endpoint") or "https://forms.gle/placeholder"}" method="post">
<input type="email" name="email" placeholder="you@company.com" required>
<button type="submit">Notify me</button>
</form>
<p class="fine">Prices in USD. Cancel anytime. 14-day refund, no questions asked.</p>"""
    write("pricing/index.html", page(
        "Pricing — free database, paid peace of mind",
        "ModelSignal pricing: free public change feed; Pro $15/mo instant alerts and impact estimates; Team $49/mo Slack, webhooks and shared watchlists.",
        body, "pricing/index.html"))

    # ---------- methodology ----------
    body = """
<h1>Methodology</h1>
<p>Trust is the product. Here is exactly how facts get onto this site.</p>
<h2>1. Sources</h2>
<p>We monitor official surfaces only: pricing documentation, rate-limit docs, changelogs, release notes, official RSS feeds and public model-catalog APIs. The full source list and its health is published at <a href="/status/">/status</a>.</p>
<h2>2. Snapshots &amp; diffing</h2>
<p>Each run fetches every source, normalizes it deterministically, and archives an immutable snapshot. Structured parsers extract records (model → field → value). Changes are computed as field-level diffs between consecutive parses — not fuzzy text comparisons.</p>
<h2>3. Materiality filter</h2>
<p>A diff is published only if it touches money or capability: prices, rate limits, quotas, credits, context windows, plan entitlements, model availability/deprecation. Navigation churn, layout shifts and boilerplate are discarded.</p>
<h2>4. Confidence labels</h2>
<ul>
<li><b>detected</b> — we observed this exact difference between two snapshots of an official page. Old and new values are shown verbatim from those snapshots.</li>
<li><b>verified</b> — additionally corroborated by an official announcement from the same vendor within a matching time window; the announcement link is shown.</li>
<li><b>inferred</b> — never auto-published. If we cannot show evidence, we don't publish the claim.</li>
</ul>
<h2>5. Explanations &amp; impact</h2>
<p>Summaries are generated from templates using only extracted fields. Impact estimates are arithmetic over published rates and clearly labeled as estimates; we never guess missing prices.</p>
<h2>6. Corrections</h2>
<p>If we got something wrong, tell us: see <a href="/about/">about/contact</a>. Corrections are applied to the record and noted on the change detail page.</p>"""
    write("methodology/index.html", page(
        "Methodology — how ModelSignal detects and verifies changes",
        "How snapshots, deterministic diffs, materiality filters and confidence labels keep ModelSignal facts trustworthy.",
        body, "methodology/index.html"))

    # ---------- faq ----------
    faqs = [
        ("Is this just another page-diff tool?",
         "No. Generic monitors stop at “the page changed”. We extract structured values (per-model prices, allowances, quotas), keep old/new pairs, filter noise, corroborate against announcements, and compute cost impact."),
        ("Where does the data come from?",
         "Official sources only: vendor pricing docs, rate-limit pages, changelogs, release notes and public APIs. Every published fact links to its exact source and archived snapshot."),
        ("What do the confidence labels mean?",
         "<b>detected</b>: observed directly via snapshot diff. <b>verified</b>: also matched to an official vendor announcement. Details in <a href='/methodology/'>methodology</a>."),
        ("Do you cover my vendor?",
         "Coverage grows from demand + source quality, not a fixed list. If a vendor matters to your stack, request it — the strongest requests get built first."),
        ("How fast are alerts?",
         "Sources are polled every 6 hours; verified material changes trigger email/webhook dispatch within minutes of detection. Free readers can use RSS."),
        ("Will you spam me?",
         "No. Alerts fire only on material, filtered changes. Trivial diffs never leave the pipeline."),
        ("Can I use the data?",
         "The public feed is available via RSS with attribution. Bulk/API access ships with Team."),
        ("How much would this have helped historically?",
         "See any vendor history page — e.g., Copilot premium-request allowance tables or Gemini scheduled price steps. Those are exactly the silent changes people miss."),
    ]
    body = "<h1>FAQ</h1>" + "".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    write("faq/index.html", page("FAQ — ModelSignal",
          "Frequently asked questions about data sources, accuracy, alerting and coverage.",
          body, "faq/index.html"))

    # ---------- about / contact ----------
    body = f"""
<h1>About ModelSignal</h1>
<p>ModelSignal is a small bootstrapped product with one job: notice when AI and developer-tool vendors change something that affects your bill or your architecture — and tell you clearly, with evidence.</p>
<p><b>Contact:</b> {CFG.get("contact_email", "hello@modelsignal.dev")} · or open an issue on our <a href="{CFG.get('repo_url', '#')}">public repo</a>.</p>
<h2>Principles</h2>
<ul>
<li>Every fact links to an official source.</li>
<li>Never publish an inferred number as a fact.</li>
<li>Show detected vs verified honestly.</li>
<li>The monitoring runs itself; humans verify, they don't babysit.</li>
</ul>"""
    write("about/index.html", page("About & contact — ModelSignal",
          "Who builds ModelSignal and how to reach us.",
          body, "about/index.html"))

    # ---------- status ----------
    sh = json.load(open(os.path.join(os.path.dirname(write.__code__.co_filename), "..", "site", "data", "source_health.json"))) if False else None
    try:
        health = json.load(open(os.path.join(CFG["_site_data"], "source_health.json")))
    except (KeyError, OSError, json.JSONDecodeError):
        health = []
    rows = "".join(
        f"<tr><td>{esc(s['id'])}</td><td>{esc(str(s['vendor']))}</td>"
        f"<td><span class='badge {'v' if s['status']=='ok' else 'd'}'>{esc(s['status'])}</span></td>"
        f"<td>{esc((s.get('last_checked') or '—')[:16])}</td>"
        f"<td>{esc((s.get('last_error') or '—')[:120])}</td></tr>"
        for s in health)
    body = f"""
<h1>Source status</h1>
<p>Honest health of every monitored source. Errors here mean our view of that vendor may be delayed — we surface them rather than hide them.</p>
<div class="twrap"><table>
<tr><th>Source</th><th>Vendor</th><th>Status</th><th>Last checked (UTC)</th><th>Last error</th></tr>
{rows}
</table></div>"""
    write("status/index.html", page("Source status — ModelSignal monitors",
          "Operational health of every official source ModelSignal monitors.",
          body, "status/index.html"))

    # ---------- newsletter ----------
    digest = ""
    try:
        dpath = os.path.join(CFG["_site_data"], "digest_latest.json")
        d = json.load(open(dpath))
        import html as _h
        md = _h.escape(d["markdown"])
        digest = f"<div class='digest'><pre>{md}</pre></div>"
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    endpoint = CFG.get("forms", {}).get("newsletter_endpoint")
    form = (f'<form class="signup" action="{endpoint}" method="post">'
            '<input type="email" name="email" placeholder="you@company.com" required>'
            '<button type="submit">Subscribe</button></form>') if endpoint else \
           '<p class="notice">Email delivery is being connected — meanwhile the full feed is available via <a href="/feed.xml">RSS</a> and the archive below updates automatically.</p>'
    body = f"""
<h1>This Week in AI Pricing &amp; Limits</h1>
<p class="sub">One email a week: the few changes developers actually need to know, each linked to its official source. No rumors, no filler.</p>
{form}
<h2>Latest edition (auto-generated)</h2>
{digest}
<p class="fine">Past editions are archived in the public repo and linked from the blog.</p>"""
    write("newsletter/index.html", page("This Week in AI Pricing & Limits",
          "Weekly digest of AI vendor pricing, limit and deprecation changes — sourced and short.",
          body, "newsletter/index.html"))

    # ---------- blog ----------
    posts = [
        ("we-started-recording-what-ai-vendors-change",
         "AI developer tools keep changing their pricing. We started recording it.",
         """<p>In 2025–2026, nearly every major AI vendor changed something material: Cursor moved frontier-model
usage to metered billing and had to publicly clarify it after backlash; GitHub introduced “premium request”
metering for Copilot and users found surprise charges; Anthropic added weekly rate caps; DeepSeek warned of a
significant price rise; Gemini published scheduled price steps (“$0.375 through December 31, 2026, $0.75 starting
January 1, 2027”) inside a pricing table most people will never re-read.</p>
<p>The pattern is always the same: the change lands in a doc page, a changelog entry or a pricing table.
The people affected find out from a tweet — or a bill.</p>
<p>We built ModelSignal because the existing options fail in predictable ways: generic page-monitors say
“this page changed” and drown you in noise; price-comparison sites show today's snapshot with no memory;
enterprise AI-data platforms cost hundreds of dollars per seat.</p>
<p>Our approach is boring on purpose. Poll official pages. Snapshot everything. Diff structured fields,
not pixels. Publish only what touches money or capability. Label everything <i>detected</i> until an official
announcement corroborates it. Show old value, new value, who's affected, and — where rates allow — what it
means in dollars, with the math shown.</p>
<p>This site is the product's public half: a free, growing, sourced record of what AI vendors change.
The paid half is knowing quickly, with impact estimates for <i>your</i> workloads.</p>
<p class="fine">Built transparently as a bootstrapped experiment. Feedback welcome via the repo.</p>"""),
    ]
    write("blog/index.html", page("Blog — ModelSignal",
          "Analysis and notes on AI vendor pricing, limits and model changes.",
          "<h1>Blog</h1><ul class='plist'>" + "".join(
              f"<li><a href='/blog/{slug}/'>{esc(title)}</a><br><span class='fine'>ModelSignal team</span></li>"
              for slug, title, _ in posts) + "</ul>", "blog/index.html"))
    for slug, title, content in posts:
        write(f"blog/{slug}/index.html", page(title, title[:150],
              f"<p><a href='/blog/'>← Blog</a></p><article><h1>{esc(title)}</h1>{content}</article>",
              f"blog/{slug}/index.html"))

    # ---------- legal ----------
    year = CFG.get("year", "2026")
    privacy = f"""
<h1>Privacy Policy</h1><p>Last updated: {year}-08-22</p>
<ul>
<li><b>Public visitors:</b> this site sets no advertising or cross-site tracking cookies and loads no third-party analytics scripts. Server access logs are retained briefly for security and debugging.</li>
<li><b>Subscribers:</b> we store your email address solely to send the digest/alerts you requested. Every email includes one-click unsubscribe; unsubscribing deletes the address from active lists.</li>
<li><b>Customers:</b> payments are processed by Stripe. We never see or store card numbers. We store account email, plan, and notification preferences.</li>
<li><b>Data:</b> monitored-source snapshots are public web pages. Watchlists and saved impact models belong to you and are deleted within 30 days of account deletion on request.</li>
<li><b>Contact:</b> {CFG.get('contact_email', 'hello@modelsignal.dev')}</li>
</ul>"""
    terms = f"""
<h1>Terms of Service</h1><p>Last updated: {year}-08-22</p>
<ol>
<li><b>Service.</b> ModelSignal monitors third-party public web pages and reports observed changes with automated interpretation. We strive for accuracy but provide the service “as is”, without warranty.</li>
<li><b>Not advice.</b> Outputs are informational; estimates are approximations based on published rates and your own inputs. Verify anything business-critical against the linked official sources.</li>
<li><b>Your accounts.</b> Keep credentials safe; you're responsible for activity under your account.</li>
<li><b>Acceptable use.</b> Don't scrape the paid API abusively, resell raw feeds without agreement, or use the service unlawfully.</li>
<li><b>Billing.</b> Paid plans renew monthly until cancelled; cancel anytime takes effect at period end. 14-day refunds on request.</li>
<li><b>Liability.</b> To the maximum extent permitted by law, our aggregate liability is limited to fees paid in the prior 3 months.</li>
<li><b>Changes.</b> Material changes to these terms will be announced by email and on this page 14 days before taking effect.</li>
</ol>"""
    write("privacy/index.html", page("Privacy Policy — ModelSignal",
          "Privacy policy: minimal data collection, no ad tracking.",
          privacy, "privacy/index.html"))
    write("terms/index.html", page("Terms of Service — ModelSignal",
          "Terms of service.",
          terms, "terms/index.html"))

    # 404
    write("404.html", page("Page not found — ModelSignal", "Not found",
          "<h1>404</h1><p>That page doesn't exist. Try the <a href='/changes/'>change feed</a>.",
          "404.html"))


def esc(s):
    import html as h
    return h.escape(str(s if s is not None else ""), quote=True)
