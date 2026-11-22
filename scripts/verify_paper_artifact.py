#!/usr/bin/env python3
"""Offline cross-check of frozen TRUSTMORE paper claims and public numeric files.

This validates the archived numerical evidence. It is not a substitute for
rerunning original WebLINX downloads and all processing.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
PIN = "36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8"


def load(path):
    return json.loads((R / path).read_text(encoding="utf-8"))


def verify():
    confirm = load("rerun-2026-11-22/confirm_summary.json")
    identifier = load("identifier_baseline_2026-11-22.json")
    residual = load("residual_70_summary_2026-11-22.json")
    pixel = load("residual_70_pixel_summary_2026-11-22.json")
    storage = load("storage_cost_summary_2026-11-22.json")
    bootstrap = load("storage_cost_cluster_bootstrap_2026-11-22.json")
    replay = load("weblinx_continuity_r3c_summary.json")

    def equal(what, actual, expected):
        if actual != expected:
            raise AssertionError(f"{what}: observed {actual!r}; expected {expected!r}")

    for label, source in (("confirm", confirm["raw_sha"]),
                          ("identifier", identifier["raw_sha"]),
                          ("residual", residual["dataset_sha"]),
                          ("pixel", pixel["dataset_sha"]),
                          ("storage", storage["dataset_revision"]),
                          ("Replay XPath", replay["dataset_revision"])):
        equal(label + " dataset revision", source, PIN)

    equal("sample actions", confirm["sampling"]["analyzed"], 600)
    equal("sample demonstrations", confirm["sampling"]["demo_n"], 55)
    equal("all joint recovery", round(confirm["all_universe"]["joint"]["unique_rate"] * 600), 530)
    equal("text recovery", round(confirm["all_universe"]["text"]["unique_rate"] * 600), 158)
    equal("text + DOM recovery", round(confirm["all_universe"]["textdom"]["unique_rate"] * 600), 403)
    for k, target_present, joint_unique in ((10, 425, 415), (20, 470, 452), (50, 521, 483)):
        b = confirm["topk_unconditional"][str(k)]
        equal(f"top {k} present", round(b["target_present_rate"] * 600), target_present)
        equal(f"top {k} end-to-end", round(b["joint_unique_over_all_actions"] * 600), joint_unique)

    full_id = identifier["by_candidate_budget"]["all"]["baselines"]
    equal("DMR XPath recovery", full_id["xpath"]["recovered"], 600)
    equal("HTML id recovery", full_id["html_id"]["recovered"], 121)
    equal("target HTML id presence", identifier["cohort"]["target_html_id_available"], 122)
    equal("Replay action XPath matches", replay["current_expression_results"], {
        "unique_recorded_target": 589, "no_node": 10, "unique_other_node": 1,
    })

    equal("residual classes", residual["mechanisms"], {
        "missing_visual_only": 19,
        "mixed_missing_and_valid": 10,
        "valid_visual_matches": 41,
    })
    equal("residual competitors", residual["counts"]["competing_candidates_total"], 308)
    equal("pixel-identical competitors", pixel["competitor_counts"]["exact_rgb_equal_competitors"], 92)
    equal("equal hash, different RGB", pixel["competitor_counts"]["same_phash_different_rgb_competitors"], 69)

    all600 = storage["cohorts"]["all_600"]
    expected = {
        "text": (267898, 158),
        "semantic": (701966, 403),
        "all_hashes": (1670040, 530),
        "selective_hashes": (792980, 530),
        "staged": (862427, 600),
        "xpath": (621808, 600),
        "uid": (1794620, 600),
        "full_frame": (206275510, 530),
        "semantic_plus_crops": (309543191, 545),
    }
    equal("final-stage counts", storage["totals"]["adaptive_stages"], {
        "text": 158, "semantic": 245, "phash": 127, "bbox": 53, "xpath": 17,
    })
    equal("600 recorded actions", all600["actions"], 600)
    for policy, (bytes_expected, success_expected) in expected.items():
        stats = all600["policies"][policy]
        equal(policy + " archived bytes", stats["bytes_total"], bytes_expected)
        equal(policy + " archived recoveries", stats["unique_recovery_n"], success_expected)
    equal("lossless PNG pHash recovery", storage["totals"]["png_phash_recovery_n"], 530)
    equal("lossless PNG exact RGB recovery", storage["totals"]["png_pixel_exact_recovery_n"], 545)
    equal("source screenshots", storage["totals"]["per_action_screenshot_bytes"], 204723458)
    equal("distinct screenshot count", storage["totals"]["unique_screenshot_references"], 546)

    with (R / "storage_cost_600_actions_2026-11-22.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        reader = csv.DictReader(stream)
        cols = set(reader.fieldnames or ())
        rows = list(reader)
    equal("numeric action records", len(rows), 600)
    equal("distinct action keys", len({(r["demo"], r["turn"]) for r in rows}), 600)
    forbidden = {"uid", "xpath", "html_id", "text", "sem", "screenshot",
                 "screenshot_path", "url", "dialogue", "cookie", "password",
                 "raw_rgb", "raw_html", "label"}
    if cols & forbidden:
        raise AssertionError("Raw/source field in public storage casebook: " +
                             repr(sorted(cols & forbidden)))
    for policy, (bytes_expected, success_expected) in expected.items():
        byte_field = ("full_frame_total_bytes" if policy == "full_frame"
                      else "semantic_plus_crops_bytes" if policy == "semantic_plus_crops"
                      else policy + "_zlib_bytes")
        equal(policy + " action-level bytes",
              sum(int(r[byte_field]) for r in rows), bytes_expected)
        equal(policy + " action-level recoveries",
              sum(int(r[policy + "_unique"]) for r in rows), success_expected)
    equal("PNG reconstructed-pHash per-case agreement",
          sum(int(r["semantic_plus_crops_phash_unique"]) != int(r["all_hashes_unique"])
              for r in rows), 0)

    equal("bootstrap demonstrations", bootstrap["demonstrations"], 55)
    equal("bootstrap replicates", bootstrap["replicates"], 5000)
    ratio = 1 - expected["selective_hashes"][0] / expected["all_hashes"][0]
    point = bootstrap["metrics"]["selective_hash_saving_vs_all_hash"]["estimate"]
    if not math.isclose(point, ratio, abs_tol=1e-12):
        raise AssertionError("Bootstrap byte-saving point estimate mismatch")
    point = bootstrap["metrics"]["gain_staged_vs_selective"]["estimate"]
    if not math.isclose(point, 70/600, abs_tol=1e-12):
        raise AssertionError("Bootstrap recovered-target gain mismatch")
    equal("pixel case count", pixel["case_n"], 70)
    for path in ("docs/PAPER_REPRODUCTION.md", "docs/DATASET_TERMS.md",
                 "docs/storage-cost-results.md", "LICENSE"):
        if not (ROOT / path).is_file():
            raise AssertionError(f"Missing release documentation: {path}")

    return "PASS: frozen 600/55 cohort, tables I-VII, Replay XPath, cost rows, PNG parity, uncertainty and source-rights documentation"


if __name__ == "__main__":
    try:
        print(verify())
    except (AssertionError, KeyError, ValueError, OSError, TypeError) as exc:
        print(f"FAIL: paper artifact audit: {exc}", file=sys.stderr)
        raise SystemExit(1)
