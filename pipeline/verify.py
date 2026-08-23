"""Corroborate detected changes against official announcement feeds.

A `detected` change is promoted to `verified` only when an official announcement
item from the SAME vendor shares significant tokens with the changed entity.
We never publish an inferred number; we only attach corroboration links.
"""
import json, os, re, sys, time

sys.path.insert(0, os.path.dirname(__file__))
import lib

def changes_path():
    return os.path.join(lib.DATA_DIR, "changes.jsonl")


def ann_path():
    return os.path.join(lib.DATA_DIR, "announcements.jsonl")

STOP = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "on", "with", "at", "by",
        "new", "update", "updates", "updated", "release", "released", "notes", "note"}
TOKEN_RE = re.compile(r"[a-z0-9]+")


def toks(text):
    return [t for t in TOKEN_RE.findall(str(text).lower()) if t not in STOP and len(t) > 1]


def overlap_ratio(entity_tokens, title_tokens):
    if not entity_tokens:
        return 0.0
    hit = sum(1 for t in entity_tokens if t in title_tokens)
    return hit / len(entity_tokens)


def parse_dt(s):
    try:
        return time.strptime(s[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def within_days(a_iso, b_iso, days):
    ta, tb = parse_dt(a_iso), parse_dt(b_iso)
    if not ta or not tb:
        return False
    return abs(time.mktime(ta) - time.mktime(tb)) <= days * 86400


def run(window_days=30):
    anns = _read(ann_path())
    changes = _read(changes_path())
    verified_ct = 0
    for chg in changes:
        if chg.get("confidence") != "detected":
            continue
        etoks = toks(" ".join([chg.get("entity") or "", chg.get("context") or "",
                               chg.get("field") or ""]))
        if not etoks:
            continue
        best, best_r = None, 0.0
        for a in anns:
            if a.get("vendor") != chg.get("vendor"):
                continue
            if not within_days(chg["detected_at"], a.get("detected_at") or a.get("published") or "", window_days):
                continue
            r = overlap_ratio(etoks, set(toks(a.get("title") or "")))
            if r > best_r:
                best, best_r = a, r
        if best and best_r >= 0.6:
            chg["confidence"] = "verified"
            chg["verification"] = {"status": "verified",
                                   "corroborated_by": best.get("url"),
                                   "corroboration_title": best.get("title"),
                                   "method": f"token-overlap {best_r:.2f} within {window_days}d"}
            verified_ct += 1
    _write(changes_path(), changes)
    return {"changes_total": len(changes), "verified_now": verified_ct,
            "verified_total": sum(1 for c in changes if c.get("confidence") == "verified")}


def _read(path):
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


def _write(path, objs):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for o in objs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
