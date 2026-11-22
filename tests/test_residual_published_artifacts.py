"""Check 70-case published CSVs against source SHA-256 and frozen aggregate JSON."""
from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"results"
FILES={
    "cases":(ROOT/"residual_70_cases_2026-11-22.csv",
             "a1d603af041fc5dd27a52f6c4e46a29b2761a6cb5ea3fbdf801fa8485302a5e3"),
    "pixels":(ROOT/"residual_70_pixel_cases_2026-11-22.csv",
              "38591f3a5749a015a23642de4ac745d0e2cbd7f8e0ae6ef027f227ca6b8d305b"),
    "summary":(ROOT/"residual_70_summary_2026-11-22.json",
               "a141e76d34b11a9dd63828293dd8cc06fc96d4aaf3292ec1ef4293bdc041e05b"),
    "pixel_summary":(ROOT/"residual_70_pixel_summary_2026-11-22.json",
                     "b26db3ca8707824551dc75dfa1a752a70138ad38362633abde79b46974facb0d"),
}


def records(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


class PublishedCasebookTests(unittest.TestCase):
    def test_file_integrity(self):
        for name,(path,expected) in FILES.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             expected, name)

    def test_full_membership_and_compatible_metrics(self):
        base=records(FILES["cases"][0])
        pixel=records(FILES["pixels"][0])
        self.assertEqual(len(base),70)
        self.assertEqual(len(pixel),70)
        keys=lambda rows:{(x["demo"],x["turn"]) for x in rows}
        self.assertEqual(keys(base),keys(pixel))
        self.assertEqual(len(keys(base)),70)
        bykey={(x["demo"],x["turn"]):x for x in pixel}
        for x in base:
            y=bykey[(x["demo"],x["turn"])]
            for k,value in x.items():
                self.assertEqual(value,y[k],f"{x['demo']}/{x['turn']} {k}")
        self.assertTrue(set(base[0]).isdisjoint(
            {"uid","xpath","html_id","text","image","raw_rgb","screenshot","url"}))

    def test_aggregate_reconciliation(self):
        base=records(FILES["cases"][0])
        pixel=records(FILES["pixels"][0])
        report=json.loads(FILES["summary"][0].read_text())
        px=json.loads(FILES["pixel_summary"][0].read_text())
        self.assertEqual(sum(int(r["competitor_n"]) for r in base),308)
        self.assertEqual(sum(int(r["missing_visual_competitor_n"]) for r in base),84)
        self.assertEqual(sum(int(r["valid_visual_competitor_n"]) for r in base),224)
        self.assertEqual(sum(int(r["exact_rgb_equal_competitors"]) for r in pixel),92)
        self.assertEqual(sum(int(r["same_phash_different_rgb_competitors"]) for r in pixel),69)
        self.assertEqual(sum(int(r["different_bbox_same_rgb_competitors"]) for r in pixel),65)
        self.assertEqual(sum(report["mechanisms"].values()),70)
        self.assertEqual(px["case_n"],70)


if __name__=="__main__":
    unittest.main()
