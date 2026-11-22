"""Actual lxml HTML-source parsing fixture tests for the R2 continuity audit."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_continuity_r2 import inspect_html_bytes,compare_pages


def html(contents):
    return ("<html><body>"+contents+"</body></html>").encode("utf-8")


class RawHtmlParsingTests(unittest.TestCase):
    def test_uid_xpath_reassignment_in_real_html_parser(self):
        before=inspect_html_bytes(html(
            '<div data-webtasks-id="stable" id="panel">Box</div>'
            '<button data-webtasks-id="old" id="action">Press</button>'
        ))
        after=inspect_html_bytes(html(
            '<div data-webtasks-id="stable" id="panel">Box</div>'
            '<button data-webtasks-id="new" id="action">Press</button>'
        ))
        self.assertEqual((before["parse_status"],after["parse_status"]),
                         ("parsed","parsed"))
        stats=compare_pages(before,after)
        self.assertEqual(stats["same_uid_at_both"],1)
        self.assertEqual(stats["same_uid_same_xpath"],1)
        self.assertEqual(stats["same_xpath_different_uid"],1)
        self.assertEqual(stats["same_uid_changed_xpath"],0)

    def test_duplicate_uid_is_excluded_from_unique_identity(self):
        doc=inspect_html_bytes(html(
            '<span data-webtasks-id="duplicate">A</span>'
            '<span data-webtasks-id="duplicate">B</span>'
            '<span data-webtasks-id="unique">C</span>'
        ))
        self.assertEqual(doc["uid_attributed_elements"],3)
        self.assertEqual(doc["unique_uid_elements"],1)
        self.assertEqual(doc["repeated_uid_values"],1)
        self.assertNotIn("duplicate",doc["uid_map"])

    def test_same_uid_moved_xpath_and_text_modified(self):
        before=inspect_html_bytes(html(
            '<section><p data-webtasks-id="id-1">Old</p></section>'
        ))
        after=inspect_html_bytes(html(
            '<div><section><p data-webtasks-id="id-1">New</p></section></div>'
        ))
        changes=compare_pages(before,after)
        self.assertEqual(changes["same_uid_at_both"],1)
        self.assertEqual(changes["same_uid_changed_xpath"],1)
        self.assertEqual(changes["same_uid_same_feature_signature"],0)
        self.assertEqual(changes["same_uid_same_xpath_and_features"],0)

    def test_file_bytes_vs_content_change(self):
        original=html('<b data-webtasks-id="same"></b>')
        first=inspect_html_bytes(original)
        same=inspect_html_bytes(original)
        newer=inspect_html_bytes(original.replace(b'same',b'changed'))
        self.assertEqual(first["sha256"],same["sha256"])
        self.assertNotEqual(first["sha256"],newer["sha256"])


if __name__=="__main__":
    unittest.main()
