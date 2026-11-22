"""Regression checks against the archived full 70-action residual audit."""
import json
import unittest
from pathlib import Path

RESULTS=Path(__file__).resolve().parents[1]/"results"/"residual_70_summary_2026-11-22.json"


class ArchivedResidualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(RESULTS.read_text(encoding="utf-8"))

    def test_cohort_and_three_mechanisms(self):
        x=self.data
        self.assertEqual(x["population"]["actions"],600)
        self.assertEqual(x["population"]["residual_actions"],70)
        self.assertEqual(x["population"]["residual_demonstrations"],33)
        self.assertEqual(x["mechanisms"],{
            "missing_visual_only":19,
            "mixed_missing_and_valid":10,
            "valid_visual_matches":41,
        })

    def test_competitor_decomposition(self):
        x=self.data["counts"]
        self.assertEqual(x["competing_candidates_total"],308)
        self.assertEqual(x["missing_crop_competitors_total"],84)
        self.assertEqual(x["valid_crop_competitors_total"],224)
        self.assertEqual(x["exact_phash_competitors_total"],161)
        self.assertEqual(x["near_phash_competitors_total"],63)

    def test_primary_qualifications(self):
        x=self.data
        d=x["orthogonal_diagnostics"]
        self.assertEqual(d["at_least_one_disjoint_bbox_competitor"],53)
        self.assertEqual(d["at_least_one_equal_phash_different_bbox"],25)
        self.assertEqual(d["strict_phash_zero_resolves"],7)
        self.assertEqual(d["xpath_available"],70)
        self.assertEqual(x["target_tags"]["div"],44)
        self.assertEqual(x["target_roles"]["absent"],69)

    def test_target_text_association(self):
        x=self.data["blank_text_association"]
        self.assertEqual((x["blank_residual"],x["blank_total"]),(63,390))
        self.assertEqual((x["nonblank_residual"],x["nonblank_total"]),(7,210))
        self.assertAlmostEqual(x["risk_difference"],63/390-7/210)
        ci=self.data["bootstrap"]["blank_minus_nonblank_risk_difference_ci95"]
        self.assertTrue(ci[0] <= x["risk_difference"] <= ci[1])


if __name__=="__main__":
    unittest.main()
