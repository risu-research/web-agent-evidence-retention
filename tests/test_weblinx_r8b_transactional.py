"""R8B network comparator avoids posthoc acceptance of changing POST routes."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import weblinx_r8b_transactional as b

class BTests(unittest.TestCase):
    def make(self):
        return {
           "mode":"control","pair":1,
           "operation":"edit","locator":"positional",
           "q1_selector":1,"q2_click":"A","q3_POST":"A",
           "q4_UI_effect":"A","q5_first_click_status":"returned",
           "q6_trace":"abstain","pixel_before_sha256":"same",
           "pixel_after_sha256":"same",
           "initial_visible_rows":{"A":"Seed-A","B":"Seed-B"},
           "final_visible_rows":{"A":"R8-COMMON","B":"Seed-B"},
           "unresolved_refs":0,"server_POST_count":1,
           "network_projection":[
             ["GET","/admin/auth/user/",200],
             ["GET","/admin/jsi18n/",200],
             ["GET","/admin/auth/user/2/change/",200],
             ["POST","/admin/auth/user/2/change/",302],
             ["GET","/admin/auth/user/",200]]
        }

    def test_auxiliary_get_cancel_is_reported_not_transactional(self):
        a=self.make()
        other=dict(a, mode="shadow",
            network_projection=[
             ["GET","/admin/auth/user/",200],
             ["GET","/admin/jsi18n/",-1],
             ["GET","/admin/auth/user/2/change/",200],
             ["POST","/admin/auth/user/2/change/",302],
             ["GET","/admin/auth/user/",200]])
        b.AUXILIARY.clear()
        verdict=b.corrected_compare(a,other)
        self.assertTrue(all(verdict.values()))
        self.assertFalse(b.AUXILIARY[-1]["auxiliary_requests_equal"])
        self.assertFalse(b.AUXILIARY[-1]["ordered_full_admin_network_equal"])

    def test_mutation_post_mismatch_fails(self):
        a=self.make()
        other=dict(a,mode="shadow",network_projection=[
            ["GET","/admin/auth/user/",200],
            ["GET","/admin/auth/user/2/change/",200],
            ["POST","/admin/auth/user/2/change/",200],
            ["GET","/admin/auth/user/",200]])
        self.assertFalse(b.corrected_compare(a,other)["network_projection"])

if __name__=="__main__":unittest.main()
