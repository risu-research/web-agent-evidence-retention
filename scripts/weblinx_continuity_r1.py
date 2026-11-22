"""R1: read pinned WebLINX replays and freeze an adjacent-HTML source pair set.

The original 55 demonstration identifiers are taken from the published
600-action measurements. This script reads official replay.json files only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

DATASET="McGill-NLP/WebLINX-full"
SHA="36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8"
ORIGINAL=Path("results/storage_cost_600_actions_2026-11-22.csv")
OUT=Path("out_continuity_r1")
RAW=Path("wl_continuity_r1")
MAX_PAIRS_PER_DEMO=3
SAFE_DEMO=re.compile(r"^[a-z0-9]{7}$")
SAFE_FILE=re.compile(r"^[A-Za-z0-9_.-]+\.html$",re.I)


def get_source(path):
    target=RAW/path
    if target.exists() and target.stat().st_size>0:
        return target
    target.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://huggingface.co/datasets/{DATASET}/resolve/{SHA}/{quote(path,safe='/')}?download=true"
    err=None
    for n in range(7):
        try:
            with requests.get(url,stream=True,timeout=(25,180)) as response:
                if response.status_code==429:
                    time.sleep(min(40,2*(n+1)**2))
                    continue
                response.raise_for_status()
                temp=target.with_suffix(target.suffix+".part")
                with temp.open("wb") as f:
                    for chunk in response.iter_content(1024*1024):
                        if chunk:f.write(chunk)
                temp.replace(target)
                return target
        except Exception as exc:
            err=exc
            time.sleep(min(25,2**n))
    raise RuntimeError(f"Unable to fetch official source {path}, {type(err).__name__}")


def load_original():
    with ORIGINAL.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==600
    by_demo=defaultdict(set)
    for r in rows:
        d=r["demo"]
        assert SAFE_DEMO.fullmatch(d)
        by_demo[d].add(int(r["turn"]))
    assert len(by_demo)==55
    return dict(sorted(by_demo.items()))


def state_name(turn,field):
    state=turn.get("state") or {}
    value=state.get(field)
    return value if isinstance(value,str) and value.strip() else None


def replay_data(source):
    obj=json.loads(source.read_text(encoding="utf-8"))
    data=obj.get("data") if isinstance(obj,dict) else obj
    if not isinstance(data,list):raise ValueError("Unexpected replay JSON schema")
    if any(not isinstance(row,dict) for row in data):
        raise ValueError("Replay contains non-object turn")
    return data


def pair_inventory(demo,turns,target_indexes):
    browser=[(i,t) for i,t in enumerate(turns) if t.get("type")=="browser"]
    direct_pages=sum(state_name(t,"page") is not None for _,t in browser)
    direct_screens=sum(state_name(t,"screenshot") is not None for _,t in browser)
    adjacent_count=0
    same_name=0
    distinct=[]
    invalid_page_names=0
    for (idx1,t1),(idx2,t2) in zip(browser,browser[1:]):
        p1=state_name(t1,"page")
        p2=state_name(t2,"page")
        if p1 is None or p2 is None:continue
        adjacent_count+=1
        if p1==p2:
            same_name+=1
            continue
        # Source location is explicitly the replay-provided page filename.
        if not SAFE_FILE.fullmatch(p1) or not SAFE_FILE.fullmatch(p2):
            invalid_page_names+=1
            continue
        dist=min(abs(idx1-k) for k in target_indexes)
        dist=min(dist,min(abs(idx2-k) for k in target_indexes))
        distinct.append({
            "demo":demo,
            "from_turn":idx1,"to_turn":idx2,
            "raw_turn_gap":idx2-idx1,
            "near_original_action_distance":dist,
            "page1":p1,"page2":p2,
            "intervening_chat_turns":idx2-idx1-1,
        })
    chosen=sorted(distinct,key=lambda r:(r["near_original_action_distance"],
                                      r["from_turn"],r["to_turn"]))[:MAX_PAIRS_PER_DEMO]
    metrics={
        "demo":demo,
        "total_turns":len(turns),
        "browser_turns":len(browser),
        "chat_or_other_turns":len(turns)-len(browser),
        "direct_html_turns":direct_pages,
        "direct_screenshot_turns":direct_screens,
        "adjacent_browser_pairs_with_html":adjacent_count,
        "adjacent_same_html_filename":same_name,
        "adjacent_distinct_html_filename":len(distinct),
        "adjacent_distinct_invalid_filenames":invalid_page_names,
        "selected_distinct_pairs":len(chosen),
        "original_action_keys":len(target_indexes),
    }
    return metrics,chosen


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    target_keys=load_original()
    summary_rows=[];selected=[];original_hashes={}
    for index,(demo,targets) in enumerate(target_keys.items(),1):
        path=get_source(f"demonstrations/{demo}/replay.json")
        original_hashes[demo]=hashlib.sha256(path.read_bytes()).hexdigest()
        turns=replay_data(path)
        if not all(0<=k<len(turns) for k in targets):
            raise AssertionError(f"Original sample outside replay for demo {demo}")
        metrics,chosen=pair_inventory(demo,turns,targets)
        metrics["replay_sha256"]=original_hashes[demo]
        summary_rows.append(metrics)
        selected.extend(chosen)
        if index%10==0:print("REPLAY_INVENTORY",index,flush=True)
    assert len(summary_rows)==55
    assert len({(r["demo"],r["from_turn"],r["to_turn"]) for r in selected})==len(selected)
    assert all(0<=r["intervening_chat_turns"] for r in selected)
    assert all(r["selected_distinct_pairs"]<=3 for r in summary_rows)
    count_fields=[k for k in summary_rows[0] if k not in {"demo","replay_sha256"}]
    totals={k:sum(r[k] for r in summary_rows) for k in count_fields}
    data={
        "protocol":"R1-pinned-55-demonstration-direct-HTML-sequence-inventory",
        "raw_revision":SHA,"demos":len(summary_rows),
        "original_action_keys":sum(len(x) for x in target_keys.values()),
        "max_selected_pairs_per_demo":MAX_PAIRS_PER_DEMO,
        "selection":"nearest of two endpoints to any original cohort action; then earlier replay turn",
        "no_imputed_html_paths":True,
        "totals":totals,
        "demos_with_any_html":sum(r["direct_html_turns"]>0 for r in summary_rows),
        "demos_with_selected_pair":sum(r["selected_distinct_pairs"]>0 for r in summary_rows),
        "replay_digest_set_sha256":hashlib.sha256(
            json.dumps(original_hashes,sort_keys=True).encode()).hexdigest(),
    }
    with (OUT/"replay_inventory_55.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(summary_rows[0]))
        writer.writeheader();writer.writerows(summary_rows)
    with (OUT/"source_pairs_frozen.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(selected[0]) if selected
              else ["demo","from_turn","to_turn","raw_turn_gap",
                    "near_original_action_distance","page1","page2",
                    "intervening_chat_turns"])
        writer.writeheader();writer.writerows(selected)
    (OUT/"source_inventory_summary.json").write_text(
        json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R1_SUMMARY",json.dumps(data,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
