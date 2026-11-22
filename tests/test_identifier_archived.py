"""Check archived identifier results against the frozen confirmatory cohort."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SUMMARY=ROOT/"results"/"identifier_baseline_2026-11-22.json"


class IdentifierResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_original_cohort_and_result(self):
        obj=self.result
        self.assertEqual(obj["cohort_n"],600)
        self.assertEqual(obj["demo_n"],55)
        self.assertEqual(obj["cohort"]["joint_residual"],70)
        self.assertEqual(obj["by_candidate_budget"]["all"]["baselines"]["joint"]["recovered"],530)
        self.assertEqual(obj["by_candidate_budget"]["10"]["baselines"]["joint"]["recovered"],415)

    def test_identifier_outcomes(self):
        obj=self.result
        rates=obj["by_candidate_budget"]
        self.assertEqual([rates[str(k)]["baselines"]["xpath"]["recovered"]
                          for k in (10,20,50)]+[rates["all"]["baselines"]["xpath"]["recovered"]],
                         [425,470,521,600])
        self.assertEqual(obj["cohort"]["target_xpath_available"],600)
        self.assertEqual(obj["cohort"]["target_html_id_available"],122)
        self.assertEqual(rates["all"]["baselines"]["html_id"]["recovered"],121)
        self.assertEqual(rates["all"]["baselines"]["joint_html_id"]["recovered"],536)
        self.assertEqual(obj["cohort"]["joint_residual_resolved_xpath"],70)
        self.assertEqual(obj["cohort"]["joint_residual_resolved_html_id"],6)
        self.assertEqual(obj["cohort"]["target_webtasks_id_equals_uid"],600)

    def test_bootstrap(self):
        b=self.result["cluster_bootstrap"]
        self.assertEqual(b["unit"],"demonstration")
        self.assertEqual(b["reps"],5000)
        self.assertEqual(b["demo_n"],55)
        gain=b["metrics"]["gain_joint_xpath"]
        self.assertAlmostEqual(gain["estimate"],70/600)
        self.assertTrue(gain["ci95"][0] <= gain["estimate"] <= gain["ci95"][1])


if __name__=="__main__":
    unittest.main()
