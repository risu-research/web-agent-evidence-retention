# WebLINX consecutive HTML source audit — Round 2

Source verification performed November 22, 2026. This round tests whether original replay-linked DOM snapshots exist and whether their UID/XPath relations can be compared. The population and measurement rules were frozen in [Round 1](weblinx-continuity-r1-protocol.md) before loading the actual HTML files.

## Full retrieval and parsing

The 165 preselected pairs reference 233 distinct HTML files. All 233 source files were fetched successfully from `McGill-NLP/WebLINX-full`, pinned revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. The two files of all 165 pairs were parsed successfully with the pinned `lxml` HTML parser. Every source-pair record is retained, including unchanged source states.

| Source check | Pairs |
| --- | ---: |
| Frozen adjacent browser-state pairs | 165 |
| Same raw HTML bytes despite different source file names | 26 |
| Different raw HTML bytes, both parsed | 139 |
| Missing source or unparseable document | 0 |

The 26 byte-identical pairs are important: a changed HTML filename alone would have misclassified these as changed snapshots.

## UID and XPath relationships in changed HTML pairs

The reported WebLINX-generated `data-webtasks-id` attribute and the computed `lxml` source XPath are two attributes of the recorded snapshot. A pair can contribute many elements to the counts below.

| Observable relation | Changed HTML pairs |
| --- | ---: |
| At least one unique UID occurs in both sources | 105 / 139 |
| No unique UID occurs in both sources | 34 / 139 |
| A repeated UID has a different source XPath | 40 / 139 |
| The same source XPath carries a different UID | 84 / 139 |

Across these pairs there are 180,821 repeated UID occurrences. Of those, 177,562 preserve their XPath and 3,259 appear at a different computed XPath. Separately, 14,627 XPath positions contain different UIDs across the two snapshots. These are repeated per-element observations nested inside 139 page pairs and must not be treated as independent actions or independent identity outcomes.

Duplicate UIDs within an individual snapshot are excluded from exact UID-to-XPath matching and counted separately in the per-pair casebook. Five pairs have at least one source with duplicate UID values.

## Navigation-context stratification

The original browser event metadata sometimes includes a URL and tab hint. Those values are included as **contextual hints**, using only same/different categories in public output. The event's URL can refer to action metadata and must not be treated as an independent document identity label.

| Changed HTML pair group | Pairs | At least one shared unique UID | A shared UID changes XPath | Same XPath changes UID |
| --- | ---: | ---: | ---: | ---: |
| Same recorded URL hint | 88 | 83 | 28 | 34 |
| Different recorded URL hint | 51 | 22 | 12 | 50 |
| **Total** | **139** | **105** | **40** | **84** |

There are 164 same-tab hints and one different-tab hint across the 165 pairs. The metadata fields are observational and may refer to a different temporal point from the HTML state. Two pairs even contain byte-identical HTML with different event URL hints. That mismatch is a reason to keep the URL field in the **hint** category.

Within the 88 byte-changed same-URL-hint pairs, 522 computed XPath positions contain changed unique UIDs. In the 51 different-URL-hint pairs, this count rises to 14,105, showing why it is essential to separate apparent navigation changes from same-URL changes.

## What has been proved

- The frozen 55 demonstrations have directly recorded consecutive replay states.
- The 165 selected source HTML pairs are complete, byte-verifiable and parseable.
- Some consecutive snapshots contain changes in the UID-to-XPath association.
- These changes persist in the subset with the same recorded URL hint.

## What remains unproved

The same UID repeated across snapshots is **not an independent logical-element label**. DOM nodes can be created, destroyed, or re-rendered; a dataset-generated UID can persist, disappear, or be regenerated. The same XPath occupied by two different UIDs therefore means the recorded mapping changed. It does not establish which logical element actually received an action, nor does it establish an incorrect XPath-based identification.

A valid next identity study should obtain cross-state target labels from a source independent of the tested XPath and dataset-generated UID. Examples include uniquely identifiable site-native IDs with a separate matching signature, independently instrumented browser event targets, or manual adjudication with documented disagreement handling. Cases without a defensible identity label should remain `unknown`.

## Provenance and reproduction

- [Original R1 inventory](weblinx-continuity-r1-results.md)
- [Frozen before-results source protocol](weblinx-continuity-r1-protocol.md)
- [R1 exact frozen pair list](../results/weblinx_continuity_r1_frozen_pairs.csv)
- [R2 HTML source audit script](../scripts/weblinx_continuity_r2.py)
- [Original R2 full HTML source validation](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45055628348)
- [Original 165-pair derived casebook](../results/weblinx_continuity_r2_pairs.csv)
- [Aggregated measured source results](../results/weblinx_continuity_r2_summary.json)
- R2 summary JSON SHA-256: `d71168fd4ea9564c4cda16471fa6902cf0e7665089cfee16cfef7b3746df174a`
- R2 165-pair CSV SHA-256: `8eeba01c2c385129bcc8238987844395e63211c5627af5078a6fc5fe1cc3536b`

The public artifacts contain counts, state-pair keys, document checksums and categorical context hints. Literal URLs, HTML content, browser screenshots and element values stay with the publisher's source data. The present source audit has no new trained model or released user trace, and no new Zenodo DOI is requested.

## Independent execution and publication

The [second complete R2 run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45055880614) retrieved and parsed the same 233 pinned HTML files again. Both derived result files, the exact parser environment, and the SHA-256 manifest were byte-identical to the [first completed run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45055628348). The 55-demo [R1 replay inventory was independently repeated](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45056042550) with all three original derived files and the manifest matching byte for byte.

A final [offline audit](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45056082602) passed 70 tests, including synthetic HTML parsing, repeated UIDs, UID relocation, exact-source equality, source-pair membership and redacted export checks.

Both rounds publish numeric source observations to `results/` in the [public repository](https://github.com/risu-research/web-agent-evidence-retention). The raw source replays and source HTML remain in the publisher's dataset at the recorded immutable revision.

**Next scientific gate:** Establish an independently adjudicated same-element label for cross-state comparisons. The present R1/R2 audit establishes source availability and exact syntactic changes. A logical-identity error rate, re-executed browser action success, and causal event-target verification remain unmeasured.
