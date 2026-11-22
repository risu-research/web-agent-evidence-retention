# Camera-ready paper: table-to-artifact reproduction

**Paper:** *What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention* (TRUSTMORE 2026 working camera-ready revision, November 22, 2026).

**Repository:** [risu-research/web-agent-evidence-retention](https://github.com/risu-research/web-agent-evidence-retention).

**Published v1.0.0 archive:** [Zenodo DOI 10.5281/zenodo.24450361](https://doi.org/10.5281/zenodo.24450361) ([GitHub release](https://github.com/risu-research/web-agent-evidence-retention/releases/tag/trustmore2026-artifact-v1.0.0)); 107 allowlisted files; original reviewed source at commit `f2333815efc93fffc882533387aed6618007dcdd`.

**Primary source:** `McGill-NLP/WebLINX-full` at revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.

**Main population:** frozen 600 actions from 55 demonstrations. The separate fixed-action candidate-expansion sensitivity uses 598 actions sampled under earlier top-10 eligibility conditions. R5–R8B controlled browser experiments address later-stage execution evidence and are exploratory extensions outside the paper's primary quantitative tables.

## Fast independent check (offline)

Use Python 3.11; the following check relies on the standard library and shipped numeric outputs only:

```bash
python scripts/verify_paper_artifact.py
```

It checks the sample, headline coverage/recovery, 70-case partition, DMR and Replay XPath distinction, encoded storage totals, individual 600-row cost aggregation, bootstrap point estimates, and separation of screenshot/pHash from exact-RGB scoring. This is an **archived-output consistency audit**, so it should be followed by source reruns when independently reproducing the experiment.

## Source-data reproduction

The source data remain with the WebLINX publisher. Review [dataset rights and terms](DATASET_TERMS.md) before fetching them. In a clean Linux or macOS environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt

# Original 600-action confirmatory analysis
python scripts/reproduce_confirm.py
python scripts/verify_results.py out_confirm/confirm_summary.json

# Primary paper's locator, residual, pixel, and actual-byte experiments.
# This program regenerates all four preceding result layers as well.
python scripts/storage_cost_casebook.py

# Extra sampling-uncertainty calculations from its output.
python scripts/storage_cost_bootstrap.py \
  --input out_storage/storage_cost_600_actions.csv \
  --out out_storage/storage_cost_cluster_bootstrap.json

# Separate 598-action within-action candidate-expansion sensitivity.
python scripts/reproduce_universe.py
python scripts/verify_universe.py out_audit/universe_summary.json
```

The storage workflow verifies existing confirmatory, identifier, residual, pixel, and storage-output SHA-256 digests against the pinned run before archiving derived results. The dataset download and screenshot processing are substantial. Generated files belong in ignored `wl_*/` and `out_*/` directories.

**Original action XPath (separate evidence field).** In a clean Python 3.11 environment, follow [the R3C workflow](../.github/workflows/weblinx-continuity-r3c.yml) and execute:

```bash
python -m pip install 'huggingface_hub==0.36.2' 'requests==2.34.2' 'lxml==5.4.0'
python scripts/weblinx_continuity_r3c.py
```

The R3C script reads original replay-action XPath strings and evaluates them against the corresponding preserved source HTML. It uses a separately pinned lxml-based source-inspection environment. Its first and independently repeated outputs have the same recorded SHA-256; the workflow checks both. Keep this distinction separate from the DMR XPath equality baseline.

## Exact table-to-file map

| Paper section / table | Primary result and source | Archived data | Full source-run evidence |
| --- | --- | --- | --- |
| IV, Table I: top-K coverage and end-to-end recovery | `scripts/reproduce_confirm.py` | `results/rerun-2026-11-22/confirm_summary.json`, `results/candidate_recoverability.csv` | [main run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684); [locked repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45032360039) |
| V, Table II: text, semantic DOM, pHash, joint discrimination | same confirmatory runner | `results/representation_results.csv`, confirmatory JSON | same two source runs |
| VI: DMR candidate XPath and HTML `id` | `scripts/identifier_baseline.py` (also run inside storage study) | `results/identifier_baseline_2026-11-22.json` | [independent locator repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45033934800) |
| VI: Replay action XPath compared with saved source HTML | `scripts/weblinx_continuity_r3c.py` | `results/weblinx_continuity_r3c_summary.json`, `results/weblinx_continuity_r3c_actions.csv` | [source check](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45057156651); [repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45057539929) |
| VI, Table III: 70 descriptive-evidence collisions | `scripts/residual_casebook.py`, `scripts/residual_pixel_casebook.py`; source-geometry check `scripts/residual_missing_crop.py` | `results/residual_70_summary_2026-11-22.json`, `results/residual_70_pixel_summary_2026-11-22.json`, `results/residual_missing_crop_summary_2026-11-22.json` | [residual audit](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45035439394); [pixel repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45035686194) |
| VII, Table IV: final staged field per action | `scripts/storage_cost_casebook.py` and `scripts/storage_costs.py` | `results/storage_cost_summary_2026-11-22.json` | [full cost repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45046505590) |
| VII, Table V: compressed bytes and decoder recovery | same storage code | `results/storage_cost_summary_2026-11-22.json`, `results/storage_cost_600_actions_2026-11-22.csv` | same full cost repeat |
| VII, Table VI: costs within each residual class | same storage code | same 600-row casebook and cohort summary | same full cost repeat |
| VII: demonstration-cluster cost uncertainty | `scripts/storage_cost_bootstrap.py` | `results/storage_cost_cluster_bootstrap_2026-11-22.json` | [storage uncertainty workflow](../.github/workflows/storage-uncertainty.yml) |
| VIII: fixed-action 598 sensitivity | `scripts/reproduce_universe.py` | `results/rerun-2026-11-22/universe_summary.json`, `results/fixed_action_sensitivity.csv` | [main run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684) |
| VIII, Table VII: 64-bit pHash thresholds | `scripts/reproduce_confirm.py` | `results/phash_sensitivity_final.csv`, confirmatory JSON | [locked repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45032360039) |

## The two XPath measurements

- **600/600:** exact equality using the `[[xpath]]` field of the *published DMR candidate records* for the target and all released candidates in the **same recorded state**. The positive dataset label chooses the field retained in the hypothetical target signature. `scripts/identifier_baseline.py` also checks the dataset UID oracle separately.
- **589/600:** the *different* XPath string in `Replay.action.arguments.element.xpath` selects the dataset-UID-labeled element when evaluated against the publisher's saved source HTML. Ten select no element and one selects a different element. These observations concern saved-source agreement. They do not measure independently observed click delivery.

In the storage table, **621,808 bytes** for DMR XPath and **50,556 bytes** for target-only DMR XPath both derive from the published candidate field, with the latter depending on an external candidate index or page state.

## Image policy interpretation

- `all_hashes` and `selective_hashes` serialize compact candidate/target signatures and use the original pHash compatibility criterion; both identify **530/600**.
- `semantic_plus_crops` creates lossless RGB PNGs, verifies their reconstructed pHashes, and scores **545/600** under **exact RGB** comparison. Under the original pHash rule the same crops recover **530/600**.
- `full_frame` adds the publisher's actual screenshot-file bytes to compressed target/candidate metadata. Its **530/600** figure uses the original pHash outcome for those regions; there is no independent full-frame packet decoder. Source screenshots retain page context beyond the narrow identification benchmark.
- These sizes measure specific JSON/zlib/PNG encodings, excluding network, runtime capture latency, filesystem metadata, encryption, and raw webpage redistribution.

## Integrity and release boundary

The previously published source runner artifacts are retained as numeric JSON/CSV under `results/`; GitHub Actions attachments have limited retention. Important source revisions, frozen seeds, checksums, and run IDs are recorded in [the reproduction record](reproduction-2026-11-22.md), [identifier results](identifier-baseline-results.md), [storage results](storage-cost-results.md), and [R3C results](weblinx-continuity-r3c-results.md).

The repo's MIT license applies to original scripts. The source dataset has [separate third-party terms](DATASET_TERMS.md). Raw HTML, screenshots, literal XPaths, sessions, and Trace ZIPs are deliberately excluded from the release. **Release completed:** The reviewed paper-only GitHub v1.0.0 release and its [Zenodo version DOI](https://doi.org/10.5281/zenodo.24450361) are published. The source archive is fixed at commit `f2333815efc93fffc882533387aed6618007dcdd`; the manuscript reproducibility section cites this DOI. The 86 core archive tests and the full 600-action source-rerun CI succeeded.
