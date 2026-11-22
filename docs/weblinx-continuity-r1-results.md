# WebLINX cross-state audit — Round 1 source inventory

**Status:** Original replay inventory verified; consecutive HTML pages selected before inspection.

## Source and population

The original 600 actions in the 55-demonstration WebLINX confirmatory cohort determine the fixed study population. All source replays were retrieved from `McGill-NLP/WebLINX-full` at immutable revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.

The [completed original source run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45055336663) independently retrieved and read the 55 official `replay.json` files. No inferred or back-filled HTML states were used in the counts.

| Audit measure | Verified count |
| --- | ---: |
| Complete demonstration replays | 55 |
| Raw turns of all types | 2,331 |
| Browser turns | 1,387 |
| Browser turns with an explicit HTML page | 1,237 |
| Browser turns with an explicit screenshot | 1,233 |
| Adjacent browser observations with directly recorded HTML on both sides | 1,125 |
| Distinct HTML filenames in those adjacent pairs | 1,123 |
| Identical HTML filename in those adjacent pairs | 2 |
| Demonstrations with at least one eligible pair | 55 |
| Source pairs frozen for raw HTML inspection | 165 |

The 1,387 browser turns span 55 demonstrations. Adjacent browser turns are consecutive in the browser-turn sequence, allowing chat messages between them. Any intervening browser turn lacking an HTML path breaks adjacency. This prevents turning two distant snapshots into a fabricated one-step transition.

## Preselected Round 2 units

From the 1,123 pairs with different source filenames, the source protocol selects at most three pairs per demonstration. Each pair is ranked by the distance of its nearer endpoint to one of the previously frozen 600 action turns. Tie-breaking uses the earlier replay index. Selection is deterministic and independent of raw page contents, UID matches or XPath results.

The 165 pairs, two source page filenames and exact replay indices are now committed in [the fixed source-pair CSV](../results/weblinx_continuity_r1_frozen_pairs.csv). Source replay SHA-256 values and per-demonstration completeness counts are preserved in [the complete 55-demonstration inventory](../results/weblinx_continuity_r1_demos.csv).

- [Frozen design and interpretive limits](weblinx-continuity-r1-protocol.md)
- [Reproduction code](../scripts/weblinx_continuity_r1.py)
- [Original aggregate source inventory](../results/weblinx_continuity_r1_summary.json)
- SHA-256 of the original 165-pair CSV: `0a739071530c8a7e16aaebf7900590689270539ed7ec60e25368c8a179a668a8`
- SHA-256 of the original 55-demo CSV: `5c0c213b5f47da8ef96f92e72304e25cdc7496ed692cd1e821edcf413a223af7`
- Replay hash-set SHA-256: `1b35a77d4f5092a95dfeacf8e551f111643cc8e962a9076b906de8ef8c12fc00`

## Findings and limits

All 55 demonstrations contain directly referenced HTML source snapshots, making a source-level cross-state audit feasible. The 1,123 adjacent pairs with differing **file names** are candidates for further inspection; changed file names do not prove changed HTML bytes. Reused UIDs in successive files cannot independently establish that the same logical element persisted.

The next source audit checks the original HTML bytes, source availability, document parsing, and the exact UID/XPath mappings in these 165 preselected pairs. A later experiment may assess identity over time only after defining an independent, defensible cross-state target label.
