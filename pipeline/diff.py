"""Diff two record sets -> material change objects."""
import re

MATERIAL_RE = re.compile(
    r"(prompt_per_mtok|completion_per_mtok|image_per_mtok|request_per_mtok|context_length|price|pricing|\$|\bper[\s_-]?(mtok|1m|million|token|request|user|seat|mo)\b|cost|bill|limit|quota|rate|"
    r"cap|credit|tier|plan|deprecat|retir|sunset|context|window|entitle|usage|allowance|premium.?request|"
    r"free.?tier|overage|discount|increase|decrease|effective)", re.I)

NOISE_RE = re.compile(r"(cookie|sign in|log ?in|subscribe to our newsletter|404|not found|javascript is required)", re.I)


def _norm(v):
    return re.sub(r"\s+", " ", str(v)).strip()


def num_close(a, b):
    try:
        return abs(float(str(a).replace(",", "").replace("$", "")) - float(str(b).replace(",", "").replace("$", ""))) < 1e-9
    except (ValueError, TypeError):
        return False


def diff_records(old, new):
    """Yield change dicts between old/new {ctx: {key: {field: val}}}."""
    changes = []
    if not isinstance(old, dict) or not isinstance(new, dict):
        return changes
    for ctx in sorted(set(old) | set(new)):
        o_tbl, n_tbl = old.get(ctx) or {}, new.get(ctx) or {}
        for key in sorted(set(o_tbl) | set(n_tbl)):
            o_row, n_row = o_tbl.get(key) or {}, n_tbl.get(key) or {}
            fields = set(o_row) | set(n_row)
            if not fields:  # row appeared/disappeared with no fields
                continue
            if not o_row:
                changes.append(_mk("item_added", ctx, key, None, _row_summary(n_row)))
                continue
            if not n_row:
                changes.append(_mk("item_removed", ctx, key, _row_summary(o_row), None))
                continue
            for f in sorted(fields):
                ov, nv = _norm(o_row.get(f, "")), _norm(n_row.get(f, ""))
                if ov == nv:
                    continue
                if ov and nv and num_close(ov, nv):
                    continue
                changes.append(_mk("field_change", ctx, key, ov, nv, field=f))
    return changes


def _row_summary(row):
    parts = [f"{k}: {_norm(v)}" for k, v in list(row.items())[:6]]
    return "; ".join(parts)


def _mk(kind, context, entity, old, new, field=None):
    c = {"kind": kind, "context": _norm(context)[:160], "entity": _norm(entity)[:200],
         "old_value": (_norm(old)[:400] if old else None),
         "new_value": (_norm(new)[:400] if new else None)}
    if field:
        c["field"] = _norm(field)[:80]
    return c


def is_material(change, category):
    blob = " ".join(str(x) for x in (change.get("context"), change.get("entity"),
                                     change.get("old_value"), change.get("new_value"),
                                     change.get("field", "")))
    if NOISE_RE.search(blob) and not MATERIAL_RE.search(blob):
        return False
    if change["kind"] in ("item_added", "item_removed"):
        return True  # model/plan appearance or disappearance is availability info
    if change["kind"] == "field_change":
        return bool(MATERIAL_RE.search(blob))
    return bool(MATERIAL_RE.search(blob))


def summarize(source, chg, vendor_name):
    """Template-generated plain-English summary. Extracted fields only — never invented."""
    cat = source["category"]
    ent = chg.get("entity") or ""
    ctx = chg.get("context") or ""
    who = f"{vendor_name} ({source['product']})"
    label = f"{ent}" + (f" [{chg['field']}]" if chg.get("field") else "")
    if chg["kind"] == "item_added":
        return f"{who}: new entry detected on the {cat} page under “{ctx}” → {label}. {chg.get('new_value') or ''}".strip()
    if chg["kind"] == "item_removed":
        return f"{who}: entry removed from the {cat} page under “{ctx}” → {label}. Prior value: {chg.get('old_value') or ''}".strip()
    return (f"{who}: “{label}” on the {cat} page (section “{ctx}”) changed "
            f"from “{chg.get('old_value') or '(none)'}” to “{chg.get('new_value') or '(none)'}”.")
