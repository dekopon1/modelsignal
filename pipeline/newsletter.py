"""Generate the weekly digest (markdown archive entry + site data).

Runs after monitor+verify. Idempotent per ISO week.
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
import lib
from monitor import load_sources, read_jsonl, changes_path, ann_path

DIGEST_DIR = os.path.join(os.path.dirname(__file__), "..", "marketing", "digests")
SITE_DATA = os.path.join(os.path.dirname(__file__), "..", "site", "data")
STATE = os.path.join(lib.DATA_DIR, "newsletter_state.json")


def week_key(ts=None):
    t = time.gmtime(ts if ts is not None else time.time())
    return f"{t.tm_year}-W{t.tm.strftime('%V') if hasattr(t,'tm') else ''}"


def iso_week(dt_epoch=None):
    t = time.gmtime(dt_epoch if dt_epoch is not None else time.time())
    return t.tm_year, t.tm_isdst and 0 or 0  # placeholder replaced below


def current_week_label():
    import datetime
    d = datetime.datetime.utcnow()
    year, wk, _ = d.isocalendar()
    return f"{year}-W{wk:02d}"


def within_last_days(iso_dt, days=7):
    import datetime
    try:
        then = datetime.datetime.strptime((iso_dt or "")[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return False
    return (datetime.datetime.utcnow() - then).days <= days


def main(force=False):
    label = current_week_label()
    st = lib.load_json(STATE, {})
    if st.get("last_digest") == label and not force:
        print(f"digest {label} already generated")
        return

    changes = [c for c in read_jsonl(changes_path()) if within_last_days(c.get("detected_at"), 7)]
    anns = [a for a in read_jsonl(ann_path())
            if a.get("material") and within_last_days(a.get("detected_at") or a.get("published"), 7)]

    os.makedirs(DIGEST_DIR, exist_ok=True)
    lines = [f"# This Week in AI Pricing & Limits — {label}",
             "",
             f"_Auto-generated from verified monitoring runs. Every item links to its official source._",
             ""]
    by_vendor = {}
    for c in sorted(changes, key=lambda x: x.get("detected_at") or ""):
        by_vendor.setdefault(c["vendor_name"], []).append(c)
    if not by_vendor and not anns:
        lines += ["No material changes detected across monitored vendors this week.",
                  "", "— ModelSignal autonomous pipeline"]
    for vendor, items in sorted(by_vendor.items()):
        lines.append(f"## {vendor}")
        for c in items:
            conf = "verified" if c.get("confidence") == "verified" else "detected"
            lines.append(f"- [{conf}] {c['summary']}")
            lines.append(f"  Source: {c['source_url']}")
        lines.append("")
    if anns:
        lines.append("## Official announcements worth reading")
        seen_titles = set()
        for a in anns[:15]:
            if a["title"] in seen_titles:
                continue
            seen_titles.add(a["title"])
            lines.append(f"- {a['vendor_name']}: [{a['title']}]({a['url']})")
        lines.append("")

    md_path = os.path.join(DIGEST_DIR, f"{label}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    lib.write_json(os.path.join(SITE_DATA, "digest_latest.json"),
                   {"week": label, "changes": len(changes),
                    "announcements": len(anns), "markdown": "\n".join(lines)})
    st["last_digest"] = label
    lib.write_json(STATE, st)
    print(f"digest written: {md_path} ({len(changes)} changes, {len(anns)} announcements)")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
