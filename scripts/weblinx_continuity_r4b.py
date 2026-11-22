"""R4B: Does the 75/75 result follow mechanically from id("target-id")?

Reads only the frozen 86-case selection and original WebLINX Replay/DMR
metadata. Never exports literal HTML ids, target UIDs or XPath expressions.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from weblinx_continuity_r1 import SHA, get_source, replay_data, load_original
from weblinx_continuity_r3 import load_positive_targets, recorded_action_element
from weblinx_continuity_r3d import ID_EXPR

ORIGINAL=Path("results/weblinx_continuity_r4_cases.csv")
FROZEN_SHA="1ba4e6d6bdc0c5060f693a201bbe0d7696fef7ae27d89bc9f3da361eb271494d"
OUT=Path("out_continuity_r4b")


def classify_xpath(expression,ordinary_target_id):
    value=(expression or "").strip()
    match=ID_EXPR.match(value)
    if match is None:
        return {
            "id_function_prefix":0,"exact_root_only":0,
            "id_function_with_suffix":0,
            "root_equals_target_native_id":0,
            "site_native_id_known":int(bool(ordinary_target_id)),
        }
    literal_id=match.group(2)
    suffix=value[match.end():].strip()
    return {
        "id_function_prefix":1,
        "exact_root_only":int(not bool(suffix)),
        "id_function_with_suffix":int(bool(suffix)),
        "root_equals_target_native_id":int(
            bool(ordinary_target_id) and literal_id==ordinary_target_id),
        "site_native_id_known":int(bool(ordinary_target_id)),
    }


def load_cohort():
    if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()!=FROZEN_SHA:
        raise AssertionError("Published R4 cohort SHA-256 changed")
    with ORIGINAL.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=86:raise AssertionError("R4 source casebook is incomplete")
    return {(r["demo"],int(r["turn"])):r["group"] for r in rows}


def summary(rows):
    if len(rows)!=86:raise AssertionError("Incorrect selection")
    def stat(group):
        subset=[r for r in rows if r["group"]==group]
        return {
            "actions":len(subset),
            "prefix_is_id_function":sum(r["id_function_prefix"] for r in subset),
            "complete_expression_is_id_only":sum(r["exact_root_only"] for r in subset),
            "id_function_has_suffix":sum(r["id_function_with_suffix"] for r in subset),
            "id_root_equals_original_target_site_id":sum(
                r["root_equals_target_native_id"] for r in subset),
            "target_site_id_available":sum(r["site_native_id_known"] for r in subset),
        }
    values={
        "source_xpath_anomaly":stat("source_xpath_anomaly"),
        "captured_only_8":stat("captured_only_8"),
        "both_67":stat("both_67"),
    }
    if [values[k]["actions"] for k in
            ("source_xpath_anomaly","captured_only_8","both_67")] != [11,8,67]:
        raise AssertionError("Source cohort selection changed")
    values["all_proxy_75"]={
        field:values["captured_only_8"][field]+values["both_67"][field]
        for field in values["captured_only_8"]
    }
    return {
        "dataset_revision":SHA,
        "protocol":"R4B post-result XPath exact id() syntax test",
        "original_cohort_n":600,
        "selected_cases":len(rows),
        "groups":values,
        "test_status":"source recorded syntax / site-id reference overlap only",
        "independent_target_identity_ground_truth":False,
        "browser_execution_verified":False,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cohort=load_cohort()
    original=load_original()
    all_keys={(demo,idx) for demo,idxs in original.items() for idx in idxs}
    if not set(cohort).issubset(all_keys):
        raise AssertionError("R4B selected keys outside original frozen cohort")
    pos=load_positive_targets(set(cohort))
    if set(pos)!=set(cohort) or any(len(v)!=1 for v in pos.values()):
        raise AssertionError("Original positive candidates changed")
    replays={demo:replay_data(get_source(f"demonstrations/{demo}/replay.json"))
             for demo in sorted({demo for demo,idx in cohort})}
    rows=[]
    for (demo,turn),group in sorted(cohort.items()):
        element=recorded_action_element(replays[demo][turn])
        target=pos[(demo,turn)][0]
        metrics=classify_xpath(
            element["xpath"],target["dmr"]["ordinary_html_id"])
        rows.append({"demo":demo,"turn":turn,"group":group,**metrics})
    result=summary(rows)
    with (OUT/"r4b_xpath_root_cases_86.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (OUT/"r4b_xpath_root_summary.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R4B_SUMMARY",json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
