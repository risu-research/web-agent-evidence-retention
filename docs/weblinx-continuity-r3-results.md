# Round 3 — Original action targets and adjacent-state site-native identifiers

## Method and source selection

The 600 original target actions in 55 WebLINX demonstrations were recovered from the previously published action-level measurement table. Candidate positive records came from `candidates/test_iid.jsonl`. Action arguments and direct `state.page` names came from the source `replay.json`. HTML was re-fetched from `McGill-NLP/WebLINX-full` at raw revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.

The [protocol](weblinx-continuity-r3-protocol.md) was frozen before source target comparisons. Each original action was paired with its **next browser observation** in the same replay. Missing next HTML pages remained in the denominator. The initial [full source job](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45056865263) completed successfully with **927 unique named HTML source files**.

## Round 3A: precise provenance of the 600 target candidates

| Original-source relation | Verified number of actions |
| --- | ---: |
| Source DMR target UID appears in Replay `action.arguments.element.attributes[data-webtasks-id]` | 600 / 600 |
| Direct current HTML exists and parses | 600 / 600 |
| Target DMR UID appears as exactly one element in current HTML | 600 / 600 |
| Positive DMR candidate XPath equals computed parser XPath of source target | 600 / 600 |
| Positive DMR target tag matches Replay element tag | 600 / 600 |
| Site-authored ordinary HTML `id` present on the target node | 122 / 600 |
| Ordinary HTML `id` unique in its own source page | 117 / 600 |

The DMR label, Replay action element UID and dataset-generated `data-webtasks-id` are parts of the same publisher recording. Their agreement confirms the **provenance and internal consistency** of the prior 600-action target-identification task. It does not measure browser event delivery independently.

The Replay element's recorded `xpath` string differs literally from the computed source XPath in **all 600 cases**, even though the DMR candidate XPath equals the computed source XPath in all 600. These are two recorded XPath representations with potentially different starting points or generators. **Literal string inequality is not a locator failure.** The source-executed expression comparison is preregistered as [Round 3C](weblinx-continuity-r3c-protocol.md), and must be evaluated before drawing any conclusion from this difference.

Action intents in the fixed 600 include 507 `click`, 78 `textInput`, and 15 `submit` turns.

## Round 3B: adjacent HTML and a separate site-native identity proxy

| Next browser state | Original actions |
| --- | ---: |
| Direct next HTML file retrieved and parsed | 560 |
| Next HTML bytes changed | 413 |
| Next HTML bytes identical | 147 |
| Next HTML missing from source observation | 40 |

Among the 413 changed next-state HTML pairs:

- 323 targets lack an ordinary site-authored HTML `id` suitable for the site-native proxy;
- eleven source target site-native IDs are absent in the next HTML;
- four source site-native IDs are duplicated in the source page;
- **75** have a unique site-native `id` in both snapshots with matching element tag and compatible stable fields (`type`, `name`, `role`).

The 75 are drawn from 31 demonstrations, including 46 `click`, 28 `textInput`, and one `submit` action. Seventy-three have the same recorded URL context hint; two have different URL hints. Within the 75:

- 59 retain the same computed XPath and **16 have a changed computed XPath**;
- 71 retain the same WebLINX `data-webtasks-id` and four have a different or unavailable WebLINX UID;
- 67 have unchanged compact element text; twelve have an ordinary parent `id` agreeing across snapshots.

The **16 changed-XPath cases** occur across ten demonstrations. Twelve have unchanged compact text. Four cases have a changed recorded UID, including two with an unchanged URL hint.

These are syntactic source observations. A site may reuse its native `id` when recreating an element. Stable names and text increase plausibility but cannot independently certify logical continuity. This group is a candidate pool for independent adjudication and a possible future XPath persistence evaluation. It is not a verified error cohort.

## Rounds 1–3 and next validity gate

- R1 established 55 fully retrieved replays and froze 165 adjacent HTML source pairs.
- R2 parsed the 165 pairs and found changed UID-to-XPath mappings in some adjacent states.
- R3A now anchors the **same exact 600 original target actions** to their source HTML and confirms their dataset target annotations.
- R3B finds a smaller site-native-id proxy pool after authentic adjacent state changes, without deriving ground truth from a WebLINX UID or XPath.

The separate R3C experiment runs the original recorded action XPath expression against the source DOM. If it selects the same DOM node as the DMR source XPath, the literal mismatch is a recording convention. The next-snapshot comparison will identify promising cases for independent source-target continuity adjudication.

**Unmeasured:** independently verified logical-element persistence, real executed event recipient, and whether a changed-state XPath causes a wrong browser action. These questions need an external event or site-specific identity reference.

## Reproduction assets

- [Pinned Round 3 protocol](weblinx-continuity-r3-protocol.md)
- [R3 action/source audit code](../scripts/weblinx_continuity_r3.py)
- [Full original R3 run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45056865263)
- [Derived numeric 600-action casebook](../results/weblinx_continuity_r3_actions.csv)
- [Original R3 source summary](../results/weblinx_continuity_r3_summary.json)
- SHA-256 original summary: `5d23045538a56bcf4faa1b9d7343fd4e75ca2585cfd33cd9e62d023b0a272c2e`
- SHA-256 original 600-row casebook: `d82723d1b7387f9c5784ee03604231efa79fa0024f39432ed8b440a5376a417f`

Only numeric results, public demonstration identifiers, original source hashes and categorical data are published; the original HTML, text, element IDs and literal XPath values remain at the publisher's source.
