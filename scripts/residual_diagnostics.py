"""Evidence-level diagnostics for WebLINX targets with non-unique joint evidence.

All exported fields contain counts, categories, or source dataset row keys.
The caller must keep literal candidate text and locator attributes in memory only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import random
import statistics

HASH_THRESHOLD = 4
KNOWN_TAGS = {
    "button", "input", "a", "span", "div", "svg", "path", "label",
    "select", "textarea", "li", "img", "option", "p", "form", "ul",
    "td", "tr", "th", "table", "i", "b", "strong", "aside", "nav",
}
KNOWN_ROLES = {
    "button", "textbox", "link", "checkbox", "radio", "option",
    "combobox", "menuitem", "tab", "listbox", "switch", "searchbox",
    "slider", "spinbutton", "dialog", "navigation",
}


def safe_tag(tag):
    tag = (tag or "").lower()
    return tag if tag in KNOWN_TAGS else "other"


def safe_role(sem):
    values = dict(sem or ())
    role = values.get("role", "").lower()
    return role if role in KNOWN_ROLES else ("other" if role else "absent")


def bbox_iou(a, b):
    if a is None or b is None:
        return 0.0
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return 0.0
    iw = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def same_semantic(candidate, target):
    return (
        candidate["text"] == target["text"]
        and (candidate["tag"], candidate["sem"]) == (target["tag"], target["sem"])
    )


def joint_compatible(candidate, target, threshold=HASH_THRESHOLD):
    if not same_semantic(candidate, target):
        return False
    if candidate["phash"] is None:
        return True
    return int(candidate["phash"] - target["phash"]) <= threshold


def analyze_residual(candidates, target, *, demo, turn, target_rank):
    """Return a privacy-filtered record for one residual action, else None."""
    positives = [c for c in candidates if c["label"] == 1]
    if len(positives) != 1 or positives[0] is not target:
        raise AssertionError("Exactly one supplied target is required")
    if target["phash"] is None:
        raise AssertionError("The frozen sample requires a valid target crop")

    text_matches = [c for c in candidates if c["text"] == target["text"]]
    semantic_matches = [c for c in candidates if same_semantic(c, target)]
    compatible = [c for c in semantic_matches if joint_compatible(c, target)]
    if len(compatible) <= 1:
        return None

    other = [c for c in compatible if c["label"] == 0]
    if len(other) != len(compatible) - 1:
        raise AssertionError("Target or competitor labels inconsistent")
    missing = [c for c in other if c["phash"] is None]
    valid = [c for c in other if c["phash"] is not None]

    if missing and valid:
        mechanism = "mixed_missing_and_valid"
    elif missing:
        mechanism = "missing_visual_only"
    else:
        mechanism = "valid_visual_matches"

    distances = [int(c["phash"] - target["phash"]) for c in valid]
    same_bbox = sum(c["bbox"] == target["bbox"] for c in other)
    exact_hash = sum(d == 0 for d in distances)
    near_hash = sum(1 <= d <= HASH_THRESHOLD for d in distances)
    equal_hash_different_bbox = sum(
        c["bbox"] != target["bbox"] and
        int(c["phash"] - target["phash"]) == 0
        for c in valid
    )
    valid_distinct = sum(c["bbox"] != target["bbox"] for c in valid)
    ious = [bbox_iou(c["bbox"], target["bbox"]) for c in other]
    strict_count = 1 + len(missing) + exact_hash
    bbox_equal_all = sum(c["bbox"] == target["bbox"] for c in candidates)
    attrs = dict(target.get("sem") or ())
    result = {
        "demo":str(demo),
        "turn":int(turn),
        "target_rank":int(target_rank),
        "target_tag":safe_tag(target["tag"]),
        "target_role":safe_role(target.get("sem")),
        "blank_text":int(not target["text"]),
        "has_aria_label":int(bool(attrs.get("aria-label"))),
        "has_placeholder":int(bool(attrs.get("placeholder"))),
        "has_name_attr":int(bool(attrs.get("name"))),
        "candidate_n":len(candidates),
        "text_match_n":len(text_matches),
        "semantic_match_n":len(semantic_matches),
        "joint_match_n":len(compatible),
        "competitor_n":len(other),
        "mechanism":mechanism,
        "missing_visual_competitor_n":len(missing),
        "valid_visual_competitor_n":len(valid),
        "missing_visual_anywhere_n":sum(c["phash"] is None for c in candidates),
        "equal_phash_competitor_n":exact_hash,
        "near_phash_competitor_n":near_hash,
        "equal_phash_different_bbox_n":equal_hash_different_bbox,
        "valid_phash_different_bbox_n":valid_distinct,
        "same_bbox_competitor_n":same_bbox,
        "iou_at_least_50_competitor_n":sum(v >= 0.5 for v in ious),
        "iou_at_least_95_competitor_n":sum(v >= 0.95 for v in ious),
        "disjoint_bbox_competitor_n":sum(v == 0.0 for v in ious),
        "max_competitor_bbox_iou":round(max(ious,default=0),6),
        "min_valid_competitor_phash_distance":min(distances,default=None),
        "max_valid_competitor_phash_distance":max(distances,default=None),
        "strict_phash_0_joint_match_n":strict_count,
        "strict_phash_0_resolves":int(strict_count == 1),
        "exact_bbox_match_n_over_all_candidates":bbox_equal_all,
        "exact_bbox_is_unique":int(bbox_equal_all == 1),
        "target_html_id_available":int(bool(target.get("html_id"))),
        "target_xpath_available":int(bool(target.get("xpath"))),
    }
    assert result["joint_match_n"] == 1 + result["competitor_n"]
    assert result["competitor_n"] == len(missing) + len(valid)
    assert exact_hash + near_hash == len(valid)
    assert result["text_match_n"] >= result["semantic_match_n"] >= result["joint_match_n"]
    return result


def rank_band(rank):
    if rank <= 10:
        return "01-10"
    if rank <= 20:
        return "11-20"
    if rank <= 50:
        return "21-50"
    if rank <= 100:
        return "51-100"
    return "101+"


def counts(rows, field):
    return dict(sorted(Counter(r[field] for r in rows).items(), key=lambda kv: str(kv[0])))


def summary_of_cases(cases, actions, reps=5000):
    """Summaries with cohort-level blank/nonblank rates and paired clustered CI."""
    if len(actions) != 600 or len(cases) != 70:
        raise AssertionError("Unexpected frozen cohort or residual count")
    keys = {(r["demo"],r["turn"]) for r in cases}
    if len(keys) != 70:
        raise AssertionError("Duplicate case keys")
    original_residual = {(r["demo"],r["turn"]) for r in actions if r["joint_n"] > 1}
    if keys != original_residual:
        raise AssertionError("Residual membership differs from frozen 600-action audit")

    blank_all = sum(r["blank"] for r in actions)
    nonblank_all = len(actions) - blank_all
    blank_cases = sum(r["blank_text"] for r in cases)
    nonblank_cases = len(cases)-blank_cases

    by_demo = defaultdict(list)
    for r in actions:
        by_demo[r["demo"]].append(r)
    demos = sorted(by_demo)
    rng = random.Random(2026112211)
    boot_diffs=[]
    boot_rates=[]
    for _ in range(reps):
        sampled=[r for __ in demos for r in by_demo[rng.choice(demos)]]
        bn=sum(r["blank"] for r in sampled)
        nn=len(sampled)-bn
        if bn == 0 or nn == 0:
            continue
        blank_fail=sum(r["joint_n"]>1 and r["blank"] for r in sampled) / bn
        nonblank_fail=sum(r["joint_n"]>1 and not r["blank"] for r in sampled) / nn
        boot_diffs.append(blank_fail-nonblank_fail)
        boot_rates.append(sum(r["joint_n"]>1 for r in sampled)/len(sampled))
    def ci(vals):
        vals=sorted(vals)
        return [vals[math.floor(.025*(len(vals)-1))],vals[math.ceil(.975*(len(vals)-1))]]
    return {
        "population":{
            "actions":len(actions),
            "demonstrations":len(demos),
            "residual_actions":len(cases),
            "residual_demonstrations":len(set(r["demo"] for r in cases)),
        },
        "mechanisms":counts(cases,"mechanism"),
        "target_text":counts(cases,"blank_text"),
        "target_tags":counts(cases,"target_tag"),
        "target_roles":counts(cases,"target_role"),
        "candidate_rank_bands":dict(sorted(Counter(rank_band(r["target_rank"]) for r in cases).items())),
        "joint_width_histogram":counts(cases,"joint_match_n"),
        "orthogonal_diagnostics":{
            "at_least_one_missing_visual_competitor":sum(r["missing_visual_competitor_n"]>0 for r in cases),
            "at_least_one_valid_visual_competitor":sum(r["valid_visual_competitor_n"]>0 for r in cases),
            "at_least_one_exact_phash_competitor":sum(r["equal_phash_competitor_n"]>0 for r in cases),
            "at_least_one_near_phash_competitor":sum(r["near_phash_competitor_n"]>0 for r in cases),
            "at_least_one_equal_phash_different_bbox":sum(r["equal_phash_different_bbox_n"]>0 for r in cases),
            "at_least_one_same_bbox_competitor":sum(r["same_bbox_competitor_n"]>0 for r in cases),
            "at_least_one_iou50_competitor":sum(r["iou_at_least_50_competitor_n"]>0 for r in cases),
            "at_least_one_disjoint_bbox_competitor":sum(r["disjoint_bbox_competitor_n"]>0 for r in cases),
            "strict_phash_zero_resolves":sum(r["strict_phash_0_resolves"] for r in cases),
            "bbox_alone_is_unique":sum(r["exact_bbox_is_unique"] for r in cases),
            "ordinary_html_id_available":sum(r["target_html_id_available"] for r in cases),
            "xpath_available":sum(r["target_xpath_available"] for r in cases),
        },
        "counts":{
            "competing_candidates_total":sum(r["competitor_n"] for r in cases),
            "missing_crop_competitors_total":sum(r["missing_visual_competitor_n"] for r in cases),
            "valid_crop_competitors_total":sum(r["valid_visual_competitor_n"] for r in cases),
            "exact_phash_competitors_total":sum(r["equal_phash_competitor_n"] for r in cases),
            "near_phash_competitors_total":sum(r["near_phash_competitor_n"] for r in cases),
        },
        "blank_text_association":{
            "blank_total":blank_all,
            "blank_residual":blank_cases,
            "blank_residual_rate":blank_cases/blank_all,
            "nonblank_total":nonblank_all,
            "nonblank_residual":nonblank_cases,
            "nonblank_residual_rate":nonblank_cases/nonblank_all,
            "risk_difference":blank_cases/blank_all-nonblank_cases/nonblank_all,
            "risk_ratio":(blank_cases/blank_all)/(nonblank_cases/nonblank_all),
        },
        "bootstrap":{
            "unit":"demonstration",
            "replicates":reps,
            "seed":2026112211,
            "valid_resamples":len(boot_diffs),
            "blank_minus_nonblank_risk_difference_ci95":ci(boot_diffs),
            "overall_residual_rate_ci95":ci(boot_rates),
        },
    }
