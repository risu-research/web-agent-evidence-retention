# R4: blinded independent-channel feasibility for source identity

Frozen on 2026-11-22 **before the first R4 source inspection**. This is a post-R3 exploratory study, based on R3D's original 86 actions (11 event-time XPath anomalies and the complete 75 site-native ID proxies). Do not reselect cases after observing semantic evidence.

## Research question

The R3D site-native-proxy outcome shares an **HTML ID anchoring mechanism** with many captured `id(...)` Replay XPath expressions. The R3D 75/75 result may depend on this mechanism. Measure how frequently the same 75 proxy links are corroborated by independent *non-ID source semantics* when the evaluator is denied XPath, `data-webtasks-id`, ordinary `id`, raw DOM positions, screen coordinates, and outcome labels.

## Predetermined populations and comparisons

- All 8 R3D `replay_only` proxies (original candidate canonical XPath misses the native-ID proxy).
- All 67 R3D `both` proxies as the complete normal comparator; no result-selected controls are dropped.
- All 11 original-state action XPath mismatches separately.
- All 86 source keys remain reported.

The frozen source is `McGill-NLP/WebLINX-full` revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. Replay source and HTML paths are taken directly from the same raw turn and next browser turn. Read and verify the original 86-case file's SHA-256 before evaluation.

## Blinded matcher

Do not use XPath or any site-generated or dataset-generated HTML ID, including `id`, `data-webtasks-id`, `for` (which references a target ID), `aria-labelledby`, or exact DOM positions. Exclude CSS class and generated ordinal indexes. The matcher sees two independently parsed HTML documents, node tags, and only the following primitive channels with exact, normalized, nonempty values:

1. **Visible text:** tag + normalized descendant text, minimum four characters, maximum 160 characters. On each source page, the tuple must refer to **exactly one element** among all source elements with the same tag.
2. **Site-authored test key:** tag + `data-testid` or `data-test` (each a separate primitive).
3. **Link destination:** tag + absolute or relative `href` (as written) for anchors with a meaningful nonempty value beyond `#` and `javascript:`. Do not emit URLs.
4. **Form semantics:** tag + `name` together with `type` where available, for `input`, `select`, `textarea`, `button`.
5. **Accessible label:** tag + `aria-label` or `title` or `placeholder` (separate primitives).

A channel constitutes unique corroboration only if the original target's channel identifies exactly one source node and exactly one next-source node, and the next node equals the *site-ID proxy* selected only by the independent evaluator. Any unique channel pointing to another node is a conflict; if any channel has duplicate matches on either page, it is ambiguous. All other channels are absent or insufficient. Record availability, uniqueness, agreeing channels, contradictions and ambiguous channels separately.

Status tiers:

- `multi_family_corroborated`: two or more distinct **families** (text, test, href, form, accessible) unambiguously match the same proxy and no contradictory unique channels.
- `single_family_corroborated`: one independent family matches proxy with no contradictory unique channels.
- `conflict`: any unique channel matches a node other than proxy.
- `none`: no independent unique channel matches proxy.
- All tiers remain **structural corroboration of a proxy**, not independently adjudicated logical identity, even if multiple families agree.

Each source snapshot is evaluated with the same blinded matching rules, including the 67 both-success comparators and 8 captured-only cases. Report results for both groups and the URL-same subgroup. Do not call a remaining XPath result a verified success unless a separate, independently adjudicated browser identity reference exists.

## Original 11 discrepancy probes

Evaluate the captured action root-ID availability categories already fixed in R3D. Independently of the root ID, count the target's semantic channels (text, test, href, form, accessible) that uniquely identify it **within the original page**. This establishes whether the saved HTML contains any independent descriptive locator with which an auditor could identify the target, even when the Replay XPath fails. A source-descriptive locator can be ambiguous or unavailable. Do not claim the event succeeded or failed.

## Negative controls and uncertainty

For every valid unique source target channel, count how often its same channel matches *a different node* in the next source, and separately report ambiguous source and next matches. All 75 proxies remain the denominator. No selected proxy is discarded because it lacks a semantic channel.

Treat multiple actions from a demonstration as correlated; provide counts by demonstration and descriptive demo-cluster bootstrap, if material. No hypothesis test of true error rate. Preserve independent source IDs and DMR target labels exclusively inside the runner. Publish numeric and categorical results only; never serialize literal attributes, source HTML, URLs, user text, browser screenshots, or target locator expressions.

## Decision gate

Advance to human blinded adjudication only if original source evidence and presentation allow reviewers to decide logical persistence without seeing either locator or the site's ID. If the semantic evidence is too thin, document the feasibility limitation and pivot to instrumented browser events or authoritative application-record IDs. An identical public snapshot is never sufficient to reconstruct event delivery.
