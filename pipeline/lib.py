"""Shared utilities: fetching, normalization, snapshot storage. Stdlib only (py3.9+)."""
import gzip, hashlib, json, os, re, time, urllib.request, urllib.error

DATA_DIR = os.environ.get("MS_DATA", os.path.join(os.path.dirname(__file__), "..", "data"))
SNAP_DIR = os.path.join(DATA_DIR, "snapshots")
UA = "ModelSignalBot/0.1 (+https://github.com/dekopon/modelsignal; monitoring AI vendor pricing changes; contact via repo)"


class _Redirect308(urllib.request.HTTPRedirectHandler):
    """Python 3.9 urllib lacks HTTP 308 handling."""
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_301(req, fp, code, msg, headers)


_opener = urllib.request.build_opener(_Redirect308)


def http_get(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    last_err = None
    for attempt in range(3):
        try:
            with _opener.open(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"fetch failed after retries: {url}: {last_err}")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def normalize(content_type_hint: str, raw: str) -> str:
    """Canonical form for hashing/diffing: stable whitespace ordering."""
    if content_type_hint == "json":
        try:
            return json.dumps(json.loads(raw), sort_keys=True, indent=1)
        except json.JSONDecodeError:
            pass
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def save_snapshot(source_id: str, text: str) -> str:
    """Store gzipped snapshot; return relative path."""
    d = os.path.join(SNAP_DIR, source_id)
    os.makedirs(d, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    rel = os.path.join("snapshots", source_id, ts + ".txt.gz")
    with gzip.open(os.path.join(DATA_DIR, rel), "wt", encoding="utf-8") as f:
        f.write(text)
    return rel


def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: str, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
