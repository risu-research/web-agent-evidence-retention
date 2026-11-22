"""Demonstration-cluster uncertainty for measured storage and recovery ratios."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


def read_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=600:
        raise AssertionError("Expected the original 600 actions")
    return rows


def aggregate(rows):
    vals=defaultdict(int)
    vals["n"]=len(rows)
    for row in rows:
        for name,field in (
            ("selective_bytes","selective_hashes_zlib_bytes"),
            ("allhash_bytes","all_hashes_zlib_bytes"),
            ("staged_bytes","staged_zlib_bytes"),
            ("png_bytes","semantic_plus_crops_bytes"),
            ("fullframe_bytes","full_frame_total_bytes"),
            ("selective_success","selective_hashes_unique"),
            ("staged_success","staged_unique"),
            ("png_success","semantic_plus_crops_unique"),
        ):
            vals[name]+=int(row[field])
    return dict(vals)


def evaluate(groups):
    result=defaultdict(int)
    for g in groups:
        for k,v in g.items():
            result[k]+=v
    n=result["n"]
    return {
        "gain_staged_vs_selective":(result["staged_success"]-
                                    result["selective_success"])/n,
        "selective_hash_saving_vs_all_hash":1-result["selective_bytes"]/result["allhash_bytes"],
        "cost_ratio_staged_to_selective":result["staged_bytes"]/result["selective_bytes"],
        "cost_ratio_png_to_fullframe":result["png_bytes"]/result["fullframe_bytes"],
        "selective_mean_bytes_per_action":result["selective_bytes"]/n,
        "staged_mean_bytes_per_action":result["staged_bytes"]/n,
        "png_mean_bytes_per_action":result["png_bytes"]/n,
        "fullframe_mean_bytes_per_action":result["fullframe_bytes"]/n,
        "png_recovery_rate":result["png_success"]/n,
    }


def bootstrap(rows,reps=5000,seed=2026112237):
    grouped=defaultdict(list)
    for r in rows:
        grouped[r["demo"]].append(r)
    demos=sorted(grouped)
    if len(demos)!=55:
        raise AssertionError("Expected 55 demonstrations")
    units={d:aggregate(g) for d,g in grouped.items()}
    point=evaluate(list(units.values()))
    rng=random.Random(seed)
    draws=defaultdict(list)
    for _ in range(reps):
        sample=[units[rng.choice(demos)] for _ in demos]
        for k,v in evaluate(sample).items():
            draws[k].append(v)
    metrics={}
    for k,v in point.items():
        ordered=sorted(draws[k])
        metrics[k]={
            "estimate":v,
            "ci95":[ordered[math.floor(.025*(reps-1))],
                    ordered[math.ceil(.975*(reps-1))]],
        }
    return {
        "source_file":"results/storage_cost_600_actions_2026-11-22.csv",
        "n":len(rows),"demonstrations":55,
        "bootstrap_unit":"demonstration",
        "replicates":reps,"seed":seed,"metrics":metrics,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path(
        "results/storage_cost_600_actions_2026-11-22.csv"))
    parser.add_argument("--out",type=Path,default=Path(
        "results/storage_cost_cluster_bootstrap_2026-11-22.json"))
    opts=parser.parse_args()
    result=bootstrap(read_rows(opts.input))
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",
                        encoding="utf-8")
    print("PASS: 5,000 clustered replicates",json.dumps(result["metrics"],sort_keys=True))


if __name__=="__main__":
    main()
