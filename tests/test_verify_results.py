"""Check reference arithmetic and result-verifier failure behavior."""
import unittest
from scripts.verify_results import EXPECTED, PIN, check


def reference_fixture():
    result = {
        "raw_sha": PIN,
        "sampling": {"analyzed": 600, "demo_n": 55, "mapped": 750,
                     "map_skips": {}, "compute_skips": {}, "fetch_failures": {}},
        "population": {"target_turns": 1422, "demo_n": 99,
                       "ambiguous_target_groups_excluded": 16},
        "topk_unconditional": {},
        "all_universe": {},
        "strata": {"blank": {"n": 390}, "nonblank": {"n": 210}},
        "phash_sensitivity": {},
    }
    for k in (10, 20, 50):
        covered, recovered = EXPECTED[f"top{k}"]
        result["topk_unconditional"][str(k)] = {
            "target_present_rate": covered / 600,
            "joint_unique_over_all_actions": recovered / 600,
            "joint_unique_conditional_present": recovered / covered,
        }
    for key in ("text", "dom", "textdom", "visual", "joint"):
        result["all_universe"][key] = {"n": 600, "unique_rate": EXPECTED[key] / 600}
    result["all_universe"]["visual_escalation_rate"] = EXPECTED["visual_escalation"] / 600
    for threshold, count in EXPECTED["phash_joint"].items():
        result["phash_sensitivity"][threshold] = {
            "overall": {"joint": {"unique_rate": count / 600}}
        }
    return result


class FrozenCountTests(unittest.TestCase):
    def test_candidate_order(self):
        entries = [EXPECTED[f"top{x}"] for x in (10, 20, 50)] + [EXPECTED["all"]]
        self.assertEqual(entries, sorted(entries))

    def test_representation_arithmetic(self):
        self.assertEqual(EXPECTED["textdom"] - EXPECTED["text"], 245)
        self.assertEqual(EXPECTED["joint"] - EXPECTED["textdom"], 127)
        self.assertEqual(600 - EXPECTED["textdom"], EXPECTED["visual_escalation"])
        self.assertEqual(600 - EXPECTED["joint"], 70)
        self.assertEqual(EXPECTED["blank"] + EXPECTED["nonblank"], 600)

    def test_reference_fixture(self):
        self.assertEqual(check(reference_fixture()), [])

    def test_rejects_wrong_revision(self):
        wrong = reference_fixture()
        wrong["raw_sha"] = "current-latest"
        self.assertTrue(any("raw_sha" in x for x in check(wrong)))

    def test_rejects_inflated_recovery(self):
        wrong = reference_fixture()
        wrong["topk_unconditional"]["10"]["joint_unique_over_all_actions"] = 0.98
        self.assertTrue(any("top10 end-to-end" in x for x in check(wrong)))

    def test_rejects_posthoc_skips(self):
        wrong = reference_fixture()
        wrong["sampling"]["compute_skips"] = {"target_no_hash": 1}
        self.assertTrue(any("compute_skips" in x for x in check(wrong)))


if __name__ == "__main__":
    unittest.main()
