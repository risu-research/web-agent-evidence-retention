# R1 — WebLINX consecutive-state source audit protocol

Frozen November 22, 2026, before running the new source inventory.

## Motivation

The previous 600-action candidate study and 70-case audit used the WebLINX DMR candidate list and linked screenshots. A recorded XPath uniquely recovered all 600 targets within the same released candidate snapshot. Consecutive replay states require a distinct provenance audit before an estimate of XPath durability can be interpreted.

The official WebLINX `Turn` API documents `state.page`, `state.screenshot`, `get_html_path()`, and `get_xpaths_dict(uid_key='data-webtasks-id')`. The DMR candidate file and a raw HTML page serve different purposes. A candidate list's recorded XPath cannot be treated as a verified cross-time identity label.

## Frozen source

- Hugging Face dataset `McGill-NLP/WebLINX-full`.
- Exact raw revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.
- The 55 demonstration identifiers and 600 action keys in the **published original measurement CSV** `results/storage_cost_600_actions_2026-11-22.csv`.
- Read each `demonstrations/<demo>/replay.json` directly, without inferring missing HTML file paths using `assign_html_path_to_turn`.

## Round 1: inventory before HTML inspection

Record, for each of 55 demonstrations, raw replay SHA-256, total turns, browser turns, turns with a directly recorded HTML path, turns with a directly recorded screenshot path, and adjacent browser-turn pairs with two directly recorded HTML paths. Count pairs that cite the same filename separately from those that cite distinct filenames.

Consecutive browser observations refer to **adjacent browser turns in raw replay order**, possibly separated by chat messages. Do not silently skip browser turns missing an HTML path to create longer-range adjacency. Preserve raw integer turn indexes.

For the next inspection round, choose up to **three distinct-filename adjacent browser pairs per demonstration**. Order all eligible pairs by minimum absolute distance from either end of the pair to one of the 600 preselected action-turn keys in that demonstration; tie-break by earlier source turn index. This deterministic selection uses no element labels or future DOM match results. Publish selection indices even for failed or missing source documents. Do not change the selection after observing HTML results.

## Round 2: verify the actual raw HTML sources

For each frozen pair, download both `pages/<replay page filename>` files from the exact raw revision. Audit missing-file status, HTML SHA-256 equality, source bytes, parseability, counts of duplicate/absent `data-webtasks-id` attributes, and whether same exact URL or tab metadata exists for the pair. The source inventory alone cannot establish logical element continuity.

For pairs with two distinct parsed HTML sources, compare same XPath and same `data-webtasks-id` mappings. Report (a) repeated UID and repeated XPath, (b) repeated UID at changed XPath, and (c) XPath occupied by a different UID. These are **syntactic snapshot comparisons only**. The UID is a dataset recording key and must never be called an independent cross-state ground truth merely because it repeats.

A stronger positive continuity label requires additional independent material (persistent site ID, action trace or manually adjudicated context). If such a label is absent, report an identified upper-bound pool of candidates and explicitly leave definitive success/failure rates unresolved.

## Safeguards and failure accounting

Use source metadata as recorded, avoid publishing URL strings, element text, raw HTML, rendered images or locator values, and exclude no failed source pair silently. Per-pair published records may include public demo/turn keys, availability and counts, source hashes, and categorical consistency indicators. A missing page and a changed navigation context are separate outcomes.

This is a feasibility and measurement-validity audit. It does not replay user actions and does not yet measure the true rate of incorrect target identity after webpage changes. Later controlled browser experiments may use the validated source conditions.
