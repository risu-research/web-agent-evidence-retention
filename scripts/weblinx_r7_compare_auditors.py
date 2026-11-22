"""R7 original Django 48-case matched comparison of two blinded auditors.

Trace auditor sees ONLY Playwright raw Trace ZIP plus static A/B IDs.
Packet auditor sees ONLY purpose-built layered observed packet values.
Independent WSGI/browser-event/SQL truth is joined after both answer.
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

import weblinx_r6_django_trace as r6
from weblinx_r7_trace_dom_auditor import trace_auditor

OUT=Path("out_round7")
ANSWERS=("A","B","none")
QUESTIONS=("Q2_visible_click_row","Q3_server_mutating_POST",
           "Q4_SQLite_effect","Q5_first_click_status")


def packet_auditor(packet):
    """A controlled auditor with access solely to its supplied packet tier."""
    return {
        "Q1_locator_kind":packet.get("locator_kind","abstain"),
        "Q2_visible_click_row":packet.get("event_receiver_row","abstain"),
        "Q3_server_mutating_POST":packet.get("server_mutating_post","abstain"),
        "Q4_SQLite_effect":packet.get("stored_SQLite_effect","abstain"),
        "Q5_first_click_status":packet.get("first_click_status","abstain")
    }


def input_packets(r):
    """Original R6 outcome sensors serialized as evidence, no Trace fields."""
    base={
        "intended":"A","locator_kind":r["locator"],
        "first_click_status":(
            "returned" if r["first_click_status"]=="returned" else "error")}
    event={
        **base,"event_receiver_row":r["first_click_row"],
        "event_link_destination":r["first_click_href_record"]}
    server={
        **event,"server_mutating_post":r["WSGI_mutation_POST_record"]}
    effect={
        **server,"stored_SQLite_effect":r["sqlite_effect_record"],
        "sqlite_A_exists":r["sqlite_A_exists"],
        "sqlite_B_exists":r["sqlite_B_exists"]}
    return {"request":base,"event":event,"server":server,"effect":effect}


def source_answers(source):
    # Native Trace parser has already run independently on raw .trace/.network
    # and reconstructed frame-snapshot tree. No oracle passed to it.
    return {
        "Q1_selector_expression_present":int(source["q1_selector_present"]),
        "Q2_visible_click_row":source["q2_visible_receiver_inferred"],
        "Q3_server_mutating_POST":source["q3_actual_POST_route"],
        "Q4_SQLite_effect":source["q4_UI_effect_inferred"],
        "Q5_first_click_status":source["q5_first_click_status"],
    }


def reference(r):
    return {
        "Q2_visible_click_row":r["first_click_row"],
        "Q3_server_mutating_POST":r["WSGI_mutation_POST_record"],
        "Q4_SQLite_effect":r["sqlite_effect_record"],
        "Q5_first_click_status":(
            "returned" if r["first_click_status"]=="returned" else "error"),
    }


def grade(predicted,truth):
    if predicted in ("abstain",None,"other","ambiguous"):
        return "abstain"
    return "correct" if predicted==truth else "wrong"


def grade_all(rows):
    report={}
    for layer in ("trace","event","server","effect"):
        result={}
        for q in QUESTIONS:
            outcomes=Counter(x[f"{layer}_{q}_grade"] for x in rows)
            answered=outcomes["correct"]+outcomes["wrong"]
            result[q]={
                "correct":outcomes["correct"],
                "wrong":outcomes["wrong"],
                "abstain":outcomes["abstain"],
                "answered":answered,
                "denominator":48,
                "coverage":answered/48,
                "accuracy_among_answered":(
                    outcomes["correct"]/answered if answered else None)}
        report[layer]=result
    return report


def one_case(browser,base_db,op,loc,cond,index):
    captured=[]
    original=r6.trace_parse
    def isolated_raw_trace(t,ids):
        # Called while the original raw Trace ZIP exists in the disposable
        # R6 episode directory. The auditor sees no reference truth.
        parsed=trace_auditor(t,ids)
        captured.append(parsed)
        return original(t,ids)
    r6.trace_parse=isolated_raw_trace
    try:
        raw=r6.episode(browser,base_db,op,loc,cond,index)
    finally:
        r6.trace_parse=original
    if len(captured)!=1:
        raise AssertionError("Must run exactly one independent Trace auditor")
    raw_trace=captured[0]
    packets=input_packets(raw)
    packet_results={k:packet_auditor(v) for k,v in packets.items()}
    trace_result=source_answers(raw_trace)

    # Evaluation truth is not supplied to either of the above functions.
    ground=reference(raw)
    output={
        "case":index,"operation":op,"locator":loc,"condition":cond,
        "truth_click_row":ground["Q2_visible_click_row"],
        "truth_server_POST":ground["Q3_server_mutating_POST"],
        "truth_SQLite_effect":ground["Q4_SQLite_effect"],
        "truth_first_click_status":ground["Q5_first_click_status"],
        "trace_q1_selector_present":trace_result["Q1_selector_expression_present"],
        "trace_DOM_snapshots_seen":raw_trace["snapshots_seen"],
        "trace_DOM_snapshots_decoded":raw_trace["snapshots_decoded"],
        "trace_DOM_refs_resolved":raw_trace["subtree_references_resolved"],
        "trace_DOM_refs_failed":raw_trace["unresolved_snapshot_references"],
        "trace_source_table_snapshots":raw_trace["source_table_snapshots"],
        "trace_first_action_snapshot_present":raw_trace["action_snapshot_present"],
        "trace_target_marker_found":raw_trace["action_target_marker_found"],
        "trace_overlay_detected":raw_trace["overlay_present_at_action"],
        "native_trace_zip_bytes":raw_trace["trace_zip_bytes"],
        "authentic_DB_state_verified":raw["render_matches_SQL"],
    }
    # Only three progressively layered packet audit regimes are scored.
    # Request packet is separately retained as cost baseline.
    for layer in ("trace","event","server","effect"):
        answers=(trace_result if layer=="trace" else packet_results[layer])
        for q in QUESTIONS:
            a=answers[q]
            output[f"{layer}_{q}_answer"]=a
            output[f"{layer}_{q}_grade"]=grade(a,ground[q])
    for tier,packet in packets.items():
        uncompressed,compressed=r6.packet_bytes(packet)
        output[f"packet_{tier}_bytes"]=uncompressed
        output[f"packet_{tier}_zlib_bytes"]=compressed
    return output


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cases=r6.matrix()
    if len(cases)!=48 or len(set(cases))!=48:
        raise AssertionError("R7 changed original 48-action cohort")
    import django
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory(prefix="r7_master_") as folder:
        db=Path(folder)/"source.sqlite"
        r6.init_django(db)
        rows=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                version=browser.version
                for i,(op,loc,cond) in enumerate(cases,1):
                    outcome=one_case(browser,db,op,loc,cond,i)
                    rows.append(outcome)
                    if i%8==0:
                        print("R7_DOM_AUDIT_EPISODES",i,"/",48,flush=True)
            finally:
                browser.close()
    if len(rows)!=48:raise AssertionError("Not all cases evaluated")
    # The same original R6 positive/negative controls are hard gates.
    assert all(x["truth_SQLite_effect"]=="A" for x in rows
               if x["condition"]=="baseline")
    assert all(x["truth_SQLite_effect"]=="none" for x in rows
               if x["condition"]=="overlay_standard")
    assert all(x["authentic_DB_state_verified"]==1 for x in rows)
    summary={
        "name":"R7 live authentic Django trace DOM reconstruction versus selective tier auditors",
        "source_app":"Django original admin/auth user-management 5.2.12",
        "source_tag_commit":r6.PIN,
        "python":sys.version.split()[0],
        "playwright":r6.PLAYWRIGHT,
        "django":django.get_version(),
        "chromium":version,
        "cases":48,
        "native_trace_DOM_decoder":"frame-snapshot HTML node arrays plus resolved subtree references",
        "first_click_oracle":"independent trusted browser capture",
        "server_oracle":"independent WSGI route log",
        "database_oracle":"fresh independent sqlite3.connect",
        "tier_auditors_evaluated_with_no_trace_input":True,
        "trace_auditor_evaluated_with_no_oracle_input":True,
        "trace_Q2_evidence":"DOM locator/action inference, not isTrusted observation",
        "trace_Q4_evidence":"DOM rendered-result inference, not committed SQL oracle",
        "evaluations":grade_all(rows),
        "native_trace_zip_total_bytes":sum(r["native_trace_zip_bytes"] for r in rows),
        "DOM_snapshot_totals":{
            "recorded":sum(r["trace_DOM_snapshots_seen"] for r in rows),
            "successfully_decoded":sum(r["trace_DOM_snapshots_decoded"] for r in rows),
            "subtree_refs_resolved":sum(r["trace_DOM_refs_resolved"] for r in rows),
            "subtree_ref_failures":sum(r["trace_DOM_refs_failed"] for r in rows),
            "original_table_snapshots":sum(r["trace_source_table_snapshots"] for r in rows),
            "action_target_markers_found":sum(r["trace_target_marker_found"] for r in rows),
        },
        "packet_bytes_by_tier":{
            k:{
                "raw_utf8":sum(r[f"packet_{k}_bytes"] for r in rows),
                "zlib9_per_episode":sum(r[f"packet_{k}_zlib_bytes"] for r in rows)}
            for k in ("request","event","server","effect")},
        "original_source_effect_counts":dict(sorted(Counter(
            r["truth_SQLite_effect"] for r in rows).items())),
        "raw_trace_ZIP_published":False,
        "audit_with_human_DOM_review":False,
        "LLM_as_judge":False,
        "production_agent_error_frequency":False,
    }
    with (OUT/"r7_trace_DOM_vs_packets_48.csv").open("w",newline="",
                                                    encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]))
        wr.writeheader();wr.writerows(rows)
    (OUT/"r7_trace_DOM_vs_packets_summary.json").write_text(
        json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R7_AUDITOR_RESULT",json.dumps(summary,sort_keys=True),flush=True)


if __name__=="__main__":
    run()
