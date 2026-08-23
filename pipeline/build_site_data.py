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

    changes.sort(key=lambda c: c.get("detected_at") or "", reverse=True)
    anns.sort(key=lambda a: a.get("detected_at") or "", reverse=True)

    vendor_list = []
    for key, meta in vendors.items():
        src_ids = [s["id"] for s in sources if s["vendor"] == key]
        st = {sid: state.get(sid, {}) for sid in src_ids}
        last_checked = max((v.get("last_checked") or "" for v in st.values()), default=None)
        errors = [v.get("last_error") for v in st.values() if v.get("last_error")]
        vendor_list.append({**meta, "key": key, "sources": src_ids,
                            "last_checked": last_checked,
                            "degraded": bool(errors),
                            "change_count": sum(1 for c in changes if c.get("vendor") == key)})

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
    for vk, sid in calc_sources.items():
        recs = lib.load_json(os.path.join(lib.SNAP_DIR, sid, "records_latest.json"), None)
        if recs:
            lib.write_json(os.path.join(SITE_DATA, f"current_{vk}.json"), recs)

    stats = {
        "generated_at": lib.now_iso(),
        "total_changes": len(changes),
        "verified_changes": sum(1 for c in changes if c.get("confidence") == "verified"),
        "vendors_monitored": len(vendors),
        "active_sources": len(sources),
        "material_announcements": sum(1 for a in anns if a.get("material")),
        "announcements_total": len(anns),
    }
    lib.write_json(os.path.join(SITE_DATA, "stats.json"), stats)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
