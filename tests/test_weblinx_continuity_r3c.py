"""Inspect captured XPath syntax by evaluation, with synthetic unchanged/changed DOM."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_continuity_r3 import html_snapshot,target_in_snapshot,anchor_proxy
from weblinx_continuity_r3c import xpath_dialect,run_xpath,current_result,next_proxy_result


class CapturedXPathTests(unittest.TestCase):
    def page(self,html):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        p=Path(folder.name)/"source.html"
        p.write_text(html,encoding="utf-8")
        return html_snapshot(p)

    def test_recorded_id_function_equals_absolute_source(self):
        s=self.page('<html><body><div id="root"><button id="go" data-webtasks-id="u">Go</button></div></body></html>')
        _,target=target_in_snapshot(s,"u")
        self.assertEqual(xpath_dialect('id("root")/button[1]'),"xpath_id_function")
        self.assertEqual(current_result(s,target,'id("root")/button[1]'),
                         "unique_recorded_target")
        self.assertEqual(current_result(s,target,'/html/body/div/button'),
                         "unique_recorded_target")
        self.assertEqual(current_result(s,target,'/html/body/div'),
                         "unique_other_node")

    def test_next_state_reassignment_against_site_native_id(self):
        first=self.page('<html><body><div id="root"><button id="save" data-webtasks-id="a">Save</button></div></body></html>')
        next_state=self.page('<html><body><div id="root"><button id="other" data-webtasks-id="x">Other</button><button id="save" data-webtasks-id="b">Save</button></div></body></html>')
        status,proxy=anchor_proxy(first,next_state,"save")
        self.assertEqual(status,"site_native_proxy_candidate")
        self.assertEqual(next_proxy_result(next_state,'id("root")/button[1]',proxy),
                         "unique_other_node")
        self.assertEqual(next_proxy_result(next_state,'id("root")/button[2]',proxy),
                         "unique_proxy_node")

    def test_missing_and_invalid_expressions_are_separate(self):
        s=self.page('<html><body><div id="root">A</div></body></html>')
        self.assertEqual(run_xpath(s,"")["status"],"missing_xpath")
        self.assertEqual(run_xpath(s,"/html/body/none")["status"],"no_node")
        self.assertEqual(run_xpath(s,"//*[")["status"],"expression_evaluation_error")
        self.assertEqual(run_xpath({"status":"no_source"},"/html")["status"],"html_unavailable")

    def test_multi_match_with_target_preserved(self):
        s=self.page('<html><body><button data-webtasks-id="a"></button><button data-webtasks-id="b"></button></body></html>')
        _,node=target_in_snapshot(s,"a")
        self.assertEqual(current_result(s,node,"//button"),"multiple_including_target")
        self.assertEqual(current_result(s,node,"//div"),"no_node")


if __name__=="__main__":
    unittest.main()
