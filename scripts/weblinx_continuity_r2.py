"""R2: independently inspect the pinned HTML byte sources of frozen R1 pairs.

Measured outcomes are source availability, parse success, syntax-level UID/XPath
agreement, and recorded navigation-context hints. Raw DOM, attributes, URLs,
and literal element identifiers are never exported.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import quote

import requests
from lxml import html as LH

from weblinx_continuity_r1 import (
    DATASET,SHA,SAFE_DEMO,SAFE_FILE,get_source,replay_data
)

IN=Path("out_continuity_r1/source_pairs_frozen.csv")
OUT=Path("out_continuity_r2")
RAW=Path("wl_continuity_r1")
MAX_SOURCE_BYTES=35_000_000
WORKERS=6
ID_FIELD="data-webtasks-id"
WS=re.compile(r"\s+")


def fetch_one(pair):
    demo,name=pair
    assert SAFE_DEMO.fullmatch(demo) and SAFE_FILE.fullmatch(name)
    path=f"demonstrations/{demo}/pages/{name}"
    file=RAW/path
    if file.exists() and file.stat().st_size>0:
        return (pair,"fetched",file)
    file.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://huggingface.co/datasets/{DATASET}/resolve/{SHA}/{quote(path,safe='/')}?download=true"
    for trial in range(6):
        try:
            with requests.get(url,stream=True,timeout=(25,180)) as r:
                if r.status_code==404:
                    return (pair,"http_404",None)
                if r.status_code==429:
                    time.sleep(min(30,2*(trial+1)**2));continue
                r.raise_for_status()
                tmp=file.with_suffix(file.suffix+".part")
                with tmp.open("wb") as h:
                    for chunk in r.iter_content(1024*1024):
                        if chunk:h.write(chunk)
                tmp.replace(file)
                return (pair,"fetched",file)
        except requests.RequestException:
            time.sleep(min(20,2**trial))
    return (pair,"source_fetch_failure",None)


def compact(value,length=120):
    return WS.sub(" ",str(value or "")).strip().casefold()[:length]


def feature_signature(node):
    attrs=node.attrib
    # This short signature is a corroborating check, not a logical identity label.
    return (
        compact(node.tag,60),
        tuple((k,compact(attrs.get(k),100)) for k in
              ("id","name","type","role","aria-label","data-testid")
              if attrs.get(k)),
        compact(node.text,80),
    )


def inspect_html_bytes(blob):
    digest=hashlib.sha256(blob).hexdigest()
    size=len(blob)
    if size>MAX_SOURCE_BYTES:
        return {"parse_status":"source_too_large","sha256":digest,"bytes":size}
    try:
        parser=LH.HTMLParser(recover=True,huge_tree=True,encoding="utf-8")
        root=LH.fromstring(blob,parser=parser)
        tree=root.getroottree()
    except (ValueError,TypeError,Exception):
        return {"parse_status":"parse_error","sha256":digest,"bytes":size}
    total_elements=0
    uid_to_nodes=defaultdict(list)
    xpath_to_node={}
    for node in root.iter():
        if not isinstance(node.tag,str):continue
        total_elements+=1
        uid=node.attrib.get(ID_FIELD)
        if uid:
            path=tree.getpath(node)
            item=(path,feature_signature(node))
            uid_to_nodes[uid].append(item)
            xpath_to_node[path]=(uid,item[1])
    unique={uid:entries[0] for uid,entries in uid_to_nodes.items()
            if len(entries)==1}
    return {
        "parse_status":"parsed",
        "sha256":digest,
        "bytes":size,
        "total_elements":total_elements,
        "uid_attributed_elements":sum(len(x) for x in uid_to_nodes.values()),
        "unique_uid_elements":len(unique),
        "repeated_uid_values":sum(len(v)>1 for v in uid_to_nodes.values()),
        "uid_map":unique,
        "xpath_map":xpath_to_node,
    }


def context_hint(turn):
    action=turn.get("action") or {}
    args=action.get("arguments") or {}
    meta=args.get("metadata") if isinstance(args,dict) else None
    props=args.get("properties") if isinstance(args,dict) else None
    state=turn.get("state") or {}
    if not isinstance(meta,dict):meta={}
    if not isinstance(props,dict):props={}
    # These values are hints taken from replay event metadata.
    url=state.get("url") or meta.get("url") or props.get("url")
    tab=state.get("tabId") or meta.get("tabId") or props.get("tabId")
    doc=state.get("documentId") or meta.get("documentId") or props.get("documentId")
    return {"url":str(url) if url else None,
            "tab":str(tab) if tab is not None else None,
            "document":str(doc) if doc is not None else None}


def compare_known(a,b):
    if a is None or b is None:return "unknown"
    return "same" if a==b else "different"


def compare_pages(p,q):
    a=p["uid_map"];b=q["uid_map"]
    au=p["xpath_map"];bu=q["xpath_map"]
    shared_uid=set(a)&set(b)
    shared_xpath=set(au)&set(bu)
    same_uid_xpath=sum(a[u][0]==b[u][0] for u in shared_uid)
    move_uid_xpath=len(shared_uid)-same_uid_xpath
    same_uid_feature=sum(a[u][1]==b[u][1] for u in shared_uid)
    unchanged_both=sum(a[u]==b[u] for u in shared_uid)
    same_xpath_uid=sum(au[x][0]==bu[x][0] for x in shared_xpath)
    changed_xpath_uid=len(shared_xpath)-same_xpath_uid
    same_xpath_tag=sum(au[x][1][0]==bu[x][1][0] for x in shared_xpath)
    return {
        "first_total_elements":p["total_elements"],
        "second_total_elements":q["total_elements"],
        "first_uid_attributed":p["uid_attributed_elements"],
        "second_uid_attributed":q["uid_attributed_elements"],
        "first_unique_uids":p["unique_uid_elements"],
        "second_unique_uids":q["unique_uid_elements"],
        "first_duplicate_uid_values":p["repeated_uid_values"],
        "second_duplicate_uid_values":q["repeated_uid_values"],
        "same_uid_at_both":len(shared_uid),
        "same_uid_same_xpath":same_uid_xpath,
        "same_uid_changed_xpath":move_uid_xpath,
        "same_uid_same_feature_signature":same_uid_feature,
        "same_uid_same_xpath_and_features":unchanged_both,
        "same_xpath_both":len(shared_xpath),
        "same_xpath_same_uid":same_xpath_uid,
        "same_xpath_different_uid":changed_xpath_uid,
        "same_xpath_same_tag":same_xpath_tag,
        "first_uids_absent_from_second":len(set(a)-set(b)),
        "second_uids_new":len(set(b)-set(a)),
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with IN.open(newline="",encoding="utf-8") as f:
        selected=list(csv.DictReader(f))
    assert len(selected)==165 and len({r["demo"] for r in selected})==55
    tasks={(r["demo"],r["page1"]) for r in selected}
    tasks.update((r["demo"],r["page2"]) for r in selected)
    fetched={}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fs={pool.submit(fetch_one,key):key for key in sorted(tasks)}
        for i,f in enumerate(as_completed(fs),1):
            key,status,path=f.result()
            fetched[key]=(status,path)
            if i%50==0:print("SOURCE_FILES",i,"/",len(tasks),flush=True)

    replay_cache={}
    page_cache={}
    rows=[]
    errors=Counter()
    previous_demo=None
    for i,r in enumerate(selected,1):
        demo=r["demo"]; idx1=int(r["from_turn"]); idx2=int(r["to_turn"])
        # Frozen pairs are ordered by demo. Release parsed DOM mappings at each
        # demo boundary so memory use does not accumulate across 55 websites.
        if previous_demo is not None and demo!=previous_demo:
            page_cache.clear()
            replay_cache.clear()
        previous_demo=demo
        if demo not in replay_cache:
            replay_cache[demo]=replay_data(get_source(
                f"demonstrations/{demo}/replay.json"))
        t1=replay_cache[demo][idx1];t2=replay_cache[demo][idx2]
        assert (t1.get("state") or {}).get("page")==r["page1"]
        assert (t2.get("state") or {}).get("page")==r["page2"]
        key1=(demo,r["page1"]);key2=(demo,r["page2"])
        stat1,path1=fetched[key1];stat2,path2=fetched[key2]
        row={
            "demo":demo,"from_turn":idx1,"to_turn":idx2,
            "raw_turn_gap":int(r["raw_turn_gap"]),
            "near_original_action_distance":int(r["near_original_action_distance"]),
            "from_source_status":stat1,"to_source_status":stat2,
            "from_html_sha256":"","to_html_sha256":"",
            "from_html_bytes":0,"to_html_bytes":0,
            "raw_html_byte_identical":None,
            "url_hint":compare_known(context_hint(t1)["url"],
                                     context_hint(t2)["url"]),
            "tab_hint":compare_known(context_hint(t1)["tab"],
                                     context_hint(t2)["tab"]),
            "document_hint":compare_known(context_hint(t1)["document"],
                                          context_hint(t2)["document"]),
        }
        if stat1!="fetched" or stat2!="fetched":
            row["result_status"]="source_unavailable"
            errors.update(["source_unavailable"])
        else:
            for key,path in ((key1,path1),(key2,path2)):
                if key not in page_cache:
                    # Cache only source pages within the current demonstration.
                    blob=path.read_bytes()
                    page_cache[key]=inspect_html_bytes(blob)
            a=page_cache[key1];b=page_cache[key2]
            row["from_html_sha256"]=a["sha256"]
            row["to_html_sha256"]=b["sha256"]
            row["from_html_bytes"]=a["bytes"]
            row["to_html_bytes"]=b["bytes"]
            row["raw_html_byte_identical"]=int(a["sha256"]==b["sha256"])
            if a["parse_status"]!="parsed" or b["parse_status"]!="parsed":
                row["result_status"]="html_parse_unavailable"
                row["from_parse_status"]=a["parse_status"]
                row["to_parse_status"]=b["parse_status"]
                errors.update(["html_parse_unavailable"])
            else:
                row.update(compare_pages(a,b))
                row["result_status"]=(
                    "identical_bytes" if row["raw_html_byte_identical"]
                    else "different_bytes_parsed")
        rows.append(row)
        if i%30==0:print("INSPECTED_SOURCE_PAIRS",i,"/",len(selected),flush=True)

    # Fill all unspecified numeric fields uniformly so the audit CSV has
    # one fixed schema, including missing-file pairs.
    counts=("first_total_elements","second_total_elements",
            "first_uid_attributed","second_uid_attributed",
            "first_unique_uids","second_unique_uids",
            "first_duplicate_uid_values","second_duplicate_uid_values",
            "same_uid_at_both","same_uid_same_xpath",
            "same_uid_changed_xpath","same_uid_same_feature_signature",
            "same_uid_same_xpath_and_features","same_xpath_both",
            "same_xpath_same_uid","same_xpath_different_uid",
            "same_xpath_same_tag","first_uids_absent_from_second",
            "second_uids_new")
    cols=list(rows[0])
    for name in counts:
        if name not in cols:cols.append(name)
    for name in ("from_parse_status","to_parse_status"):
        if name not in cols:cols.append(name)
    for row in rows:
        for name in cols:
            row.setdefault(name,None)
    parsed=[r for r in rows if r["result_status"] in
            ("identical_bytes","different_bytes_parsed")]
    changed=[r for r in rows if r["result_status"]=="different_bytes_parsed"]
    result={
        "protocol":"R2-source-HTML-adjacent-snapshot-UID-XPath-feasibility",
        "dataset_revision":SHA,
        "R1_source_pair_count":165,
        "unique_referenced_html_files":len(tasks),
        "source_file_statuses":dict(sorted(Counter(v[0] for v in fetched.values()).items())),
        "pair_statuses":dict(sorted(Counter(r["result_status"] for r in rows).items())),
        "url_hints":dict(sorted(Counter(r["url_hint"] for r in rows).items())),
        "tab_hints":dict(sorted(Counter(r["tab_hint"] for r in rows).items())),
        "parsed_pairs":len(parsed),
        "changed_html_bytes_pairs":len(changed),
        "changed_html_pairs_with_reused_uid":sum(
            r["same_uid_at_both"]>0 for r in changed),
        "changed_html_pairs_with_uid_relocated":sum(
            r["same_uid_changed_xpath"]>0 for r in changed),
        "changed_html_pairs_with_xpath_uid_collision":sum(
            r["same_xpath_different_uid"]>0 for r in changed),
        "changed_html_pairs_with_no_uid_overlap":sum(
            r["same_uid_at_both"]==0 for r in changed),
        "changed_html_pairs_uid_overlaps_total":sum(
            r["same_uid_at_both"] for r in changed),
        "changed_html_pairs_uid_relocated_total":sum(
            r["same_uid_changed_xpath"] for r in changed),
        "changed_html_pairs_xpath_reassigned_total":sum(
            r["same_xpath_different_uid"] for r in changed),
        "changed_html_pairs_xpath_same_uid_total":sum(
            r["same_xpath_same_uid"] for r in changed),
        "published_outputs_are_derived_only":True,
        "cross_state_ground_truth_status":"NOT_INDEPENDENTLY_ADJUDICATED",
    }
    assert len(rows)==165 and len({(r["demo"],r["from_turn"],r["to_turn"])
                                  for r in rows})==165
    with (OUT/"source_pair_diagnostics_165.csv").open("w",newline="",
            encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
    (OUT/"source_pair_summary.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R2_SUMMARY",json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
