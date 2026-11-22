#!/usr/bin/env python3
"""Check the fixed-action candidate-expansion experiment against frozen rates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RAW_PIN = "36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8"
PRE_PIN = "a30ff2cbecb75f2d04fac75a2b92721c6c9e3f13"
REFERENCE = {
    "10": (82.9, 98.2, 17.1),
    "20": (80.1, 97.7, 19.9),
    "50": (78.6, 94.6, 21.4),
    "all": (76.8, 91.3, 23.2),
}


def check(summary: dict) -> list[str]:
    errors = []
    pins = summary.get("dataset_pins", {})
    for name, expected in (("raw", RAW_PIN), ("preprocessed", PRE_PIN)):
        if pins.get(name) != expected:
            errors.append(f"dataset_pins.{name} mismatch")
    values = summary.get("universe_sensitivity", {})
    for key, (td, joint, escalate) in REFERENCE.items():
        row = values.get(key, {})
        if row.get("n") != 598:
            errors.append(f"{key}.n: expected 598, got {row.get('n')!r}")
        checks = (
            ("textdom", row.get("textdom", {}).get("unique_rate"), td),
            ("joint", row.get("joint", {}).get("unique_rate"), joint),
            ("visual escalation", row.get("visual_escalation_rate"), escalate),
        )
        for label, value, expected in checks:
            if value is None or abs(float(value) * 100 - expected) > 0.051:
                errors.append(f"{key}.{label}: expected {expected:.1f}%, got {value!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="out_audit/universe_summary.json")
    args = parser.parse_args()
    failures = check(json.loads(args.path.read_text(encoding="utf-8")))
    for problem in failures:
        print("FAIL", problem)
    if failures:
        return 1
    print("PASS: fixed-action sensitivity matches frozen reported rates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
