"""R5B complete external Flaskr source/SQLite outcome and trace-cost archive checks."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"results"


class FlaskrVerifiedArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads((DATA/"weblinx_round5b_flaskr_summary.json").read_text())
        with (DATA/"weblinx_round5b_flaskr_cases.csv").open(newline="",
                encoding="utf-8") as f:
            rd=csv.DictReader(f)
            cls.fields=set(rd.fieldnames)
            cls.rows=list(rd)

    def test_all_48_cases_and_original_external_source(self):
        d=self.summary
        self.assertEqual(len(self.rows),48)
        self.assertEqual(len({(r["operation"],r["locator"],r["condition"])
                              for r in self.rows}),48)
        self.assertEqual(Counter(r["operation"] for r in self.rows),{
            "edit":24,"delete":24})
        self.assertEqual(Counter(r["locator"] for r in self.rows),{
            "positional":16,"href_exact":16,"contextual_role":16})
        self.assertEqual(d["upstream_commit"],
                         "49943b5a94413a530761350f04e896f76e8d620e")
        self.assertEqual(d["environment"]["flask"],"3.1.2")
        self.assertEqual(d["environment"]["playwright"],"1.65.2")
        self.assertTrue(d["source_app_unmodified"])
        self.assertTrue(d["independent_authoritative_SQLite_readback"])
        self.assertFalse(d["real_agent_trajectories"])
        self.assertFalse(d["raw_playwright_traces_published"])

    def test_db_truth_and_staged_success_disagreement(self):
        total=self.summary["total"]
        self.assertEqual(total["sqlite_effect_counts"],{"A":16,"B":8,"none":24})
        self.assertEqual(total["click_status_counts"],{
            "returned":36,"timeout":10,"playwright_error":2})
        self.assertEqual(total["returned_clicks_without_SQL_effect"],12)
        self.assertEqual(total["mismatched_event_article_and_SQL_effect"],6)
        self.assertTrue(all(r["rendered_matches_SQL"]=="1"
                            for r in self.rows))
        self.assertTrue(all(r["db_rows_changed_count"] in ("0","1")
                            for r in self.rows))
        self.assertEqual(sum(r["sqlite_effect_record"]=="B" for r in self.rows),8)

    def test_event_link_identity_is_not_effect_identity(self):
        matrix=Counter((r["first_click_article"],r["sqlite_effect_record"])
                       for r in self.rows)
        self.assertEqual(matrix,{
            ("A","A"):14,("A","B"):4,("A","none"):6,
            ("B","A"):2,("B","B"):4,("none","none"):18
        })
        self.assertEqual(
            sum(r["first_click_article"]=="A" and
                r["sqlite_effect_record"]=="B" for r in self.rows),4)
        self.assertEqual(
            sum(r["first_click_article"]=="B" and
                r["sqlite_effect_record"]=="A" for r in self.rows),2)
        self.assertEqual(
            self.summary["by_condition"]["swap_href"]["mismatched_event_article_and_SQL_effect"],6)

    def test_individual_real_db_and_trace_baseline_bytes(self):
        sizes=self.summary["total"]["bytes_by_evidence_tier"]
        expect={
            "request":(5090,4286),
            "event":(9230,6228),
            "server":(14822,8181),
            "effect":(18638,10123)
        }
        for name,(raw,zlib_size) in expect.items():
            self.assertEqual(sizes[name],{
                "sum_utf8_bytes":raw,
                "sum_zlib_per_episode_bytes":zlib_size
            })
            self.assertEqual(sum(int(r[name+"_bytes"]) for r in self.rows),raw)
            self.assertEqual(sum(int(r[name+"_zlib_bytes"]) for r in self.rows),
                             zlib_size)
        self.assertEqual(self.summary["total"]["playwright_trace_zip_total_bytes"],
                         343784)
        self.assertEqual(self.summary["total"]["playwright_trace_network_lines"],312)
        self.assertTrue(all(int(r["trace_zip_bytes"])>0 for r in self.rows))
        self.assertTrue(self.fields.isdisjoint({
            "password","cookie","session","raw_trace","raw_html",
            "user_text","sqlite_dump","full_response"
        }))


if __name__=="__main__":
    unittest.main()
