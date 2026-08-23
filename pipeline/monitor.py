"""ModelSignal monitor: fetch -> snapshot -> parse -> diff -> material change objects.

Usage: python3 monitor.py [--source SOURCE_ID]
Idempotent: identical content never produces duplicate changes.
"""
import argparse, json, os, re, sys, time
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
import lib
import parsers
import diff as diffmod

ROOT = lib.DATA_DIR
STATE_PATH = os.path.join(ROOT, "state.json")


def changes_path():
    return os.path.join(lib.DATA_DIR, "changes.jsonl")


def ann_path():
    return os.path.join(lib.DATA_DIR, "announcements.jsonl")


def load_sources():
    cfg = lib.load_json(os.path.join(os.path.dirname(__file__), "sources.json"), {})
    return cfg.get("sources", []), cfg.get("vendors", {})


# --- publication guard: test/example data must never reach production ---
BLOCKED_HOSTS = {"example.com", "example.org", "example.net", "localhost",
                 "127.0.0.1", "0.0.0.0", "httpbin.org", "test.local"}
TEST_ID_RE = re.compile(r"^(test|fixture|sample|dummy|fake)[-_]", re.I)


def validate_source(src):
    """Raise ValueError if a source looks like a test fixture or points off-domain."""
    sid = str(src.get("id", ""))
    if TEST_ID_RE.match(sid):
        raise ValueError(f"publication guard: test-like source id '{sid}'")
    url = str(src.get("url", ""))
    host = urllib.parse.urlparse(url).hostname or ""
    if host.lower() in BLOCKED_HOSTS:
        raise ValueError(f"publication guard: non-official host '{host}'")
    if not url.startswith("https://"):
        raise ValueError(f"publication guard: only https official sources allowed, got {url[:60]}")
    return True


def extract_effective_date(*texts):
    """Only trust dates literally present in the changed content itself."""
    blob = " ".join(t for t in texts if t)
    m = re.search(r"(?:effective|starting|begins?|from|through|until)[\s:]*([A-Z][a-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})", blob, re.I)
    return m.group(1) if m else None


def process_source(src, state, vendors):
    sid = src["id"]
    st = state.setdefault(sid, {})
    result = {"id": sid, "ok": False}
    try:
        validate_source(src)
    except ValueError as e:
        st["last_error"] = f"{lib.now_iso()} {e}"
        result["error"] = st["last_error"]
        result["blocked"] = True
        return result
    try:
        raw = lib.http_get(src["url"])
        norm = lib.normalize("json" if src["parser"] == "json_models" else "text", raw)
        h = lib.sha(norm)
        result["http_chars"] = len(raw)
        if st.get("hash") == h:
            st["last_checked"] = lib.now_iso()
            result.update(ok=True, changed=False)
            return result

        recs = parsers.PARSERS[src["parser"]](norm)
        snap_rel = lib.save_snapshot(sid, norm)
        lib.write_json(os.path.join(lib.SNAP_DIR, sid, "records_latest.json"), recs)

        prev_recs = lib.load_json(os.path.join(lib.SNAP_DIR, sid, "records_prev.json"), None) if st.get("hash") else None

        new_changes, new_announcements = [], []
        if src["role"] == "announcements":
            prev_items = lib.load_json(os.path.join(lib.SNAP_DIR, sid, "items_latest.json"), {})
            if src["parser"] == "rss":
                items = recs
            else:
                # dated changelog pages: each top-level section (heading) is an entry
                items = {}
                for ctx in recs.keys():
                    title = re.sub(r"\s+", " ", ctx).strip()
                    if not title or len(title) > 120:
                        continue
                    slug = lib.sha(title)[:12]
                    items[slug] = {"title": title, "date": "", "summary": "",
                                   "url": src["url"]}
            for key, meta in items.items():
                if key not in prev_items and meta.get("title"):
                    material_ann = bool(diffmod.MATERIAL_RE.search(meta["title"].lower()))
                    new_announcements.append({
                        "id": lib.sha(sid + key)[:16], "vendor": src["vendor"],
                        "vendor_name": vendors.get(src["vendor"], {}).get("name", src["vendor"]),
                        "product": src["product"], "title": meta["title"],
                        "url": meta.get("url", src["url"]),
                        "published": meta.get("date") or "", "detected_at": lib.now_iso(),
                        "source_id": sid,
                        "material": material_ann})
            # first run = baseline only, never flood
            if not st.get("hash"):
                new_announcements = []
            lib.write_json(os.path.join(lib.SNAP_DIR, sid, "items_latest.json"), items)
        elif prev_recs is not None:
            for chg in diffmod.diff_records(prev_recs, recs):
                if not diffmod.is_material(chg, src["category"]):
                    continue
                cid = lib.sha("|".join([sid, chg["kind"], str(chg.get("entity")), str(chg.get("field")),
                                        str(chg.get("old_value")), str(chg.get("new_value"))]))[:16]
                summary = diffmod.summarize(src, chg, vendors.get(src["vendor"], {}).get("name", src["vendor"]))
                eff = extract_effective_date(chg.get("new_value"), chg.get("context"))
                new_changes.append({
                    "id": cid, "vendor": src["vendor"],
                    "vendor_name": vendors.get(src["vendor"], {}).get("name", src["vendor"]),
                    "product": src["product"], "category": src["category"],
                    **chg, "summary": summary,
                    "effective_date": eff, "detected_at": lib.now_iso(),
                    "source_url": src["url"], "snapshot": snap_rel,
                    "confidence": "detected",
                    "verification": {"status": "unverified", "corroborated_by": None}})

        # rotate current records into prev for next run
        if src["role"] != "announcements":
            cur = lib.load_json(os.path.join(lib.SNAP_DIR, sid, "records_latest.json"), {})
            lib.write_json(os.path.join(lib.SNAP_DIR, sid, "records_prev.json"), cur)

        # append (dedupe against existing ids)
        seen_c = {c["id"] for c in read_jsonl(changes_path())}
        seen_a = {a["id"] for a in read_jsonl(ann_path())}
        added = [c for c in new_changes if c["id"] not in seen_c]
        added_a = [a for a in new_announcements if a["id"] not in seen_a]
        append_jsonl(changes_path(), added)
        append_jsonl(ann_path(), added_a)

        st.pop("last_error", None)  # a successful run clears prior failure state
        st.update(hash=h, last_snapshot=snap_rel, last_checked=lib.now_iso(),
                  last_changed=lib.now_iso() if (added or added_a) else st.get("last_changed"),
                  first_seen=st.get("first_seen") or lib.now_iso())
        result.update(ok=True, changed=True, changes=len(added), announcements=len(added_a))
        return result
    except Exception as e:
        st["last_error"] = f"{lib.now_iso()} {type(e).__name__}: {e}"
        result["error"] = st["last_error"]
        return result


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    out.append(json.loads(ln))
    except OSError:
        pass
    return out


def append_jsonl(path, objs):
    if not objs:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for o in objs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="limit to one source id")
    args = ap.parse_args()

    sources, vendors = load_sources()
    state = lib.load_json(STATE_PATH, {})
    report = {"run_at": lib.now_iso(), "results": []}
    for src in sources:
        if args.source and src["id"] != args.source:
            continue
        r = process_source(src, state, vendors)
        report["results"].append(r)
        print(f"[{r['id']}] ok={r.get('ok')} changed={r.get('changed')} "
              f"changes={r.get('changes', 0)} ann={r.get('announcements', 0)} "
              + (f"ERROR={r['error']}" if r.get("error") else ""))
    lib.write_json(STATE_PATH, state)
    lib.write_json(os.path.join(ROOT, "run_report.json"), report)


if __name__ == "__main__":
    main()
