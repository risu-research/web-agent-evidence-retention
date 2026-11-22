"""R3: original target-action provenance and site-native cross-state feasibility.

Frozen inputs:
  WebLINX-full @ 36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8
  600 exact action keys from results/storage_cost_600_actions_2026-11-22.csv
No source HTML, URLs, element values, UID values, XPath strings or screenshots
are exported; only numeric and categorical diagnostics are retained.

This audit measures recorded source consistency and exploratory continuity
proxies; it does not independently establish action delivery or identity.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
import time
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

from huggingface_hub import hf_hub_download
from lxml import html as LH

from weblinx_continuity_r1 import (
    SHA, DATASET, RAW, SAFE_DEMO, SAFE_FILE, get_source, load_original,
    replay_data, state_name,
)
from weblinx_continuity_r2 import (
    MAX_SOURCE_BYTES, compact, context_hint, compare_known, fetch_one,
)

OUT=Path("out_continuity_r3")
WORKERS=8
ATTR="data-webtasks-id"
DOC_FIELD=re.compile(r"\[\[([a-zA-Z_]+)\]\]\s*(.*?)(?=(?:\[\[[a-zA-Z_]+\]\])|\Z)",re.S)
DOC_ATTR=re.compile(r"""([:\w-]+)\s*=\s*(['"])(.*?)\2""",re.S)
SAFE_ATTRS=("type","name","role")


def parse_dmr(doc):
    values={m.group(1).lower():m.group(2).strip() for m in DOC_FIELD.finditer(str(doc or ""))}
    attrs={k.lower():value.strip() for k,_,value in DOC_ATTR.findall(
        values.get("attributes",""))}
    return {
        "uid_in_attributes":attrs.get(ATTR,""),
        "xpath":values.get("xpath",""),
        "ordinary_html_id":attrs.get("id",""),
        "tag":compact(values.get("tag",""),60),
    }


def load_positive_targets(keys):
    positive=defaultdict(list)
    file=hf_hub_download(DATASET,"candidates/test_iid.jsonl",
                         repo_type="dataset",revision=SHA)
    with open(file,encoding="utf-8") as fh:
        for line in fh:
            obj=json.loads(line)
            key=(str(obj["demo_name"]),int(obj["turn_index"]))
            if key not in keys:continue
            if int(obj.get("label",0))==1:
                positive[key].append({
                    "uid":str(obj["uid"]),
                    "dmr":parse_dmr(obj.get("doc","")),
                    "target_rank":int(obj.get("rank",0)),
                })
    return positive


def recorded_action_element(turn):
    action=turn.get("action") if isinstance(turn,dict) else None
    action=action if isinstance(action,dict) else {}
    args=action.get("arguments") or {}
    if not isinstance(args,dict):args={}
    element=args.get("element")
    if not isinstance(element,dict):element={}
    attrs=element.get("attributes") or {}
    if not isinstance(attrs,dict):attrs={}
    # A separately authored string UID can be present; it must never stand
    # in for the embedded action-element observation.
    return {
        "intent":str(action.get("intent") or "unknown"),
        "element_present":bool(element),
        "uid":str(attrs.get(ATTR) or ""),
        "xpath":str(element.get("xpath") or ""),
        "tag":compact(element.get("tagName") or "",60),
        "ordinary_html_id":str(attrs.get("id") or ""),
        "args_uid":str(args.get("uid") or ""),
    }


def next_browser_idx(turns,index):
    for i in range(index+1,len(turns)):
        if turns[i].get("type")=="browser":
            return i
    return None


def html_snapshot(path):
    try:
        b=path.read_bytes()
        source_sha=hashlib.sha256(b).hexdigest()
        if len(b)>MAX_SOURCE_BYTES:
            return {"status":"over_size_limit","sha256":source_sha,
                    "bytes":len(b)}
        parser=LH.HTMLParser(recover=True,huge_tree=True,encoding="utf-8")
        root=LH.fromstring(b,parser=parser)
        tree=root.getroottree()
        uid_map=defaultdict(list)
        site_id_map=defaultdict(list)
        element_count=0
        for node in root.iter():
            if not isinstance(node.tag,str):continue
            element_count+=1
            uid=node.attrib.get(ATTR)
            if uid:uid_map[uid].append(node)
            ident=node.attrib.get("id")
            if ident:site_id_map[ident].append(node)
        return {
            "status":"parsed","bytes":len(b),"sha256":source_sha,
            "tree":tree,"uid_map":uid_map,"site_id_map":site_id_map,
            "element_count":element_count,
            "duplicate_uid_values":sum(len(v)>1 for v in uid_map.values()),
            "duplicate_site_id_values":sum(len(v)>1 for v in site_id_map.values()),
        }
    except Exception:
        return {"status":"parse_error"}


def target_in_snapshot(snapshot,uid):
    if snapshot.get("status")!="parsed":return ("source_unavailable",None)
    if not uid:return ("target_uid_missing",None)
    matches=snapshot["uid_map"].get(uid,[])
    if not matches:return ("target_uid_absent_from_html",None)
    if len(matches)!=1:return ("target_uid_duplicated_in_html",None)
    return ("target_uid_unique",matches[0])


def original_site_id(node):
    if node is None:return ""
    value=node.attrib.get("id","")
    return value.strip() if isinstance(value,str) else ""


def stable_attrs_compatible(a,b):
    if a.tag!=b.tag:return False
    # A changed attribute is an explicit contradiction when both sides have it.
    return all(a.attrib[k]==b.attrib[k] for k in SAFE_ATTRS
               if k in a.attrib and k in b.attrib)


def anchor_proxy(first,second,site_id):
    """No logical identity ground truth is created by this operation."""
    if not site_id:
        return "no_site_native_id",None
    a=first["site_id_map"].get(site_id,[])
    b=second["site_id_map"].get(site_id,[])
    if len(a)!=1:
        return ("source_id_duplicated" if len(a)>1 else
                "source_id_absent"),None
    if len(b)==0:
        return "next_id_absent",None
    if len(b)>1:
        return "next_id_duplicated",None
    if not stable_attrs_compatible(a[0],b[0]):
        return "site_id_signature_conflict",None
    return "site_native_proxy_candidate",b[0]


def parent_id(node):
    p=node.getparent() if node is not None else None
    return original_site_id(p)


def assess_action(demo,index,turns,positive,files,cache):
    item=positive
    action=recorded_action_element(turns[index])
    observed=turns[index]
    current_file=state_name(observed,"page")
    next_idx=next_browser_idx(turns,index)
    follow=turns[next_idx] if next_idx is not None else None
    next_file=state_name(follow,"page") if follow is not None else None
    current_key=(demo,current_file) if current_file else None
    next_key=(demo,next_file) if next_file else None
    src_status,src_path=files.get(current_key,("no_direct_html",None))
    nxt_status,nxt_path=files.get(next_key,("no_next_html",None))
    def snapshot(key,status,path):
        if status!="fetched" or path is None:return {"status":status}
        if key not in cache:
            cache[key]=html_snapshot(path)
        return cache[key]
    first=snapshot(current_key,src_status,src_path)
    second=snapshot(next_key,nxt_status,nxt_path)

    row={
        "demo":demo,"turn":index,"intent":action["intent"],
        "target_rank":item["target_rank"],
        "positive_candidate_count":1,
        "action_element_present":int(action["element_present"]),
        "action_element_uid_available":int(bool(action["uid"])),
        "action_args_uid_available":int(bool(action["args_uid"])),
        "dmr_attribute_uid_available":int(bool(item["dmr"]["uid_in_attributes"])),
        "dmr_uid_matches_dmr_attribute":int(
            bool(item["dmr"]["uid_in_attributes"])
            and item["dmr"]["uid_in_attributes"]==item["uid"]),
        "action_uid_equals_positive_uid":int(bool(action["uid"]) and
                                           action["uid"]==item["uid"]),
        "action_args_uid_equals_positive_uid":int(
            bool(action["args_uid"]) and action["args_uid"]==item["uid"]),
        "dmr_xpath_available":int(bool(item["dmr"]["xpath"])),
        "action_xpath_available":int(bool(action["xpath"])),
        "dmr_xpath_equals_action_xpath":int(
            bool(item["dmr"]["xpath"]) and
            item["dmr"]["xpath"]==action["xpath"]),
        "dmr_tag_equals_action_tag":int(
            bool(action["tag"]) and action["tag"]==item["dmr"]["tag"]),
        "direct_current_html":int(current_file is not None),
        "current_html_fetch_status":src_status,
        "current_html_parse_status":first.get("status"),
        "current_html_bytes":int(first.get("bytes",0)),
        "current_html_sha256":first.get("sha256",""),
        "current_html_element_n":int(first.get("element_count",0)),
        "current_uid_duplicates":int(first.get("duplicate_uid_values",0)),
        "current_site_id_duplicates":int(first.get("duplicate_site_id_values",0)),
        "current_target_uid_status":"unobserved",
        "recorded_uid_equals_html_site_node":0,
        "dmr_xpath_equals_computed_source_xpath":0,
        "action_xpath_equals_computed_source_xpath":0,
        "dmr_site_id_matches_html":0,
        "action_site_id_matches_html":0,
        "next_browser_turn":int(next_idx) if next_idx is not None else "",
        "has_next_browser_turn":int(next_idx is not None),
        "direct_next_html":int(next_file is not None),
        "next_html_fetch_status":nxt_status,
        "next_html_parse_status":second.get("status"),
        "next_html_bytes":int(second.get("bytes",0)),
        "next_html_sha256":second.get("sha256",""),
        "next_html_element_n":int(second.get("element_count",0)),
        "next_uid_duplicates":int(second.get("duplicate_uid_values",0)),
        "next_site_id_duplicates":int(second.get("duplicate_site_id_values",0)),
        "url_context_hint":(compare_known(
            context_hint(observed)["url"],context_hint(follow)["url"])
            if follow is not None else "unknown"),
        "tab_context_hint":(compare_known(
            context_hint(observed)["tab"],context_hint(follow)["tab"])
            if follow is not None else "unknown"),
        "same_html_bytes":-1,
        "continuity_proxy_status":"source_not_eligible",
        "source_target_has_site_id":0,
        "source_target_site_id_unique":0,
        "next_site_id_unique":0,
        "site_native_anchor_has_same_tag":0,
        "site_native_anchor_same_text":0,
        "site_native_anchor_same_parent_id":0,
        "site_native_anchor_same_xpath":0,
        "site_native_anchor_same_webtasks_uid":0,
    }
    state,node=target_in_snapshot(first,item["uid"])
    row["current_target_uid_status"]=state
    if node is not None:
        xpath=first["tree"].getpath(node)
        row["recorded_uid_equals_html_site_node"]=1
        row["dmr_xpath_equals_computed_source_xpath"]=int(
            bool(item["dmr"]["xpath"]) and item["dmr"]["xpath"]==xpath)
        row["action_xpath_equals_computed_source_xpath"]=int(
            bool(action["xpath"]) and action["xpath"]==xpath)
        html_id=original_site_id(node)
        row["dmr_site_id_matches_html"]=int(bool(html_id) and
                                          html_id==item["dmr"]["ordinary_html_id"])
        row["action_site_id_matches_html"]=int(bool(html_id) and
                                             html_id==action["ordinary_html_id"])
        row["source_target_has_site_id"]=int(bool(html_id))
        row["source_target_site_id_unique"]=int(
            bool(html_id) and len(first["site_id_map"].get(html_id,[]))==1)

    if first.get("status")=="parsed" and second.get("status")=="parsed":
        row["same_html_bytes"]=int(first["sha256"]==second["sha256"])
        if first["sha256"]==second["sha256"]:
            row["continuity_proxy_status"]="identical_html_bytes"
        elif node is None:
            row["continuity_proxy_status"]="target_uid_not_unique_in_source"
        else:
            html_id=original_site_id(node)
            status,anchor=anchor_proxy(first,second,html_id)
            row["continuity_proxy_status"]=status
            if html_id:
                row["next_site_id_unique"]=int(
                    len(second["site_id_map"].get(html_id,[]))==1)
            if anchor is not None:
                row["site_native_anchor_has_same_tag"]=int(node.tag==anchor.tag)
                row["site_native_anchor_same_text"]=int(
                    compact(" ".join(node.itertext()))==
                    compact(" ".join(anchor.itertext())))
                row["site_native_anchor_same_parent_id"]=int(
                    bool(parent_id(node)) and
                    parent_id(node)==parent_id(anchor))
                row["site_native_anchor_same_xpath"]=int(
                    first["tree"].getpath(node)==
                    second["tree"].getpath(anchor))
                row["site_native_anchor_same_webtasks_uid"]=int(
                    bool(node.attrib.get(ATTR)) and
                    node.attrib.get(ATTR)==anchor.attrib.get(ATTR))
    return row


def numeric_summary(rows):
    if len(rows)!=600:
        raise AssertionError(f"Frozen cohort changed: {len(rows)}")
    group=lambda col:dict(sorted(Counter(r[col] for r in rows).items(),
                                 key=lambda kv:str(kv[0])))
    count=lambda col:sum(int(r[col]) for r in rows)
    numeric_fields=[
        "action_element_present","action_element_uid_available",
        "action_args_uid_available","dmr_attribute_uid_available",
        "dmr_uid_matches_dmr_attribute","action_uid_equals_positive_uid",
        "action_args_uid_equals_positive_uid","dmr_xpath_available",
        "action_xpath_available","dmr_xpath_equals_action_xpath",
        "dmr_tag_equals_action_tag","direct_current_html",
        "recorded_uid_equals_html_site_node",
        "dmr_xpath_equals_computed_source_xpath",
        "action_xpath_equals_computed_source_xpath",
        "dmr_site_id_matches_html","action_site_id_matches_html",
        "has_next_browser_turn","direct_next_html",
        "source_target_has_site_id","source_target_site_id_unique",
        "next_site_id_unique","site_native_anchor_has_same_tag",
        "site_native_anchor_same_text",
        "site_native_anchor_same_parent_id",
        "site_native_anchor_same_xpath",
        "site_native_anchor_same_webtasks_uid",
    ]
    valid=[r for r in rows if r["continuity_proxy_status"]=="site_native_proxy_candidate"]
    changed=[r for r in rows if r["same_html_bytes"]==0]
    by_url={}
    for category in ("same","different","unknown"):
        subset=[r for r in changed if r["url_context_hint"]==category]
        by_url[category]={
            "changed_html_pairs":len(subset),
            "native_id_proxy_candidates":sum(
                r["continuity_proxy_status"]=="site_native_proxy_candidate"
                for r in subset),
            "native_id_relocated_xpath":sum(
                r["continuity_proxy_status"]=="site_native_proxy_candidate" and
                not r["site_native_anchor_same_xpath"] for r in subset),
        }
    return {
        "experiment":"Round 3 original action provenance and proxy continuity",
        "dataset":DATASET,"dataset_revision":SHA,
        "source_cohort":"same 600 actions in 55 demos as storage-cost baseline",
        "action_count":len(rows),"demonstration_count":len(set(r["demo"] for r in rows)),
        "numeric_totals":{k:count(k) for k in numeric_fields},
        "action_intents":group("intent"),
        "current_html_fetch_statuses":group("current_html_fetch_status"),
        "current_html_parse_statuses":group("current_html_parse_status"),
        "current_target_uid_statuses":group("current_target_uid_status"),
        "next_html_fetch_statuses":group("next_html_fetch_status"),
        "next_html_parse_statuses":group("next_html_parse_status"),
        "original_to_next_html_equal_counts":group("same_html_bytes"),
        "url_context_hint_counts":group("url_context_hint"),
        "continuity_proxy_statuses":group("continuity_proxy_status"),
        "eligible_same_site_native_id_proxy_n":len(valid),
        "eligible_proxy_changed_xpath_n":sum(
            not r["site_native_anchor_same_xpath"] for r in valid),
        "eligible_proxy_changed_recorded_uid_n":sum(
            not r["site_native_anchor_same_webtasks_uid"] for r in valid),
        "changed_source_url_strata":by_url,
        "independent_logical_identity_ground_truth":False,
        "independent_browser_event_recipient_ground_truth":False,
        "raw_source_html_exported":False,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    by_demo=load_original()
    keys={(demo,index) for demo,idxs in by_demo.items() for index in idxs}
    if len(keys)!=600:raise AssertionError("Duplicate original cohort keys")
    positives=load_positive_targets(keys)
    if set(positives)!=keys:
        raise AssertionError("Missing positive candidate group")
    if any(len(v)!=1 for v in positives.values()):
        raise AssertionError("Ambiguous target label in fixed cohort")
    replays={}
    for demo in by_demo:
        replays[demo]=replay_data(
            get_source(f"demonstrations/{demo}/replay.json"))
        if any(i>=len(replays[demo]) for i in by_demo[demo]):
            raise AssertionError("Turn index outside official replay")

    # Freeze all requested source page paths from original replay metadata
    # before looking at whether a target is traceable.
    needed=set()
    for demo,idxs in by_demo.items():
        ts=replays[demo]
        for index in idxs:
            current=state_name(ts[index],"page")
            j=next_browser_idx(ts,index)
            nxt=state_name(ts[j],"page") if j is not None else None
            for path in (current,nxt):
                if path is not None:
                    if not SAFE_FILE.fullmatch(path):
                        raise AssertionError("Unrecognized recorded filename")
                    needed.add((demo,path))
    sources={}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures={ex.submit(fetch_one,pair):pair for pair in sorted(needed)}
        for n,f in enumerate(as_completed(futures),1):
            pair,status,path=f.result()
            sources[pair]=(status,path)
            if n%100==0:print("R3_FETCHED_SOURCE_COUNT",n,len(needed),flush=True)
    rows=[]
    for demo,idxs in by_demo.items():
        cache={}
        ts=replays[demo]
        for index in sorted(idxs):
            row=assess_action(demo,index,ts,positives[(demo,index)][0],
                              sources,cache)
            rows.append(row)
            if len(rows)%100==0:
                print("R3_ANALYZED_ACTIONS",len(rows),flush=True)
        # Keep only current demo's decoded pages, limiting retained source DOM.
        cache.clear()
    assert len(rows)==600
    observed_keys={(r["demo"],r["turn"]) for r in rows}
    if observed_keys!=keys:
        raise AssertionError("R3 did not preserve every frozen sample action")
    report=numeric_summary(rows)
    report["unique_named_html_sources"]=len(needed)
    report["source_retrieval_statuses"]=dict(sorted(Counter(
        status for status,_ in sources.values()).items()))
    report["positive_candidate_count_total"]=sum(len(v) for v in positives.values())
    report["source_selection_preceded_content_analysis"]=True
    report["target_identity_inference_used_in_sample_selection"]=False

    with (OUT/"r3_action_source_600.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT/"r3_summary.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R3_SUMMARY",json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
