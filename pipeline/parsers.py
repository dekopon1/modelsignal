"""Parsers: turn fetched content into (normalized_text, records).

records: {context: {entity_key: {field: value}}}  — deterministic, comparable.
All extraction is deterministic; no LLM involved.
"""
import json
import re
from html.parser import HTMLParser


# ---------- markdown ----------
_MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_MD_EM = re.compile(r"\*+|`+")


def _clean_md(text: str) -> str:
    text = _MD_LINK.sub(r"\1", text)
    text = _MD_EM.sub("", text)
    return text.strip()


def parse_markdown_tables(raw: str):
    """Extract heading-contextualized pipe tables."""
    records, ctx, cur_table = {}, "page", []
    headers = None

    def flush():
        nonlocal cur_table, headers
        if headers and len(headers) >= 2 and cur_table:
            tbl = records.setdefault(ctx, {})
            for row in cur_table:
                key = row[0]
                if not key:
                    continue
                entry = tbl.setdefault(key, {})
                for i, col in enumerate(headers[1:], start=1):
                    if i < len(row) and row[i]:
                        entry[col] = row[i]
        cur_table, headers = [], None

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("#"):
            flush()
            new_ctx = _clean_md(line.lstrip("#"))[:120] or "page"
            if new_ctx != ctx:
                ctx = new_ctx
                records.setdefault(ctx, {})  # register sections even without tables
        elif line.startswith("|") and line.endswith("|"):
            cells = [_clean_md(c) for c in line[1:-1].split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if headers is None:
                headers = [c or f"col{i}" for i, c in enumerate(cells)]
            else:
                cur_table.append(cells)
        else:
            flush()
    flush()
    return records


# ---------- html ----------
class _HTMLText(HTMLParser):
    """Extract tables as rows + headings as context + visible text lines."""

    BLOCKS = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "br", "section", "article"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.records, self.text_lines = {}, []
        self.ctx, self.headers, self.row, self.in_table = "page", None, None, False
        self.cell, self.heading_buf, self.heading_level = None, None, 0
        self.skip = 0
        self._pending_label = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
            return
        if tag == "table":
            self._flush_row()
            self.in_table = True
            self._pending_label = ""
            self.records.setdefault(self.ctx, {})
        elif tag == "tr":
            self._flush_row()
            self.row = []
        elif tag in ("td", "th"):
            self.cell = [] if self.cell is None else self.cell
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_buf, self.heading_level = [], int(tag[1])
        elif tag in self.BLOCKS:
            self._end_line()

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip = max(0, self.skip - 1)
        elif tag in ("td", "th") and self.cell is not None:
            txt = re.sub(r"\s+", " ", "".join(self.cell)).strip()
            self.row.append(txt) if self.row is not None else None
            self.cell = None
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")
        elif tag == "tr":
            self._flush_row()
        elif tag == "table":
            self._flush_row()
            self.in_table = False
            self.headers = None
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.heading_buf is not None:
            t = re.sub(r"\s+", " ", "".join(self.heading_buf)).strip()
            if t:
                if self.heading_level <= 3:
                    if t != self.ctx:
                        self.ctx = t[:120]
                        self.headers = None
                        self.records.setdefault(self.ctx, {})  # register section even w/o table
                elif not self.in_table:
                    self._emit(t)
            self.heading_buf = None
        elif tag in self.BLOCKS:
            self._end_line()

    def handle_data(self, data):
        if self.skip:
            return
        if self.heading_buf is not None:
            self.heading_buf.append(data)
        elif self.cell is not None:
            self.cell.append(data)
        elif not self.in_table:
            self._buf_line(data)

    # line buffer for non-table text
    def __init_line_buf(self):
        pass

    def _buf_line(self, data):
        if not hasattr(self, "_line_acc"):
            self._line_acc = []
        self._line_acc.append(data)

    def _end_line(self):
        acc = getattr(self, "_line_acc", None)
        if acc:
            t = re.sub(r"\s+", " ", "".join(acc)).strip()
            if t:
                self.text_lines.append(t)
            self._line_acc = []

    def _emit(self, t):
        self.text_lines.append(t)

    def _flush_row(self):
        if self.row:
            cells = [c.strip() for c in self.row]
            if all(re.fullmatch(r"[-–—]*", c) for c in cells):  # separator junk
                self.row = None
                return
            if self.in_table:
                if not any(c for c in cells):
                    self.row = None
                    return
                tbl = self.records.setdefault(self.ctx, {})
                if len(cells) >= 2 and (self.headers is None):
                    self.headers = cells
                    self.row = None
                    return
                # rowspan carry-forward: rows starting with empty cells continue
                # the previous row's label (e.g. DeepSeek pricing matrices)
                lead = 0
                while lead < len(cells) and not cells[lead]:
                    lead += 1
                if lead == 0:
                    if cells[0]:
                        self._pending_label = cells[0]
                    key = cells[0] or (self._pending_label or "row")
                else:
                    rest = cells[lead:]
                    base = self._pending_label or "row"
                    key = f"{base} | {rest[0]}" if rest and rest[0] else base
                if not key:
                    self.row = None
                    return
                entry = tbl.setdefault(key, {})
                hdrs = self.headers or []
                for j, col in enumerate(hdrs[1:] if hdrs else [], start=1):
                    idx = lead + j
                    if idx < len(cells) and cells[idx]:
                        label = col or f"col{j}"
                        old = entry.get(label)
                        entry[label] = f"{old} | {cells[idx]}" if old and old != cells[idx] else cells[idx]
            else:
                line = " | ".join(c for c in cells if c)
                if line:
                    self.text_lines.append(line)
        self.row = None


def finish_html(p: _HTMLText):
    p._end_line()
    return p


def parse_html_tables(raw: str):
    p = _HTMLText()
    try:
        p.feed(raw)
        p.close()
        finish_html(p)
    except Exception:
        pass  # malformed html: return whatever we captured
    return p.records


# ---------- rss / atom ----------
_TAG = re.compile(r"<[^>]+>")
_CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.S)


def _clean_feed(seg: str) -> str:
    return _TAG.sub("", _CDATA.sub(lambda m: m.group(1), seg)).strip()


def parse_rss(raw: str):
    """Return {link_or_guid: {title, date, summary}} via paired block matching."""
    items = {}
    blocks = re.findall(r"<item[^>]*>(.*?)</item>", raw, re.S) or \
             re.findall(r"<entry[^>]*>(.*?)</entry>", raw, re.S)
    for b in blocks[:300]:

        def grab(*tags):
            for t in tags:
                m = re.search(rf"<{t}[^>]*>(.*?)</{t}>", b, re.S)
                if m:
                    return _clean_feed(m.group(1))[:600]
            return ""

        link = ""
        m = re.search(r'<link[^>]*href="([^"]+)"', b) or re.search(r"<link>(.*?)</link>", b, re.S)
        if m:
            link = _clean_feed(m.group(1))
        guid = grab("guid", "id")
        key = link or guid
        title = grab("title")
        if not key or not title:
            continue
        items[key] = {"title": title, "date": grab("pubDate", "published", "updated"),
                      "summary": grab("description", "summary", "content")[:500]}
    return items


# ---------- openrouter-style model json ----------
def parse_json_models(raw: str):
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    data = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(data, list):
        return {}
    recs = {}
    for m in data:
        mid = m.get("id")
        if not mid:
            continue
        entry = {}
        if m.get("name"):
            entry["name"] = m["name"]
        if m.get("context_length") is not None:
            entry["context_length"] = str(m["context_length"])
        pr = m.get("pricing") or {}
        for k in ("prompt", "completion", "request", "image"):
            v = pr.get(k)
            if v is None:
                continue
            try:
                f = float(v)
                entry[f"{k}_per_mtok"] = f"{f * 1_000_000:.4f}".rstrip("0").rstrip(".")
            except (TypeError, ValueError):
                entry[f"{k}"] = str(v)
        recs[mid] = entry
    return recs


PARSERS = {
    "markdown_tables": lambda raw: parse_markdown_tables(raw),
    "html_tables": lambda raw: parse_html_tables(raw),
    "rss": parse_rss,
    "json_models": parse_json_models,
}
