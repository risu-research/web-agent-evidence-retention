"""R4 blind non-ID semantic evidence matcher tests (offline HTML fixtures)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_continuity_r3 import html_snapshot,target_in_snapshot,anchor_proxy
from weblinx_continuity_r4 import (
    channels,channel_matches_without_ids,source_only_channel_availability,
    root_relation,aggregate
)


class R4BlindedEvidenceTests(unittest.TestCase):
    def html(self,body):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p=Path(tmp.name)/"source.html"
        p.write_text("<html><body>"+body+"</body></html>",encoding="utf-8")
        return html_snapshot(p)

    def test_identity_fields_excluded_from_semantic_matcher(self):
        original=self.html(
            '<a id="first" class="action" data-webtasks-id="web-A" '
            'href="/order/47" title="Review order">View order</a>'
        )
        next_state=self.html(
            '<div><a id="second" class="changed" data-webtasks-id="web-B" '
            'href="/order/47" title="Review order">View order</a></div>'
        )
        status,target=target_in_snapshot(original,"web-A")
        self.assertEqual(status,"target_uid_unique")
        feature=channels(target)
        for forbidden in ("id","data-webtasks-id","xpath","class"):
            self.assertNotIn(forbidden,feature)
        data=channel_matches_without_ids(original,target,next_state)
        self.assertEqual(set(data),{"text","href","title"})
        self.assertTrue(all(v["status"]=="next_unique" for v in data.values()))

    def test_unique_text_can_select_wrong_node(self):
        original=self.html(
            '<button id="a" data-webtasks-id="A">Send later</button>'
        )
        next_state=self.html(
            '<button id="a" data-webtasks-id="B">Confirm</button>'
            '<button id="b" data-webtasks-id="C">Send later</button>'
        )
        _,target=target_in_snapshot(original,"A")
        status,proxy=anchor_proxy(original,next_state,"a")
        self.assertEqual(status,"site_native_proxy_candidate")
        evidence=channel_matches_without_ids(original,target,next_state)
        self.assertEqual(evidence["text"]["status"],"next_unique")
        self.assertIsNot(evidence["text"]["next_node"],proxy)

    def test_nonunique_source_text_blocks_false_confirmation(self):
        first=self.html(
            '<button id="a" data-webtasks-id="A">Continue</button>'
            '<button id="z">Continue</button>'
        )
        after=self.html(
            '<button id="a" data-webtasks-id="B">Continue</button>'
        )
        _,target=target_in_snapshot(first,"A")
        observations=channel_matches_without_ids(first,target,after)
        self.assertEqual(observations["text"]["status"],"source_ambiguous")
        availability=source_only_channel_availability(first,target)
        self.assertEqual(availability["unique_channel_count"],0)

    def test_ancestor_id_is_separate_from_blinded_evidence(self):
        original=self.html(
            '<div id="root"><button id="save" data-webtasks-id="u">Proceed</button></div>'
        )
        next_state=self.html(
            '<div id="root"><button id="save" data-webtasks-id="v">Proceed</button></div>'
        )
        _,target=target_in_snapshot(original,"u")
        relation,persist=root_relation('id("root")/button',original,target,next_state)
        self.assertEqual((relation,persist),("target_ancestor",1))
        relation,persist=root_relation('id("save")',original,target,next_state)
        self.assertEqual((relation,persist),("target_node",1))
        relation,persist=root_relation('id("nonexistent")',original,target,next_state)
        self.assertEqual((relation,persist),("absent_from_source",0))


if __name__=="__main__":
    unittest.main()
