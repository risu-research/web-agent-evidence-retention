"""R5B-2 frozen external Flaskr server-validation negative-control audit."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"results"


class ArchivedFlaskrRejectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads(
            (ROOT/"weblinx_round5b2_rejection_summary.json").read_text())
        with (ROOT/"weblinx_round5b2_rejection_cases.csv").open(
                newline="",encoding="utf-8") as f:
            rd=csv.DictReader(f)
            cls.cols=set(rd.fieldnames)
            cls.rows=list(rd)

    def test_six_server_post_rejections_without_commits(self):
        self.assertEqual(len(self.rows),6)
        self.assertEqual(len({(r["locator"],r["condition"]) for r in self.rows}),6)
        self.assertEqual(Counter(r["condition"] for r in self.rows),{
            "baseline":3,"reorder":3})
        self.assertEqual(self.summary["first_click_results"],{"returned":6})
        self.assertEqual(self.summary["post_response_codes"],{"200":6})
        self.assertEqual(self.summary["server_POST_count_total"],6)
        self.assertEqual(self.summary["server_POST_with_no_SQL_commit"],6)
        self.assertEqual(self.summary["flash_validation_n"],6)
        self.assertTrue(self.summary["all_SQL_A_unchanged"])
        self.assertTrue(self.summary["all_SQL_B_unchanged"])
        self.assertTrue(all(r["browser_render_matches_SQL"]=="1"
                            for r in self.rows))

    def test_distinct_browser_recipient_and_server_rejection(self):
        self.assertEqual(sum(r["first_click_article"]=="B" for r in self.rows),1)
        self.assertTrue(all(r["server_edit_POST_status"]=="200" for r in self.rows))
        self.assertTrue(all(r["server_side_validation_message"]=="1" for r in self.rows))
        self.assertTrue(all(r["sql_rows_changed_count"]=="0" for r in self.rows))
        self.assertTrue(all(int(r["playwright_trace_zip_bytes"])>0 for r in self.rows))

    def test_source_and_publication_boundary(self):
        self.assertEqual(
            self.summary["source_commit"],
            "49943b5a94413a530761350f04e896f76e8d620e")
        self.assertTrue(self.summary["real_external_app_backend_unchanged"])
        self.assertTrue(self.summary["actual_independent_SQLite_reads"])
        self.assertFalse(self.summary["raw_trace_archives_published"])
        self.assertTrue(self.cols.isdisjoint({
            "password","cookie","session","raw_trace","raw_html",
            "sql_dump","user_text","literal_href"
        }))


if __name__=="__main__":
    unittest.main()
