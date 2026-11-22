"""Exercise migrated parser rules without fetching WebLINX."""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "raw_sha": "36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8",
    "pre_sha": "a30ff2cbecb75f2d04fac75a2b92721c6c9e3f13",
}


def load_helpers(path):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    names = {"WS", "FIELD", "KV", "NUM"}
    fns = {"norm", "parse_bbox", "parse_doc"}
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in names for t in node.targets
        ):
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in fns:
            nodes.append(node)
    isolated = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    ns = {"re": re}
    exec(compile(isolated, str(path), "exec"), ns)
    return ns, src


class OriginalProtocolTests(unittest.TestCase):
    def test_both_sources_parse(self):
        for name in ("reproduce_confirm.py", "reproduce_universe.py"):
            path = ROOT / "scripts" / name
            ast.parse(path.read_text(encoding="utf-8"))

    def test_dataset_pins(self):
        for name in ("reproduce_confirm.py", "reproduce_universe.py"):
            src = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn(PINS["raw_sha"], src)
            self.assertNotIn('dataset_info("McGill-NLP/', src)
            if name == "reproduce_universe.py":
                self.assertIn(PINS["pre_sha"], src)

    def test_semantic_attributes_exclude_locators(self):
        doc = (
            '[[tag]] BUTTON [[text]] Delete '
            '[[attributes]] role="button" id="secret-id" class="row" '
            'for="other" aria-label="Remove" href="/remove" '
            '[[bbox]] x=10 y=20 width=30 height=40'
        )
        for name in ("reproduce_confirm.py", "reproduce_universe.py"):
            ns, src = load_helpers(ROOT / "scripts" / name)
            candidate = ns["parse_doc"](doc, "uid-one")
            self.assertEqual(candidate["text"], "delete")
            self.assertEqual(candidate["tag"], "button")
            self.assertEqual(candidate["bbox"], (10.0, 20.0, 30.0, 40.0))
            sem = dict(candidate["sem"])
            self.assertEqual(sem["role"], "button")
            self.assertEqual(sem["aria-label"], "remove")
            self.assertNotIn("id", sem)
            self.assertNotIn("class", sem)
            self.assertNotIn("for", sem)
            self.assertIn('c["phash"] is None or', src)
            self.assertIsNone(ns["parse_bbox"]("x=10 y=20 width=0 height=40"))


if __name__ == "__main__":
    unittest.main()
