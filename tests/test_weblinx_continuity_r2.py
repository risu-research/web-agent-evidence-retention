"""Tests for syntactic cross-state source inspection and URL metadata boundaries."""
import ast
import json
import unittest
from pathlib import Path


def api():
    src=Path(__file__).resolve().parents[1]/"scripts"/"weblinx_continuity_r2.py"
    tree=ast.parse(src.read_text(encoding="utf-8"))
    wanted={"compare_pages","compare_known","context_hint"}
    methods=[node for node in tree.body if
             isinstance(node,ast.FunctionDef) and node.name in wanted]
    ns={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods,type_ignores=[])),
                 str(src),"exec"),ns)
    return ns


class CrossStateTests(unittest.TestCase):
    def setUp(self):
        self.m=api()

    def test_uid_relocated_and_xpath_reassigned_are_distinct(self):
        same_signature=("button",(("id","go"),),"Go")
        a={"uid_map":{"u1":("/html/body/button[1]",same_signature),
                      "u2":("/html/body/button[2]",same_signature)},
           "xpath_map":{
             "/html/body/button[1]":("u1",same_signature),
             "/html/body/button[2]":("u2",same_signature)},
           "total_elements":4,"uid_attributed_elements":2,
           "unique_uid_elements":2,"repeated_uid_values":0}
        b={"uid_map":{"u1":("/html/body/button[2]",same_signature),
                      "u3":("/html/body/button[1]",same_signature)},
           "xpath_map":{
             "/html/body/button[1]":("u3",same_signature),
             "/html/body/button[2]":("u1",same_signature)},
           "total_elements":4,"uid_attributed_elements":2,
           "unique_uid_elements":2,"repeated_uid_values":0}
        m=self.m["compare_pages"](a,b)
        self.assertEqual(m["same_uid_at_both"],1)
        self.assertEqual(m["same_uid_changed_xpath"],1)
        self.assertEqual(m["same_xpath_different_uid"],2)
        self.assertEqual(m["same_uid_same_xpath"],0)
        self.assertEqual(m["same_uid_same_feature_signature"],1)
        self.assertEqual(m["same_xpath_same_tag"],2)

    def test_missing_context_is_unknown(self):
        c=self.m["compare_known"]
        self.assertEqual(c(None,None),"unknown")
        self.assertEqual(c(None,"https://example.org"),"unknown")
        self.assertEqual(c("tab1","tab1"),"same")
        self.assertEqual(c("tab1","tab2"),"different")

    def test_hints_cannot_be_confused_with_identity(self):
        h=self.m["context_hint"]
        t={"type":"browser","state":{"page":"page-1-0.html"},
           "action":{"arguments":{"metadata":{
               "url":"https://example.org/one","tabId":11}}}}
        hint=h(t)
        self.assertEqual(hint["tab"],"11")
        self.assertEqual(hint["url"],"https://example.org/one")
        self.assertIsNone(hint["document"])

    def test_raw_uid_map_has_no_ground_truth_discriminator(self):
        code=Path(__file__).resolve().parents[1]/"scripts"/"weblinx_continuity_r2.py"
        text=code.read_text(encoding="utf-8")
        self.assertIn('"NOT_INDEPENDENTLY_ADJUDICATED"',text)
        self.assertIn("raw_html_byte_identical",text)


if __name__=="__main__":
    unittest.main()
