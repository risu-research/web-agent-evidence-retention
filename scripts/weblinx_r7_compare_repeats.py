"""Compare two independently executed, original Django R7 blind audit runs.

All case-level classification, audit answer, outcome truth, compressed packet
byte sizes and privacy flags must match. Legitimate original Playwright Trace
ZIP bytes, transient snapshot counts and reference volumes are measured but
never falsely required to be bit-identical.
"""
from __future__ import annotations
import csv
import json
import hashlib
from pathlib import Path

FIRST=Path("r7_first/out_round7")
REPEAT=Path("r7_repeat/out_round7")
OUT=Path("results/weblinx_r7_independent_repeat.json")
VOLATILE={
    "native_trace_zip_bytes",
    "trace_DOM_snapshots_seen",
    "trace_DOM_snapshots_decoded",
    "trace_DOM_refs_resolved",
    "trace_DOM_refs_failed",
    "trace_source_table_snapshots",
    "trace_first_action_snapshot_present",
    "trace_target_marker_found",
    "trace_overlay_detected"
}


def rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    ap=FIRST/"r7_trace_DOM_vs_packets_48.csv"
    bp=REPEAT/"r7_trace_DOM_vs_packets_48.csv"
    asp=FIRST/"r7_trace_DOM_vs_packets_summary.json"
    bsp=REPEAT/"r7_trace_DOM_vs_packets_summary.json"
    a,b=rows(ap),rows(bp)
    one,two=json.loads(asp.read_text()),json.loads(bsp.read_text())
    assert len(a)==len(b)==48
    key=lambda r:(r["operation"],r["locator"],r["condition"])
    a={key(x):x for x in a}
    b={key(x):x for x in b}
    if len(a)!=48 or set(a)!=set(b):
        raise AssertionError("R7 source cohort changed")
    if set(next(iter(a.values())))!=set(next(iter(b.values()))):
        raise AssertionError("Result schema changed")
    compared=sorted(set(next(iter(a.values())))-VOLATILE)
    differences=[]
    for k in sorted(a):
        for field in compared:
            if a[k][field]!=b[k][field]:
                differences.append({"case":list(k),"field":field,
                                    "first":a[k][field],"repeat":b[k][field]})
    stable=("source_app","source_tag_commit","cases","python",
            "django","chromium","playwright",
            "native_trace_DOM_decoder","first_click_oracle",
            "server_oracle","database_oracle",
            "tier_auditors_evaluated_with_no_trace_input",
            "trace_auditor_evaluated_with_no_oracle_input",
            "trace_Q2_evidence","trace_Q4_evidence",
            "evaluations","packet_bytes_by_tier","original_source_effect_counts",
            "raw_trace_ZIP_published","audit_with_human_DOM_review",
            "LLM_as_judge","production_agent_error_frequency")
    for field in stable:
        if one[field]!=two[field]:
            differences.append({"summary_field":field})
    result={
        "study":"R7 blind Trace DOM reconstruction and selective evidence tier audit",
        "source_tag_commit":one["source_tag_commit"],
        "cases":48,
        "stable_fields_compared_per_case":len(compared),
        "different_fields_n":len(differences),
        "differences":differences,
        "initial_scores":one["evaluations"],
        "repeat_scores":two["evaluations"],
        "initial_native_trace_zip_bytes":one["native_trace_zip_total_bytes"],
        "repeat_native_trace_zip_bytes":two["native_trace_zip_total_bytes"],
        "initial_DOM_snapshot_counts":one["DOM_snapshot_totals"],
        "repeat_DOM_snapshot_counts":two["DOM_snapshot_totals"],
        "trace_bytes_and_snapshot_counts_allowed_to_vary":True,
        "sha256":{
            "first_casebook":digest(ap),"repeat_casebook":digest(bp),
            "first_summary":digest(asp),"repeat_summary":digest(bsp)
        }
    }
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",
                   encoding="utf-8")
    print("R7_REPEAT_COMPARISON",json.dumps(result,sort_keys=True),flush=True)
    if differences:
        raise AssertionError("Blind R7 categorical results differed across runs")


if __name__=="__main__":run()
