"""Demo-cluster uncertainty for post-observation 75 site-native proxy cases.

Fixed seed and exact per-demo resampling. Conditional on the selected
same-ordinary-HTML-id cohort, not a full population error estimate.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

INPUT=Path("results/weblinx_continuity_r3d_cases.csv")
OUTPUT=Path("results/weblinx_continuity_r3d_cluster_bootstrap.json")
SEED=2026112239
REPS=5000


def calculate(rows):
    demos=defaultdict(list)
    for row in rows:
        if row["in_site_native_75"]=="1":
            demos[row["demo"]].append(row)
    if sum(map(len,demos.values()))!=75 or len(demos)!=31:
        raise AssertionError("Selected proxy cohort changed")
    keys=sorted(demos)
    rng=random.Random(SEED)
    def rates(chunks):
        flat=[r for chunk in chunks for r in chunk]
        a=sum(r["replay_xpath_selects_proxy"]=="unique_proxy_node" for r in flat)
        b=sum(r["canonical_xpath_selects_proxy"]=="unique_proxy_node" for r in flat)
        n=len(flat)
        return a/n,b/n,(a-b)/n
    observed=rates(list(demos.values()))
    samples=[rates([demos[rng.choice(keys)] for _ in keys]) for __ in range(REPS)]
    ci=[]
    for i in range(3):
        arr=sorted(row[i] for row in samples)
        ci.append([arr[math.floor((REPS-1)*.025)],
                   arr[math.ceil((REPS-1)*.975)]])
    return {
        "method":"resample original demonstrations, retaining all their selected actions",
        "scope":"post-observation 75 source-native id proxies, NOT independent logical-element ground truth",
        "seed":SEED,"replicates":REPS,
        "selected_actions":75,"demonstrations":len(demos),
        "metrics":{
            "replay_xpath_proxy_recovery":{"estimate":observed[0],"ci95":ci[0]},
            "canonical_xpath_proxy_recovery":{"estimate":observed[1],"ci95":ci[1]},
            "paired_replay_minus_canonical":{"estimate":observed[2],"ci95":ci[2]},
        },
    }


def main():
    with INPUT.open(newline="",encoding="utf-8") as f:
        data=list(csv.DictReader(f))
    out=calculate(data)
    OUTPUT.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R3D_CLUSTER",json.dumps(out,sort_keys=True))


if __name__=="__main__":
    main()
