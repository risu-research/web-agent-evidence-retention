"""R3D post-result fixed cohort: investigate 11 source XPath mismatches and
75 site-native-id proxies with both recorded and canonical XPath generators.

The two populations are taken from the archived R3C numeric action table.
HTML and original locator strings remain in memory only.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

from weblinx_continuity_r1 import (
    SHA, load_original, replay_data, get_source, state_name, SAFE_FILE
)
from weblinx_continuity_r2 import fetch_one,context_hint,compare_known
from weblinx_continuity_r3 import (
    load_positive_targets,recorded_action_element,next_browser_idx,
    html_snapshot,target_in_snapshot,original_site_id,anchor_proxy,WORKERS
)
from weblinx_continuity_r3c import (
    run_xpath,current_result,next_proxy_result,xpath_dialect
)

ORIGINAL=Path("results/weblinx_continuity_r3c_actions.csv")
OUT=Path("out_continuity_r3d")
ID_EXPR=re.compile(r"""^id\(\s*(['"])(.*?)\1\s*\)""",re.I)


def load_selected():
    with ORIGINAL.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==600 and len({(r["demo"],r["turn"]) for r in rows})==600
    anomalies={(r["demo"],int(r["turn"])) for r in rows
               if r["current_expression_result"]!="unique_recorded_target"}
    proxies={(r["demo"],int(r["turn"])) for r in rows
             if r["site_native_proxy_status"]=="site_native_proxy_candidate"}
    if len(anomalies)!=11 or len(proxies)!=75:
        raise AssertionError("Source-selected follow-up populations differ")
    return anomalies,proxies,anomalies|proxies,rows


def root_anchor_diagnostic(expr,snap,target):
    match=ID_EXPR.match(expr.strip())
    if match is None:
        return "other_expression",0,0
    root_id=match.group(2)
    # XPath id("a b") could reference multiple IDs. Treat as unknown without
    # reinterpretation of a browser-side ID() expression.
    if not root_id or any(c.isspace() for c in root_id):
        return "complex_id_expression",0,0
    nodes=snap["site_id_map"].get(root_id,[])
    if not nodes:return "root_anchor_absent",0,0
    if len(nodes)>1:return "root_anchor_duplicated",0,0
    root=nodes[0]
    target_ancestors={snap["tree"].getpath(n) for n in target.iterancestors()}
    return (
        "root_anchor_unique",1,
        int(snap["tree"].getpath(root) in target_ancestors or root is target)
    )


def assess(demo,turn,ts,positive,requested,cache,is_anomaly,is_proxy):
    current=ts[turn]
    idx=next_browser_idx(ts,turn)
    next_event=ts[idx] if idx is not None else None
    first_name=state_name(current,"page")
    next_name=state_name(next_event,"page") if next_event is not None else None
    def get(name):
        if name is None:return {"status":"no_direct_source"}
        key=(demo,name)
        status,path=requested.get(key,("unavailable",None))
        if status!="fetched" or path is None:return {"status":status}
        if key not in cache:cache[key]=html_snapshot(path)
        return cache[key]
    first=get(first_name)
    second=get(next_name)
    state,target=target_in_snapshot(first,positive["uid"])
    if state!="target_uid_unique":raise AssertionError("Original source target missing")
    assert first["tree"].getpath(target)==positive["dmr"]["xpath"]
    expr=recorded_action_element(current)["xpath"]
    original=current_result(first,target,expr)
    anchor_status,anchor_known,ancestor=root_anchor_diagnostic(expr,first,target)
    if is_anomaly and original=="unique_recorded_target":
        raise AssertionError("Original 11-case anomaly changed")

    record={
        "demo":demo,"turn":turn,
        "in_original_11":int(is_anomaly),
        "in_site_native_75":int(is_proxy),
        "action_xpath_dialect":xpath_dialect(expr),
        "action_xpath_original_result":original,
        "root_id_anchor_status":anchor_status if is_anomaly else "not_audited",
        "root_id_anchor_is_unique":anchor_known if is_anomaly else 0,
        "target_descendant_of_root_anchor":ancestor if is_anomaly else 0,
        "source_html_parsed":int(first["status"]=="parsed"),
        "next_html_parsed":int(second.get("status")=="parsed"),
        "source_next_same_raw_bytes":(
            int(first["sha256"]==second["sha256"])
            if first.get("status")==second.get("status")=="parsed" else -1),
        "url_context_hint":(
            compare_known(context_hint(current)["url"],
                          context_hint(next_event)["url"])
            if next_event is not None else "unknown"),
        "site_native_proxy_status":"not_selected",
        "replay_xpath_selects_proxy":"not_selected",
        "canonical_xpath_selects_proxy":"not_selected",
        "proxy_canonical_path_changed":0,
        "site_native_proxy_text_unchanged":0,
        "recorded_uid_unchanged":0,
    }
    if is_proxy:
        if second.get("status")!="parsed" or first["sha256"]==second["sha256"]:
            raise AssertionError("Original changed-HTML proxy eligibility changed")
        status,proxy=anchor_proxy(first,second,original_site_id(target))
        if status!="site_native_proxy_candidate" or proxy is None:
            raise AssertionError("Original site-native proxy selection changed")
        record["site_native_proxy_status"]=status
        record["replay_xpath_selects_proxy"]=next_proxy_result(
            second,expr,proxy)
        record["canonical_xpath_selects_proxy"]=next_proxy_result(
            second,positive["dmr"]["xpath"],proxy)
        record["proxy_canonical_path_changed"]=int(
            first["tree"].getpath(target)!=second["tree"].getpath(proxy))
        record["site_native_proxy_text_unchanged"]=int(
            " ".join(target.itertext()).strip().casefold()==
            " ".join(proxy.itertext()).strip().casefold())
        record["recorded_uid_unchanged"]=int(bool(target.attrib.get("data-webtasks-id")) and
                                          target.attrib.get("data-webtasks-id")==
                                          proxy.attrib.get("data-webtasks-id"))
    return record


def summarize(rows):
    anomalies=[r for r in rows if r["in_original_11"]]
    proxy=[r for r in rows if r["in_site_native_75"]]
    if len(anomalies)!=11 or len(proxy)!=75:
        raise AssertionError("Missing selected cases")
    counts=lambda arr,name:dict(sorted(Counter(r[name] for r in arr).items()))
    paired=Counter()
    for r in proxy:
        a=r["replay_xpath_selects_proxy"]=="unique_proxy_node"
        c=r["canonical_xpath_selects_proxy"]=="unique_proxy_node"
        paired["both" if a and c else "replay_only" if a else
               "canonical_only" if c else "neither"]+=1
    by_url={}
    for label in ("same","different","unknown"):
        subset=[r for r in proxy if r["url_context_hint"]==label]
        by_url[label]={
            "n":len(subset),
            "replay_xpath_unique_proxy_n":sum(
                r["replay_xpath_selects_proxy"]=="unique_proxy_node"
                for r in subset),
            "canonical_xpath_unique_proxy_n":sum(
                r["canonical_xpath_selects_proxy"]=="unique_proxy_node"
                for r in subset),
        }
    return {
        "protocol":"post-observation fixed 11+75 source XPath diagnostics",
        "dataset_revision":SHA,
        "selected_action_n":len(rows),
        "initial_action_locator_anomalies_n":len(anomalies),
        "site_native_proxy_n":len(proxy),
        "cohort_overlap_n":sum(r["in_original_11"] and r["in_site_native_75"]
                               for r in rows),
        "original_anomaly_xpath_statuses":counts(anomalies,"action_xpath_original_result"),
        "original_anomaly_root_anchor_statuses":counts(anomalies,"root_id_anchor_status"),
        "original_anomaly_root_ancestors_confirmed":sum(
            r["target_descendant_of_root_anchor"] for r in anomalies),
        "proxy_replay_xpath_outcomes":counts(proxy,"replay_xpath_selects_proxy"),
        "proxy_canonical_xpath_outcomes":counts(proxy,"canonical_xpath_selects_proxy"),
        "proxy_paired_recovery":dict(sorted(paired.items())),
        "proxy_canonical_path_changed_n":sum(r["proxy_canonical_path_changed"] for r in proxy),
        "proxy_url_strata":by_url,
        "independent_logical_element_identity_labels":False,
        "browser_execution_trace_evaluated":False,
        "population_selected_after_original_R3C_results":True,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    anomalies,proxies,keys,_=load_selected()
    original=load_original()
    if not keys.issubset({(d,i) for d,ii in original.items() for i in ii}):
        raise AssertionError("Selected follow-up outside original frozen cohort")
    pos=load_positive_targets(keys)
    if set(pos)!=keys or any(len(v)!=1 for v in pos.values()):
        raise AssertionError("Target source inconsistency")
    demos=sorted({d for d,_ in keys})
    replays={d:replay_data(get_source(f"demonstrations/{d}/replay.json")) for d in demos}
    needed=set()
    for d,i in keys:
        t=replays[d]
        j=next_browser_idx(t,i)
        for name in (state_name(t[i],"page"),
                     state_name(t[j],"page") if j is not None else None):
            if name:
                if not SAFE_FILE.fullmatch(name):raise AssertionError("Unexpected source page")
                needed.add((d,name))
    fetched={}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fs={pool.submit(fetch_one,k):k for k in sorted(needed)}
        for n,f in enumerate(as_completed(fs),1):
            k,status,path=f.result()
            fetched[k]=(status,path)
            if n%50==0:print("R3D_FETCHED_FILES",n,len(needed),flush=True)
    rows=[]
    for d in demos:
        cache={}
        for i in sorted(index for name,index in keys if name==d):
            rows.append(assess(d,i,replays[d],pos[(d,i)][0],
                               fetched,cache,
                               (d,i) in anomalies,(d,i) in proxies))
        cache.clear()
    result=summarize(rows)
    result["original_cohort_n"]=600
    result["fetched_html_count"]=len(fetched)
    result["source_fetch_statuses"]=dict(sorted(
        Counter(status for status,path in fetched.values()).items()))
    with (OUT/"r3d_selected_cases.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (OUT/"r3d_summary.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R3D_SUMMARY",json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
