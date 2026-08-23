"""End-to-end flow test: baseline -> price change -> detection -> dedupe."""
import json, os, shutil, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import lib
import monitor

PAGE_V1 = """# Pricing

| Model | Input | Output |
|---|---|---|
| gpt-test | $2.00 | $8.00 |

Sign in
"""

PAGE_V2 = PAGE_V1.replace("$2.00", "$4.00")  # real material change


class TestMonitorFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_data = lib.DATA_DIR
        lib.DATA_DIR = os.path.join(self.tmp, "data")
        lib.SNAP_DIR = os.path.join(lib.DATA_DIR, "snapshots")
        monitor.lib.SNAP_DIR = lib.SNAP_DIR
        self.src = {"id": "test-vendor", "vendor": "openai", "product": "Test API",
                    "category": "pricing", "url": "https://example.com/pricing",
                    "parser": "markdown_tables", "role": "primary"}
        self.vendors = {"openai": {"name": "OpenAI", "slug": "openai"}}
        self.state = {}
        self.payload = PAGE_V1
        self._orig_get = lib.http_get
        lib.http_get = lambda url, timeout=30: self.payload

    def tearDown(self):
        lib.http_get = self._orig_get
        shutil.rmtree(self.tmp)

    def run_src(self):
        return monitor.process_source(self.src, self.state, self.vendors)

    def changes(self):
        return monitor.read_jsonl(os.path.join(lib.DATA_DIR, "changes.jsonl"))

    def test_full_loop(self):
        # run 1: baseline — no changes ever published on first observation
        r = self.run_src()
        self.assertTrue(r["ok"])
        self.assertEqual(r["changes"], 0)
        self.assertEqual(self.changes(), [])

        # run 2: no content change -> no changes
        r = self.run_src()
        self.assertFalse(r["changed"])
        self.assertEqual(len(self.changes()), 0)

        # run 3: price change -> exactly one material change object
        self.payload = PAGE_V2
        r = self.run_src()
        self.assertTrue(r["changed"])
        chgs = self.changes()
        self.assertEqual(len(chgs), 1)
        c = chgs[0]
        self.assertEqual(c["entity"], "gpt-test")
        self.assertEqual(c["old_value"], "$2.00")
        self.assertEqual(c["new_value"], "$4.00")
        self.assertEqual(c["confidence"], "detected")
        self.assertIn("OpenAI", c["summary"])

        # run 4: same content again -> idempotent, no duplicates
        r = self.run_src()
        self.assertFalse(r["changed"])
        self.assertEqual(len(self.changes()), 1)

    def test_cosmetic_change_not_material(self):
        self.run_src()
        self.payload = PAGE_V1.replace("Sign in", "Log in")
        r = self.run_src()
        self.assertTrue(r["changed"])  # snapshot updated...
        self.assertEqual(len(self.changes()), 0)  # ...but nothing published

    def test_fetch_failure_recorded_not_fatal(self):
        def boom(url, timeout=30):
            raise RuntimeError("boom")
        lib.http_get = boom
        r = self.run_src()
        self.assertFalse(r.get("ok"))
        self.assertIn("boom", r["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
