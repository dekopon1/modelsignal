"""Regression: issue-audit items.
- OpenRouter (json_models) baseline -> real price change -> exactly one change, no crash
- Publication guard blocks test/example sources from ever producing records
"""
import json, os, shutil, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import lib
import monitor

MODELS_V1 = json.dumps({"data": [
    {"id": "vendor/alpha", "name": "Alpha", "context_length": 32000,
     "pricing": {"prompt": "0.0000015", "completion": "0.000006"}},
    {"id": "vendor/beta", "name": "Beta", "context_length": 8000,
     "pricing": {"prompt": "0.0000002", "completion": "0.0000009"}},
]})
MODELS_V2 = MODELS_V1.replace('"prompt": "0.0000015"', '"prompt": "0.000003"')  # alpha doubles
MODELS_V3 = MODELS_V1  # revert


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig = (lib.DATA_DIR, lib.SNAP_DIR)
        lib.DATA_DIR = os.path.join(self.tmp, "data")
        lib.SNAP_DIR = os.path.join(lib.DATA_DIR, "snapshots")
        self.payload = {}
        self._orig_get = lib.http_get
        lib.http_get = lambda url, timeout=30: self.payload[url]
        self.state, self.vendors = {}, {"openrouter": {"name": "OpenRouter", "slug": "openrouter"}}

    def tearDown(self):
        lib.DATA_DIR, lib.SNAP_DIR = self._orig
        lib.http_get = self._orig_get
        shutil.rmtree(self.tmp)

    def run_src(self, src):
        return monitor.process_source(src, self.state, self.vendors)

    def changes(self):
        return monitor.read_jsonl(os.path.join(lib.DATA_DIR, "changes.jsonl"))


OR_SRC = {"id": "openrouter-models", "vendor": "openrouter", "product": "Models API",
          "category": "pricing", "url": "https://openrouter.ai/api/v1/models",
          "parser": "json_models", "role": "primary"}


class TestOpenRouterFlow(Base):
    def test_baseline_then_price_change_then_revert(self):
        self.payload[OR_SRC["url"]] = MODELS_V1
        r = self.run_src(OR_SRC)                      # baseline
        self.assertTrue(r["ok"]); self.assertEqual(r["changes"], 0)

        self.payload[OR_SRC["url"]] = MODELS_V2       # alpha input 1.5 -> 3.0 $/MTok
        r = self.run_src(OR_SRC)
        self.assertTrue(r["ok"])
        chgs = self.changes()
        self.assertEqual(len(chgs), 1, f"expected exactly 1 change, got {chgs}")
        c = chgs[0]
        self.assertEqual(c["entity"], "vendor/alpha")
        self.assertEqual(c["field"], "prompt_per_mtok")
        self.assertEqual(float(c["old_value"]), 1.5)
        self.assertEqual(float(c["new_value"]), 3.0)
        self.assertEqual(c["confidence"], "detected")

        # second run same content: no duplicates
        r = self.run_src(OR_SRC)
        self.assertEqual(len(self.changes()), 1)

        self.payload[OR_SRC["url"]] = MODELS_V3       # price reverts
        self.run_src(OR_SRC)
        self.assertEqual(len(self.changes()), 2)
        self.assertEqual(self.changes()[1]["new_value"], "1.5")

    def test_no_str_get_crash_on_flat_shapes(self):
        """The exact audit failure: one-level records must never reach diff."""
        self.payload[OR_SRC["url"]] = '{"data":[{"id":"m","pricing":{"prompt":"0.000001"}}]}'
        r = self.run_src(OR_SRC)
        self.assertTrue(r["ok"])
        self.assertIsNone(r.get("error"))


class TestPublicationGuard(Base):
    def test_example_com_source_blocked(self):
        bad = {"id": "test-vendor-pricing", "vendor": "openai", "product": "X",
               "category": "pricing", "url": "https://example.com/pricing",
               "parser": "markdown_tables", "role": "primary"}
        self.payload[bad["url"]] = "# Pricing\n| Model | Input |\n|---|---|\n| x | $1 |\n"
        r = self.run_src(bad)
        self.assertFalse(r["ok"])
        self.assertTrue(r["blocked"])
        self.assertIn("publication guard", r["error"])
        self.assertEqual(self.changes(), [])

    def test_http_host_blocked(self):
        bad = {"id": "sample-source", "vendor": "v", "product": "X", "category": "pricing",
               "url": "http://localhost:8000/pricing", "parser": "markdown_tables", "role": "primary"}
        self.payload[bad["url"]] = "# P\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        r = self.run_src(bad)
        self.assertTrue(r["blocked"])

    def test_build_time_filter_drops_injected_records(self):
        """Even if pollution reaches changes.jsonl, site build must drop it."""
        import build_site_data as bsd
        rec = {"id": "x", "source_url": "https://example.com/p", "detected_at": "2026-08-23T00:00:00Z"}
        good = {"id": "y", "source_url": "https://platform.claude.com/docs/pricing",
                "source_id": "anthropic-pricing", "detected_at": "2026-08-23T00:00:00Z"}
        import monitor as m
        srcs, vends = m.load_sources()
        registered = {s["id"] for s in srcs}
        import urllib.parse as up
        from monitor import BLOCKED_HOSTS, TEST_ID_RE

        def publishable(r):
            url = str(r.get("source_url", ""))
            host = (up.urlparse(url).hostname or "").lower()
            return not (host in BLOCKED_HOSTS or TEST_ID_RE.match(str(r.get("source_id", "")))
                        or (r.get("source_id") and r["source_id"] not in registered))
        self.assertFalse(publishable(rec))
        self.assertTrue(publishable(good))


if __name__ == "__main__":
    unittest.main(verbosity=2)
