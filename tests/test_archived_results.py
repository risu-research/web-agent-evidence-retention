"""Validate the archived result files against the historical source protocol."""
import json
import unittest
from pathlib import Path

from scripts.verify_results import check as check_confirm
from scripts.verify_universe import check as check_universe

ROOT = Path(__file__).resolve().parents[1] / "results" / "rerun-2026-11-22"


class ArchivedResultsTests(unittest.TestCase):
    def test_confirmatory_600(self):
        result = json.loads((ROOT / "confirm_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(check_confirm(result), [])
        self.assertEqual(result["bootstrap"]["reps"], 5000)
        self.assertEqual(result["bootstrap"]["unit"], "demo")
        self.assertEqual(result["bootstrap"]["demo_n"], 55)
        self.assertEqual(result["protocol_audit"]["candidate_total"], 155553)
        self.assertEqual(result["protocol_audit"]["candidate_visual_valid_total"], 154553)

    def test_candidate_expansion_598(self):
        result = json.loads((ROOT / "universe_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(check_universe(result), [])
        self.assertEqual(result["selected_sample"]["compute_skips"],
                         {"no_official_records": 1, "target_count": 1})
        self.assertEqual(result["sampling_flow"]["screenshot_fetch_failures"], 0)


if __name__ == "__main__":
    unittest.main()
