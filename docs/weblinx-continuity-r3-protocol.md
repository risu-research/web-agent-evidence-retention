# Round 3 — recorded-target provenance and cross-state identity feasibility

## Preregistered scope

Freeze before reading new target-level source results. Date 2026-11-22.

Original fixed cohort: the **same 600 action keys in 55 demonstrations** published in `results/storage_cost_600_actions_2026-11-22.csv`. Ground-truth target candidate records are loaded from `candidates/test_iid.jsonl` at the raw dataset revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. Source replay JSON and directly named HTML pages are taken from that exact revision.

### R3A: candidate-to-recording consistency (600 actions)

Inspect the positive DMR candidate's UID, literal XPath and ordinary HTML id, the `action.arguments.element` UID / tag / XPath in original replay.json, and the matching element inside the HTML page named *directly* in that same replay turn's `state.page`.

Each key is classified by available recorded evidence: exactly one positive DMR candidate; browser action and action-element record present; action UID agrees with positive DMR UID; directly named source HTML available; target UID uniquely present in parsed source HTML; original DMR XPath equals the parser's source XPath; action-element XPath equals each of these separately. Report missing paths, parser failures, absent UID, duplicate UID and mismatches as separate categories. A mismatch between string XPath formats is counted only as a syntactic disagreement. No XPath regeneration or page assignment is allowed as a silent substitute for a missing `state.page`.

Recorded `action.arguments.element` and positive DMR label are both produced through the source dataset. Agreement is **source consistency**, not an independent browser-event recipient observation.

### R3B: adjacent target continuity candidates

For each of these 600 original actions, pair its replay turn with its **next browser turn in the same demonstration**, regardless of whether that later turn has HTML. This is fixed from turn order, not from apparent match success. Count every missing HTML source, changed vs identical bytes and same/different/unknown URL context hint. A next-state result is a snapshot comparison and is **not an action re-execution**.

In cases with two directly recorded, parsed, byte-distinct HTML documents, select the original target by its DMR UID only on the first page. Compare the source target's **ordinary site-native HTML `id`** against the next snapshot. The eligible diagnostic pool requires non-empty site-native id, exactly one such id in *each* document, unchanged tag and unchanged stable attributes (`type`, `name`, `role`) when both exist. Separately record whether target inner text is unchanged, whether its ordinary parent node has a stable site-native id, whether the source XPath changes, and whether WebLINX UID changes. These are **candidate continuity proxies**, not validated logical-element identity. Count site-native ids duplicated across either page and cross-page tag/signature changes.

A site-native id reused at another point in time can describe a newly created node. Site-native identifiers and attributes can themselves be reused. Therefore the project must obtain a separate adjudication (site-specific authoritative record or blinded human judgment with dual adjudicators and conflict resolution) before any target persistence rate can be called verified ground truth. Source-proxy numbers are conditional descriptive measurements only.

### Sampling, fairness, and boundaries

No target filtering based on source availability or match success. Per-action failure statuses must be exported for all 600. The next-browser cohort is fixed before content inspection. Original 165 R1/R2 pairs remain a separate *source-audit cohort*; do not substitute those for these target transitions. No rebranding of `data-webtasks-id` as site-native `id`.

Report source retrieval, missing action elements, raw source bytes, source hashes and categorical outcomes. Export only public demo/turn keys, boolean indicators and numeric counts. Literal URLs, user dialogue, account information, raw HTML, original screenshots, exact site-native ids, DMR UIDs and XPath strings must stay out of public GitHub. Avoid publishing per-action element text or text digests which could leak user content.

All source and environment versions are pinned. Write independent tests for UID duplicates, missing state pages, source XPath disagreement, site-native id reuse and next-browser selection. R3A and R3B are exploratory follow-up experiments that reuse the 600-action cohort. Findings must be cross-checked against the previously frozen `results/` references.

### Decision gate

Advance to a genuine XPath persistence **accuracy** study only after confirming enough instances of a defensible *independently adjudicated* logical-element identity. If no independent labels exist, record a feasibility result and next experiment plan. R3 cannot establish actual browser event delivery through Replay metadata alone.
