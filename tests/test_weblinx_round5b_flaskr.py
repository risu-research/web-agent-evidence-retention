"""Unit tests for frozen R5B external application and audit boundaries."""
import ast
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from weblinx_round5b_flaskr import (
    fixed_cases,UPSTREAM_SHA,OPERATIONS,LOCATORS,CONDITIONS,
    route_identity,db_rows,encode_bytes,CAPTURE_JS
)


class ExternalFlaskrPilotTests(unittest.TestCase):
    def test_prospective_matrix_is_complete(self):
        cases=fixed_cases()
        self.assertEqual(len(cases),48)
        self.assertEqual(len(set(cases)),48)
        self.assertEqual(set(op for op,_,_ in cases),set(OPERATIONS))
        self.assertEqual(set(loc for _,loc,_ in cases),set(LOCATORS))
        self.assertEqual(set(cond for _,_,cond in cases),set(CONDITIONS))
        self.assertEqual(UPSTREAM_SHA,"49943b5a94413a530761350f04e896f76e8d620e")

    def test_server_post_route_identity(self):
        ids={"A":1,"B":2}
        self.assertEqual(route_identity("/1/update",ids),"A")
        self.assertEqual(route_identity("/2/delete",ids),"B")
        self.assertEqual(route_identity("/4/update",ids),"other")
        self.assertEqual(route_identity("/",ids),"none")

    def test_readback_from_separate_SQLite_connection(self):
        with tempfile.TemporaryDirectory() as dirname:
            db=Path(dirname)/"test.sqlite"
            with sqlite3.connect(db) as connection:
                connection.execute(
                    "CREATE TABLE post(id INTEGER PRIMARY KEY, title TEXT,"
                    " body TEXT,author_id INTEGER)")
                connection.executemany(
                    "INSERT INTO post VALUES (?,?,?,?)",
                    [(1,"R5B-A","Dummy A",1),(2,"R5B-B","Dummy B",1)])
                connection.commit()
            before=db_rows(db,{"A":1,"B":2})
            self.assertEqual(before["A"]["title"],"R5B-A")
            with sqlite3.connect(db) as connection:
                connection.execute("UPDATE post SET title='edited' WHERE id=2")
                connection.commit()
            after=db_rows(db,{"A":1,"B":2})
            self.assertEqual(after["A"],before["A"])
            self.assertNotEqual(after["B"],before["B"])

    def test_independent_init_script_executes_instead_of_only_defining_function(self):
        self.assertIn("(() => {",CAPTURE_JS)
        self.assertTrue(CAPTURE_JS.strip().endswith("})();"))
        self.assertIn("e.isTrusted",CAPTURE_JS)
        self.assertIn("__r5b_emit_capture",CAPTURE_JS)

    def test_encoded_log_sizes_are_actual_bytes(self):
        record={"intent":"A","record":"B","source":"third party"}
        raw,zipped=encode_bytes(record)
        self.assertGreater(raw,0)
        self.assertGreater(zipped,0)


if __name__=="__main__":
    unittest.main()
