"""Check exact original bounding-box validity criteria without network imports."""
import ast
import math
import re
import unittest
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/"scripts"/"residual_missing_crop.py"


def get_rule():
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
    selection=[]
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {"FIELD","NUM"} for t in n.targets):
            selection.append(n)
        elif isinstance(n,ast.FunctionDef) and n.name=="classify_bbox":
            selection.append(n)
    ns={"re":re,"math":math}
    exec(compile(ast.fix_missing_locations(ast.Module(body=selection,type_ignores=[])),str(SOURCE),"exec"),ns)
    return ns["classify_bbox"]


class MissingGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rule=get_rule()

    def test_absent(self):
        self.assertEqual(self.rule("[[tag]] div",1920,1080),"bbox_absent")

    def test_incomplete(self):
        self.assertEqual(self.rule("[[bbox]] x=3 y=4 width=20",1920,1080),"bbox_incomplete")

    def test_small(self):
        self.assertEqual(self.rule("[[bbox]] x=3 y=4 width=2 height=20",1920,1080),"bbox_too_small")

    def test_clipped_off_frame(self):
        self.assertEqual(self.rule("[[bbox]] x=300 y=4 width=20 height=20",100,100),
                         "bbox_clipped_below_three")

    def test_valid_and_partially_clipped(self):
        self.assertEqual(self.rule("[[bbox]] x=3 y=4 width=20 height=20",100,100),"valid")
        self.assertEqual(self.rule("[[bbox]] x=-10 y=4 width=20 height=20",100,100),"valid")


if __name__=="__main__":
    unittest.main()
