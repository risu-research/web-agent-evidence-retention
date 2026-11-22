"""Deterministic replay inventory and no-imputation regression cases."""
import ast
import json
import re
import unittest
from pathlib import Path


def load_inventory_functions():
    source=Path(__file__).resolve().parents[1]/"scripts"/"weblinx_continuity_r1.py"
    tree=ast.parse(source.read_text(encoding="utf-8"))
    names={"state_name","replay_data","pair_inventory"}
    nodes=[node for node in tree.body
           if isinstance(node,ast.FunctionDef) and node.name in names]
    ns={"json":json,"SAFE_FILE":re.compile(r"^[A-Za-z0-9_.-]+\.html$",re.I)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
                 str(source),"exec"),ns)
    return ns


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.methods=load_inventory_functions()

    def test_direct_pages_only_with_intervening_chat(self):
        turns=[
            {"type":"browser","state":{"page":"page-1-0.html","screenshot":"s1.png"}},
            {"type":"chat","utterance":"This chat is not a browser step"},
            {"type":"browser","state":{"page":"page-2-0.html","screenshot":"s2.png"}},
            {"type":"browser","state":{"page":None}},
            {"type":"browser","state":{"page":"page-4-0.html"}},
            {"type":"browser","state":{"page":"page-4-0.html"}},
            {"type":"browser","state":{"page":"page-7-0.html"}},
        ]
        metrics,pairs=self.methods["pair_inventory"]("abcdefg",turns,{2})
        self.assertEqual(metrics["browser_turns"],6)
        self.assertEqual(metrics["direct_html_turns"],5)
        self.assertEqual(metrics["adjacent_browser_pairs_with_html"],3)
        self.assertEqual(metrics["adjacent_same_html_filename"],1)
        self.assertEqual(len(pairs),2)
        self.assertEqual((pairs[0]["from_turn"],pairs[0]["to_turn"]),(0,2))
        self.assertEqual(pairs[0]["intervening_chat_turns"],1)
        self.assertEqual((pairs[1]["from_turn"],pairs[1]["to_turn"]),(5,6))

    def test_deterministic_source_selection_before_html(self):
        turns=[{"type":"browser","state":{"page":f"page-{i}-0.html"}}
               for i in range(8)]
        _,pairs=self.methods["pair_inventory"]("abcdefg",turns,{5})
        self.assertEqual(len(pairs),3)
        self.assertEqual([(p["from_turn"],p["to_turn"]) for p in pairs],
                         [(4,5),(5,6),(3,4)])
        self.assertTrue(all(p["near_original_action_distance"]<=1 for p in pairs))

    def test_schema_and_missing_values(self):
        parsed=self.methods["replay_data"]
        path=Path("/tmp/weblinx_dummy_replay_schema_test.json")
        try:
            path.write_text(json.dumps({"data":[{"type":"browser","state":{}},
                                                {"type":"chat"}]}),encoding="utf-8")
            self.assertEqual(len(parsed(path)),2)
            self.assertIsNone(self.methods["state_name"](
                {"state":{"page":{"unexpected":"object"}}},"page"))
        finally:
            path.unlink(missing_ok=True)


if __name__=="__main__":
    unittest.main()
