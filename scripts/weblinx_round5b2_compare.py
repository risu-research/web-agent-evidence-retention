"""Verify second independent six-case Flaskr POST rejection experiment.

The browser trace ZIP byte sizes are descriptive; they can change with
execution timestamps and host runtime. Compare actual browser/server/SQL
outcomes and source file provenance exactly instead.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

SOURCE=Path("results/weblinx_round5b2_rejection_cases.csv")
SECOND=Path("out_round5b2/r5b2_server_rejections_6.csv")
BASE=Path("results/weblinx_round5b2_rejection_summary.json")
REPEAT=Path("out_round5b2/r5b2_server_rejection_summary.json")
OUTPUT=Path("out_round5b2/r5b2_independent_comparison.json")

NON_DETERMINISTIC={
    "playwright_trace_zip_bytes",
    "playwright_trace_records",
    "playwright_trace_network_records",
}


def read_csv(file):
    with file.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    one,two=read_csv(SOURCE),read_csv(SECOND)
    assert len(one)==len(two)==6
    key=lambda r:(r["locator"],r["condition"])
    a={key(r):r for r in one}
    b={key(r):r for r in two}
    if set(a)!=set(b) or len(a)!=6:
        raise AssertionError("R5B2 source cohort differed")
    compared=set(one[0])-NON_DETERMINISTIC
    diffs=[]
    for k in sorted(a):
        for field in sorted(compared):
            if a[k][field]!=b[k][field]:
                diffs.append({"case":k,"field":field,
                              "first":a[k][field],"second":b[k][field]})
    aa=json.loads(BASE.read_text())
    bb=json.loads(REPEAT.read_text())
    for field in ("source_commit","source_file_checksums","environment",
                  "first_click_results","post_response_codes",
                  "server_POST_count_total","server_POST_with_no_SQL_commit",
                  "flash_validation_n","all_SQL_A_unchanged","all_SQL_B_unchanged"):
        if aa[field]!=bb[field]:
            diffs.append({"summary_field":field})
    result={
        "comparison":"six first-party-browser runs against unchanged third-party Flaskr",
        "cases":6,"compared_categorical_fields":len(compared),
        "different_fields":len(diffs),"differences":diffs,
        "all_six_real_POSTs_rejected_without_SQL_change":(
            bb["server_POST_with_no_SQL_commit"]==6),
        "first_trace_zip_total_bytes":aa["trace_zip_total_bytes"],
        "repeat_trace_zip_total_bytes":bb["trace_zip_total_bytes"],
        "browser_trace_bytes_not_required_to_be_equal":True,
        "independent_db_readback_in_both_runs":(
            aa["actual_independent_SQLite_reads"] and
            bb["actual_independent_SQLite_reads"])
    }
    OUTPUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("R5B2_REPEAT",json.dumps(result,sort_keys=True),flush=True)
    if diffs:raise AssertionError("Independent six-case source outcome changed")


if __name__=="__main__":
    main()
