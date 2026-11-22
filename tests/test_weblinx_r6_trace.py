"""Trace-only scorer guardrails: synthetic trace archives with no SQLite oracle.

The file parser cannot access WSGI, browser capture or SQL. Tests explicitly
exercise the Playwright before/after call stream and separate .network stream.
"""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_r6_django_trace import (
    matrix,OPS,LOCATORS,CONDITIONS,trace_parse,route_id,packet_bytes
)

class TraceInspectorTests(unittest.TestCase):
    def trace(self,events,network):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        p=Path(folder.name)/"trace.zip"
        with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as f:
            f.writestr("trace.trace","".join(json.dumps(x)+"\n" for x in events))
            f.writestr("trace.network","".join(json.dumps(x)+"\n" for x in network))
        return p

    def test_frozen_48_cases(self):
        self.assertEqual(len(matrix()),48)
        self.assertEqual(len(set(matrix())),48)
        self.assertEqual(len(OPS),2)
        self.assertEqual(len(LOCATORS),3)
        self.assertEqual(len(CONDITIONS),8)

    def test_trace_only_finds_actual_post_route(self):
        raw=self.trace([
            {"type":"before","method":"click","callId":"c1",
             "params":{"selector":"a#demo"}},
            {"type":"after","callId":"c1"},
        ],[
            {"type":"resource-snapshot",
             "snapshot":{"request":{"method":"GET",
                 "url":"http://127.0.0.1/admin/auth/user/2/change/"}}},
            {"type":"resource-snapshot",
             "snapshot":{"request":{"method":"POST",
                 "url":"http://127.0.0.1/admin/auth/user/3/change/"}}},
        ])
        result=trace_parse(raw,{"A":2,"B":3})
        self.assertEqual(result["first_click_selector"],"present")
        self.assertEqual(result["first_click_status"],"returned")
        self.assertEqual(result["trace_POST_route_unique"],"B")
        self.assertFalse(result["first_click_record_is_observed_trusted_event"])

    def test_trace_without_post_does_not_claim_SQL_state(self):
        raw=self.trace([
            {"type":"before","method":"click","callId":"bad",
             "params":{"selector":"#unknown"}},
            {"type":"after","callId":"bad","error":{"message":"Timeout"}},
        ],[])
        result=trace_parse(raw,{"A":2,"B":3})
        self.assertEqual(result["trace_POST_route_unique"],"none")
        self.assertEqual(result["first_click_status"],"error")
        self.assertFalse(result["first_click_record_is_observed_trusted_event"])

    def test_multiple_post_routes_do_not_become_unique(self):
        raw=self.trace([],[
            {"type":"resource-snapshot",
             "snapshot":{"request":{"method":"POST",
                 "url":"http://x/admin/auth/user/2/change/"}}},
            {"type":"resource-snapshot",
             "snapshot":{"request":{"method":"POST",
                 "url":"http://x/admin/auth/user/3/delete/"}}},
        ])
        result=trace_parse(raw,{"A":2,"B":3})
        self.assertEqual(result["trace_POST_route_unique"],"ambiguous")

    def test_packet_bytes_are_serialized(self):
        raw,zip9=packet_bytes({"intended":"A","record":"B"})
        self.assertGreater(raw,10)
        self.assertGreater(zip9,10)

if __name__=="__main__":
    unittest.main()
