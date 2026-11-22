"""R7 real compact Playwright DOM decoder and conservative audit unit checks."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_r7_trace_dom_auditor import (
    SnapshotDecoder,Node,rows_from_admin_snapshot,
    target_row_from_snapshot,trace_auditor
)


def original_table(first_a="Seed-A",first_b="Seed-B",include_b=True):
    rows=[]
    for name,value in [("r6_a",first_a),("r6_b",first_b)]:
        if name=="r6_b" and not include_b:continue
        rows.append(["TR",{},["TH",{"class":"field-username"},
                                ["A",{"__playwright_target__":""} if name=="r6_a" else {},name]],
                              ["TD",{"class":"field-first_name"},value]])
    return ["HTML",{},["BODY",{},["TABLE",{"id":"result_list"},
                                  ["TBODY",{},*rows]]]]


class R7SnapshotTests(unittest.TestCase):
    def test_real_playwright_array_encoding_not_string_find(self):
        decoder=SnapshotDecoder()
        tree=decoder.decode({"frameId":"frame-A","html":original_table()})
        self.assertIsInstance(tree,Node)
        self.assertEqual(rows_from_admin_snapshot(tree),{
            "A":"Seed-A","B":"Seed-B"})
        guess,found,_=target_row_from_snapshot(tree)
        self.assertEqual(guess,"A")
        self.assertTrue(found)

    def test_cross_snapshot_subtree_reference_uses_postorder_node_index(self):
        decoder=SnapshotDecoder()
        source=["HTML",{},["BODY",{},["DIV",{"id":"target"},"ok"]]]
        root=decoder.decode({"frameId":"frame-A","html":source})
        self.assertEqual(root.name,"HTML")
        # POSTORDER: text "ok" index0, DIV index1, BODY index2, HTML index3.
        reused=decoder.decode({"frameId":"frame-A","html":[[1,3]]})
        self.assertIs(root,reused)
        self.assertEqual(decoder.ref_count,1)
        self.assertEqual(decoder.ref_failures,0)
        self.assertEqual(rows_from_admin_snapshot(reused),None)

    def test_unresolved_reference_is_explicit_not_silent(self):
        decoder=SnapshotDecoder()
        self.assertIsNone(decoder.decode({"frameId":"frame-X","html":[[1,2]]}))
        self.assertEqual(decoder.ref_failures,1)

    def test_screen_edit_and_delete_deltas_are_visible(self):
        decoder=SnapshotDecoder()
        before=rows_from_admin_snapshot(decoder.decode({
            "frameId":"x","html":original_table()}))
        after_edit=rows_from_admin_snapshot(decoder.decode({
            "frameId":"x","html":original_table(first_a="R6-EDIT-01")}))
        after_delete=rows_from_admin_snapshot(decoder.decode({
            "frameId":"x","html":original_table(include_b=False)}))
        self.assertEqual([k for k in before if before[k]!=after_edit.get(k)],["A"])
        self.assertEqual([k for k in before if before[k]!=after_delete.get(k)],["B"])

    def test_raw_trace_does_not_require_original_observer_or_SQL(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"source.zip"
            records=[
               {"type":"before","callId":"c","method":"click",
                "params":{"selector":"a.action"}},
               {"type":"frame-snapshot","snapshot":{
                    "callId":"c","phase":"action","isMainFrame":True,
                    "frameId":"F","frameUrl":"http://local/admin/auth/user/",
                    "html":original_table()}},
               {"type":"after","callId":"c"}
            ]
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("trace.trace","".join(json.dumps(x)+"\n" for x in records))
                z.writestr("trace.network","")
            result=trace_auditor(p,{"A":2,"B":3})
            self.assertEqual(result["q1_selector_present"],1)
            self.assertEqual(result["q2_visible_receiver_inferred"],"A")
            self.assertEqual(result["q3_actual_POST_route"],"none")
            self.assertEqual(result["q4_UI_effect_inferred"],"abstain")
            self.assertEqual(result["q5_first_click_status"],"returned")
            self.assertFalse(result["raw_trace_retained"])

if __name__=="__main__":unittest.main()
