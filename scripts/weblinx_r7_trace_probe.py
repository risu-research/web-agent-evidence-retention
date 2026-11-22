"""R7 safe one-case trace snapshot FORMAT probe. No raw trace data exported."""
from __future__ import annotations
import collections
import json
import tempfile
import zipfile
from pathlib import Path

import weblinx_r6_django_trace as r6


def shape(node,depth=0):
    if depth>=3:return {"depth_limit":True,"node_type":type(node).__name__}
    if isinstance(node,dict):
        return {"kind":"object","keys":list(node)[:18],
                "children":{k:shape(v,depth+1) for k,v in list(node.items())[:3]}}
    if isinstance(node,list):
        return {"kind":"array","length":len(node),
                "first":shape(node[0],depth+1) if node else None,
                "second":shape(node[1],depth+1) if len(node)>1 else None}
    if isinstance(node,str):return {"kind":"string","length":len(node)}
    return {"kind":type(node).__name__}


def sanitized_probe(p,ids):
    with zipfile.ZipFile(p) as z:
        trace=[]
        names=z.namelist()
        for name in names:
            if name.endswith(".trace"):
                trace.extend(json.loads(s) for s in z.read(name).splitlines())
        types=collections.Counter(e.get("type") for e in trace)
        snap=[e for e in trace if e.get("type")=="frame-snapshot"]
        clicks=[e for e in trace if e.get("type")=="before"
                and e.get("method")=="click"]
        all_snames=collections.Counter(
            s.get("snapshot",{}).get("snapshotName") if "snapshot" in s else s.get("snapshotName")
            for s in snap)
        example=[{
            "outer_keys":list(e),
            "snapshot_keys":list(e.get("snapshot",{})),
            "snapshotName":e.get("snapshot",{}).get("snapshotName"),
            "main":e.get("snapshot",{}).get("isMainFrame"),
            "dom_shape":shape(e.get("snapshot",{}).get("html"))
        } for e in snap[:3]]
        firstclick=[{
            "keys":list(e),"params_keys":list(e.get("params",{})),
            "call_id_present":"callId" in e,
            "input_snapshot":e.get("inputSnapshot"),
            "point_keys":list(e.get("point",{})) if isinstance(e.get("point"),dict) else type(e.get("point")).__name__
        } for e in clicks[:2]]
        print("R7_PROBE",json.dumps({
           "types":types,"members_count":len(names),
           "frame_snapshots":len(snap),
           "snapshot_name_examples":list(all_snames.items())[:12],
           "snapshot_examples":example,
           "click_examples":firstclick,
           "html_derived_literal_presence":{
               "r6_a":sum('"r6_a"' in json.dumps(s.get("snapshot",{}).get("html")) for s in snap),
               "r6_b":sum('"r6_b"' in json.dumps(s.get("snapshot",{}).get("html")) for s in snap),
               "Seed-A":sum('"Seed-A"' in json.dumps(s.get("snapshot",{}).get("html")) for s in snap),
           },
        },sort_keys=True),flush=True)
    return r6.trace_parse_original(p,ids)


def main():
    with tempfile.TemporaryDirectory() as folder:
        db=Path(folder)/"base.sqlite3"
        r6.init_django(db)
        r6.trace_parse_original=r6.trace_parse
        r6.trace_parse=sanitized_probe
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                row=r6.episode(browser,db,"edit","positional","baseline",1)
                assert row["sqlite_effect_record"]=="A"
                assert row["trace_zip_bytes"]>0
                print("R7_SMOKE_COMPLETE",row["case"],row["sqlite_effect_record"],flush=True)
            finally:browser.close()


if __name__=="__main__":main()
