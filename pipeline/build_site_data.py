"""Generate JSON data files consumed by the static site generator."""
import json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import lib
from monitor import load_sources, read_jsonl, changes_path, ann_path

SITE_DATA = os.path.join(os.path.dirname(__file__), "..", "site", "data")


def main():
    sources, vendors = load_sources()
    state = lib.load_json(os.path.join(lib.DATA_DIR, "state.json"), {})
    changes = read_jsonl(changes_path())
    anns = read_jsonl(ann_path())

    # defense-in-depth publication filter (mirrors monitor.validate_source)
    from monitor import BLOCKED_HOSTS, TEST_ID_RE
    import urllib.parse as _up
    registered = {s["id"] for s in sources}

    def publishable(rec):
        url = str(rec.get("source_url", ""))
        host = (_up.urlparse(url).hostname or "").lower()
        if host in BLOCKED_HOSTS or not url.startswith("https://"):
            return False
        if rec.get("source_id") and rec["source_id"] not in registered:
            return False
        if TEST_ID_RE.match(str(rec.get("source_id", ""))):
            return False
        return True

    dropped = [c for c in changes if not publishable(c)]
    changes = [c for c in changes if publishable(c)]
    anns = [a for a in anns if publishable(a)]
    if dropped:
        print(f"publication guard: dropped {len(dropped)} non-official record(s) at build time")

    changes.sort(key=lambda c: c.get("detected_at") or "", reverse=True)
    anns.sort(key=lambda a: a.get("detected_at") or "", reverse=True)

    vendor_list = []
    for key, meta in vendors.items():
        src_ids = [s["id"] for s in sources if s["vendor"] == key]
        st = {sid: state.get(sid, {}) for sid in src_ids}
        last_checked = max((v.get("last_checked") or "" for v in st.values()), default=None)
        errors = [v.get("last_error") for v in st.values() if v.get("last_error")]
        has_primary = any(s["vendor"] == key and s.get("role") == "primary" for s in sources)
        has_ann = any(s["vendor"] == key and s.get("role") == "announcements" for s in sources)
        status = "active" if has_primary else ("announcements_only" if has_ann else "none")
        vendor_list.append({**meta, "key": key,
                            "sources": [{"id": sid} for sid in src_ids],
                            "status": status,
                            "last_checked": last_checked if status == "active" else None,
                            "degraded": bool(errors),
                            "change_count": sum(1 for c in changes if c.get("vendor") == key)})
    vendor_list = [v for v in vendor_list if v["status"] != "none"]

    # per-source health for ops transparency page
    source_health = [{"id": s["id"], "vendor": s["vendor"], "url": s["url"],
                      "category": s["category"], "role": s["role"],
                      "status": ("error" if state.get(s["id"], {}).get("last_error")
                                 else ("ok" if state.get(s["id"], {}).get("last_checked") else "pending")),
                      "last_checked": state.get(s["id"], {}).get("last_checked"),
                      "last_error": state.get(s["id"], {}).get("last_error")}
                     for s in sources]

    lib.write_json(os.path.join(SITE_DATA, "changes.json"), changes[:2000])
    lib.write_json(os.path.join(SITE_DATA, "announcements.json"), anns[:1000])
    lib.write_json(os.path.join(SITE_DATA, "vendors.json"), sorted(vendor_list, key=lambda v: -v["change_count"]))
    lib.write_json(os.path.join(SITE_DATA, "source_health.json"), source_health)

    # current-state records for impact calculators (only structured pricing sources)
    calc_sources = {"anthropic": "anthropic-pricing", "openrouter": "openrouter-models",
                    "deepseek": "deepseek-pricing"}
    calculator_models = 0
    for vk, sid in calc_sources.items():
        recs = lib.load_json(os.path.join(lib.SNAP_DIR, sid, "records_latest.json"), None)
        if recs:
            lib.write_json(os.path.join(SITE_DATA, f"current_{vk}.json"), recs)
            for tbl in recs.values():
                if isinstance(tbl, dict):
                    calculator_models += len(tbl)

    active_vendors = [v for v in vendor_list if v["status"] == "active"]
    ann_only = [v for v in vendor_list if v["status"] == "announcements_only"]
    stats = {
        "generated_at": lib.now_iso(),
        "total_changes": len(changes),
        "verified_changes": sum(1 for c in changes if c.get("confidence") == "verified"),
        "vendors_monitored": len(active_vendors),          # primary monitors only
        "vendors_announcements_only": len(ann_only),       # relayed, not diffed
        "active_sources": len(sources),
        "primary_sources": sum(1 for s in sources if s.get("role") == "primary"),
        "material_announcements": sum(1 for a in anns if a.get("material")),
        "announcements_total": len(anns),
        "calculator_models": calculator_models,
        "degraded_sources": sum(1 for s in source_health if s.get("last_error")),
    }
    lib.write_json(os.path.join(SITE_DATA, "stats.json"), stats)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
