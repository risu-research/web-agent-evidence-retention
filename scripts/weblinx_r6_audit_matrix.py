"""R6 audit-question comparison: conservative direct-evidence scoring.

Only *after* the Trace ZIP was separately parsed into categorical fields do
we join with event, WSGI and SQLite truth. No retained event or DB field is
used to construct the Trace answer. This is a machine-readable-field audit,
not human inspection of full DOM snapshots.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

SOURCE=Path("results/weblinx_r6_django_cases.csv")
R5B=Path("results/weblinx_round5b_flaskr_cases.csv")
OUTPUT=Path("results/weblinx_r6_audit_matrix.json")
CASES=Path("results/weblinx_r6_audit_cases.csv")


def evaluate(rows):
    assert len(rows)==48
    assert len({(r["operation"],r["locator"],r["condition"]) for r in rows})==48
    audited=[]
    for r in rows:
        truth_post=r["WSGI_mutation_POST_record"]
        trace_post=r["trace_server_POST_record"]
        trace_click=r["trace_first_click_status"]
        click_status=r["first_click_status"]
        recorded_status=(
            "returned" if click_status=="returned"
            else "error"
        )
        trace_click_explicit=trace_click in ("returned","error")
        q3_answer=trace_post in ("A","B","none")
        audited.append({
            "operation":r["operation"],
            "locator":r["locator"],
            "condition":r["condition"],
            # Q1: trace records literal selector expression; the compact
            # request packet provides the locator *kind* instead.
            "q1_trace_selector_explicit":int(
                r["trace_first_click_selector"]=="present"),
            "q1_compact_request_kind_available":1,
            # Q2: a trusted event row is directly captured by observer.
            # Trace action selector and DOM snapshot are not a direct
            # isTrusted click-recipient record.
            "q2_trace_trusted_row_direct":int(
                r["trace_event_trusted_target_explicit"]=="1"),
            "q2_compact_trusted_row_observed":1,
            # Q3: compare original Trace-derived network POST route with
            # independently logged WSGI route. The labels are joined
            # ONLY in this stage, after trace parsing.
            "q3_trace_network_route_answered":int(q3_answer),
            "q3_trace_network_route_correct":int(
                q3_answer and trace_post==truth_post),
            "q3_compact_wsgi_route_answered":1,
            # Q4: no direct authoritative SQL row observation occurs
            # in the stock browser Trace. This is a strict query, and
            # DOM snapshot inference is intentionally not equivalent.
            "q4_trace_authenticated_SQL_answered":int(
                r["trace_SQL_commit_explicit"]=="1"),
            "q4_compact_SQLite_result_answered":1,
            # Q5: Trace may include after/error for first Playwright click.
            "q5_trace_first_click_answered":int(trace_click_explicit),
            "q5_trace_first_click_correct":int(
                trace_click_explicit and trace_click==recorded_status),
            "q5_compact_request_status_answered":1,
            "actual_sql_effect":r["sqlite_effect_record"],
            "actual_wsgi_post":truth_post,
        })
    counts={}
    keys=[key for key in audited[0] if key.startswith("q")]
    for key in keys:
        counts[key]=sum(int(r[key]) for r in audited)
    q3_with_answer=counts["q3_trace_network_route_answered"]
    q5_with_answer=counts["q5_trace_first_click_answered"]
    result={
        "protocol":"R6 conservative direct-evidence audit questions",
        "cases":48,
        "questions":{
            "Q1_attempted_locator_expression":{
                "trace_selector_explicit_n":counts["q1_trace_selector_explicit"],
                "compact_request_locator_kind_available_n":
                    counts["q1_compact_request_kind_available"],
                "note":"the packet stores locator type; raw selector string exists in Trace only"},
            "Q2_trusted_event_receiver_row":{
                "trace_explicit_trusted_event_row_n":
                    counts["q2_trace_trusted_row_direct"],
                "compact_independent_capture_available_n":
                    counts["q2_compact_trusted_row_observed"],
                "note":"Trace snapshots can support manual inference, not an isTrusted event attribution"},
            "Q3_actual_mutating_HTTP_route":{
                "trace_answered_n":q3_with_answer,
                "trace_correct_n":counts["q3_trace_network_route_correct"],
                "trace_accuracy_among_answered":(
                    counts["q3_trace_network_route_correct"]/q3_with_answer
                    if q3_with_answer else None),
                "compact_wsgi_route_available_n":
                    counts["q3_compact_wsgi_route_answered"],
            },
            "Q4_independent_committed_SQLite_row":{
                "trace_explicit_SQLite_oracle_n":
                    counts["q4_trace_authenticated_SQL_answered"],
                "compact_separate_SQL_readback_n":
                    counts["q4_compact_SQLite_result_answered"],
                "note":"additional privileged database instrumentation creates this information difference"},
            "Q5_first_locator_return_or_error":{
                "trace_answered_n":q5_with_answer,
                "trace_correct_n":counts["q5_trace_first_click_correct"],
                "trace_accuracy_among_answered":(
                    counts["q5_trace_first_click_correct"]/q5_with_answer
                    if q5_with_answer else None),
                "compact_API_status_available_n":
                    counts["q5_compact_request_status_answered"],
            },
        },
        "source_separation":{
            "trace_parser_input":"genuine raw Playwright trace ZIP + static A/B mapping only",
            "effect_oracle":"separate sqlite3.connect after actual browser operations",
            "server_oracle":"independent read-only WSGI wrapper",
            "conservative_trace_audit_only":True,
            "manual_snapshot_review_performed":False,
            "human_trace_inference_equivalence_claimed":False,
        }
    }
    return audited,result


def app_comparison(django_rows,flask_rows):
    assert len(flask_rows)==len(django_rows)==48
    def totals(rows):
        return {
            "A":sum(r["sqlite_effect_record"]=="A" for r in rows),
            "B":sum(r["sqlite_effect_record"]=="B" for r in rows),
            "no_effect":sum(r["sqlite_effect_record"]=="none" for r in rows),
            "returned_first_click_no_DB_effect":sum(
                r["returned_click_without_SQL_effect"]=="1"
                if "returned_click_without_SQL_effect" in r
                else r["click_returned_no_DB_effect"]=="1"
                for r in rows),
            "event_visible_row_differs_from_DB_effect":sum(
                r["event_row_differs_from_effect"]=="1"
                if "event_row_differs_from_effect" in r
                else r["event_article_differs_from_SQL_effect"]=="1"
                for r in rows),
        }
    return {
        "django_admin_48":totals(django_rows),
        "flaskr_48":totals(flask_rows),
        "caveat":"two different upstream apps, independently controlled; same failures deliberately induced; no population frequency",
    }


def main():
    with SOURCE.open(newline="",encoding="utf-8") as f:
        source=list(csv.DictReader(f))
    with R5B.open(newline="",encoding="utf-8") as f:
        flask=list(csv.DictReader(f))
    rows,report=evaluate(source)
    report["two_external_apps"]=app_comparison(source,flask)
    with CASES.open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]))
        wr.writeheader();wr.writerows(rows)
    OUTPUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R6_AUDIT_SUMMARY",json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
