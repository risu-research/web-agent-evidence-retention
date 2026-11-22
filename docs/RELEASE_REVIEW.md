# Final release boundary and pre-Zenodo review

This checklist defines the recommended source archive for the camera-ready paper *What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention*.

## Included in the paper's public reproduction package

- `README.md`, `CITATION.cff`, the repository's code `LICENSE`, and `requirements.lock.txt`.
- The core paper scripts: `reproduce_confirm.py`, `reproduce_universe.py`, `verify_results.py`, `verify_universe.py`, `identifier_baseline.py`, the `residual_*` scripts, `storage_costs.py`, `storage_cost_casebook.py`, `storage_cost_bootstrap.py`, `verify_paper_artifact.py`, and the R1–R3C source-audit scripts required for the saved-action XPath check.
- Corresponding core unit tests and verified numerical casebooks under `results/`, including the 600-action storage CSV, 70-case residual CSVs, DMR identifier baseline, saved-action R3C results, 598-action sensitivity, and both bootstrap outputs.
- Methods and data-rights documents: [paper-to-code map](PAPER_REPRODUCTION.md), [dataset license and terms](DATASET_TERMS.md), [frozen source protocol](protocol.md), [historical provenance](provenance.md), [independent rerun record](reproduction-2026-11-22.md), identifier/residual/cost protocols and results, and the R3C source-provenance protocol/results.

The GitHub repository also contains R5–R8B experimental studies; they are useful exploratory work, and their original run history should remain public in GitHub. The **camera-ready archive** can be a curated, reviewed subset centered on the paper's measured claims. Recheck all import dependencies and numeric checks in that exact subset before creating it. Never claim an untested subset reproduces the full paper.

## Exclude from the camera-ready archive

- Any downloaded WebLINX candidate document, raw replay JSON, screenshot, webpage HTML or user dialogue.
- Raw browser Trace ZIPs, HARs, session/cookie values, authentication material, synthetic login credentials, database dumps or sqlite journal files.
- Working directories (`wl_*/`, `out_*/`), virtual environments, Python caches and transient CI files.
- Internal drafts, editorial emails, local absolute paths, unreviewed annotations or experimental handoff archives.
- Exploratory R5–R8B source/results from the **paper-specific** archive unless a later manuscript explicitly uses and reviews them.

The repository's `.gitignore` reduces accidental commits of common raw outputs; it is a convenience guard, **not a content review or a substitute for credential scanning**.

## Before minting a permanent DOI

1. Run `python scripts/verify_paper_artifact.py` and the relevant paper unit tests.
2. Recreate the source results with `scripts/storage_cost_casebook.py`; confirm the original full-cohort checksums and the same exact byte counts.
3. Check the separate R3C source-XPath experiment and 598-action sensitivity by the documented pinned environments.
4. Review the final included-file list manually, scan for secrets, raw webpage data, screenshots, and unexpected local references.
5. Check the WebLINX publisher's [dataset license and extra terms](DATASET_TERMS.md), and retain attribution and source-rights notices in the archive.
6. Freeze the Git commit or release tag; generate a SHA-256 file manifest from the actual archive contents, and validate it after downloading the archive.
7. Confirm the final paper metadata and references. Publish the reviewed archive, then add the actual issued DOI to the manuscript and citation metadata.

**Status (2026-11-22):** Reproduction code and derived numeric records are public. Artifact-maintenance checks and the source rerun are tracked in the repository's GitHub Actions. The paper-specific archive and its permanent DOI require a separate final release decision.
