"""R3C: evaluate recorded action XPath expressions on current/next source HTML.

The frozen 600 actions remain the denominator. WebLINX-reported action
XPath may use a different syntax from the canonical DMR source XPath. This
study evaluates the actual expression against the original source DOM,
without publishing any literal locator, site ID, URL or page content.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from lxml import etree

from weblinx_continuity_r1 import load_original,replay_data,get_source,state_name,SHA
from weblinx_continuity_r2 import fetch_one,context_hint,compare_known
from weblinx_continuity_r3 import (
    load_positive_targets, recorded_action_element,next_browser_idx,
    html_snapshot,target_in_snapshot,original_site_id,anchor_proxy,
    SAFE_FILE,WORKERS
)

OUT=Path("out_continuity_r3c")
MAX_EXPR_LEN=5000


def xpath_dialect(expr):
    value=(expr or "").strip()
    if not value:return "missing"
    if value.startswith(("id(", "ID(")):return "xpath_id_function"
    if value.startswith("//"):return "root_double_slash"
    if value.startswith("/"):return "absolute_path"
    if value.startswith(("./", ".//")):return "relative_dot_path"
    return "other_expression"


def run_xpath(snapshot,expression):
    """Execute the captured XPath against the exact publisher DOM."""
    if snapshot.get("status")!="parsed":return {"status":"html_unavailable","nodes":[]}
    expr=(expression or "").strip()
    if not expr:return {"status":"missing_xpath","nodes":[]}
    if len(expr)>MAX_EXPR_LEN:return {"status":"expression_too_long","nodes":[]}
    try:
        found=snapshot["tree"].xpath(expr)
    except (etree.XPathError,ValueError,TypeError):
        return {"status":"expression_evaluation_error","nodes":[]}
    if not isinstance(found,list):
        return {"status":"non_element_result","nodes":[]}
    if any(not isinstance(node,etree._Element) for node in found):
        return {"status":"non_element_result","nodes":[]}
    if not found:return {"status":"no_node","nodes":[]}
    if len(found)>1:return {"status":"multiple_nodes","nodes":found}
    return {"status":"unique_node","nodes":found}


def current_result(snapshot, target, expression):
    result=run_xpath(snapshot,expression)
    status=result["status"]
    nodes=result["nodes"]
    if target is None:
        return "original_target_unavailable"
    if status=="unique_node":
        return ("unique_recorded_target" if
                snapshot["tree"].getpath(nodes[0])==
                snapshot["tree"].getpath(target)
                else "unique_other_node")
    if status=="multiple_nodes":
        paths={snapshot["tree"].getpath(node) for node in nodes}
        target_path=snapshot["tree"].getpath(target)
        return "multiple_including_target" if target_path in paths else "multiple_other_nodes"
    return status


def next_proxy_result(second, expression, site_anchor):
    if site_anchor is None:return "no_site_native_proxy"
    result=run_xpath(second,expression)
    if result["status"]=="unique_node":
        return ("unique_proxy_node" if
                second["tree"].getpath(result["nodes"][0])==
                second["tree"].getpath(site_anchor)
                else "unique_other_node")
    if result["status"]=="multiple_nodes":
        paths={second["tree"].getpath(node) for node in result["nodes"]}
        return ("multiple_including_proxy" if
                second["tree"].getpath(site_anchor) in paths
                else "multiple_other_nodes")
    return result["status"]


def measure(demo,idx,turns,positive,paths,cache):
    turn=turns[idx]
    action=recorded_action_element(turn)
    expr=action["xpath"]
    first_name=state_name(turn,"page")
    next_idx=next_browser_idx(turns,idx)
    follow=turns[next_idx] if next_idx is not None else None
    next_name=state_name(follow,"page") if follow is not None else None
    def source(name):
        if not name:return {"status":"no_direct_html"}
        key=(demo,name)
        stat,path=paths.get(key,("no_source",None))
        if stat!="fetched" or path is None:return {"status":stat}
        if key not in cache:cache[key]=html_snapshot(path)
        return cache[key]
    first=source(first_name)
    second=source(next_name)
    status,target=target_in_snapshot(first,positive["uid"])
    if status!="target_uid_unique":
        raise AssertionError("R3 target/source consistency unexpectedly changed")
    computed=first["tree"].getpath(target)
    if positive["dmr"]["xpath"]!=computed:
        raise AssertionError("R3 DMR/source exact correspondence unexpectedly changed")
    current=current_result(first,target,expr)
    next_eval=run_xpath(second,expr)
    pair_byte_identical=(
        int(first["sha256"]==second["sha256"])
        if first.get("status")==second.get("status")=="parsed" else -1)
    anchor_status="not_eligible"
    anchor=None
    if pair_byte_identical==0:
        anchor_status,anchor=anchor_proxy(first,second,original_site_id(target))
    proxy=next_proxy_result(second,expr,anchor)
    current_uid_val=target.attrib.get("data-webtasks-id","")
    next_uid_result="unavailable"
    if next_eval["status"]=="unique_node":
        next_uid=next_eval["nodes"][0].attrib.get("data-webtasks-id","")
        next_uid_result=("same_uid" if current_uid_val and
                         next_uid==current_uid_val
                         else "different_or_unset_uid")
    return {
        "demo":demo,"turn":idx,
        "dialect":xpath_dialect(expr),
        "current_expression_result":current,
        "next_expression_result":next_eval["status"],
        "next_expression_uid_relation":next_uid_result,
        "both_html_sources_available":int(pair_byte_identical!=-1),
        "html_bytes_identical":pair_byte_identical,
        "url_context_hint":compare_known(
            context_hint(turn)["url"],context_hint(follow)["url"])
            if follow is not None else "unknown",
        "site_native_proxy_status":anchor_status,
        "next_expression_proxy_result":proxy,
        "next_xpath_returns_single_node":int(next_eval["status"]=="unique_node"),
    }


def summary(rows):
    assert len(rows)==600
    group=lambda k:dict(sorted(Counter(r[k] for r in rows).items()))
    original=[r for r in rows if r["current_expression_result"]=="unique_recorded_target"]
    changed=[r for r in rows if r["html_bytes_identical"]==0]
    eligible=[r for r in rows if r["site_native_proxy_status"]=="site_native_proxy_candidate"]
    eligible_same=[r for r in eligible if r["url_context_hint"]=="same"]
    return {
        "protocol":"Recorded action XPath expression evaluation on frozen 600 raw DOM sources",
        "dataset_revision":SHA,
        "source_action_n":len(rows),
        "source_unique_target_recovered_n":len(original),
        "xpath_dialects":group("dialect"),
        "current_expression_results":group("current_expression_result"),
        "next_expression_results":group("next_expression_result"),
        "next_expression_uid_relations":group("next_expression_uid_relation"),
        "source_next_html_pairs":sum(r["both_html_sources_available"] for r in rows),
        "changed_next_html_pairs":len(changed),
        "site_native_proxy_eligible_n":len(eligible),
        "site_native_proxy_eligible_same_url_n":len(eligible_same),
        "site_native_proxy_expression_results":dict(sorted(
            Counter(r["next_expression_proxy_result"] for r in eligible).items())),
        "same_url_site_native_proxy_expression_results":dict(sorted(
            Counter(r["next_expression_proxy_result"] for r in eligible_same).items())),
        "site_native_proxy_not_independent_ground_truth":True,
        "browser_action_reexecution_measured":False,
        "logical_element_identity_independently_adjudicated":False,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    by_demo=load_original()
    keys={(demo,turn) for demo,idxs in by_demo.items() for turn in idxs}
    assert len(keys)==600
    positive=load_positive_targets(keys)
    if set(positive)!=keys or any(len(v)!=1 for v in positive.values()):
        raise AssertionError("Source candidate cohort changed")
    demos={d:replay_data(get_source(f"demonstrations/{d}/replay.json")) for d in by_demo}
    needed=set()
    for demo,idxs in by_demo.items():
        t=demos[demo]
        for i in idxs:
            nextidx=next_browser_idx(t,i)
            names=[state_name(t[i],"page")]
            if nextidx is not None:names.append(state_name(t[nextidx],"page"))
            for name in names:
                if not name:continue
                if not SAFE_FILE.fullmatch(name):
                    raise AssertionError("Unexpected recorded source HTML filename")
                needed.add((demo,name))
    fetched={}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fs={pool.submit(fetch_one,key):key for key in sorted(needed)}
        for n,f in enumerate(as_completed(fs),1):
            pair,status,path=f.result()
            fetched[pair]=(status,path)
            if n%200==0:print("R3C_SOURCE_FETCH",n,len(needed),flush=True)
    rows=[]
    for demo,idxs in by_demo.items():
        cache={}
        for index in sorted(idxs):
            rows.append(measure(demo,index,demos[demo],positive[(demo,index)][0],
                                fetched,cache))
            if len(rows)%100==0:print("R3C_TARGETS_CHECKED",len(rows),flush=True)
        cache.clear()
    if {(r["demo"],r["turn"]) for r in rows}!=keys:
        raise AssertionError("Action denominator changed")
    aggregate=summary(rows)
    aggregate["retrieved_html_sources"]=len(needed)
    aggregate["source_fetch_statuses"]=dict(sorted(Counter(
        status for status,_ in fetched.values()).items()))
    with (OUT/"r3c_action_xpath_600.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (OUT/"r3c_summary.json").write_text(
        json.dumps(aggregate,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R3C_SUMMARY",json.dumps(aggregate,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
