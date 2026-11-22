"""Frozen original R7 truth-vs-Trace DOM and packet answers, 48 source cases."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"results"


class R7ArchivedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=json.loads(
            (DATA/"weblinx_r7_DOM_vs_packets_summary.json").read_text())
        with (DATA/"weblinx_r7_DOM_vs_packets_48.csv").open(
                newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f);cls.fields=set(reader.fieldnames)
            cls.rows=list(reader)

    def test_original_matrix_source_and_all_truth_labels(self):
        self.assertEqual(self.s["cases"],len(self.rows))
        self.assertEqual(len(self.rows),48)
        self.assertEqual(len({(x["operation"],x["locator"],x["condition"])
                              for x in self.rows}),48)
        self.assertEqual(self.s["source_tag_commit"],
                         "4f382ca672f86dd4a1e4d071c91d0caad0e124b3")
        self.assertEqual(self.s["original_source_effect_counts"],{
            "A":16,"B":8,"none":24})
        self.assertTrue(self.s["trace_auditor_evaluated_with_no_oracle_input"])
        self.assertTrue(self.s["tier_auditors_evaluated_with_no_trace_input"])

    def test_actual_DOM_snapshot_decode_and_references(self):
        v=self.s["DOM_snapshot_totals"]
        self.assertEqual(v["recorded"],1088)
        self.assertEqual(v["successfully_decoded"],1088)
        self.assertEqual(v["subtree_refs_resolved"],14825)
        self.assertEqual(v["subtree_ref_failures"],0)
        self.assertGreater(v["action_target_markers_found"],0)

    def test_every_question_and_tier_accounted_for(self):
        for layer,questions in self.s["evaluations"].items():
            for q,v in questions.items():
                self.assertEqual(sum(v[k] for k in
                                     ("correct","wrong","abstain")),48)
        for q in ("Q2_visible_click_row","Q3_server_mutating_POST",
                  "Q4_SQLite_effect","Q5_first_click_status"):
            self.assertEqual(self.s["evaluations"]["trace"][q]["correct"],48)
            self.assertEqual(self.s["evaluations"]["effect"][q]["correct"],48)
        self.assertEqual(self.s["evaluations"]["event"][
            "Q4_SQLite_effect"]["abstain"],48)
        self.assertEqual(self.s["evaluations"]["server"][
            "Q4_SQLite_effect"]["abstain"],48)

    def test_packet_bytes_original_and_data_protection(self):
        s=self.s["packet_bytes_by_tier"]
        self.assertEqual(s["request"]["zlib9_per_episode"],3670)
        self.assertEqual(s["event"]["zlib9_per_episode"],5026)
        self.assertEqual(s["server"]["zlib9_per_episode"],5734)
        self.assertEqual(s["effect"]["zlib9_per_episode"],7290)
        self.assertEqual(self.s["native_trace_zip_total_bytes"],1655362)
        self.assertFalse(self.s["raw_trace_ZIP_published"])
        self.assertFalse(self.s["audit_with_human_DOM_review"])
        self.assertTrue(self.fields.isdisjoint({
            "cookie","password","session","raw_trace","raw_html","literal_selector",
            "DOM_snapshot","sql_dump","full_response","raw_network"}))


if __name__=="__main__":
    unittest.main()
