"""R3 candidate/replay provenance and ordinary HTML id proxy tests."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_continuity_r3 import (
    parse_dmr, recorded_action_element, next_browser_idx, html_snapshot,
    target_in_snapshot, anchor_proxy, stable_attrs_compatible, assess_action,
    numeric_summary,
)


class R3SourceTests(unittest.TestCase):
    def html_file(self,content):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path=Path(tmp.name)/"source.html"
        path.write_text("<html><body>"+content+"</body></html>",encoding="utf-8")
        return path

    def test_action_element_uid_is_separate_from_dmr_label(self):
        doc='[[tag]] button [[xpath]] /html/body/button [[attributes]] data-webtasks-id="d1" id="run"'
        obj=parse_dmr(doc)
        self.assertEqual(obj["uid_in_attributes"],"d1")
        self.assertEqual(obj["ordinary_html_id"],"run")
        self.assertEqual(obj["xpath"],"/html/body/button")
        action=recorded_action_element({
            "action":{"intent":"click","arguments":{
                "element":{"attributes":{"data-webtasks-id":"r1","id":"run"},
                           "tagName":"BUTTON","xpath":"/html/body/button"},
                "uid":"a2",
            }}
        })
        self.assertEqual(action["uid"],"r1")
        self.assertEqual(action["args_uid"],"a2")
        self.assertNotEqual(obj["uid_in_attributes"],action["uid"])

    def test_browser_adjacency_never_skips_to_third_browser(self):
        turns=[
            {"type":"browser","state":{"page":"first.html"}},
            {"type":"chat"},
            {"type":"browser","state":{}},
            {"type":"chat"},
            {"type":"browser","state":{"page":"later.html"}},
        ]
        self.assertEqual(next_browser_idx(turns,0),2)
        self.assertEqual(next_browser_idx(turns,2),4)
        self.assertIsNone(next_browser_idx(turns,4))

    def test_target_uid_duplicate_is_ambiguous(self):
        snapshot=html_snapshot(self.html_file(
            '<p data-webtasks-id="same" id="a">A</p>'
            '<p data-webtasks-id="same" id="b">B</p>'
        ))
        self.assertEqual(snapshot["status"],"parsed")
        status,node=target_in_snapshot(snapshot,"same")
        self.assertEqual(status,"target_uid_duplicated_in_html")
        self.assertIsNone(node)

    def test_site_id_reuse_with_changed_type_excluded(self):
        first=html_snapshot(self.html_file(
            '<input id="row1" name="amount" type="text" data-webtasks-id="u1">'
        ))
        after=html_snapshot(self.html_file(
            '<input id="row1" name="amount" type="checkbox" data-webtasks-id="u2">'
        ))
        status,node=anchor_proxy(first,after,"row1")
        self.assertEqual(status,"site_id_signature_conflict")
        self.assertIsNone(node)

    def test_site_id_reuse_same_tag_only_is_proxy(self):
        first=html_snapshot(self.html_file(
            '<button id="pay" name="submit" data-webtasks-id="u1">Pay</button>'
        ))
        second=html_snapshot(self.html_file(
            '<button id="pay" name="submit" data-webtasks-id="u2">Pay</button>'
        ))
        status,node=anchor_proxy(first,second,"pay")
        self.assertEqual(status,"site_native_proxy_candidate")
        self.assertEqual(node.attrib["data-webtasks-id"],"u2")
        self.assertTrue(stable_attrs_compatible(
            first["site_id_map"]["pay"][0],node))

    def test_source_missing_is_unknown_without_imputation(self):
        source=self.html_file('<button id="same" data-webtasks-id="uid1">Go</button>')
        turns=[
            {"type":"browser","state":{},"action":{"intent":"click",
              "arguments":{"element":{"attributes":{"data-webtasks-id":"uid1"},
                                      "xpath":"/html/body/button",
                                      "tagName":"BUTTON"}}}},
            {"type":"browser","state":{"page":"later.html"}},
        ]
        row=assess_action(
            "example",0,turns,{
                "uid":"uid1",
                "dmr":{"uid_in_attributes":"uid1","xpath":"/html/body/button",
                       "ordinary_html_id":"same","tag":"button"},
                "target_rank":1
            },{("example","later.html"):("fetched",source)},{}
        )
        self.assertEqual(row["direct_current_html"],0)
        self.assertEqual(row["current_target_uid_status"],"source_unavailable")
        self.assertEqual(row["continuity_proxy_status"],"source_not_eligible")
        self.assertEqual(row["action_uid_equals_positive_uid"],1)


if __name__=="__main__":
    unittest.main()
