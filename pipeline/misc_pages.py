"""Static informational pages for ModelSignal. All internal links go through u()."""
import html
import json
import os


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def build_all(write, page, CFG, stats, changes, vendors, u):
    # ---------- pricing ----------
    endpoint = (CFG.get("forms") or {}).get("newsletter_endpoint")
    body = f"""
<h1>Pricing</h1>
<p class="sub">The public database is free. Paid tiers are <b>planned, not yet available</b> — nothing below can be purchased today, and we won't pretend otherwise.</p>

<h2>Available now — free</h2>
<div class="plans"><div class="plan featured">
<h3>Public database</h3><p class="price">$0</p>
<ul>
<li>Change feed with evidence pages (old/new values + official source links)</li>
<li>Per-vendor pricing &amp; limits history pages</li>
<li>RSS feed of all detected changes</li>
<li>LLM cost calculator using live-extracted published rates ({stats.get("calculator_models", "?")} models)</li>
<li>Weekly digest archive (auto-generated)</li>
<li>Honest per-source health reporting</li>
</ul>
<p><a class="big" href="{u('changes/')}">Use it now</a></p>
</div></div>

<h2>Planned paid tiers — not yet purchasable</h2>
<p class="fine">These require owner infrastructure work tracked in OWNER_ACTIONS.md. Proposed prices; they may change before launch.</p>
<div class="plans">
<div class="plan">
<h3>Pro <span class="fine">(planned · proposed $15/mo)</span></h3>
<ul>
<li>Email alerts on material changes for a personal watchlist</li>
<li>Saved usage assumptions feeding impact estimates</li>
<li>CSV/JSON export of change history</li>
<li>Digest by email</li>
</ul>
</div>
<div class="plan">
<h3>Team <span class="fine">(planned · proposed $49/mo)</span></h3>
<ul>
<li>Everything in Pro</li>
<li>Shared watchlists, up to 10 teammates</li>
<li>Slack + webhook notifications</li>
<li>Bulk/API access to verified records</li>
</ul>
</div>
</div>

<h2>{"Get notified when paid tiers launch" if endpoint else "Email signup is not available yet"}</h2>
{f'''<form class="signup" action="{esc(endpoint)}" method="post">
<input type="email" name="email" placeholder="you@company.com" required>
<button type="submit">Notify me</button>
</form><p class="fine">Used only to notify you once when paid tiers launch.</p>''' if endpoint else
f'''<p>We have not connected an email-capture service yet, so there is no signup form here — we won't collect addresses we can't safely store or use. Meanwhile:</p>
<ul>
<li>Subscribe to the <a href="{u('feed.xml')}">RSS feed</a> for every detected change</li>
<li>Watch the <a href="{esc(CFG.get("repo_url", "#"))}">public repo</a> for launch announcements</li>
</ul>'''}"""
    write("pricing/index.html", page(
        "Pricing — free database now; paid tiers planned",
        "ModelSignal pricing: the change database, history pages, RSS and calculator are free now. Pro ($15/mo) and Team ($49/mo) alerting is planned and not yet purchasable.",
        body, "pricing/index.html"))

    # ---------- methodology ----------
    body = f"""
<h1>Methodology</h1>
<p>Trust is the product. Here is exactly how facts get onto this site — and what we refuse to do.</p>
<h2>1. Sources</h2>
<p>We monitor official surfaces only: pricing documentation, rate-limit docs, changelogs, release notes, official RSS feeds and public model-catalog APIs. The full source list and its health is published at <a href="{u('status/')}">/status</a>.</p>
<p><b>Vendors vs sources:</b> a vendor is “actively monitored” only if at least one of its primary pricing/limits sources is being polled and diffed. Vendors where we relay announcements only are labeled as such everywhere — their names never appear in our monitored-vendor counts. Vendors whose pages render only via JavaScript (no working monitor) are excluded until a browser-based runner ships.</p>
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
<p>Summaries are generated from templates using only extracted fields. The public calculator performs arithmetic over published rates and is labeled as an estimate. We do not currently offer personalized impact calculations tied to your account — that requires the (unbuilt) accounts layer, and product copy says so.</p>
<h2>6. Publication guard</h2>
<p>Records from non-official hosts (example.com, localhost, etc.) or unregistered test sources are rejected by the pipeline and filtered again at site-build time. Test fixtures physically cannot reach production data paths.</p>
<h2>7. Corrections</h2>
<p>If we got something wrong, tell us: see <a href="{u('about/')}">about/contact</a>. Corrections are applied to the record and noted on the change detail page.</p>"""
    write("methodology/index.html", page(
        "Methodology — how ModelSignal detects and verifies changes",
        "How snapshots, deterministic diffs, materiality filters, confidence labels and the publication guard keep ModelSignal facts trustworthy.",
        body, "methodology/index.html"))

    # ---------- faq ----------
    faqs = [
        ("Is this just another page-diff tool?",
         "No. Generic monitors stop at “this page changed”. We extract structured values (per-model prices, allowances, quotas), keep old/new pairs, filter noise, corroborate against announcements, and publish a permanent, sourced record."),
        ("Where does the data come from?",
         "Official sources only: vendor pricing docs, rate-limit pages, changelogs, release notes and public APIs. Every published fact links to its exact source and archived snapshot."),
        ("Which vendors are actively monitored versus not?",
         "The <a href='/vendors-x'>vendor directory</a> states this per vendor. “Active monitor” = we diff its official pricing/limits surfaces. “Announcements only” = we relay official posts but don't diff pricing pages yet. Vendors without a working monitor aren't listed."),
        ("Do you offer email alerts today?",
         "No. Email alerting is a planned paid feature and does not exist yet. Today you can follow every change via RSS."),
        ("Can I pay for anything right now?",
         "No. Checkout is intentionally disabled until payment infrastructure exists. See <a href='/pricing-x'>pricing</a> for what's real today versus planned."),
        ("What do the confidence labels mean?",
         "<b>detected</b>: observed directly via snapshot diff. <b>verified</b>: also matched to an official vendor announcement. Details in <a href='/methodology-x'>methodology</a>."),
        ("Will you spam me?",
         "No. Alerts (when they exist) fire only on material, filtered changes. Trivial diffs never leave the pipeline."),
        ("How accurate are the calculators?",
         "They use published per-million-token rates extracted verbatim from official pages, updated automatically when those pages change. Your provider's actual billing (caching, batching, tiers) may differ — estimates only."),
    ]
    body = "<h1>FAQ</h1>" + "".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    body = (body.replace("/vendors-x", u("vendors/"))
                .replace("/pricing-x", u("pricing/"))
                .replace("/methodology-x", u("methodology/")))
    write("faq/index.html", page("FAQ — ModelSignal",
          "Frequently asked questions about data sources, accuracy, what exists today versus planned.",
          body, "faq/index.html"))

    # ---------- about / contact ----------
    body = f"""
<h1>About ModelSignal</h1>
<p>ModelSignal is a small bootstrapped project with one job: notice when AI and developer-tool vendors change something that affects your bill or your architecture — and record it clearly, with evidence.</p>
<p><b>Contact:</b> {CFG.get("contact_email", "")} · or open an issue on our <a href="{esc(CFG.get("repo_url", "#"))}">public repo</a>.</p>
<h2>Principles</h2>
<ul>
<li>Every fact links to an official source.</li>
<li>Never publish an inferred number as a fact.</li>
<li>Show detected vs verified honestly — and say plainly which vendors we do and don't monitor.</li>
<li>Never sell what doesn't exist: planned features are labeled planned.</li>
</ul>"""
    write("about/index.html", page("About & contact — ModelSignal",
          "Who builds ModelSignal and how to reach us.",
          body, "about/index.html"))

    # ---------- status ----------
    try:
        health = json.load(open(os.path.join(CFG["_site_data"], "source_health.json")))
    except (KeyError, OSError, json.JSONDecodeError):
        health = []
    errors = [s for s in health if s.get("last_error")]
    banner = ('<div class="notice"><b>Some sources are currently failing.</b> Their data may be stale; '
              'all other sources continue independently.</div>') if errors else ""
    def _badge(sv):
        if sv == "ok":
            return '<span class="badge v">ok</span>'
        return f'<span class="badge d">{esc(sv)}</span>'

    rows = "".join(
        f"<tr><td>{esc(s['id'])}</td><td>{esc(str(s['vendor']))}</td>"
        f"<td>{_badge(s['status'])}</td>"
        f"<td>{esc((s.get('last_checked') or '—')[:16])}</td>"
        f"<td>{esc((s.get('last_error') or '—')[:120])}</td></tr>"
        for s in health)
    body = f"""
<h1>Source status</h1>
{banner}
<p>Honest health of every registered source. An error here means our view of that vendor may be delayed — errors clear automatically after the next successful run for that source, and are never hidden.</p>
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
        md = html.escape(d["markdown"])
        digest = f"<div class='digest'><pre>{md}</pre></div>"
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    if endpoint:
        form = (f'<form class="signup" action="{esc(endpoint)}" method="post">'
                '<input type="email" name="email" placeholder="you@company.com" required>'
                '<button type="submit">Subscribe</button></form>')
    else:
        form = (f'<p class="notice">Email delivery is not connected yet, so there is nothing to subscribe to — '
                f'we won\u2019t put up a form that goes nowhere. The same content is available via '
                f'<a href="{u("feed.xml")}">RSS</a>, and the latest edition is archived below (updated automatically).</p>')
    body = f"""
<h1>This Week in AI Pricing &amp; Limits</h1>
<p class="sub">The few changes developers actually need to know, each linked to its official source. No rumors, no filler.</p>
{form}
<h2>Latest edition (auto-generated)</h2>
{digest}"""
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
announcement corroborates it. Show old value, new value, who's affected, and — where rates allow — arithmetic
over published prices, with the math shown.</p>
<p>This site is the product's public half: a free, growing, sourced record of what AI vendors change.
Fast, personalized alerting is planned as a paid tier and does not exist yet — we'd rather show you the free
database and let it speak.</p>
<p class="fine">Built transparently as a bootstrapped experiment. Feedback welcome via the repo.</p>"""),
    ]
    write("blog/index.html", page("Blog — ModelSignal",
          "Analysis and notes on AI vendor pricing, limits and model changes.",
          "<h1>Blog</h1><ul class='plist'>" + "".join(
              f"<li><a href='{u('blog/' + slug + '/')}'>{esc(title)}</a><br><span class='fine'>ModelSignal team</span></li>"
              for slug, title, _ in posts) + "</ul>", "blog/index.html"))
    for slug, title, content in posts:
        write(f"blog/{slug}/index.html", page(title, title[:150],
              f"<p><a href='{u('blog/')}'>← Blog</a></p><article><h1>{esc(title)}</h1>{content}</article>",
              f"blog/{slug}/index.html"))

    # ---------- legal ----------
    year = CFG.get("year", "2026")
    privacy = f"""
<h1>Privacy Policy</h1><p>Last updated: {year}-08-23</p>
<ul>
<li><b>Public visitors:</b> this site sets no advertising or cross-site tracking cookies and loads no third-party analytics scripts. Server access logs are retained briefly for security and debugging.</li>
<li><b>Subscribers:</b> we do not currently collect email addresses. When email features launch, we will store your address solely to send what you requested, with one-click unsubscribe.</li>
<li><b>Customers:</b> there is no purchasing today. When payments launch they will be processed by Stripe; card numbers will never touch our systems.</li>
<li><b>Data:</b> monitored-source snapshots are public web pages. Any future watchlist/saved-model data will belong to you and be deleted within 30 days of account deletion on request.</li>
<li><b>Contact:</b> {CFG.get('contact_email', '')}</li>
</ul>"""
    terms = f"""
<h1>Terms of Service</h1><p>Last updated: {year}-08-23</p>
<ol>
<li><b>Service.</b> ModelSignal monitors third-party public web pages and reports observed changes with automated interpretation, free of charge today. We strive for accuracy but provide the service “as is”, without warranty.</li>
<li><b>Not advice.</b> Outputs are informational; estimates are approximations based on published rates and your own inputs. Verify anything business-critical against the linked official sources.</li>
<li><b>Paid tiers.</b> Do not exist yet. If/when launched, these terms will be updated 14 days beforehand and billing terms will appear here.</li>
<li><b>Acceptable use.</b> Don't scrape the site abusively or use the service unlawfully.</li>
<li><b>Liability.</b> To the maximum extent permitted by law, our aggregate liability is limited to fees paid in the prior 3 months (currently zero).</li>
<li><b>Changes.</b> Material changes to these terms will be announced on this page 14 days before taking effect.</li>
</ol>"""
    write("privacy/index.html", page("Privacy Policy — ModelSignal",
          "Privacy policy: minimal data collection, no ad tracking, no email collected at present.",
          privacy, "privacy/index.html"))
    write("terms/index.html", page("Terms of Service — ModelSignal",
          "Terms of service.",
          terms, "terms/index.html"))

    # 404
    write("404.html", page("Page not found — ModelSignal", "Not found",
          f"<h1>404</h1><p>That page doesn't exist. Try the <a href='{u('changes/')}'>change feed</a>.",
          "404.html"))
