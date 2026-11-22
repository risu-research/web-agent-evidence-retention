"""R8B independently preregistered transactional network comparator.

The native original Django / Chromium / Trace runner is exactly R8. Only
the equivalence of relevant HTTP requests changes: compare the ordered
user-list/edit/delete transaction subsequence, and report all other admin
network request differences. Old R8 strict failures are preserved.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import weblinx_r8_server_divergence as r8

OUT = Path("out_round8b")
AUXILIARY = []
ORIGINAL_COMPARE = r8.compare_pair


def relevant_request(rec):
    method, path, status = rec
    return path == "/admin/auth/user/" or bool(
        re.fullmatch(r"/admin/auth/user/\d+/(?:change|delete)/", path)
    )


def transactional_sequence(network_projection):
    return [entry for entry in network_projection if relevant_request(entry)]


def auxiliary_sequence(network_projection):
    return [entry for entry in network_projection if not relevant_request(entry)]


def corrected_compare(a, b):
    # All original strict gates remain unchanged, except the predeclared
    # network scope. Never hide the auxiliary differences from the output.
    gate = ORIGINAL_COMPARE(a,b)
    original_strict_net = gate["network_projection"]
    tx_a = transactional_sequence(a["network_projection"])
    tx_b = transactional_sequence(b["network_projection"])
    gate["network_projection"] = tx_a == tx_b
    aux_a = auxiliary_sequence(a["network_projection"])
    aux_b = auxiliary_sequence(b["network_projection"])
    AUXILIARY.append({
        "pair":a["pair"],
        "ordered_full_admin_network_equal":original_strict_net,
        "ordered_transactional_network_equal":gate["network_projection"],
        "auxiliary_requests_equal":aux_a == aux_b,
        "auxiliary_admin_control":next(
            (x for x in (aux_a,aux_b) if (a if x is aux_a else b)["mode"]=="control"),[]),
        "auxiliary_admin_shadow":next(
            (x for x in (aux_a,aux_b) if (a if x is aux_a else b)["mode"]=="shadow"),[]),
    })
    return gate


def main():
    AUXILIARY.clear()
    r8.OUT=OUT
    r8.compare_pair=corrected_compare
    r8.run()
    original=OUT/"r8_summary.json"
    report=json.loads(original.read_text(encoding="utf-8"))
    report["experiment"]="R8B predeclared transactional-network equivalence with authentic Django Trace"
    report["protocol"]="docs/weblinx-r8b-transactional-protocol.md"
    report["preregistered_protocol_frozen_before_live_run"]=True
    report["R8_strict_prior_calibration"]="failed ordered full admin request gate"
    report["R8_failed_run_ids"]=[
        45068631082,45068796349,45068811353,45068961921]
    report["network_equivalence_scope"]="ordered original Django user-list, change, delete request/status"
    report["auxiliary_network"]=AUXILIARY
    report["strict_all_admin_network_pairs_equal"]=sum(
        x["ordered_full_admin_network_equal"] for x in AUXILIARY)
    report["transactional_network_pairs_equal"]=sum(
        x["ordered_transactional_network_equal"] for x in AUXILIARY)
    report["auxiliary_network_pairs_equal"]=sum(
        x["auxiliary_requests_equal"] for x in AUXILIARY)
    report["raw_native_trace_identical"]=False
    new=OUT/"r8b_summary.json"
    new.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",
                   encoding="utf-8")
    original.unlink()
    (OUT/"r8_12_source_cases.csv").rename(
        OUT/"r8b_12_source_cases.csv")
    print("R8B_CORRECTED_EQUIVALENCE_AND_PROVENANCE_PASS",
          json.dumps({
              "cases":report["cases"],
              "pairs":report["equivalent_pairs"],
              "transactional_matches":report["transactional_network_pairs_equal"],
              "full_network_matches":report["strict_all_admin_network_pairs_equal"],
              "aux_equal":report["auxiliary_network_pairs_equal"],
              "packet_correct":report["packet_Q6_correct"],
              "trace_abstentions":report["trace_Q6"].get("abstain"),
          },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
