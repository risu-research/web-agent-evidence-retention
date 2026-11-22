"""Focused R3D generator comparison and root-anchor diagnostics."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_continuity_r3 import html_snapshot,target_in_snapshot,anchor_proxy
from weblinx_continuity_r3d import root_anchor_diagnostic


class RootAnchorTests(unittest.TestCase):
    def page(self,body):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path=Path(temp.name)/"site.html"
        path.write_text("<html><body>"+body+"</body></html>",encoding="utf-8")
        return html_snapshot(path)

    def test_anchor_descendant(self):
        source=self.page('<div id="root"><section><button data-webtasks-id="real" id="save">S</button></section></div>')
        _,target=target_in_snapshot(source,"real")
        self.assertEqual(root_anchor_diagnostic('id("root")/section/button',
                                                source,target),
                         ("root_anchor_unique",1,1))
        self.assertEqual(root_anchor_diagnostic('id("other")/section/button',
                                                source,target),
                         ("root_anchor_absent",0,0))

    def test_root_anchor_present_but_not_ancestor(self):
        source=self.page('<main id="root"></main><div><button data-webtasks-id="real">B</button></div>')
        _,target=target_in_snapshot(source,"real")
        self.assertEqual(root_anchor_diagnostic('id("root")/button',source,target),
                         ("root_anchor_unique",1,0))

    def test_duplicate_and_nonstandard_id(self):
        source=self.page('<div id="root"></div><div id="root"></div><button data-webtasks-id="real"></button>')
        _,target=target_in_snapshot(source,"real")
        self.assertEqual(root_anchor_diagnostic("id('root')/button",source,target),
                         ("root_anchor_duplicated",0,0))
        self.assertEqual(root_anchor_diagnostic("/html/body/button",source,target),
                         ("other_expression",0,0))


if __name__=="__main__":
    unittest.main()
