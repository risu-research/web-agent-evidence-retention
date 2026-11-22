"""Independent R5B external Flaskr rerun comparison.

Compare categorical and structured outcomes exactly for 48 fixed episodes.
Playwright trace ZIP size and event line counts are genuinely measured but can
vary across repetitions due to trace archive timestamps, rendering resources
and instance-specific browser network traffic. Do not falsely demand binary
trace archive equality or change a failed case to force a match.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REFERENCE=Path("results/weblinx_round5b_flaskr_cases.csv")
REPEAT=Path("out_round5b/round5b_flaskr_actions_48.csv")
REFERENCE_SUMMARY=Path("results/weblinx_round5b_flaskr_summary.json")
REPEAT_SUMMARY=Path("out_round5b/round5b_flaskr_summary.json")
OUT=Path("out_round5b/round5b_independent_comparison.json")
NONDETERMINISTIC={
    "trace_zip_bytes",
    "trace_event_lines",
    "trace_network_lines",
    "trace_resource_files",
    "trace_member_files"
}


def load_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compare():
    a=load_rows(REFERENCE)
    b=load_rows(REPEAT)
    assert len(a)==len(b)==48
    key=lambda r:(r["operation"],r["locator"],r["condition"])
    amap={key(r):r for r in a}
    bmap={key(r):r for r in b}
    if set(amap)!=set(bmap):
        raise AssertionError("The 48 source condition keys changed")
    if len(amap)!=48:
        raise AssertionError("Repeated source keys in comparison")
    mismatches=[]
    comparable_fields=set(a[0])-NONDETERMINISTIC
    if set(a[0])!=set(b[0]):
        raise AssertionError("Source public field schema changed")
    for k in sorted(amap):
        for field in sorted(comparable_fields):
            if amap[k][field]!=bmap[k][field]:
                mismatches.append({
                    "case":list(k),"field":field,
                    "original":amap[k][field],
                    "repeated":bmap[k][field]
                })
    s1=json.loads(REFERENCE_SUMMARY.read_text())
    s2=json.loads(REPEAT_SUMMARY.read_text())
    for key in ("upstream_commit","upstream_original_file_sha256",
                "environment","fixed_conditions","by_locator",
                "by_condition","by_operation"):
        if s1[key]!=s2[key]:
            mismatches.append({"summary_field":key,"status":"changed"})
    fields=("sqlite_effect_counts","click_status_counts",
            "event_article_counts","wrong_SQL_effects",
            "mismatched_event_article_and_SQL_effect",
            "returned_clicks_without_SQL_effect")
    for field in fields:
        if s1["total"][field]!=s2["total"][field]:
            mismatches.append({"summary_field":"total."+field,"status":"changed"})
    report={
        "comparison":"two independently initialized 48-case upstream Flaskr app runs",
        "upstream_commit":s1["upstream_commit"],
        "case_count":48,
        "categorical_and_packet_fields_compared":len(comparable_fields),
        "categorical_field_mismatches":len(mismatches),
        "mismatches":mismatches,
        "trace_archive_bytes_are_descriptive_not_bitwise_comparable":True,
        "original_trace_total_bytes":s1["total"]["playwright_trace_zip_total_bytes"],
        "repeated_trace_total_bytes":s2["total"]["playwright_trace_zip_total_bytes"],
        "original_trace_median_bytes":s1["total"]["playwright_trace_zip_median_bytes"],
        "repeated_trace_median_bytes":s2["total"]["playwright_trace_zip_median_bytes"],
        "original_trace_event_lines":s1["total"]["playwright_trace_action_event_lines"],
        "repeated_trace_event_lines":s2["total"]["playwright_trace_action_event_lines"],
        "original_trace_network_lines":s1["total"]["playwright_trace_network_lines"],
        "repeated_trace_network_lines":s2["total"]["playwright_trace_network_lines"],
        "same_authoritative_sql_counts":s1["total"]["sqlite_effect_counts"]==
                                         s2["total"]["sqlite_effect_counts"],
        "raw_playwright_trace_archives_exported":False
    }
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if mismatches:
        print("R5B_REPEAT_DIFFERENCES",json.dumps(mismatches),flush=True)
        raise AssertionError("Independent R5B run diverged; keep all mismatches")
    print("R5B_REPEAT_VERIFIED",json.dumps(report,sort_keys=True),flush=True)
    return report


if __name__=="__main__":
    compare()
