"""Quality gate behavior: healthy / partial / total / missing report."""
import contextlib, io, json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import quality_gate


class TestQualityGate(unittest.TestCase):
    def run_gate(self, report):
        tmp = tempfile.mkdtemp()
        old = os.getcwd()
        if report is not None:
            os.makedirs(os.path.join(tmp, "data"), exist_ok=True)
            with open(os.path.join(tmp, "data", "run_report.json"), "w") as f:
                json.dump(report, f)
        os.chdir(tmp)
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = quality_gate.main()
            return rc, out.getvalue()
        finally:
            os.chdir(old)

    def test_all_healthy_passes(self):
        r = {"run_at": "t", "results": [{"id": "a", "ok": True}, {"id": "b", "ok": True}]}
        rc, out = self.run_gate(r)
        self.assertEqual(rc, 0)
        self.assertNotIn("::error::", out)

    def test_partial_failure_fails_loudly(self):
        r = {"run_at": "t", "results": [{"id": "a", "ok": True},
                                        {"id": "b", "ok": False, "error": "404"}]}
        rc, out = self.run_gate(r)
        self.assertEqual(rc, 1)
        self.assertIn("PARTIAL SOURCE FAILURE (1/2)", out)
        self.assertIn("DEGRADED RUN", out)

    def test_total_failure_distinguished(self):
        r = {"run_at": "t", "results": [{"id": "a", "ok": False, "error": "x"},
                                        {"id": "b", "ok": False, "error": "y"}]}
        rc, out = self.run_gate(r)
        self.assertEqual(rc, 1)
        self.assertIn("COMPLETE MONITOR FAILURE", out)

    def test_missing_report_is_complete_failure(self):
        rc, out = self.run_gate(None)
        self.assertEqual(rc, 1)
        self.assertIn("COMPLETE MONITOR FAILURE", out)

    def test_guard_blocks_are_notices_not_errors(self):
        r = {"run_at": "t", "results": [{"id": "test-x", "ok": False, "blocked": True}]}
        # blocked-only run: failed == results -> still a failure, but marked as guard
        rc, out = self.run_gate(r)
        self.assertEqual(rc, 1)
        self.assertIn("publication guard blocked source test-x", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
