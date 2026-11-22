#!/usr/bin/env python3
"""Check a confirmatory WebLINX run against the frozen published aggregates."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PIN = "36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8"
EXPECTED = {
    "top10": (425, 415),
    "top20": (470, 452),
    "top50": (521, 483),
    "all": (600, 530),
    "text": 158,
    "dom": 273,
    "textdom": 403,
    "visual": 158,
    "joint": 530,
    "blank": 390,
    "nonblank": 210,
    "visual_escalation": 197,
    "phash_joint": {"0": 537, "4": 530, "8": 521, "12": 512},
}


def check(summary: dict) -> list[str]:
    errors: list[str] = []

    def same(name: str, actual, expected) -> None:
        if actual != expected:
            errors.append(f"{name}: expected {expected!r}, got {actual!r}")

    def near(name: str, actual, expected: float, tolerance: float = 1e-8) -> None:
        if actual is None or not math.isclose(float(actual), expected, abs_tol=tolerance):
            errors.append(f"{name}: expected {expected:.9f}, got {actual!r}")

    same("raw_sha", summary.get("raw_sha"), PIN)
    sampling = summary.get("sampling", {})
    same("analyzed", sampling.get("analyzed"), 600)
    same("demo_n", sampling.get("demo_n"), 55)
    same("mapped", sampling.get("mapped"), 750)
    same("map_skips", sampling.get("map_skips"), {})
    same("compute_skips", sampling.get("compute_skips"), {})
    same("fetch_failures", sampling.get("fetch_failures"), {})
    population = summary.get("population", {})
    same("target_turns", population.get("target_turns"), 1422)
    same("population demos", population.get("demo_n"), 99)
    same("ambiguous groups", population.get("ambiguous_target_groups_excluded"), 16)

    for k in (10, 20, 50):
        coverage, recovered = EXPECTED[f"top{k}"]
        values = summary.get("topk_unconditional", {}).get(str(k), {})
        near(f"top{k} coverage", values.get("target_present_rate"), coverage / 600)
        near(f"top{k} end-to-end", values.get("joint_unique_over_all_actions"), recovered / 600)
        near(f"top{k} conditional", values.get("joint_unique_conditional_present"), recovered / coverage)

    full = summary.get("all_universe", {})
    for field in ("text", "dom", "textdom", "visual", "joint"):
        near(f"all_universe {field}", full.get(field, {}).get("unique_rate"), EXPECTED[field] / 600)
        same(f"all_universe {field} n", full.get(field, {}).get("n"), 600)
    near("visual escalation", full.get("visual_escalation_rate"), 197 / 600)
    same("blank", summary.get("strata", {}).get("blank", {}).get("n"), 390)
    same("nonblank", summary.get("strata", {}).get("nonblank", {}).get("n"), 210)
    for threshold, count in EXPECTED["phash_joint"].items():
        value = summary.get("phash_sensitivity", {}).get(threshold, {}).get("overall", {}).get("joint", {}).get("unique_rate")
        near(f"pHash {threshold} joint", value, count / 600)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="out_confirm/confirm_summary.json")
    args = parser.parse_args()
    actual = json.loads(args.path.read_text(encoding="utf-8"))
    errors = check(actual)
    if errors:
        for message in errors:
            print("FAIL", message)
        return 1
    print("PASS: confirmatory summary matches frozen 600-action results and source revision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
