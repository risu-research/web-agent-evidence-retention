"""Offline regression for verified first-party R5A real Chromium event/effect data."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"results"


class LiveChromiumArchivedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads((ROOT/"weblinx_round5a_browser_summary.json").read_text(encoding="utf-8"))
        with (ROOT/"weblinx_round5a_browser_cases.csv").open(newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f)
            cls.columns=set(reader.fieldnames)
            cls.cases=list(reader)

    def group(self,name):
        return [r for r in self.cases if r["condition"]==name]

    def test_full_72_case_matrix_and_app_independence(self):
        self.assertEqual(len(self.cases),72)
        self.assertEqual(len({(r["app"],r["condition"],r["locator"]) for r in self.cases}),72)
        self.assertEqual(Counter(r["app"] for r in self.cases),{"list":36,"table":36})
        self.assertEqual(Counter(r["locator"] for r in self.cases),{
            "positional":24,"native_id":24,"accessible_role":24})
        self.assertTrue(all(r["state_render_verified"]=="1" for r in self.cases))
        self.assertTrue(self.summary["real_trusted_browser_clicks"])
        self.assertFalse(self.summary["external_live_websites"])
        self.assertFalse(self.summary["original_weblinx_replay_reexecuted"])

    def test_all_browsers_and_effects_are_accounted_for(self):
        t=self.summary["total"]
        self.assertEqual(t["effect_counts"],{"A":30,"B":6,"none":36})
        self.assertEqual(t["event_path_counts"],{
            "A":42,"B":6,"OVERLAY":6,"none":18})
        self.assertEqual(t["handler_item_counts"],{"A":36,"B":6,"none":30})
        self.assertEqual(t["status_counts"],{
            "returned":54,"timeout":16,"playwright_error_Error":2})
        self.assertEqual(t["tool_returned_but_no_effect"],18)
        self.assertEqual(t["event_without_handler"],12)
        self.assertEqual(t["handler_without_effect"],6)

    def test_controlled_wrong_target_mechanisms(self):
        for condition in ("reorder","reuse_id","target_removed"):
            rows=self.group(condition)
            self.assertEqual(len(rows),6)
            self.assertEqual(sum(r["effect_item"]=="B" for r in rows),2)
        self.assertEqual(len(self.group("baseline")),6)
        self.assertTrue(all(r["effect_item"]=="A" for r in self.group("baseline")))
        self.assertTrue(all(r["effect_item"]=="A" for r in self.group("nested_icon")))
        self.assertTrue(all(r["event_raw_target_tag"]=="SPAN"
                            for r in self.group("nested_icon")))

    def test_event_handler_and_effect_are_distinct(self):
        self.assertTrue(all(r["click_status"]=="timeout" and r["effect_item"]=="none"
                            for r in self.group("overlay_standard")))
        self.assertTrue(all(r["event_path_item"]=="OVERLAY" and
                            r["click_status"]=="returned" and
                            r["handler_item"]=="none"
                            for r in self.group("overlay_force")))
        self.assertTrue(all(r["event_path_item"]=="A" and
                            r["handler_item"]=="none" and
                            r["effect_item"]=="none"
                            for r in self.group("stop_bubble")))
        self.assertTrue(all(r["handler_item"]=="A" and
                            r["effect_item"]=="none" for r in
                            self.group("handler_no_effect")))

    def test_actual_retained_packet_bytes_and_public_schema(self):
        expected={
            "request":(5880,5500),
            "event":(13416,10221),
            "handler":(14910,11064),
            "effect":(21318,13564)
        }
        measured=self.summary["total"]["bytes_by_retention_tier"]
        for key,(raw,compressed) in expected.items():
            self.assertEqual(measured[key],{
                "sum_utf8":raw,"sum_zlib_per_episode":compressed})
            self.assertEqual(sum(int(r[f"{key}_bytes"]) for r in self.cases),raw)
            self.assertEqual(sum(int(r[f"{key}_zlib_bytes"]) for r in self.cases),compressed)
        self.assertTrue(self.columns.isdisjoint({
            "raw_html","html","url","site_id","xpath","password",
            "browser_profile","event_payload_raw","user_text"
        }))


if __name__=="__main__":
    unittest.main()
