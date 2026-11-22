"""Full 600-action R3 target provenance and continuity regression checks."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"results"


class R3ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads((ROOT/"weblinx_continuity_r3_summary.json")
                               .read_text(encoding="utf-8"))
        with (ROOT/"weblinx_continuity_r3_actions.csv").open(
                newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f)
            cls.columns=set(reader.fieldnames)
            cls.rows=list(reader)

    def test_original_600_record_cohort(self):
        self.assertEqual(len(self.rows),600)
        self.assertEqual(len({(r["demo"],r["turn"]) for r in self.rows}),600)
        self.assertEqual(len({r["demo"] for r in self.rows}),55)
        self.assertEqual(self.summary["source_retrieval_statuses"],{"fetched":927})
        self.assertEqual(self.summary["numeric_totals"]["action_uid_equals_positive_uid"],600)
        self.assertEqual(self.summary["numeric_totals"]["recorded_uid_equals_html_site_node"],600)
        self.assertEqual(self.summary["numeric_totals"]["dmr_xpath_equals_computed_source_xpath"],600)
        self.assertEqual(self.summary["numeric_totals"]["dmr_xpath_equals_action_xpath"],0)

    def test_adjacent_source_is_complete_or_missing(self):
        self.assertEqual(self.summary["next_html_parse_statuses"],
                         {"parsed":560,"no_next_html":40})
        self.assertEqual(self.summary["original_to_next_html_equal_counts"],
                         {"-1":40,"0":413,"1":147})
        self.assertEqual(Counter(r["continuity_proxy_status"] for r in self.rows),{
            "identical_html_bytes":147,
            "no_site_native_id":323,
            "next_id_absent":11,
            "source_id_duplicated":4,
            "site_native_proxy_candidate":75,
            "source_not_eligible":40,
        })

    def test_site_native_proxy_not_ground_truth(self):
        self.assertEqual(self.summary["eligible_same_site_native_id_proxy_n"],75)
        self.assertEqual(self.summary["eligible_proxy_changed_xpath_n"],16)
        self.assertEqual(self.summary["eligible_proxy_changed_recorded_uid_n"],4)
        self.assertFalse(self.summary["independent_logical_identity_ground_truth"])
        self.assertFalse(self.summary["independent_browser_event_recipient_ground_truth"])
        eligible=[r for r in self.rows if r["continuity_proxy_status"]==
                  "site_native_proxy_candidate"]
        self.assertEqual(sum(r["url_context_hint"]=="same" for r in eligible),73)
        self.assertEqual(sum(r["site_native_anchor_same_xpath"]=="0" for r in eligible),16)
        self.assertEqual(sum(r["site_native_anchor_same_text"]=="1" for r in eligible),67)

    def test_no_raw_html_or_locator_publication(self):
        blocked={"uid","xpath","html","url","text","site_id",
                 "source_doc","event_target","screenshot","dialogue"}
        self.assertTrue(self.columns.isdisjoint(blocked))
        self.assertTrue(all(r["positive_candidate_count"]=="1" for r in self.rows))


if __name__=="__main__":
    unittest.main()
