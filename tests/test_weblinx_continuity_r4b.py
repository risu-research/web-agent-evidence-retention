"""R4B recorded-source XPath terminal ID expression regression tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_continuity_r4b import classify_xpath


class XPathTerminalRootTests(unittest.TestCase):
    def test_simple_exact_id_node(self):
        x=classify_xpath('id("some-native-id")',"some-native-id")
        self.assertEqual(x["exact_root_only"],1)
        self.assertEqual(x["id_function_with_suffix"],0)
        self.assertEqual(x["root_equals_target_native_id"],1)

    def test_id_prefix_with_nonempty_steps(self):
        x=classify_xpath("id('native')/div[2]/span","native")
        self.assertEqual(x["exact_root_only"],0)
        self.assertEqual(x["id_function_with_suffix"],1)
        self.assertEqual(x["root_equals_target_native_id"],1)

    def test_nonmatching_native_id(self):
        x=classify_xpath('id("other")',"expected")
        self.assertEqual(x["exact_root_only"],1)
        self.assertEqual(x["root_equals_target_native_id"],0)

    def test_absolute_xpath_separate(self):
        x=classify_xpath("/html/body/div[1]/button","something")
        self.assertEqual(x["id_function_prefix"],0)
        self.assertEqual(x["exact_root_only"],0)
        self.assertEqual(x["root_equals_target_native_id"],0)


if __name__=="__main__":
    unittest.main()
