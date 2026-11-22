"""Unit tests for the frozen-cohort identifier baseline."""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "identifier_baseline.py"


def isolated_functions():
    tree=ast.parse(SCRIPT.read_text(encoding="utf-8"))
    wanted={"norm","parse_bbox","parse_doc","locator_fields","is_joint_compatible","measure_identifier_action"}
    names={"WS","FIELD","KV","NUM","PHASH_T"}
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in wanted:
            nodes.append(node)
        elif isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id in names for t in node.targets):
            nodes.append(node)
    ns={"re":re}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
                 str(SCRIPT),"exec"),ns)
    return ns


class LocatorTests(unittest.TestCase):
    def setUp(self):
        self.ns=isolated_functions()
        self.parser=self.ns["locator_fields"]

    def test_xpath_id_and_dataset_uid_separation(self):
        doc=("[[tag]] button [[xpath]] /html/body/Div[2]/button[1] "
             "[[text]] Save [[bbox]] x=1 y=2 width=20 height=10 "
             "[[attributes]] id='submit' data-webtasks-id='instrumented-42' "
             "class='row' for='input'")
        a=self.parser(doc)
        self.assertEqual(a["xpath"],"/html/body/Div[2]/button[1]")
        self.assertEqual(a["html_id"],"submit")
        self.assertEqual(a["webtasks_id"],"instrumented-42")
        self.assertNotIn("class",a)
        self.assertNotIn("for",a)

    def test_missing_identifier_has_no_id_only_success(self):
        target={"uid":"a","label":1,"rank":1,"xpath":"","html_id":"",
                "webtasks_id":"","text":"submit","tag":"button","sem":(),"phash":None}
        self.assertIsNone(self.ns["measure_identifier_action"]([target],target)["all_html_id_n"])
        self.assertIsNone(self.ns["measure_identifier_action"]([target],target)["all_xpath_n"])

    def test_exact_xpath_disambiguates_joint_collision(self):
        target={"uid":"target","label":1,"rank":1,"xpath":"/html/body/button[1]",
                "html_id":"action-one","webtasks_id":"instrumented",
                "text":"delete","tag":"button","sem":(),"phash":None}
        competing={**target,"uid":"other","label":0,"rank":2,
                   "xpath":"/html/body/button[2]","html_id":"action-two",
                   "webtasks_id":"second"}
        out=self.ns["measure_identifier_action"]([target,competing],target)
        self.assertEqual(out["all_joint_n"],2)
        self.assertEqual(out["all_xpath_n"],1)
        self.assertEqual(out["all_joint_xpath_n"],1)
        self.assertEqual(out["all_html_id_n"],1)
        self.assertEqual(out["all_uid_n"],1)

    def test_target_omission_survives_perfect_identifier(self):
        target={"uid":"target","label":1,"rank":11,"xpath":"/body/target",
                "html_id":"x","webtasks_id":"dataset-uid",
                "text":"submit","tag":"button","sem":(),"phash":None}
        competitor={**target,"uid":"other","label":0,"rank":1,
                    "xpath":"/body/other","html_id":"y","webtasks_id":"other"}
        out=self.ns["measure_identifier_action"]([target,competitor],target)
        self.assertEqual(out["10_present"],0)
        self.assertEqual(out["10_uid_n"],0)
        self.assertEqual(out["all_uid_n"],1)

    def test_no_xpath_falls_back_to_joint(self):
        target={"uid":"target","label":1,"rank":1,"xpath":"",
                "html_id":"","webtasks_id":"",
                "text":"save","tag":"button","sem":(),"phash":None}
        competitor={**target,"uid":"other","label":0,"rank":2}
        out=self.ns["measure_identifier_action"]([target,competitor],target)
        self.assertEqual(out["all_joint_xpath_n"],out["all_joint_n"])
        self.assertEqual(out["all_joint_html_id_n"],out["all_joint_n"])


if __name__=="__main__":
    unittest.main()
