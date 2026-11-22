"""R6 exact two-run comparison, preserving genuine Trace archive-size drift.

Input: two original GitHub Actions artifacts, *not* a locally modified result.
Compare every original 48-case categorical field and packet size. Exclude
only real measured Trace ZIP byte counts and trace/event-line volume, which
can legitimately vary with runtime. Trace-derived categorical answers,
including server POST and locator outcome, must still agree exactly.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter

FIRST=Path("source_run_first/out_round6")
SECOND=Path("source_run_repeat/out_round6")
OUTPUT=Path("results/weblinx_r6_independent_repeat.json")
VOLATILE={
    "trace_zip_bytes",
    "trace_event_lines",
    "trace_network_lines"
}

def read_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    fa=FIRST/"r6_django_48.csv"
    fb=SECOND/"r6_django_48.csv"
    sa=FIRST/"r6_django_summary.json"
    sb=SECOND/"r6_django_summary.json"
    aa,bb=read_rows(fa),read_rows(fb)
    one,two=json.loads(sa.read_text()),json.loads(sb.read_text())
    assert len(aa)==len(bb)==48
    key=lambda row:(row["operation"],row["locator"],row["condition"])
    a={key(x):x for x in aa}
    b={key(x):x for x in bb}
    if set(a)!=set(b) or len(a)!=48:raise AssertionError("48-case cohort changed")
    fields=set(aa[0]) - VOLATILE
    if set(aa[0])!=set(bb[0]):raise AssertionError("Public source fields changed")
    differences=[]
    for k in sorted(a):
        for field in sorted(fields):
            if a[k][field]!=b[k][field]:
                differences.append({
                    "case":list(k),"field":field,
                    "original":a[k][field],
                    "independent_run":b[k][field]
                })
    stable_keys=(
        "source","upstream_tag_commit","upstream_source_sha256","runtime",
        "predeclared_cases","total","by_operation","by_locator",
        "by_condition","bytes","oracle_sources","raw_trace_published",
        "sql_state_not_present_as_trace_oracle",
        "second_independent_project","synthetic_DOM_interventions"
    )
    for k in stable_keys:
        if one[k]!=two[k]:
            differences.append({"summary_field":k,"status":"changed"})
    result={
        "source":"two independently initialized and fully completed 48-case Django admin runs",
        "upstream_commit":one["upstream_tag_commit"],
        "original_run":45064967915,
        "repeat_run":45064981005,
        "cases":48,
        "compared_categorical_and_packet_fields_per_case":len(fields),
        "differences_n":len(differences),
        "differences":differences,
        "oracle_effect_counts_original":one["total"]["effects"],
        "oracle_effect_counts_repeat":two["total"]["effects"],
        "trace_network_post_route_concordance_original":
            one["trace"]["server_POST_record_correct_n"],
        "trace_network_post_route_concordance_repeat":
            two["trace"]["server_POST_record_correct_n"],
        "trace_zip_bytes_original":one["trace"]["zip_total_bytes"],
        "trace_zip_bytes_repeat":two["trace"]["zip_total_bytes"],
        "trace_event_lines_original":one["trace"]["trace_record_count"],
        "trace_event_lines_repeat":two["trace"]["trace_record_count"],
        "trace_network_lines_original":one["trace"]["network_record_count"],
        "trace_network_lines_repeat":two["trace"]["network_record_count"],
        "source_file_sha256":{
            "original_summary":digest(sa),
            "original_cases":digest(fa),
            "repeat_summary":digest(sb),
            "repeat_cases":digest(fb)
        },
        "trace_zip_byte_identity_required":False,
        "raw_traces_published":False,
    }
    OUTPUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R6_INDEPENDENT_REPEAT",json.dumps(result,sort_keys=True),flush=True)
    if differences:raise AssertionError("Original and repeat source outcomes differed")

if __name__=="__main__":
    main()
