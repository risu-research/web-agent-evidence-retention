"""Lock source-validated R3C/R3D outcomes and category-only publication."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"results"


def load_csv(name):
    with (ROOT/name).open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        fields=set(reader.fieldnames)
        rows=list(reader)
    return fields,rows


class ArchivedRecordedXPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads((ROOT/"weblinx_continuity_r3c_summary.json").read_text())
        cls.d=json.loads((ROOT/"weblinx_continuity_r3d_summary.json").read_text())
        cls.b=json.loads((ROOT/"weblinx_continuity_r3d_cluster_bootstrap.json").read_text())
        cls.cfields,cls.crows=load_csv("weblinx_continuity_r3c_actions.csv")
        cls.dfields,cls.drows=load_csv("weblinx_continuity_r3d_cases.csv")

    def test_original_source_xpath_dialect(self):
        self.assertEqual(len(self.crows),600)
        self.assertEqual(self.c["xpath_dialects"],{
            "absolute_path":32,"xpath_id_function":568
        })
        self.assertEqual(self.c["current_expression_results"],{
            "unique_recorded_target":589,"no_node":10,"unique_other_node":1
        })
        self.assertEqual(self.c["next_expression_results"],{
            "unique_node":458,"no_node":102,"html_unavailable":40
        })
        self.assertFalse(self.c["logical_element_identity_independently_adjudicated"])

    def test_selected_anomalies_and_proxy_cohort(self):
        self.assertEqual(len(self.drows),86)
        self.assertEqual(len({(r["demo"],r["turn"]) for r in self.drows}),86)
        self.assertEqual(self.d["initial_action_locator_anomalies_n"],11)
        self.assertEqual(self.d["site_native_proxy_n"],75)
        self.assertEqual(self.d["cohort_overlap_n"],0)
        self.assertEqual(self.d["original_anomaly_root_anchor_statuses"],{
            "root_anchor_absent":7,"root_anchor_unique":4
        })
        self.assertEqual(self.d["proxy_replay_xpath_outcomes"],{
            "unique_proxy_node":75
        })
        self.assertEqual(self.d["proxy_canonical_xpath_outcomes"],{
            "no_node":7,"unique_other_node":1,"unique_proxy_node":67
        })
        self.assertEqual(self.d["proxy_paired_recovery"],{"both":67,"replay_only":8})
        self.assertFalse(self.d["independent_logical_element_identity_labels"])

    def test_original_75_site_native_subset_consistency(self):
        proxies=[r for r in self.drows if r["in_site_native_75"]=="1"]
        self.assertEqual(len(proxies),75)
        self.assertEqual(len({r["demo"] for r in proxies}),31)
        self.assertEqual(sum(r["proxy_canonical_path_changed"]=="1" for r in proxies),16)
        self.assertEqual(sum(r["url_context_hint"]=="same" for r in proxies),73)
        self.assertEqual(sum(r["canonical_xpath_selects_proxy"]=="unique_proxy_node"
                             and r["proxy_canonical_path_changed"]=="1"
                             for r in proxies),8)

    def test_bootstrap_and_public_schema(self):
        self.assertEqual(self.b["replicates"],5000)
        self.assertEqual(self.b["demonstrations"],31)
        self.assertEqual(self.b["seed"],2026112239)
        self.assertAlmostEqual(
            self.b["metrics"]["paired_replay_minus_canonical"]["estimate"],
            8/75)
        self.assertTrue(self.cfields.isdisjoint({
            "xpath","uid","html","text","url","site_id","source_doc"
        }))
        self.assertTrue(self.dfields.isdisjoint({
            "xpath","uid","html","text","url","site_id","source_doc"
        }))


if __name__=="__main__":
    unittest.main()
