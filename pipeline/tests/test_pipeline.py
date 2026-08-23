import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import parsers, diff


class TestMarkdownTables(unittest.TestCase):
    def test_basic_table(self):
        md = """# Pricing
| Model | Input | Output |
|---|---|---|
| gpt-x | $2.00 | $8.00 |
| gpt-mini | $0.50 | $2.00 |
"""
        r = parsers.parse_markdown_tables(md)
        self.assertIn("Pricing", r)
        self.assertEqual(r["Pricing"]["gpt-x"]["Input"], "$2.00")

    def test_links_and_bold_cleaned(self):
        md = """# P
| Model | Price |
|---|---|
| [claude-x](https://x) **retired** | $5 |
"""
        r = parsers.parse_markdown_tables(md)
        key = [k for k in r["P"] if k.startswith("claude-x")][0]
        self.assertEqual(r["P"][key]["Price"], "$5")

    def test_sections_without_tables_registered(self):
        md = "### August 20, 2026\nSome text\n\n### August 1, 2026\nOther\n"
        r = parsers.parse_markdown_tables(md)
        self.assertIn("August 20, 2026", r)
        self.assertIn("August 1, 2026", r)


HTML = """<html><body>
<h2>March 1, 2026</h2>
<table><tr><td colspan="2">MODEL</td><td>v4-flash</td><td>v4-pro</td></tr>
<tr><td colspan="2">PRICE 1M INPUT</td><td>$0.22</td><td>$0.66</td></tr>
<tr><td></td><td>OFF-PEAK</td><td>$0.11</td><td>$0.33</td></tr>
<tr><td colspan="2">MAX OUTPUT</td><td>8k</td><td>8k</td></tr>
</table>
<p>plain text</p>
</body></html>"""


class TestHtmlTables(unittest.TestCase):
    def setUp(self):
        self.r = parsers.parse_html_tables(HTML)

    def test_transposed_matrix(self):
        tbl = self.r["March 1, 2026"]
        self.assertEqual(tbl["PRICE 1M INPUT"]["v4-pro"], "$0.66")

    def test_rowspan_carry_forward(self):
        tbl = self.r["March 1, 2026"]
        self.assertIn("PRICE 1M INPUT | OFF-PEAK", tbl)
        self.assertEqual(tbl["PRICE 1M INPUT | OFF-PEAK"]["v4-flash"], "$0.11")

    def test_script_style_skipped(self):
        html = "<script>var x='<table><tr><td>nope</td></tr></table>';</script><h2>Real</h2><p>ok</p>"
        r = parsers.parse_html_tables(html)
        self.assertNotIn("nope", str(r))


class TestRss(unittest.TestCase):
    def test_cdata_titles_and_links(self):
        feed = """<rss><channel><item>
<title><![CDATA[Cutting prices by 50%]]></title>
<link>https://openai.com/news/x</link>
<pubDate>Sat, 22 Aug 2026 19:00:00 GMT</pubDate>
</item></channel></rss>"""
        r = parsers.parse_rss(feed)
        self.assertEqual(list(r.values())[0]["title"], "Cutting prices by 50%")

    def test_atom_entries(self):
        feed = """<feed><entry>
<title>Model deprecated</title><id>urn:x</id>
<link href="https://example.com/a"/><updated>2026-01-01</updated>
</entry></feed>"""
        r = parsers.parse_rss(feed)
        self.assertIn("https://example.com/a", r)


class TestJsonModels(unittest.TestCase):
    def test_pricing_conversion(self):
        raw = '{"data":[{"id":"m-1","name":"Model 1","context_length":128000,"pricing":{"prompt":"0.0000015","completion":"0.000006"}}]}'
        r = parsers.parse_json_models(raw)
        self.assertEqual(r["models"]["m-1"]["prompt_per_mtok"], "1.5")
        self.assertEqual(r["models"]["m-1"]["completion_per_mtok"], "6")


class TestDiff(unittest.TestCase):
    def old_new(self):
        old = {"T": {"m1": {"Input": "$2", "Out": "$8"}, "m2": {"Input": "$1"}}}
        new = {"T": {"m1": {"Input": "$4", "Out": "$8"}, "m2": {"Input": "$1"}}}
        return old, new

    def test_price_change_detected(self):
        chgs = diff.diff_records(*self.old_new())
        self.assertEqual(len(chgs), 1)
        self.assertEqual(chgs[0]["entity"], "m1")
        self.assertEqual(chgs[0]["old_value"], "$2")
        self.assertEqual(chgs[0]["new_value"], "$4")

    def test_numeric_equality_not_change(self):
        old = {"T": {"m1": {"p": "0.50"}}}
        new = {"T": {"m1": {"p": "0.5"}}}
        self.assertEqual(diff.diff_records(old, new), [])

    def test_item_removed(self):
        old = {"T": {"m1": {"Input": "$2"}}}
        new = {"T": {}}
        chgs = diff.diff_records(old, new)
        self.assertEqual(chgs[0]["kind"], "item_removed")

    def test_materiality(self):
        chg = {"kind": "field_change", "context": "T", "entity": "m1", "field": "Input",
               "old_value": "$2", "new_value": "$4"}
        self.assertTrue(diff.is_material(chg, "pricing"))
        chg2 = {"kind": "field_change", "context": "footer", "entity": "copyright", "field": "year",
                "old_value": "2025", "new_value": "2026"}
        self.assertFalse(diff.is_material(chg2, "pricing"))

    def test_noise_not_material(self):
        chg = {"kind": "field_change", "context": "nav", "entity": "Sign in link", "field": "text",
               "old_value": "Sign in", "new_value": "Log in"}
        self.assertFalse(diff.is_material(chg, "pricing"))


class TestSummaries(unittest.TestCase):
    def test_summary_contains_values_and_vendor(self):
        src = {"vendor": "x", "product": "API", "category": "pricing"}
        chg = {"kind": "field_change", "context": "Model pricing", "entity": "gpt-x",
               "field": "Input", "old_value": "$2", "new_value": "$4"}
        s = diff.summarize(src, chg, "OpenAI")
        self.assertIn("$2", s) and self.assertIn("$4", s) and self.assertIn("OpenAI", s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
