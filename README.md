# Web-Agent Evidence Retention

Reproducibility code for **What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention** (TRUSTMORE 2026).

The study measures whether the target of a recorded web-agent action appears in the candidates available for later review and whether the retained text, semantic DOM, and visual evidence distinguish it from competing elements.

The confirmatory analysis uses 600 WebLINX actions from 55 demonstrations. With the top 10 DMR candidates, target coverage was 70.83% and end-to-end recovery was 69.17%. Joint evidence over the full released candidate sets uniquely identified 88.33% of targets.

## Reproduce

Use Python 3.11 in a clean working directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
python scripts/reproduce_confirm.py
python scripts/verify_results.py out_confirm/confirm_summary.json
```

On Windows, activate the environment with `.venv\Scripts\activate`.

The confirmatory script downloads the official ranked candidates, replay files, and screenshots for the frozen dataset revision. It reconstructs the sample, compares evidence representations, and calculates clustered bootstrap intervals. The download is substantial.

The earlier fixed-action candidate-expansion analysis can be run separately:

```bash
python scripts/reproduce_universe.py
python scripts/verify_universe.py out_audit/universe_summary.json
```

That analysis uses an earlier, top-10-conditioned sample. Its results belong to a separate sensitivity test.

## Contents

- `scripts/reproduce_confirm.py`: final 600-action confirmatory analysis
- `scripts/reproduce_universe.py`: fixed-action candidate-expansion sensitivity
- `scripts/verify_results.py` and `scripts/verify_universe.py`: compare newly generated summaries with the frozen results
- `results/`: published aggregate reference tables
- `docs/protocol.md`: fixed data and experiment definitions
- `docs/provenance.md`: links to the original computation commits and successful runs

The reference tables record the submitted findings. The full dataset analysis needs to finish successfully before its outputs can be called independently reproduced in this repository.

## Source data

WebLINX is hosted by its original publisher. The scripts download the necessary records. Local raw data and generated outputs stay outside the versioned source tree.

The historical experiments were independently rerun on November 22, 2026. The resulting summaries and environment are preserved in [the reproduction record](docs/reproduction-2026-11-22.md). The archival DOI and citation metadata will be added after final validation and release.

## Identifier retention baseline

The same 600 actions were tested with retained element identifiers. Within the published candidate sets, a stored XPath uniquely identifies all 600 targets; the original text, semantic DOM and visual evidence identifies 530. The conventional HTML `id` appears in 122 target descriptions and uniquely identifies 121. Exact UID matching gives the same-snapshot upper bound.

See [the baseline results](docs/identifier-baseline-results.md) and [the frozen method](docs/identifier-baseline-protocol.md). The script runs as:

```bash
python scripts/identifier_baseline.py
```

The script also writes an action-level metrics CSV with no literal locator strings. Its `out_confirm/confirm_summary.json` must match the original confirmatory experiment.

## Residual collision audit

The original joint-evidence experiment left 70 of 600 actions with multiple compatible targets. A complete action-level audit found 41 cases with valid visual-hash collisions, 19 cases with unavailable competing visual crops, and ten cases with both. In those cases, 308 competing candidates survived the original evidence rule.

Direct RGB-crop comparisons further separated 92 pixel-identical competitors from 69 candidates with equal perceptual hashes but different pixels. Another 63 had pHash distances from one to four; 84 lacked usable crops. Source-geometry checks traced those 84 crops to 41 boxes with a dimension of two pixels or less and 43 boxes clipped below three pixels within the screenshot. These categories account for every competing candidate.

The [full 70-case findings](docs/residual-failure-results.md), [frozen classification rules](docs/residual-failure-protocol.md), [pixel audit method](docs/residual-pixel-protocol.md), and [redacted case-level CSV](results/residual_70_pixel_cases_2026-11-22.csv) are available in this repository. The computation can be repeated with:

```bash
python scripts/residual_casebook.py
python scripts/residual_pixel_casebook.py
```

Both scripts use the frozen 600-action sample and reproduce the original confirmatory and locator-baseline results before producing the additional diagnostics.

## Measured retention cost

A full replay measured the actual encoded sizes of candidate text, semantic DOM, 64-bit pHash, exact same-state locators, the publisher's compressed screenshots, and generated lossless PNG element crops. Recovery was checked by decoding each retained record across the same 600 actions.

Adding pHash only where semantic evidence is ambiguous takes **792,980 bytes** and identifies **530/600** targets. A text → semantic → pHash → bounding box → XPath record takes **862,427 bytes** and identifies **600/600** within the frozen candidate snapshots. A complete candidate XPath list with the recorded target XPath takes **621,808 bytes** and also identifies all 600.

The selective lossless-crop variant takes **309,543,191 bytes** and identifies **545/600**. Original compressed screenshots plus candidate descriptions and box coordinates take **206,275,510 bytes** using the original pHash recovery rule.

The [full measured results](docs/storage-cost-results.md), [frozen comparison protocol](docs/storage-cost-protocol.md), and [600-action numeric measurement table](results/storage_cost_600_actions_2026-11-22.csv) retain the exact costs and their interpretation.

```bash
python scripts/storage_cost_casebook.py
```

The code retrieves source images from the original publisher and exports derived numeric records. The Zenodo release remains scheduled for the final artifact audit.
