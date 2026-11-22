# Identifier retention on the frozen 600-action cohort

Computed on November 22, 2026 using [GitHub Actions run 45033429624](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45033429624).

## Main results

The original 600 actions from 55 WebLINX demonstrations were replayed at the same pinned dataset revision. Throughout this baseline, XPath means the `[[xpath]]` in the published DMR candidate document; it is separate from the Replay action's `action.arguments.element.xpath` field, whose agreement with saved source HTML is measured in the [R3C study](weblinx-continuity-r3c-results.md). The confirmatory summary was reproduced byte for byte (SHA-256 `e03b5b07f44997b9017393a1eb0871bde1fd57c5299fe5818538e038224269e3`).

| Candidate set | Target present | Joint text+semantic DOM+visual | XPath alone | UID oracle |
| --- | ---: | ---: | ---: | ---: |
| Top 10 | 425 | 415 | 425 | 425 |
| Top 20 | 470 | 452 | 470 | 470 |
| Top 50 | 521 | 483 | 521 | 521 |
| Entire published candidate set | 600 | 530 | 600 | 600 |

Counts represent end-to-end recoveries among the 600 actions. Every recorded target has a published XPath, and each XPath uniquely matches its target within the tested published candidate sets. The instrumented `data-webtasks-id` agrees with the official target UID for all 600 actions and has the same recovery counts.

The ordinary HTML `id` attribute appears in 122/600 target candidate descriptions. It uniquely distinguishes 121 of those 122 targets in the full published candidate sets. With `id` added to the original joint evidence, unique recovery rises from 530 to 536 actions.

The original joint evidence left 70 actions unresolved. An exact XPath resolves all 70 in this same-state experiment. The ordinary HTML `id` resolves 6 of these 70. Full-set joint+XPath rises by 11.67 percentage points, with a paired demonstration-cluster bootstrap interval of 8.23 to 15.25 points (5,000 replicates).

The 155,553 candidate records in this confirmatory set contain a published XPath for every candidate. Only 14,190 candidate records have an HTML `id` field. This describes the released candidate text representation.

## Interpretation

The UID result is an exact-match oracle using a dataset-provided element key. The XPath result is a same-record, same-state check of the XPath already included in the released candidate documents. Neither test measures persistence after page changes, event-target consistency, or a browser recorder's ability to store a trustworthy locator.

The current descriptive-evidence recoverability result (530/600) characterizes records that omit exact locators. The 70 unresolved cases remain useful for studying that explicit representation restriction. The full snapshot results give no evidence that text, semantic DOM or target-region pHash is needed to distinguish a target when its exact published XPath remains available.

Top-K candidate omission survives perfect within-set identity matching: Top-10 has 175/600 targets outside the set. This is an evaluation of candidate-limited retrospective lookup. A production audit that preserves the executed locator and the original DOM could use a different retrieval strategy.

The reported HTML `id` availability refers to the published DMR candidate descriptions; the underlying HTML may contain additional attributes. The candidate data are filtered and formatted by WebLINX.

## Files and checks

- [Comparison script](../scripts/identifier_baseline.py)
- [Frozen design](identifier-baseline-protocol.md)
- [Validated summary JSON](../results/identifier_baseline_2026-11-22.json)
- [Workflow run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45033429624)
- [Action-level metrics artifact](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45033429624/artifacts/14758593691), available until the standard GitHub Actions artifact retention date

The action-level CSV contains cohort keys, ranks, availability indicators and match counts. Literal locator values, raw HTML, screenshots and dialogue remain at their original data source.

The original workflow artifacts recorded:
- `identifier_summary.json` SHA-256: `12444432bff93d75e3117a7e81eca9b764f7928bfd92a9a13685d63863004b58`
- `identifier_action_metrics.csv` SHA-256: `6d18a92e487d3505431d9c9d1bf02beff85ea1d5b705d4556e7c06f2522781f3`
- `out_confirm/confirm_summary.json` SHA-256: `e03b5b07f44997b9017393a1eb0871bde1fd57c5299fe5818538e038224269e3`

The public summary JSON was reconstructed from the successful job's printed JSON values and reformatted for readability. Its content agrees with the runner-produced summary.

## Independent repeat with exact matching files

A separate [locked-environment run 45033934800](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45033934800) on November 22, 2026 repeated the entire 600-action calculation. The confirmatory JSON, identifier summary JSON, per-action CSV, environment file, and generated checksum file matched the first run byte for byte. All five locator unit tests passed.

- [Independent repeat artifact](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45033934800/artifacts/14758094190)
- Comparison source commit: `e531ac31b63c49e3a18d9ea998e08527b969fe69` for the locked baseline workflow
- Exact environment: `requirements.lock.txt`

