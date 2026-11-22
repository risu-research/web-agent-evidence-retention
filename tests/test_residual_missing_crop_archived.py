"""Validate the 29-case public source-geometry audit against the 70-case cohort."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"results"
CASES=ROOT/"residual_missing_crop_29_cases_2026-11-22.csv"
SUMMARY=ROOT/"residual_missing_crop_summary_2026-11-22.json"
ORIGINAL=ROOT/"residual_70_cases_2026-11-22.csv"


def rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


class MissingCropArchivedTests(unittest.TestCase):
    def test_sha256(self):
        self.assertEqual(
            hashlib.sha256(CASES.read_bytes()).hexdigest(),
            "21796fe86ace4352281897f36bf8d8212be191f994f8ca06d24f3c48c990d657")
        self.assertEqual(
            hashlib.sha256(SUMMARY.read_bytes()).hexdigest(),
            "c29061924ad3fb9024e58bed8817d2b311433f082cc485050cdb7d892026df31")

    def test_case_membership_and_reasons(self):
        prior={(r["demo"],r["turn"]):r for r in rows(ORIGINAL)}
        records=rows(CASES)
        self.assertEqual(len(records),29)
        self.assertEqual(len({(r["demo"],r["turn"]) for r in records}),29)
        for r in records:
            original=prior[(r["demo"],r["turn"])]
            self.assertEqual(r["missing_visual_competitor_n"],
                             original["missing_visual_competitor_n"])
            self.assertEqual(int(r["bbox_absent"]),0)
            self.assertEqual(int(r["bbox_incomplete"]),0)
        self.assertEqual(sum(int(r["bbox_too_small"]) for r in records),41)
        self.assertEqual(sum(int(r["bbox_clipped_below_three"]) for r in records),43)
        self.assertTrue(set(records[0]).isdisjoint(
            {"uid","xpath","html_id","text","screenshot","url"}))

    def test_summary(self):
        obj=json.loads(SUMMARY.read_text())
        self.assertEqual(obj["affected_actions"],29)
        self.assertEqual(obj["missing_crop_competitors"],84)
        self.assertEqual(obj["mechanisms"],{
            "bbox_too_small":41,
            "bbox_clipped_below_three":43,
        })


if __name__=="__main__":
    unittest.main()
