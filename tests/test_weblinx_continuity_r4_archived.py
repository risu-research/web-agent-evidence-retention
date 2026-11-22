"""Regression checks for R4 construct-validity correction and blinded evidence."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"results"


class R4ArchivedResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r4=json.loads((DATA/"weblinx_continuity_r4_summary.json").read_text())
        cls.r4b=json.loads((DATA/"weblinx_continuity_r4b_summary.json").read_text())
        with (DATA/"weblinx_continuity_r4_cases.csv").open(
                newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f);cls.f4=set(reader.fieldnames)
            cls.cases4=list(reader)
        with (DATA/"weblinx_continuity_r4b_cases.csv").open(
                newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f);cls.fb=set(reader.fieldnames)
            cls.casesb=list(reader)

    def test_exact_86_cases_and_paired_cohort(self):
        self.assertEqual(len(self.cases4),86)
        self.assertEqual(len(self.casesb),86)
        self.assertEqual(Counter(r["group"] for r in self.cases4),{
            "source_xpath_anomaly":11,"captured_only_8":8,"both_67":67})
        tokeys=lambda rows:{(r["demo"],r["turn"]) for r in rows}
        self.assertEqual(tokeys(self.cases4),tokeys(self.casesb))
        self.assertEqual(self.r4["original_named_source_file_count"],145)
        self.assertEqual(self.r4["source_file_fetch_statuses"],{"fetched":145})

    def test_id_overlap_is_exact_terminal_expression_for_every_proxy(self):
        self.assertEqual(self.r4["all_proxy_75"]["root_id_relation"],{
            "target_node":75})
        x=self.r4b["groups"]["all_proxy_75"]
        self.assertEqual(x["actions"],75)
        self.assertEqual(x["complete_expression_is_id_only"],75)
        self.assertEqual(x["id_root_equals_original_target_site_id"],75)
        self.assertEqual(x["id_function_has_suffix"],0)
        self.assertFalse(self.r4b["independent_target_identity_ground_truth"])

    def test_non_id_semantic_comparisons_have_all_denominators(self):
        self.assertEqual(self.r4["all_proxy_75"]["blinded_semantic_outcomes"],{
            "multi_family_corroborated":22,"single_family_corroborated":39,
            "none":14})
        self.assertEqual(self.r4["captured_only_8"]["blinded_semantic_outcomes"],{
            "multi_family_corroborated":3,"single_family_corroborated":5})
        self.assertEqual(self.r4["both_67"]["blinded_semantic_outcomes"],{
            "multi_family_corroborated":19,"single_family_corroborated":34,
            "none":14})
        self.assertEqual(self.r4["all_proxy_75"]["unique_channel_conflict_n"],0)

    def test_original_xpath_anomaly_independent_cue_availability(self):
        x=self.r4["anomalies_11"]
        self.assertEqual(x["n"],11)
        self.assertEqual(x["with_one_or_more_unique_source_semantic_channel"],4)
        self.assertEqual(x["with_two_or_more_unique_source_semantic_families"],0)
        self.assertEqual(self.r4b["groups"]["source_xpath_anomaly"]["complete_expression_is_id_only"],6)
        self.assertEqual(self.r4b["groups"]["source_xpath_anomaly"]["id_function_has_suffix"],5)

    def test_public_schema_has_no_source_identity_or_text(self):
        forbidden={"uid","xpath","url","text","html","site_id","href",
                   "raw_html","source_doc","event_target","account"}
        self.assertTrue(self.f4.isdisjoint(forbidden))
        self.assertTrue(self.fb.isdisjoint(forbidden))
        self.assertFalse(self.r4["source_native_id_proxy_independently_adjudicated"])
        self.assertFalse(self.r4["browser_action_recipient_independently_logged"])


if __name__=="__main__":
    unittest.main()
