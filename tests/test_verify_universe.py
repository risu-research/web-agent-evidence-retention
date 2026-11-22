"""Regression checks for the frozen candidate-expansion sensitivity."""
import unittest
from scripts.verify_universe import RAW_PIN, PRE_PIN, REFERENCE, check


def fixture():
    return {
        "dataset_pins": {"raw": RAW_PIN, "preprocessed": PRE_PIN},
        "universe_sensitivity": {
            str(k): {
                "n": 598,
                "textdom": {"unique_rate": rates[0] / 100},
                "joint": {"unique_rate": rates[1] / 100},
                "visual_escalation_rate": rates[2] / 100,
            }
            for k, rates in REFERENCE.items()
        },
    }


class SensitivityTests(unittest.TestCase):
    def test_frozen_rates(self):
        self.assertEqual(check(fixture()), [])

    def test_failed_rates_rejected(self):
        sample = fixture()
        sample["universe_sensitivity"]["50"]["joint"]["unique_rate"] = .999
        self.assertTrue(any("50.joint" in s for s in check(sample)))


if __name__ == "__main__":
    unittest.main()
