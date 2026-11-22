# Web-Agent Evidence Retention

Reproducibility code for **What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention** (TRUSTMORE 2026).

The study measures whether the target of a recorded web-agent action appears in the candidates available for later review and whether the retained text, semantic DOM, and visual evidence distinguish it from competing elements.

The confirmatory analysis uses 600 WebLINX actions from 55 demonstrations. With the top 10 DMR candidates, target coverage was 70.83% and end-to-end recovery was 69.17%. Joint evidence over the full released candidate sets uniquely identified 88.33% of targets.

## Reproduce

Use Python 3.11 in a clean working directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/reproduce_confirm.py
python scripts/verify_results.py out_confirm/confirm_summary.json
```

On Windows, activate the environment with `.venv\Scripts\activate`.

The confirmatory script downloads the official ranked candidates, replay files, and screenshots for the frozen dataset revision. It reconstructs the sample, compares evidence representations, and calculates clustered bootstrap intervals. The download is substantial.

The earlier fixed-action candidate-expansion analysis can be run separately:

```bash
python scripts/reproduce_universe.py
```

That analysis uses an earlier, top-10-conditioned sample. Its results belong to a separate sensitivity test.

## Contents

- `scripts/reproduce_confirm.py`: final 600-action confirmatory analysis
- `scripts/reproduce_universe.py`: fixed-action candidate-expansion sensitivity
- `scripts/verify_results.py`: validates a freshly generated summary against the frozen results
- `results/`: published aggregate reference tables
- `docs/protocol.md`: fixed data and experiment definitions
- `docs/provenance.md`: links to the original computation commits and successful runs

The reference tables record the submitted findings. The full dataset analysis needs to finish successfully before its outputs can be called independently reproduced in this repository.

## Source data

WebLINX is hosted by its original publisher. The scripts download the necessary records. Local raw data and generated outputs stay outside the versioned source tree.

The archival DOI and citation metadata will be added after final validation and release.
