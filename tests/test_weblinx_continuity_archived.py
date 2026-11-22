"""Guard the source-validity claims against the archived 55+165 original records."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"results"


def csv_rows(name):
    with (RESULTS/name).open(encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f)
        return set(rd.fieldnames),list(rd)


class ContinuitySourceArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r1=json.loads((RESULTS/"weblinx_continuity_r1_summary.json").read_text(encoding="utf-8"))
        cls.r2=json.loads((RESULTS/"weblinx_continuity_r2_summary.json").read_text(encoding="utf-8"))
        cls.r1c,cls.pairs=csv_rows("weblinx_continuity_r1_frozen_pairs.csv")
        cls.r2c,cls.records=csv_rows("weblinx_continuity_r2_pairs.csv")
        _,cls.demos=csv_rows("weblinx_continuity_r1_demos.csv")

    def test_round1_counts_and_source_freeze(self):
        self.assertEqual(self.r1["demos"],55)
        self.assertEqual(self.r1["original_action_keys"],600)
        self.assertEqual(len(self.demos),55)
        self.assertEqual(len(self.pairs),165)
        self.assertEqual(self.r1["totals"]["browser_turns"],1387)
        self.assertEqual(self.r1["totals"]["direct_html_turns"],1237)
        self.assertEqual(self.r1["totals"]["adjacent_browser_pairs_with_html"],1125)
        self.assertEqual(self.r1["totals"]["adjacent_distinct_html_filename"],1123)
        self.assertEqual(len({r["demo"] for r in self.pairs}),55)

    def test_round2_all_pinned_pairs_present(self):
        self.assertEqual(self.r2["R1_source_pair_count"],165)
        self.assertEqual(self.r2["source_file_statuses"],{"fetched":233})
        self.assertEqual(self.r2["parsed_pairs"],165)
        self.assertEqual(self.r2["pair_statuses"],{
            "identical_bytes":26,"different_bytes_parsed":139})
        cohort=lambda rows:{(r["demo"],r["from_turn"],r["to_turn"]) for r in rows}
        self.assertEqual(cohort(self.pairs),cohort(self.records))

    def test_uid_xpath_correspondence_is_a_source_observation(self):
        self.assertEqual(self.r2["cross_state_ground_truth_status"],
                         "NOT_INDEPENDENTLY_ADJUDICATED")
        self.assertEqual(self.r2["changed_html_pairs_with_reused_uid"],105)
        self.assertEqual(self.r2["changed_html_pairs_with_no_uid_overlap"],34)
        self.assertEqual(self.r2["changed_html_pairs_with_uid_relocated"],40)
        self.assertEqual(self.r2["changed_html_pairs_with_xpath_uid_collision"],84)
        self.assertEqual(self.r2["changed_html_pairs_uid_overlaps_total"],180821)
        self.assertEqual(self.r2["changed_html_pairs_uid_relocated_total"],3259)
        self.assertEqual(self.r2["changed_html_pairs_xpath_reassigned_total"],14627)
        self.assertEqual(self.r2["changed_html_pairs_xpath_same_uid_total"],177562)

    def test_context_hint_stratification(self):
        self.assertEqual(self.r2["url_hints"],{"same":112,"different":53})
        self.assertEqual(self.r2["tab_hints"],{"same":164,"different":1})
        changed=[r for r in self.records if r["result_status"]=="different_bytes_parsed"]
        self.assertEqual(Counter(r["url_hint"] for r in changed),{"same":88,"different":51})
        same=[r for r in changed if r["url_hint"]=="same"]
        self.assertEqual(sum(int(r["same_xpath_different_uid"])>0 for r in same),34)
        self.assertEqual(sum(int(r["same_uid_changed_xpath"])>0 for r in same),28)
        self.assertEqual(sum(int(r["same_xpath_different_uid"]) for r in same),522)
        identical=[r for r in self.records if r["result_status"]=="identical_bytes"]
        self.assertEqual(sum(r["url_hint"]=="different" for r in identical),2)

    def test_derived_only_public_schema(self):
        prohibited={"url","html","xpath","uid","element_text",
                    "element_content","event_target","raw_html","screenshot"}
        self.assertTrue(self.r1c.isdisjoint(prohibited))
        self.assertTrue(self.r2c.isdisjoint(prohibited))


if __name__=="__main__":
    unittest.main()
