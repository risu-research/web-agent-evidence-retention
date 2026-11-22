"""R8 predeclared matrix and leakage/strict-equivalence regression tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from weblinx_r8_server_divergence import (
    paired_matrix, packet_auditor, compare_pair, safe_packet_size
)


class ServerDivergenceTests(unittest.TestCase):
    def test_original_locator_action_matrix_is_complete(self):
        episodes = paired_matrix()
        self.assertEqual(len(episodes), 12)
        self.assertEqual(len(set(episodes)), 12)
        self.assertEqual(len({(p, op, loc) for p, op, loc, m in episodes}), 6)
        for pair in range(1, 7):
            modes = [m for p, op, loc, m in episodes if p == pair]
            self.assertEqual(set(modes), {"control", "shadow"})
            self.assertEqual(modes, ["control","shadow"] if pair%2 else
                             ["shadow","control"])

    def test_packet_is_based_on_SQL_bytes_not_assignment(self):
        self.assertEqual(packet_auditor({
            "before_B_last_login":None,"after_B_last_login":None
        }), "unchanged")
        self.assertEqual(packet_auditor({
            "before_B_last_login":None,
            "after_B_last_login":"2026-01-01 00:00:00"
        }), "changed")
        self.assertEqual(packet_auditor({}), "abstain")

    def test_unchanged_projection_with_divergent_oracle(self):
        x = {"mode":"control", "operation":"edit", "locator":"positional",
             "q1_selector":1, "q2_click":"A", "q3_POST":"A",
             "q4_UI_effect":"A", "q5_first_click_status":"returned",
             "q6_trace":"abstain",
             "pixel_before_sha256":"abc", "pixel_after_sha256":"def",
             "initial_visible_rows":{"A":"Seed-A","B":"Seed-B"},
             "final_visible_rows":{"A":"R8-COMMON","B":"Seed-B"},
             "network_projection":[["GET","/admin/auth/user/",200],
                                    ["POST","/admin/auth/user/2/change/",302]],
             "unresolved_refs":0, "server_POST_count":1,
             "q6_truth":"unchanged"}
        y = dict(x,mode="shadow",q6_truth="changed")
        self.assertTrue(all(compare_pair(x,y).values()))
        y["network_projection"]=[["POST","/admin/auth/user/2/change/",302]]
        self.assertFalse(compare_pair(x,y)["network_projection"])
        y["network_projection"]=x["network_projection"]
        y["final_visible_rows"]={"A":"Seed-A","B":"Seed-B"}
        self.assertFalse(compare_pair(x,y)["final_visible_rows"])

    def test_packet_byte_cost_measured(self):
        a,z = safe_packet_size(None,"2026-01-01 00:00:00")
        self.assertGreater(a,z)
        self.assertGreater(z,0)


if __name__=="__main__":
    unittest.main()
