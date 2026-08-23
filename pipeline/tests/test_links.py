"""Every internal link in built HTML must resolve to a real file in site/dist.

Catches root-relative-link regressions on subpath deployments (e.g. GitHub Pages
project sites). Run after `python3 pipeline/ssg.py`.
"""
import json, os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(ROOT, "site", "dist")
CFG = json.load(open(os.path.join(ROOT, "site", "config.json")))
SITE_URL = CFG["site_url"].rstrip("/")

HREF_RE = re.compile(r'<a\s[^>]*href="([^"]+)"')


def iter_internal_anchors(html):
    """Yield (raw_href, path_after_base_or_None_if_root_relative)."""
    for m in HREF_RE.findall(html):
        if m.startswith(("mailto:", "#", "//")):
            continue
        if "${" in m or "'+" in m or "+'" in m:
            continue  # generated at runtime by page JS; validated via live checks
        if m.startswith("${BASE}"):            # JS template literal, base injected at runtime
            yield m, m[len("${BASE}"):]
        elif m.startswith("http"):
            if m.startswith(SITE_URL):
                rest = m[len(SITE_URL):]
                yield m, rest if rest else "/"
        elif m.startswith("/"):
            yield m, None                       # ROOT-RELATIVE -> always broken here
        else:
            yield m, "/" + m                    # page-relative; treat from dist root


def resolve(target):
    target = target.split("#")[0]
    if target in ("", "/"):
        return os.path.isfile(os.path.join(DIST, "index.html"))
    t = target.lstrip("/")
    if t.endswith("/"):
        return os.path.isdir(os.path.join(DIST, t))
    return os.path.isfile(os.path.join(DIST, t)) or os.path.isfile(os.path.join(DIST, t, "index.html"))


class TestInternalLinks(unittest.TestCase):
    def setUp(self):
        self.pages = {}
        for dirpath, _, files in os.walk(DIST):
            for fn in files:
                if fn.endswith(".html"):
                    p = os.path.join(dirpath, fn)
                    self.pages[os.path.relpath(p, DIST)] = open(p, encoding="utf-8").read()
        self.assertTrue(self.pages, "no built pages found — run pipeline/ssg.py first")

    def test_no_root_relative_links(self):
        bad = [f"{rel} -> {href}"
               for rel, html in self.pages.items()
               for href, after in iter_internal_anchors(html)
               if after is None]
        self.assertEqual(bad, [], "root-relative anchors (404 on subpath deploys):\n" + "\n".join(bad[:40]))

    def test_all_internal_targets_exist(self):
        missing = [f"{rel} -> {after}"
                   for rel, html in self.pages.items()
                   for href, after in iter_internal_anchors(html)
                   if after is not None and not resolve(after)]
        self.assertEqual(missing, [], "dangling internal links:\n" + "\n".join(missing[:40]))

    def test_sitemap_urls_exist(self):
        xml = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
        for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
            self.assertTrue(loc.startswith(SITE_URL), f"sitemap loc outside base: {loc}")
            t = loc[len(SITE_URL):].lstrip("/")
            fs = os.path.join(DIST, t) if t else os.path.join(DIST, "index.html")
            self.assertTrue(
                os.path.isfile(fs) or os.path.isfile(os.path.join(fs, "index.html")),
                f"sitemap lists non-existent page: {loc}")

    def test_feed_urls_exist(self):
        import re as _re
        xml = open(os.path.join(DIST, "feed.xml"), encoding="utf-8").read()
        for link in _re.findall(r"<link>([^<]+)</link>", xml):
            if link.startswith(SITE_URL):
                t = link[len(SITE_URL):].lstrip("/")
                fs = os.path.join(DIST, t) if t else os.path.join(DIST, "index.html")
                self.assertTrue(
                    os.path.isfile(fs) or os.path.isfile(os.path.join(fs, "index.html")),
                    f"feed lists non-existent page: {link}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
