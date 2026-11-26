# Web-Agent Evidence Retention: TRUSTMORE 2026 reproduction archive

A frozen camera-ready artifact for the paper **What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention**, by Moon Hwan Lee (RISU Institute).

This archive contains the code, protocols, and numeric results needed to verify the 600-action WebLINX study and the separately analyzed 598-action candidate-expansion sensitivity. The main research repository remains at https://github.com/risu-research/web-agent-evidence-retention.

**Start here:** [Paper-to-artifact map](docs/PAPER_REPRODUCTION.md). The offline consistency check uses the Python standard library and needs no original WebLINX download:

```bash
python scripts/verify_paper_artifact.py
```

To reproduce the published computations from the original publisher-hosted source, follow [the pinned-source instructions](docs/PAPER_REPRODUCTION.md) and the corresponding CI workflows. The source data revision is `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. The confirmed 600-action, byte-accurate source rerun is [GitHub Actions #45077986130](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45077986130).

## Runtime effect identification

Run `python scripts/effects/verify_effects.py` for the offline native-packet and finite-model checks. Follow [the runtime reproduction guide](docs/EFFECT_REPRODUCTION.md) to rerun the actual Django and Playwright experiments.

## Results and what they mean

- Top-10 candidate coverage 425/600; end-to-end joint identification 415/600.
- Full candidate sets with text, semantic DOM, and pHash identify 530/600.
- Published DMR candidate XPath identifies 600/600 within the fixed candidate state. Separately recorded Replay action XPath selects the recorded target in source HTML in 589/600.
- Selective pHash retention: 792,980 encoded bytes for 530/600; all-candidate hashes: 1,670,040 bytes for 530/600.
- Candidate-indexed DMR XPath: 621,808 bytes for 600/600; staged packet: 862,427 bytes for 600/600.
- These are same-snapshot identification measurements, with the exact extraction and decoding rules documented in the accompanying protocols.

## Rights and archival boundary

Original source images, browser HTML, literal locator values, user dialogue, sessions, and raw browser Trace archives are excluded. They can be obtained only from their original rights holder, where allowed. WebLINX-full's **CC BY-NC-SA 4.0 license and additional publisher terms** are described in [DATASET_TERMS.md](docs/DATASET_TERMS.md). Our original scripts are MIT-licensed under [LICENSE](LICENSE).

This updated artifact adds the selected runtime experiments reported in Section IX of the revised paper. See [runtime reproduction](docs/EFFECT_REPRODUCTION.md) for source scripts, archived derived results and independent verification. Other exploratory experiments are outside this archive.

## Provenance

Source repository commit: `a37a6bf2ac6b03ef0c85f292fbf74e50c94d88e9`.
Full-data checked source rerun commit: `a1e2e4f84b7abbeaf5f1ee5a2f76f9b09d2a3733`.
Original 600-row storage summary SHA-256: `fa28e1b7981642ce4d8cb20d879129bf90cb4e5cbfbb531f018e7ff7ff549465`.
Original 600-row storage CSV SHA-256: `1a7459d7a9fa1f81c1c4855ec85634db282e0ae9697e960eea030e1cb8741145`.
See [the original rerun report](docs/reproduction-2026-11-22.md) for other fixed checksums.

The preceding v1.0.0 archive remains available at https://doi.org/10.5281/zenodo.24450361. This extension requires its own archival version.
