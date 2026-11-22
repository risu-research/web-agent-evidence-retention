"""Regression checks of the measured 600-action storage study."""
import csv
import json
import unittest
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
SUMMARY=ROOT/"results"/"storage_cost_summary_2026-11-22.json"
CASES=ROOT/"results"/"storage_cost_600_actions_2026-11-22.csv"


class StorageArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
        with CASES.open(newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f)
            cls.columns=set(reader.fieldnames)
            cls.rows=list(reader)

    def test_complete_public_casebook(self):
        self.assertEqual(len(self.rows),600)
        self.assertEqual(len({(r["demo"],r["turn"]) for r in self.rows}),600)
        self.assertTrue(self.columns.isdisjoint({
            "uid","xpath","html_id","text","sem","source_doc",
            "raw_rgb","screenshot","screenshot_path","url","label"
        }))
        self.assertEqual(Counter(r["mechanism"] for r in self.rows),{
            "originally_resolved":530,
            "valid_visual_matches":41,
            "missing_visual_only":19,
            "mixed_missing_and_valid":10,
        })

    def test_byte_accounting_and_actual_recovery(self):
        policies={
            "text":(267898,158),
            "semantic":(701966,403),
            "all_hashes":(1670040,530),
            "selective_hashes":(792980,530),
            "staged":(862427,600),
            "uid":(1794620,600),
            "xpath":(621808,600),
            "semantic_plus_crops":(309543191,545),
            "full_frame":(206275510,530),
        }
        for name,(expected_bytes,expected_success) in policies.items():
            row=self.summary["cohorts"]["all_600"]["policies"][name]
            self.assertEqual(row["bytes_total"],expected_bytes)
            self.assertEqual(row["unique_recovery_n"],expected_success)
            bytekey=(name+"_total_bytes" if name=="full_frame" else
                     name+"_bytes" if name=="semantic_plus_crops" else
                     name+"_zlib_bytes")
            self.assertEqual(sum(int(r[bytekey]) for r in self.rows),expected_bytes)
            self.assertEqual(sum(int(r[name+"_unique"]) for r in self.rows),expected_success)

    def test_source_screen_deduplication(self):
        totals=self.summary["totals"]
        self.assertEqual(totals["per_action_screenshot_bytes"],204723458)
        self.assertEqual(totals["unique_screenshot_bytes"],186931927)
        self.assertEqual(totals["unique_screenshot_references"],546)
        self.assertEqual(totals["lossless_png_bytes"],308794163)
        self.assertEqual(totals["retained_png_crop_count"],9242)
        self.assertEqual(totals["png_pixel_exact_recovery_n"],545)
        self.assertEqual(totals["png_phash_recovery_n"],530)

    def test_residual_mechanisms_and_escalation(self):
        s=self.summary["cohorts"]
        self.assertEqual(s["residual_70"]["actions"],70)
        self.assertEqual(s["missing_visual_only"]["actions"],19)
        self.assertEqual(s["mixed_missing_and_valid"]["actions"],10)
        self.assertEqual(s["valid_visual_matches"]["actions"],41)
        self.assertEqual(self.summary["totals"]["adaptive_stages"],{
            "text":158,"semantic":245,"phash":127,"bbox":53,"xpath":17
        })
        residual=[r for r in self.rows if r["mechanism"]!="originally_resolved"]
        self.assertEqual(sum(r["semantic_plus_crops_unique"]=="1" for r in residual),15)
        self.assertEqual(sum(r["semantic_plus_crops_unique"]=="1" and
                             r["staged_level"]=="xpath" for r in residual),0)


if __name__=="__main__":
    unittest.main()
