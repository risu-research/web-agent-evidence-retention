# Independent reproduction on 2026-11-22

Both historical WebLINX experiments were run from a clean GitHub-hosted Ubuntu runner with Python 3.11 and frozen source-data revisions.

## Confirmatory study

- [Successful workflow run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684), job `137236244378`
- 600 analyzed actions from 55 demonstrations; 750 actions mapped; no mapping, fetch, or compute skips
- Top-10 coverage: 425/600; top-10 unique end-to-end recovery: 415/600
- Full-set joint unique recovery: 530/600; 197 visual escalations; 70 residual ambiguities
- 5,000 demonstration-cluster bootstrap replicates; full-set joint 95% interval: 0.8460–0.9184
- Full candidate population in this sample: 155,553 candidate records; 154,553 candidates with valid visual crop
- Verification: `python scripts/verify_results.py out_confirm/confirm_summary.json` passed
- [Run artifact](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684/artifacts/14757662991) (90-day retention)
- ZIP SHA-256: `7a9a8a3885168170c7b878d8b57634ca1dfa5885500c41e98ce8777edef252bb`
- Original `out_confirm/confirm_summary.json` SHA-256: `e03b5b07f44997b9017393a1eb0871bde1fd57c5299fe5818538e038224269e3`

## Fixed-action candidate-expansion sensitivity

- Same [workflow run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684), job `137236244078`
- 598 analyzed actions; two exclusions from the 600 selected actions (one lacked official records, one had an inconsistent target count)
- Joint uniqueness at top 10/20/50/all: 98.2%, 97.7%, 94.6%, 91.3% (rounded)
- Verification: `python scripts/verify_universe.py out_audit/universe_summary.json` passed
- [Run artifact](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684/artifacts/14757986686) (90-day retention)
- ZIP SHA-256: `431ecc5b78661be60fbd5f20de3225976fb623fb3e18c4a92c43b51f28c7b0bc`
- Original `out_audit/universe_summary.json` SHA-256: `5809d09d034f6ba2a09b1436e02eddbccb0220a6b9b6040dfa5010c27343d612`

## Exact environment

Both runs yielded an identical `pip freeze` output, now recorded in `requirements.lock.txt` (SHA-256 `799972d01c564de25c5ace046ca6d51b72277930d3bafd435c90a3ec318bc357`).

The aggregated JSON values are preserved in `results/rerun-2026-11-22/`. The workflow artifact archives hold the runner-generated files and recorded hashes. The public JSON copies were reconstructed from the exact JSON data printed in the successful job logs and may differ in whitespace from the hashed runner files.

The full WebLINX source data remains with its publisher; the scripts fetch the relevant candidate records, replay files, and screenshots at the pinned revisions.

No archival release or DOI has been created.
