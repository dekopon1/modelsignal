#!/usr/bin/env python3
"""ModelSignal static site generator. Reads site/data/*.json -> writes HTML into site/dist.

Zero dependencies. Deterministic output. All numbers on pages come from extracted data.
"""
import html as H
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(ROOT), "site")
DATA = os.path.join(SITE, "data")
DIST = os.path.join(SITE, "dist")

CFG = json.load(open(os.path.join(SITE, "config.json"), encoding="utf-8"))
URL = CFG["site_url"].rstrip("/")


def u(path: str) -> str:
    """Base-path-aware internal URL. ALL internal links must go through this."""
    if path.startswith(("http://", "https://", "mailto:", "#")):
        return path
    return f"{URL}/{path.lstrip('/')}"


LAST_CALC_MODELS = 0


def esc(s):
    return H.escape(str(s if s is not None else ""), quote=True)


def load(name, default):
    p = os.path.join(DATA, name)
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def dt(iso):
    return (iso or "")[:10].replace("T", " ")


def write(path, content):
    full = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


ANALYTICS = CFG.get("analytics_script")


def page(title, desc, body, path, extra_head=""):
    canon = f"{URL}/{path}" if path != "index.html" else f"{URL}/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<link rel="alternate" type="application/rss+xml" title="ModelSignal — AI &amp; dev-tool change feed" href="{URL}/feed.xml">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="website">
<style>{CSS}</style>
{f'<script defer src="{esc(ANALYTICS)}"></script>' if ANALYTICS else ''}
{extra_head}
</head>
<body>
<header class="top">
  <a class="brand" href="{u('/')}">Model<span>Signal</span></a>
  <nav>
    <a href="{u('changes/')}">Changes</a>
    <a href="{u('vendors/')}">Vendors</a>
    <a href="{u('calculators/llm-cost/')}">Calculator</a>
    <a href="{u('pricing/')}">Pricing</a>
    <a href="{u('blog/')}">Blog</a>
  </nav>
  <a class="cta" href="{u('pricing/')}">Free database &amp; pricing</a>
</header>
<main>
{body}
</main>
<footer>
  <div class="cols">
    <div><strong>ModelSignal</strong><br>We watch what AI &amp; dev-tool vendors change — prices, limits, models, plans — and tell you what it means.<br><a href="{u('feed.xml')}">RSS</a></div>
    <div>
      <a href="{u('changes/')}">Change feed</a><br>
      <a href="{u('vendors/')}">Vendor directory</a><br>
      <a href="{u('methodology/')}">Methodology &amp; accuracy</a><br>
      <a href="{u('faq/')}">FAQ</a>
    </div>
    <div>
      <a href="{u('calculators/llm-cost/')}">LLM cost calculator</a><br>
      <a href="{u('newsletter/')}">Newsletter</a><br>
      <a href="{esc(CFG.get("repo_url", "#"))}">Source &amp; issue tracker</a><br>
      <a href="{u('about/')}">About / contact</a>
    </div>
    <div>
      <a href="{u('privacy/')}">Privacy</a><br>
      <a href="{u('terms/')}">Terms</a><br>
      <a href="{u('status/')}">Source status</a>
    </div>
  </div>
  <p class="fine">Facts link to official sources. Estimates are labeled as estimates. © {CFG.get("year", "2026")} ModelSignal.</p>
</footer>
</body>
</html>"""


CONF_BADGE = {
    "verified": '<span class="badge v" title="Corroborated by an official announcement from the vendor">verified</span>',
    "detected": '<span class="badge d" title="Detected by diffing the official source page; not yet corroborated by an announcement">detected</span>',
}


def change_card(c, link=True):
    title = c.get("entity") or c.get("context") or "Change"
    inner = f"""
    <article class="card">
      <div class="meta"><strong>{esc(c.get("vendor_name"))}</strong> · {esc(c.get("product"))} · {esc(c.get("category"))} · {dt(c.get("detected_at"))} {CONF_BADGE.get(c.get('confidence'), '')}</div>
      <h3>{esc(title)}{" — " + esc(c["field"]) if c.get("field") else ""}</h3>
      {(f'<p class="summary">{esc(c.get("summary"))}</p>' if link else f'<p class="summary">{esc(c.get("summary"))}</p>')}
      {"<p class='ov'><del>" + esc(c.get("old_value")) + "</del> → <ins>" + esc(c.get("new_value")) + "</ins></p>" if c.get("old_value") or c.get("new_value") else ""}
    </article>"""
    if link:
        return f'<a class="plain" href="{u("changes/" + c["id"] + "/")}">{inner}</a>'
    return inner


def fmt_table(records, max_rows=40, max_cols=7):
    """records: {ctx: {key: {field: val}}} -> html sections."""
    out = []
    for ctx, tbl in list(records.items())[:12]:
        rows = [(k, v) for k, v in tbl.items() if isinstance(v, dict) and v]
        if not rows:
            continue
        cols = []
        for _, v in rows[:max_rows]:
            for c in v:
                if c not in cols:
                    cols.append(c)
            if len(cols) >= max_cols:
                break
        cols = cols[:max_cols]
        t = [f"<h4>{esc(ctx)}</h4>", "<div class='twrap'><table><tr><th></th>" +
             "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr>"]
        for k, v in rows[:max_rows]:
            t.append("<tr><th>" + esc(k) + "</th>" + "".join(
                f"<td>{esc(v.get(c, ''))}</td>" for c in cols) + "</tr>")
        t.append("</table></div>")
        out.append("\n".join(t))
    return "\n".join(out)


# ---------------- pages ----------------

def pg_index(stats, changes, vendors):
    recent = "".join(change_card(c) for c in changes[:6]) or \
             "<p>The first monitoring runs are establishing baselines. Changes will appear here as vendors make them.</p>"
    vend = " ".join(
        f'<a class="chip" href="{u("vendors/" + v["slug"] + "/")}">{esc(v["name"])}</a>'
        for v in vendors if v.get("status") == "active")
    ann_only = " ".join(esc(v["name"]) for v in vendors if v.get("status") == "announcements_only")
    body = f"""
<section class="hero">
  <h1>AI vendors change prices, limits and models constantly.<br><em>We record each change — and show what it may cost you.</em></h1>
  <p class="sub">ModelSignal polls {stats.get("active_sources", 0)} official sources across {stats.get("vendors_monitored", 0)} AI &amp; developer-tool vendors
  ({stats.get("vendors_announcements_only", 0)} more are announcements-only). When something material changes on a watched surface, you get the old value, the new value,
  and a link to the official source — never a vague “this page changed”.</p>
  <p class="cta-row"><a class="big" href="{u('changes/')}">Browse the live change feed</a> <a class="ghost" href="{u('calculators/llm-cost/')}">Try the cost calculator</a></p>
  <p class="fine">Free public database · No account needed · Paid alerting is planned, not yet available — see {esc('')}<a href="{u('pricing/')}">pricing</a> for exactly what exists today</p>
</section>
<section class="statsbar">
  <div><strong>{stats.get("vendors_monitored", 0)}</strong><span>vendors actively monitored</span></div>
  <div><strong>{stats.get("active_sources", 0)}</strong><span>official sources polled</span></div>
  <div><strong>{stats.get("total_changes", 0)}</strong><span>changes recorded</span></div>
  <div><strong>{stats.get("verified_changes", 0)}</strong><span>vendor-corroborated</span></div>
</section>
{f'<p class="fine">Announcement feeds only (no pricing-page monitors yet): {ann_only}.</p>' if ann_only else ''}
<section>
  <h2>Latest detected changes</h2>
  {recent}
  <p><a href="{u('changes/')}">See all changes →</a></p>
</section>
<section>
  <h2>Currently monitored</h2>
  <p>{vend} <span class="chip more">+ more added from verified demand</span></p>
</section>
<section class="how">
  <h2>How it works</h2>
  <ol>
    <li><strong>Poll.</strong> Official pricing/docs/changelog/API endpoints fetched on schedule. Raw snapshots archived.</li>
    <li><strong>Diff.</strong> Structured extraction per source (tables, model catalogs, feeds); deterministic field-level diffs. Cosmetic noise filtered.</li>
    <li><strong>Verify.</strong> Detected changes are corroborated against official announcements when possible — labeled <span class="badge v">verified</span>, otherwise shown as <span class="badge d">detected</span>.</li>
    <li><strong>Explain.</strong> Plain-English summaries and impact estimates computed only from published numbers, always linked to evidence.</li>
  </ol>
  <p><a href="{u('methodology/')}">Read the methodology →</a></p>
</section>"""
    return page("ModelSignal — Know what AI vendors change, before it costs you",
                "Monitoring and explained history of pricing, limits, quotas, deprecations and plan changes across OpenAI, Anthropic, Google Gemini, Cursor, Copilot and more.",
                body, "index.html")


def pg_changes(changes):
    items_json = json.dumps([{
        "id": c["id"], "vendor": c.get("vendor_name"), "cat": c.get("category"),
        "conf": c.get("confidence"), "date": dt(c.get("detected_at")),
        "sum": c.get("summary"), "ent": c.get("entity") or ""} for c in changes[:500]])
    items_json_safe = items_json.replace("</", "<\\/")
    body_head = f"""
<h1>Change feed</h1>
<p>Every material change our monitors detected on official vendor surfaces. <span class="badge v">verified</span> = corroborated by an official announcement. <span class="badge d">detected</span> = seen directly on the official page.</p>
<div class="filters">
  <input id="q" placeholder="Filter by text…" aria-label="Filter changes">
  <select id="vc" aria-label="Vendor"><option value="">All vendors</option></select>
  <select id="cc" aria-label="Category"><option value="">All categories</option></select>
</div>
<div id="feed"></div>
<script id="data" type="application/json">{items_json_safe}</script>
<script>""" + FEED_JS.replace("{BASE_JS}", json.dumps(URL + "/")) + """</script>"""
    return page("Change feed — every detected AI vendor change",
                "Live feed of pricing, limit, quota, model availability and plan changes across major AI and developer-tool vendors, with old/new values and sources.",
                body_head, "changes/index.html")


def pg_change_detail(c):
    corrob = ""
    if c.get("verification") and c["verification"].get("corroborated_by"):
        corrob = f"""<p><strong>Corroboration:</strong> <a rel="nofollow" href="{esc(c['verification']['corroborated_by'])}">{esc(c['verification'].get('corroboration_title') or 'official announcement')}</a>
        <span class="fine">({esc(c['verification'].get('method', ''))})</span></p>"""
    body = f"""
<p><a href="{u('changes/')}">← All changes</a></p>
<article class="detail">
<h1>{esc(c.get("vendor_name"))}: {esc(c.get("entity") or c.get("kind"))}{(" — " + esc(c["field"])) if c.get("field") else ""}</h1>
<div class="meta">{esc(c.get("product"))} · {esc(c.get("category"))} · detected {dt(c.get("detected_at"))} · {CONF_BADGE.get(c.get('confidence'), '')}</div>
<p class="summary big-summary">{esc(c.get("summary"))}</p>
<table class="kv">
<tr><th>Old value</th><td><del>{esc(c.get("old_value") or "—")}</del></td></tr>
<tr><th>New value</th><td><ins>{esc(c.get("new_value") or "—")}</ins></td></tr>
<tr><th>Section</th><td>{esc(c.get("context") or "—")}</td></tr>
<tr><th>Effective date</th><td>{esc(c.get("effective_date") or "Not stated on the source page")}</td></tr>
<tr><th>Who may be affected</th><td>{esc(AFFECTED.get(c.get("category"), "Users of this product."))}</td></tr>
<tr><th>Evidence</th><td><a rel="nofollow" href="{esc(c.get("source_url"))}">Official source page</a> (archived snapshot: <code>{esc(c.get("snapshot", ""))}</code>)</td></tr>
</table>
{corrob}
<p class="fine">Confidence: <b>{esc(c.get("confidence"))}</b>. “detected” means we observed this exact difference between two snapshots of the official page. It becomes “verified” when an official vendor announcement matches. We do not publish inferred or invented values.</p>
</article>"""
    return page(f"{c.get('vendor_name')}: {c.get('entity')} — {c.get('field') or c.get('category')} change",
                c.get("summary", "Vendor change detail"),
                body, f"changes/{c['id']}/index.html")


AFFECTED = {
    "pricing": "Teams paying API/subscription rates for this product — costs scale with your usage.",
    "limits": "Teams near usage ceilings — throttling, forced upgrades, or workflow interruptions.",
    "plans": "Subscribers evaluating plan value or renewals.",
    "changelog": "Anyone building on this platform.",
}


STATUS_LABEL = {"active": "Active monitor", "announcements_only": "Announcements only"}


def pg_vendors(vendors):
    rows = "".join(
        f"<tr><td><a href='{u('vendors/' + v['slug'] + '/')}'>{esc(v['name'])}</a></td>"
        f"<td>{STATUS_LABEL.get(v.get('status'), esc(v.get('status')))}</td>"
        f"<td>{len([s for s in v['sources'] if s])} sources</td>"
        f"<td>{'degraded' if v.get('degraded') else 'healthy'}</td>"
        f"<td>{dt(v.get('last_checked')) or 'pending'}</td></tr>"
        for v in vendors)
    body = f"""
<h1>Tracked vendors</h1>
<p><b>Active monitor</b> = we poll this vendor's official pricing/limits surfaces and diff them. <b>Announcements only</b> = we relay the vendor's official announcements, but do not yet diff its pricing pages (usually because they render only via JavaScript). We do not list vendors we cannot actually monitor.</p>
<div class="twrap"><table>
<tr><th>Vendor</th><th>Status</th><th>Sources</th><th>Health</th><th>Last checked (UTC)</th></tr>
{rows}
</table></div>"""
    return page("Tracked vendors — AI & developer tools",
                "Directory of vendors ModelSignal tracks: which have active pricing/limits monitors, which are announcements-only, and current health.",
                body, "vendors/index.html")


def pg_vendor(v, changes, anns, current_records=None):
    slug = v["slug"]
    if v.get("status") == "announcements_only":
        coverage = ("We currently relay this vendor's official announcements only. "
                    f"{esc(v['name'])}'s pricing pages render via JavaScript, so we do not yet diff them — "
                    "no pricing changes are published for this vendor until that monitor exists. "
                    "<b>Planned</b>, not active.")
    else:
        if v.get("degraded"):
            health_txt = f'degraded — see <a href="{u("status/")}">status</a>'
        else:
            health_txt = "ok"
        coverage = (f"{len(v['sources'])} official sources polled · "
                    f"last checked {dt(v.get('last_checked')) or 'pending'} UTC · monitor health: {health_txt}")
    if not changes and v.get("status") == "active":
        chg_html = "<p>No material changes detected yet. Baselines were captured on day one — any future change will appear here. Nothing is back-filled or invented.</p>"
    elif not changes:
        chg_html = "<p>No changes recorded — we do not yet run pricing monitors for this vendor (see status above).</p>"
    else:
        chg_html = "".join(change_card(c) for c in changes[:25])
    ann_html = ""
    va = [a for a in anns if a.get("vendor") == v["key"]][:12]
    if va:
        ann_html = "<h2>Official announcements we relayed</h2><ul class=" + '"anns"' + ">" + "".join(
            f'<li><a rel="nofollow" href="{esc(a["url"])}">{esc(a["title"])}</a> <span class="fine">{esc((a.get("published") or "")[:16])}</span></li>'
            for a in va) + "</ul>"
    cur_html = ""
    if current_records:
        cur_html = "<h2>Current published rates (extracted)</h2>" + fmt_table(current_records, max_rows=30)
        cur_html += "<p class=\"fine\">Extracted verbatim from official pages. Values are shown exactly as published; see source links on each change.</p>"
    body = f"""
<p><a href="{u('vendors/')}">← All vendors</a></p>
<h1>{esc(v["name"])} — changes &amp; pricing history</h1>
<p>{coverage}</p>
<h2>Recent changes</h2>
{chg_html}
{f'<p><a href="{u("vendors/" + slug + "/pricing-history/")}">Full pricing &amp; limits history →</a></p>' if v.get("status") == "active" else ''}
{cur_html}
{ann_html}"""
    return page(f"{v['name']} pricing & limits history",
                f"Every detected {v['name']} pricing, quota, limit and plan change with dates, old/new values and links to official sources.",
                body, f"vendors/{slug}/index.html")


def pg_vendor_history(v, changes):
    if v.get("status") != "active":
        chg_html = ("<p>No pricing-change history exists: we do not yet run pricing monitors for this vendor.</p>")
    elif not changes:
        chg_html = ("<p>No material changes detected yet. This page grows automatically as our monitors observe "
                    "changes on " + esc(v["name"]) + "'s official surfaces. Nothing here is back-filled or invented.</p>")
    else:
        parts = []
        for c in changes:
            parts.append(f"<h2>{dt(c.get('detected_at'))}</h2>")
            parts.append(change_card(c, link=False))
        chg_html = "\n".join(parts)
    body = f"""
<p><a href="{u('vendors/' + v["slug"] + '/')}">← {esc(v["name"])} overview</a></p>
<h1>{esc(v["name"])} — pricing &amp; limits history</h1>
<p>A chronological record of every material change observed on official {esc(v["name"])} surfaces since we started watching. Each entry links to the exact source and preserves old/new values.</p>
{chg_html}"""
    return page(f"{v['name']} pricing history — every change, dated and sourced",
                f"Complete history of {v['name']} pricing, rate-limit, quota and plan changes with evidence links.",
                body, f"vendors/{v['slug']}/pricing-history/index.html")


def pg_calculator(anthropic, openrouter, deepseek):
    models = {}
    # anthropic markdown tables: {ctx: {model: {col: val}}}
    for ctx, tbl in (anthropic or {}).items():
        if "model pricing" not in ctx.lower():
            continue
        for m, fields in tbl.items():
            inp = _rate(fields.get("Base Input Tokens") or fields.get("Input") or "")
            out = _rate(fields.get("Output Tokens") or fields.get("Output") or "")
            if inp and out and "retired" not in m.lower():
                models[f"Anthropic {m}"] = {"in": inp, "out": out,
                                            "src": "https://platform.claude.com/docs/en/about-claude/pricing"}
    or_models = (openrouter or {}).get("models", openrouter or {})
    if not isinstance(or_models, dict):
        or_models = {}
    for mid, fields in or_models.items():
        if not isinstance(fields, dict):
            continue
        try:
            i = float(fields.get("prompt_per_mtok", "0") or 0)
            o = float(fields.get("completion_per_mtok", "0") or 0)
        except ValueError:
            continue
        if i > 0 and o > 0 and i < 1000:
            models[f"OpenRouter {fields.get('name', mid)}"] = {
                "in": i, "out": o, "src": "https://openrouter.ai"}
    for ctx, tbl in (deepseek or {}).items():
        for row, fields in tbl.items():
            if "OUTPUT TOKENS" not in row.upper() or "MAX" in row.upper():
                continue
            for col, val in fields.items():
                r = _rate(val)
                if r:
                    models[f"DeepSeek {col} ({row.strip()})"] = {
                        "in": r * 0.5, "out": r,
                        "src": "https://api-docs.deepseek.com/quick_start/pricing"}
    global LAST_CALC_MODELS
    LAST_CALC_MODELS = len(models)
    payload = json.dumps(models)[:400000]
    payload_safe = payload.replace("</", "<\\/")
    body = f"""
<h1>LLM workload cost calculator</h1>
<p>Estimates monthly cost from <b>currently published rates</b> our monitors extracted from official sources. Rates update automatically when vendors change them — that's the point.</p>
<div class="calc">
<label>Model <select id="model"></select></label>
<label>Input tokens / month <input id="tin" type="number" value="10000000"></label>
<label>Output tokens / month <input id="tout" type="number" value="2000000"></label>
<button id="go">Calculate</button>
<output id="res"></output>
<p class="fine" id="src"></p>
<p class="fine">Estimates use published per-million-token rates; your provider's actual billing (caching, batching, tiers) may differ. Rates: see source link after calculating.</p>
<script id="rates" type="application/json">{payload_safe}</script>
<script>""" + CALC_JS + """</script>"""
    return page("LLM cost calculator — current published rates",
                "Compare monthly LLM API costs across models using latest published per-token rates, updated automatically when vendors change pricing.",
                body, "calculators/llm-cost/index.html")


def _rate(s):
    m = re.search(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)", str(s or ""))
    try:
        return float(m.group(1).replace(",", ""))
    except (AttributeError, ValueError):
        return None


FEED_JS = """
const BASE={BASE_JS};
const D=JSON.parse(document.getElementById('data').textContent);
const feed=document.getElementById('feed'),q=document.getElementById('q'),
vc=document.getElementById('vc'),cc=document.getElementById('cc');
[...new Set(D.map(x=>x.vendor))].forEach(v=>vc.add(new Option(v,v)));
[...new Set(D.map(x=>x.cat))].forEach(v=>cc.add(new Option(v,v)));
function render(){
 const term=(q.value||'').toLowerCase();
 const rows=D.filter(x=>(!term||(x.sum+' '+x.ent).toLowerCase().includes(term))
   &&(!vc.value||x.vendor===vc.value)&&(!cc.value||x.cat===cc.value));
 feed.innerHTML=rows.slice(0,120).map(x=>`<a class="plain" href="${BASE}changes/${x.id}/">
  <article class="card"><div class="meta"><strong>${x.vendor}</strong> · ${x.cat} · ${x.date}
  <span class="badge ${x.conf==='verified'?'v':'d'}">${x.conf}</span></div>
  <p class="summary">${x.sum}</p></article></a>`).join('')
  ||'<p>No matching changes.</p>';
}
[q,vc,cc].forEach(el=>el.addEventListener('input',render));render();
"""

CALC_JS = """
const R=JSON.parse(document.getElementById('rates').textContent);
const sel=document.getElementById('model');
Object.keys(R).sort((a,b)=>R[a].out-R[b].out).forEach(k=>sel.add(new Option(k,k)));
function money(n){return n>=1?'$'+n.toFixed(2):'$'+n.toFixed(4);}
function calc(){
 const r=R[sel.value],ti=+document.getElementById('tin').value,to=+document.getElementById('tout').value;
 if(!r)return;
 const ci=ti*r.in/1e6, co=to*r.out/1e6;
 document.getElementById('res').textContent=`≈ ${money(ci+co)} / month  (input ${money(ci)} + output ${money(co)})`;
 document.getElementById('src').innerHTML='Rate source: <a rel="nofollow" href="'+r.src+'">'+r.src+'</a>';
}
document.getElementById('go').addEventListener('click',calc);
sel.addEventListener('change',calc);calc();
"""

CSS = open(os.path.join(SITE, "static", "style.css"), encoding="utf-8").read()


def main():
    import shutil
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)
    stats = load("stats.json", {})
    changes = load("changes.json", [])
    vendors = load("vendors.json", [])
    anns = load("announcements.json", [])
    anth = load("current_anthropic.json", None)
    orr = load("current_openrouter.json", None)
    dsk = load("current_deepseek.json", None)

    write("calculators/llm-cost/index.html", pg_calculator(anth, orr, dsk))
    stats["calculator_models"] = LAST_CALC_MODELS
    with open(os.path.join(DATA, "stats.json"), "w") as f:
        json.dump(stats, f, indent=1)

    write("index.html", pg_index(stats, changes, vendors))
    write("changes/index.html", pg_changes(changes))
    for c in changes[:300]:
        write(f"changes/{c['id']}/index.html", pg_change_detail(c))
    write("vendors/index.html", pg_vendors(vendors))
    for v in vendors:
        vc = [c for c in changes if c.get("vendor") == v["key"]]
        write(f"vendors/{v['slug']}/index.html", pg_vendor(v, vc, anns))
        if v.get("status") == "active":
            write(f"vendors/{v['slug']}/pricing-history/index.html",
                  pg_vendor_history(v, vc))

    # informational pages
    CFG["_site_data"] = DATA
    import misc_pages as mp
    mp.build_all(write, page, CFG, stats, changes, vendors, u)

    # rss
    write("feed.xml", rss_feed(changes, anns))
    # sitemap + robots
    write("sitemap.xml", sitemap(changes, vendors))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {URL}/sitemap.xml\n")
    print("site built:", DIST)


def rss_feed(changes, anns):
    items = []
    for c in changes[:60]:
        items.append(f"""<item><title>{esc(c.get('vendor_name'))}: {esc(c.get('entity') or '')} changed</title>
<link>{URL}/changes/{c['id']}/</link><guid isPermaLink="false">{c['id']}</guid>
<pubDate>{rfc2822(c.get('detected_at'))}</pubDate>
<description>{esc(c.get('summary'))}</description></item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>ModelSignal — AI &amp; dev-tool pricing/limits changes</title>
<link>{URL}/changes/</link>
<description>Explained changes to AI and developer tool pricing, limits, quotas and model availability. Facts link to official sources.</description>
{''.join(items)}
</channel></rss>"""


def rfc2822(iso):
    import time, email.utils
    try:
        t = time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")
        return email.utils.formatdate(time.mktime(t), localtime=False)
    except (ValueError, TypeError):
        return email.utils.formatdate()


def sitemap(changes, vendors):
    urls = ["/", "/changes/", "/vendors/", "/pricing/", "/methodology/", "/faq/",
            "/about/", "/newsletter/", "/calculators/llm-cost/", "/privacy/",
            "/terms/", "/status/", "/blog/"]
    urls += [f"/vendors/{v['slug']}/" for v in vendors]
    urls += [f"/vendors/{v['slug']}/pricing-history/" for v in vendors if v.get("status") == "active"]
    urls += [f"/changes/{c['id']}/" for c in changes[:300]]
    xml = "".join(f"<url><loc>{URL}{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml}</urlset>'


if __name__ == "__main__":
    main()
