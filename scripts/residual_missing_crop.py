"""Trace unavailable visual crops among the 29 affected residual actions.

Uses the frozen 70-row casebook to select cases and fetches source WebLINX
candidate descriptions, replay metadata and screenshot dimensions.
Exports only derived counts by public demonstration/turn key.
"""
import csv
import json
import math
import re
import time
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image
from huggingface_hub import hf_hub_download
import weblinx as wl

SHA="36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8"
DATASET="McGill-NLP/WebLINX-full"
RAW=Path("wl_missing_crop")
OUT=Path("out_missing_crop")
OUT.mkdir(exist_ok=True)

WS=re.compile(r"\s+")
FIELD=re.compile(r"\[\[([a-zA-Z_]+)\]\]\s*(.*?)(?=(?:\[\[[a-zA-Z_]+\]\])|\Z)",re.S)
KV=re.compile(r"""([:\w-]+)\s*=\s*(['"])(.*?)\2""",re.S)
NUM=re.compile(r"""(x|y|width|height)\s*=\s*(-?\d+(?:\.\d+)?)""")


def norm(x,lim=240):
    return WS.sub(" ",str(x or "")).strip().lower()[:lim]


def parse_doc(doc):
    f={}
    for m in FIELD.finditer(str(doc or "")):
        f[m.group(1).lower()]=norm(m.group(2),2000)
    attrs={k.lower():norm(v,160) for k,_,v in KV.findall(f.get("attributes",""))}
    sem=tuple((k,attrs.get(k,"")) for k in (
        "role","type","name","aria-label","title","placeholder","alt","href","value")
        if attrs.get(k))
    return {"tag":norm(f.get("tag",""),40),
            "text":norm(f.get("text",""),240),"sem":sem}


def raw_get(source_path,optional=False):
    dest=RAW/source_path
    if dest.exists() and dest.stat().st_size>0:
        return dest
    dest.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://huggingface.co/datasets/{DATASET}/resolve/{SHA}/{quote(source_path,safe='/')}?download=true"
    last=None
    for i in range(8):
        try:
            response=requests.get(url,stream=True,timeout=(25,180))
            if optional and response.status_code==404:
                return None
            if response.status_code==429:
                time.sleep(min(45,2*(i+1)**2))
                continue
            response.raise_for_status()
            tmp=dest.with_suffix(dest.suffix+".part")
            with tmp.open("wb") as h:
                for chunk in response.iter_content(1024*1024):
                    if chunk:
                        h.write(chunk)
            tmp.replace(dest)
            return dest
        except Exception as exc:
            last=exc
            time.sleep(min(30,2**i))
    if optional:
        return None
    raise RuntimeError(f"Failed to retrieve source asset: {type(last).__name__}")


def classify_bbox(doc,width,height):
    parts={m.group(1).lower():m.group(2) for m in FIELD.finditer(str(doc or ""))}
    bbox=parts.get("bbox","")
    if not bbox.strip():
        return "bbox_absent"
    coords={k:float(v) for k,v in NUM.findall(bbox)}
    if not all(k in coords for k in ("x","y","width","height")):
        return "bbox_incomplete"
    x,y,w,h=(coords[k] for k in ("x","y","width","height"))
    if w<=2 or h<=2:
        return "bbox_too_small"
    left=max(0,int(math.floor(x)))
    top=max(0,int(math.floor(y)))
    right=min(width,int(math.ceil(x+w)))
    bottom=min(height,int(math.ceil(y+h)))
    if right-left<3 or bottom-top<3:
        return "bbox_clipped_below_three"
    return "valid"


def main():
    path=Path("results/residual_70_cases_2026-11-22.csv")
    with path.open(newline="",encoding="utf-8") as h:
        cases=list(csv.DictReader(h))
    affected=[r for r in cases if int(r["missing_visual_competitor_n"])>0]
    assert len(cases)==70 and len(affected)==29
    selected={(r["demo"],int(r["turn"])):r for r in affected}
    records=defaultdict(list)
    candidates=hf_hub_download(DATASET,"candidates/test_iid.jsonl",
                               repo_type="dataset",revision=SHA)
    with open(candidates,encoding="utf-8") as handle:
        for line in handle:
            v=json.loads(line)
            key=(str(v["demo_name"]),int(v["turn_index"]))
            if key in selected:
                records[key].append(v)
    assert set(records)==set(selected)

    demos=sorted({d for d,_ in selected})
    for d in demos:
        raw_get(f"demonstrations/{d}/replay.json")
        raw_get(f"demonstrations/{d}/metadata.json",optional=True)
        raw_get(f"demonstrations/{d}/form.json",optional=True)

    replays={}
    for d in demos:
        replays[d]=wl.Replay.from_demonstration(
            wl.Demonstration(d,base_dir=RAW/"demonstrations"))
    counts=Counter()
    rows=[]
    for (d,turn),record in sorted(selected.items()):
        replay=replays[d]
        event=replay[turn]
        if not event.has_screenshot():
            replay.assign_screenshot_to_turn(event)
        name=(event.get("state") or {}).get("screenshot")
        assert name, "Replay screenshot missing"
        image_path=raw_get(f"demonstrations/{d}/screenshots/{name}")
        with Image.open(image_path) as im:
            width,height=im.size
        positives=[x for x in records[(d,turn)] if int(x.get("label",0))==1]
        assert len(positives)==1
        target=parse_doc(positives[0]["doc"])
        cc=Counter()
        for c in records[(d,turn)]:
            if int(c.get("label",0))==1:
                continue
            v=parse_doc(c["doc"])
            if (v["text"],v["tag"],v["sem"]) != (target["text"],target["tag"],target["sem"]):
                continue
            reason=classify_bbox(c["doc"],width,height)
            if reason!="valid":
                cc[reason]+=1
        missing=sum(cc.values())
        assert missing==int(record["missing_visual_competitor_n"]),(
            d,turn,missing,record["missing_visual_competitor_n"])
        counts.update(cc)
        rows.append({
            "demo":d,"turn":turn,
            "missing_visual_competitor_n":missing,
            "bbox_absent":cc["bbox_absent"],
            "bbox_incomplete":cc["bbox_incomplete"],
            "bbox_too_small":cc["bbox_too_small"],
            "bbox_clipped_below_three":cc["bbox_clipped_below_three"],
        })
    assert len(rows)==29 and sum(counts.values())==84
    summary={
        "protocol":"WebLINX-source-geometry-of-84-unavailable-matching-crops",
        "dataset_sha":SHA,
        "affected_actions":len(rows),
        "missing_crop_competitors":sum(counts.values()),
        "mechanisms":dict(sorted(counts.items())),
        "screenshot_required":True,
        "source":"released WebLINX test_iid candidate descriptions and replay-linked screenshots",
    }
    with (OUT/"missing_crop_cases.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (OUT/"missing_crop_summary.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("MISSING_CROP_SUMMARY",json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    main()
