"""Frozen R5B-2 authentic Flaskr server rejection case-matrix tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_round5b2_server_rejection import (
    cases,LOCATORS,SCENARIOS,OPERATIONS,UPSTREAM_SHA
)


class R5B2ServerNegativeControls(unittest.TestCase):
    def test_exact_six_case_followup(self):
        matrix=cases()
        self.assertEqual(len(matrix),6)
        self.assertEqual(len(set(matrix)),6)
        self.assertEqual(set(r[0] for r in matrix),set(LOCATORS))
        self.assertEqual(set(r[1] for r in matrix),set(SCENARIOS))
        self.assertEqual(OPERATIONS,("edit_blank_title",))

    def test_same_external_source_and_version(self):
        self.assertEqual(UPSTREAM_SHA,
                         "49943b5a94413a530761350f04e896f76e8d620e")
        self.assertEqual(set(SCENARIOS),{"baseline","reorder"})


if __name__=="__main__":
    unittest.main()
