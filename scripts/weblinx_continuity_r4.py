"""R4 exploratory non-ID semantic corroboration on all 11+75 fixed WebLINX cases.

Target in ORIGINAL source is found by official WebLINX UID. The SEMANTIC MATCHER
itself receives only HTML tags, inner text and native non-ID semantic fields.
Next-state site-native ID proxy is accessed only AFTER producing the independent
semantic channel match statuses; neither XPath nor any UID/ID is passed to the
matcher. Raw attributes, user text, URLs and locator strings stay in memory.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

from weblinx_continuity_r1 import (
    SHA,SAFE_FILE,get_source,load_original,replay_data,state_name
)
from weblinx_continuity_r2 import fetch_one,compare_known,context_hint
from weblinx_continuity_r3 import (
    load_positive_targets,html_snapshot,target_in_snapshot,
    original_site_id,anchor_proxy,next_browser_idx,recorded_action_element,
    WORKERS
)
from weblinx_continuity_r3d import ID_EXPR

FROZEN=Path("results/weblinx_continuity_r3d_cases.csv")
FROZEN_SHA="234352ddb7656d7f8d8f60a65f5222fc971f37a6dea0f1b983bfb6dc54646e61"
OUT=Path("out_continuity_r4")
SPACE=re.compile(r"\s+")

# All are disjoint from "id", data-webtasks-id, xpath and DOM coordinates.
FAMILIES={
    "text":"text",
    "data-testid":"test",
    "data-test":"test",
    "href":"href",
    "name_type":"form",
    "aria-label":"accessible",
    "title":"accessible",
    "placeholder":"accessible",
}
FORM_TAGS=frozenset(("input","select","textarea","button"))


def normalized(value,max_chars=160):
    if value is None:return None
    if isinstance(value,str):
        value=SPACE.sub(" ",value).strip().casefold()
    else:return None
    return value if 4<=len(value)<=max_chars else None


def small_text(node):
    pieces=[];total=0
    for v in node.itertext():
        total+=len(v)
        if total>360:return None
        pieces.append(v)
    return normalized(" ".join(pieces),160)


def channels(node):
    tag=str(node.tag).casefold()
    attrs=node.attrib
    features={}
    txt=small_text(node)
    if txt and tag not in ("script","style","noscript"):
        features["text"]=(tag,txt)
    for k in ("data-testid","data-test","aria-label","title","placeholder"):
        v=normalized(attrs.get(k))
        if v:features[k]=(tag,v)
    href=attrs.get("href")
    if tag=="a" and isinstance(href,str):
        raw=href.strip()
        if raw and raw!="block" and raw!="#" and not raw.lower().startswith(("javascript:","data:")):
            norm=normalized(raw,1000)
            if norm:features["href"]=(tag,norm)
    if tag in FORM_TAGS:
        name=normalized(attrs.get("name"),160)
        if name:
            typ=str(attrs.get("type") or "").strip().casefold()
            features["name_type"]=(tag,name,typ)
    return features


def channel_matches_without_ids(source,target,next_state):
    """Build matcher indexes without access to XPath, UID or HTML site ID.

    Site-native ID proxy is applied by caller ONLY AFTER this call completes.
    All unique matches returned are actual parsed elements.
    """
    if source.get("status")!="parsed" or next_state.get("status")!="parsed":
        raise AssertionError("Source pair expected parsed")
    target_ch=channels(target)
    tag=target.tag
    all_source=[n for n in source["tree"].getroot().iter() if n.tag==tag]
    all_next=[n for n in next_state["tree"].getroot().iter() if n.tag==tag]
    source_values=defaultdict(lambda:defaultdict(list))
    next_values=defaultdict(lambda:defaultdict(list))
    for n in all_source:
        for key,value in channels(n).items():
            source_values[key][value].append(n)
    for n in all_next:
        for key,value in channels(n).items():
            next_values[key][value].append(n)
    out={}
    for key,value in target_ch.items():
        current_hits=source_values[key].get(value,[])
        later_hits=next_values[key].get(value,[])
        assert target in current_hits
        if len(current_hits)!=1:
            status="source_ambiguous"
        elif not later_hits:
            status="next_absent"
        elif len(later_hits)>1:
            status="next_ambiguous"
        else:
            status="next_unique"
        out[key]={
            "status":status,
            "source_n":len(current_hits),
            "next_n":len(later_hits),
            "next_node":later_hits[0] if status=="next_unique" else None,
        }
    return out


def source_only_channel_availability(snapshot,target):
    """11 anomaly cohort: original-page unique semantic cues independent of XPath."""
    source=defaultdict(lambda:defaultdict(int))
    target_features=channels(target)
    for node in snapshot["tree"].getroot().iter():
        if node.tag!=target.tag:continue
        for k,v in channels(node).items():
            if k in target_features:
                source[k][v]+=1
    return {
        "channel_count":len(target_features),
        "families_present":len({FAMILIES[k] for k in target_features}),
        "unique_channel_count":sum(
            source[k][value]==1 for k,value in target_features.items()
        ),
        "unique_families":len({
            FAMILIES[k] for k,value in target_features.items()
            if source[k][value]==1
        }),
    }


def root_relation(expr,first,target,second):
    match=ID_EXPR.match((expr or "").strip())
    if match is None:return "not_root_id",0
    root_id=match.group(2)
    if not root_id or any(c.isspace() for c in root_id):
        return "complex_root_id",0
    source_nodes=first["site_id_map"].get(root_id,[])
    next_nodes=second["site_id_map"].get(root_id,[])
    unique_next=int(len(next_nodes)==1)
    if not source_nodes:return "absent_from_source",unique_next
    if len(source_nodes)!=1:return "duplicated_in_source",unique_next
    root=source_nodes[0]
    if root is target:return "target_node",unique_next
    if root in set(target.iterancestors()):return "target_ancestor",unique_next
    return "outside_target_ancestry",unique_next


def audit_action(demo,index,ts,item,source_files,cache,group):
    current=ts[index]
    nextidx=next_browser_idx(ts,index)
    follow=ts[nextidx] if nextidx is not None else None
    page=state_name(current,"page")
    later=state_name(follow,"page") if follow is not None else None
    def doc(name):
        if not name:return {"status":"missing_direct_path"}
        key=(demo,name)
        status,path=source_files.get(key,("source_unavailable",None))
        if status!="fetched" or path is None:return {"status":status}
        if key not in cache:cache[key]=html_snapshot(path)
        return cache[key]
    first=doc(page)
    second=doc(later) if group!="source_xpath_anomaly" else {"status":"not_needed"}
    status,target=target_in_snapshot(first,item["uid"])
    if status!="target_uid_unique":
        raise AssertionError("Original frozen source target changed")
    assert first["tree"].getpath(target)==item["dmr"]["xpath"]
    action=recorded_action_element(current)
    row={
        "demo":demo,"turn":index,"group":group,
        "original_html_status":first["status"],
        "next_html_status":second["status"],
        "same_url_hint":(
            compare_known(context_hint(current)["url"],context_hint(follow)["url"])
            if follow is not None else "unknown"),
        "blinded_status":"not_a_pair",
        "source_semantic_channel_n":0,"source_semantic_family_n":0,
        "matched_channel_n":0,"matched_family_n":0,
        "unique_next_channel_n":0,"conflicting_unique_channel_n":0,
        "source_ambiguous_channel_n":0,"next_ambiguous_channel_n":0,
        "next_absent_channel_n":0,
        "unique_semantic_channel_n_original":0,
        "unique_semantic_family_n_original":0,
        "root_id_relation":"not_applicable","root_id_unique_in_next":0,
        "original_source_xpath_status":"not_evaluated",
    }
    if group=="source_xpath_anomaly":
        from weblinx_continuity_r3c import current_result
        from weblinx_continuity_r3d import root_anchor_diagnostic
        xpath_status=current_result(first,target,action["xpath"])
        if xpath_status=="unique_recorded_target":
            raise AssertionError("Unexpected disappearance of original XPath anomaly")
        row["original_source_xpath_status"]=xpath_status
        availability=source_only_channel_availability(first,target)
        row["source_semantic_channel_n"]=availability["channel_count"]
        row["source_semantic_family_n"]=availability["families_present"]
        row["unique_semantic_channel_n_original"]=availability["unique_channel_count"]
        row["unique_semantic_family_n_original"]=availability["unique_families"]
        root_status,_,_=root_anchor_diagnostic(action["xpath"],first,target)
        row["root_id_relation"]=root_status
        return row

    if second.get("status")!="parsed" or first["sha256"]==second["sha256"]:
        raise AssertionError("Original native ID proxy source pairs unexpectedly invalid")
    proxy_status,proxy=anchor_proxy(first,second,original_site_id(target))
    if proxy_status!="site_native_proxy_candidate" or proxy is None:
        raise AssertionError("Previously fixed source-native proxy changed")

    # The matcher has no notion of target ID, UID, or XPath. Its matches are
    # produced before the source-native ID reference node is compared.
    match_data=channel_matches_without_ids(first,target,second)
    agreeing=[];conflicts=[];other=Counter()
    for key,entry in match_data.items():
        if entry["status"]=="next_unique":
            selected=entry["next_node"]
            if selected is proxy:agreeing.append(key)
            else:conflicts.append(key)
        else:other[entry["status"]]+=1
    families_agree={FAMILIES[key] for key in agreeing}
    if conflicts:
        status="conflict"
    elif len(families_agree)>=2:
        status="multi_family_corroborated"
    elif len(families_agree)==1:
        status="single_family_corroborated"
    else:status="none"
    root_status,root_unique_next=root_relation(action["xpath"],first,target,second)
    row.update({
        "blinded_status":status,
        "source_semantic_channel_n":len(match_data),
        "source_semantic_family_n":len({FAMILIES[k] for k in match_data}),
        "matched_channel_n":len(agreeing),
        "matched_family_n":len(families_agree),
        "unique_next_channel_n":len(agreeing)+len(conflicts),
        "conflicting_unique_channel_n":len(conflicts),
        "source_ambiguous_channel_n":other["source_ambiguous"],
        "next_ambiguous_channel_n":other["next_ambiguous"],
        "next_absent_channel_n":other["next_absent"],
        "root_id_relation":root_status,
        "root_id_unique_in_next":root_unique_next,
    })
    return row


def aggregate(rows):
    if len(rows)!=86:raise AssertionError("Frozen union changed")
    group=lambda rows,k:dict(sorted(Counter(r[k] for r in rows).items()))
    anomal=[r for r in rows if r["group"]=="source_xpath_anomaly"]
    miss=[r for r in rows if r["group"]=="captured_only_8"]
    ctrl=[r for r in rows if r["group"]=="both_67"]
    if (len(anomal),len(miss),len(ctrl))!=(11,8,67):
        raise AssertionError("Missing cases from original fixed groups")
    def describe(subset):
        return {
            "n":len(subset),
            "blinded_semantic_outcomes":group(subset,"blinded_status"),
            "original_semantic_family_counts":group(subset,"source_semantic_family_n"),
            "matching_semantic_family_counts":group(subset,"matched_family_n"),
            "root_id_relation":group(subset,"root_id_relation"),
            "root_id_unique_in_next_n":sum(r["root_id_unique_in_next"] for r in subset),
            "unique_channel_conflict_n":sum(r["conflicting_unique_channel_n"]>0
                                            for r in subset),
            "source_ambiguous_case_n":sum(r["source_ambiguous_channel_n"]>0
                                         for r in subset),
            "next_ambiguous_case_n":sum(r["next_ambiguous_channel_n"]>0
                                       for r in subset),
            "next_absent_case_n":sum(r["next_absent_channel_n"]>0
                                    for r in subset),
        }
    same=[r for r in miss+ctrl if r["same_url_hint"]=="same"]
    return {
        "study":"R4 fixed 8 generator disagreements, 67 all both-success controls, 11 original source anomalies",
        "revision":SHA,
        "case_count":len(rows),
        "demo_count":len({r["demo"] for r in rows}),
        "anomalies_11":{
            "n":len(anomal),
            "source_xpath_outcomes":group(anomal,"original_source_xpath_status"),
            "source_unique_semantic_channel_count_distribution":group(
                anomal,"unique_semantic_channel_n_original"),
            "source_unique_semantic_family_count_distribution":group(
                anomal,"unique_semantic_family_n_original"),
            "with_one_or_more_unique_source_semantic_channel":sum(
                r["unique_semantic_channel_n_original"]>0 for r in anomal),
            "with_two_or_more_unique_source_semantic_families":sum(
                r["unique_semantic_family_n_original"]>=2 for r in anomal),
        },
        "captured_only_8":describe(miss),
        "both_67":describe(ctrl),
        "all_proxy_75":describe(miss+ctrl),
        "same_url_proxy_subset":describe(same),
        "blind_comparator_excluded_locator_fields":[
            "XPath","source WebLINX UID","HTML id","DOM coordinates","CSS class"],
        "source_native_id_proxy_independently_adjudicated":False,
        "browser_action_recipient_independently_logged":False,
        "identity_label_status":"SOURCE_SEMANTIC_CORROBORATION_ONLY",
    }


def load_original_cohort():
    if hashlib.sha256(FROZEN.read_bytes()).hexdigest()!=FROZEN_SHA:
        raise AssertionError("Original 86-case source file SHA changed")
    with FROZEN.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==86
    assigned={}
    for r in rows:
        key=(r["demo"],int(r["turn"]))
        if r["in_original_11"]=="1":
            category="source_xpath_anomaly"
        elif r["in_site_native_75"]=="1":
            category=("both_67" if r["canonical_xpath_selects_proxy"]==
                      "unique_proxy_node" else "captured_only_8")
        else:raise AssertionError("Unassigned source case")
        if key in assigned:raise AssertionError("Duplicate key")
        assigned[key]=category
    counts=Counter(assigned.values())
    assert counts=={"source_xpath_anomaly":11,"captured_only_8":8,"both_67":67}
    return dict(sorted(assigned.items()))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    chosen=load_original_cohort()
    original_keys=load_original()
    all_keys={(d,i) for d,idx in original_keys.items() for i in idx}
    if not set(chosen).issubset(all_keys):
        raise AssertionError("Follow-up outside frozen original 600 actions")
    pos=load_positive_targets(set(chosen))
    if set(pos)!=set(chosen) or any(len(v)!=1 for v in pos.values()):
        raise AssertionError("Candidate target unavailable")
    demos={d:replay_data(get_source(f"demonstrations/{d}/replay.json"))
           for d in sorted({key[0] for key in chosen})}
    paths=set()
    for (demo,i),group in chosen.items():
        turns=demos[demo]
        requested=[state_name(turns[i],"page")]
        if group!="source_xpath_anomaly":
            next_idx=next_browser_idx(turns,i)
            requested.append(state_name(turns[next_idx],"page")
                             if next_idx is not None else None)
        for name in requested:
            if not name:continue
            if not SAFE_FILE.fullmatch(name):
                raise AssertionError("Malformed original HTML path")
            paths.add((demo,name))
    fetched={}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fs={pool.submit(fetch_one,k):k for k in sorted(paths)}
        for n,f in enumerate(as_completed(fs),1):
            k,status,path=f.result()
            fetched[k]=(status,path)
            if n%50==0:print("R4_SOURCE_FILES",n,len(paths),flush=True)
    casebook=[]
    for demo in sorted(demos):
        cache={}
        for _,idx in sorted(k for k in chosen if k[0]==demo):
            row=audit_action(demo,idx,demos[demo],pos[(demo,idx)][0],
                             fetched,cache,chosen[(demo,idx)])
            casebook.append(row)
        cache.clear()
    assert {(r["demo"],r["turn"]) for r in casebook}==set(chosen)
    report=aggregate(casebook)
    report["original_named_source_file_count"]=len(paths)
    report["source_file_fetch_statuses"]=dict(sorted(Counter(
        value[0] for value in fetched.values()).items()))
    with (OUT/"r4_semantic_cases_86.csv").open("w",newline="",encoding="utf-8") as f:
        fields=list(casebook[0])
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(casebook)
    (OUT/"r4_semantic_summary.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R4_SUMMARY",json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
