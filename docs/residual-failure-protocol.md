# Residual collision audit protocol

This is the fixed analysis plan for the 70 non-unique targets in the 600-action WebLINX confirmatory sample. The sample, dataset revision, image crop geometry, semantic attributes, and perceptual-hash threshold are inherited unchanged from the reproducible 2026-10-04 confirmatory protocol.

The unit of analysis is a recorded target action. A residual case has exactly one positive ground-truth target candidate and **more than one** candidate compatible with that target's text, semantic DOM signature, and screenshot-crop pHash (Hamming distance <= 4). The target is included in the count. A residual is an inability to identify a target uniquely from these selected representations, not a failed browser interaction.

## Mutually exclusive evidence mechanisms

Each residual is assigned to exactly one mechanism by inspecting the **competing** compatible candidates after excluding the ground-truth target:

1. `missing_visual_only`: every competitor has an unavailable or invalid visual crop. The available visual hashes distinguish the target, but unresolved visual evidence leaves at least one competitor.
2. `mixed_missing_and_valid`: at least one competitor has unavailable visual evidence and at least one has a valid perceptual hash within the acceptance threshold.
3. `valid_visual_matches`: every competitor has a valid perceptual hash within the acceptance threshold.

These classes are determined from the observed evidence, not a subjective explanation of why the website was built as it was.

## Complementary, overlapping diagnostics

- Blank or nonblank target text.
- The target's HTML tag (standard tags or `other`) and accessibility role when present.
- Number of text-equivalent, semantic-DOM-equivalent, and fully compatible candidates.
- Number of fully compatible competitors with exactly equal crop hashes (Hamming 0) and with hashes at distances 1 through 4.
- Exactly equal bounding boxes, boxes overlapping the target at IoU >= .5 or >= .95, and disjoint boxes. Bounding-box comparison uses the original released coordinates without rounding.
- Number of compatible alternatives with missing visual evidence, separated from missing crops across the entire candidate population.
- Whether a stricter pHash threshold 0 would distinguish the target; this is a sensitivity diagnostic, not a validated better operating threshold.
- Whether the exact target bounding box is unique among all published candidates at that screenshot, as a same-state geometric comparator.
- Number of target descriptions with ordinary HTML `id` values; existing XPath results are treated as the documented same-state oracle.

Exact pHash equality across different bounding boxes measures a perceptual-hash collision. It does not prove the two rendered objects are visually identical.

## Analyses

The pipeline will reproduce the frozen original confirmatory JSON and its SHA-256, assert the same 600/55 cohort and 70 original residual keys, and export 70 per-case diagnostic rows.

Report the number of residual cases in each exclusive mechanism and the overlap of the other diagnostics. Report counts by blank text, tag, collision multiplicity, and target-rank band. Use all 600 actions as the denominator for failure rates by blank versus nonblank target text. Paired demonstration-cluster bootstrap (5,000 replicates, seed 2026112211) will quantify uncertainty in the difference of those two residual rates.

Representative case descriptions will cite demonstration and turn identifiers, evidence counts, and reproducible diagnostics. Any qualitative diagnosis requiring inspection of raw rendered crops must be labeled as pending visual inspection. Numeric matching patterns alone cannot verify human-perceived similarity.

## Public outputs

A machine-readable per-case CSV may contain public demonstration keys, turn indices, rank bands, tag labels, evidence counts, hash-distance categories, and overlap indicators. It must exclude exact target or competitor text, HTML attributes, URLs, XPath strings, UIDs, screenshots, and dialogue. Aggregates, tests, and exact source provenance will be published.

The study intentionally retains the earlier identifier result: the published XPath uniquely distinguished all 600 targets in the same-state candidate collections. The current audit describes ambiguity when those exact locators are omitted.
