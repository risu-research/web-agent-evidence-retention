# Web-Agent Evidence Retention

Reproducibility artifact for **What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention** (TRUSTMORE 2026), by Moon Hwan Lee, RISU Institute.

The study asks which element a web agent acted on and which permissions a user lost after an identified action. The archive includes the 600-action WebLINX study, the separate 598-action sensitivity analysis, and controlled Django Admin experiments.

## Start here

With Python 3.11, run the following commands from the archive root:

```bash
python scripts/verify_paper_artifact.py
python scripts/effects/verify_effects.py
```

Both commands use the Python standard library and the included numeric results. The second also executes the finite SQLite model. For a fresh computation from the original data and applications, follow:

- [WebLINX reproduction and table-to-file map](docs/PAPER_REPRODUCTION.md)
- [Django runtime experiments and permission-loss records](docs/EFFECT_REPRODUCTION.md)

## Principal results

| Study | Result |
| --- | --- |
| WebLINX top-ten candidate coverage | 425/600 |
| Top-ten joint evidence recovery | 415/600 |
| Joint evidence, all released candidates | 530/600 |
| DMR XPath, original candidate state | 600/600 |
| Recorded Replay XPath, original HTML | 589/600 |
| Selective / all-candidate pHash records | 792,980 / 1,670,040 bytes, both 530/600 |
| Django user-row Trace study | 48/48 correct on each of four audit questions |
| Django group deletion | Four matched contrasts with distinct permission-loss sets, including a pair with identical loss counts by user and by permission |
| Permission-loss packets | Exact recovery in all 12 assigned conditions, repeated twice |

The WebLINX results concern target identification within recorded page states. The Django group experiments use 12 assigned conditions across nine initial grant-relation states. The finite model separately enumerates 4,096 configurations.

## Source and rights

WebLINX-full is available from its publisher at revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. Review the [dataset license and terms](docs/DATASET_TERMS.md) before downloading. Original scripts use the [MIT license](LICENSE). The archive distributes derived numeric results and synthetic experiment code. Raw WebLINX HTML, images, dialogue, locator values, browser sessions and Trace archives remain outside the distributed files.

The [earlier version](https://doi.org/10.5281/zenodo.24450361) preserves the original WebLINX-only artifact. Cite the version corresponding to the results used. See [CITATION.cff](CITATION.cff) and the [repository](https://github.com/risu-research/web-agent-evidence-retention) for citation and release metadata.
