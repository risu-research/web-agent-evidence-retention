# Implications of the 70-case source audit for the manuscript

The 70 residual actions were identified in the original 600-action WebLINX confirmatory sample. This analysis preserves the original data revision and evaluates causes of failure to uniquely recover the target from text, semantic DOM and pHash-compatible crop evidence.

## Observations worth reporting

1. **A missing crop and an indistinguishable valid crop have different causes.** Nineteen actions remain ambiguous solely because of competitors with missing crop evidence; ten contain both missing and valid matching crops; 41 contain matching valid crops throughout.
2. **All 84 unavailable competitor crops have traceable geometric causes.** Forty-one published boxes have a width or height at most two pixels. Forty-three clip to fewer than three pixels inside the replay screenshot. All 29 affected actions have replay screenshots.
3. **Visual evidence can repeat exactly.** Among the 224 compatible candidates with valid crops, 92 have RGB pixels identical to their targets. Sixty-five of these repetitions occur at different candidate bounding boxes.
4. **pHash also loses some differences between crops.** Sixty-nine competitors have pHash distance zero despite different RGB crop pixels. Another 63 have distances one through four.
5. **The frozen semantic representation often contains little distinguishing text.** Sixty-three residual targets have blank text and 69 lack a standard accessibility role in the published candidate description.
6. **Exact same-state locators close the observed identification gap.** Preserving the published XPath identifies all 600 targets. The effect of omitting an exact locator belongs in the interpretation of the original 88.3% descriptive-evidence recovery result.

## Consequences for selective evidence retention

The evidence suggests three distinct escalation needs.

- A geometry failure calls for a valid captured region, viewport/context coordinates, or another way to reference the relevant element.
- A repeated, pixel-identical crop calls for context beyond that tight crop, such as an ancestor element, a neighboring row label, or an execution-time locator.
- A pHash collision across different RGB crops creates a testable opportunity for retaining a higher-fidelity image representation. The improvement and storage cost need direct measurement.

The three conditions can coexist within one recorded action. A single global visual-evidence fallback would be difficult to justify without measuring its behavior separately on each condition.

## Scope for the accepted paper

These findings support the original division between candidate omission and evidence collision under the paper's chosen reconstruction model. They also sharpen a material limitation: **exact execution-time locators distinguish every target within the same published candidate snapshot**. A production design that retains those locators and its original browser state can follow a different audit path.

A stronger next experiment would compare actual recording and later replay: original target locator, verified event recipient, page state changes, and failure modes when the interface evolves. The present WebLINX snapshot study supplies a controlled baseline for such work.

The storage-cost experiment remains separate. Current figures measure target identification and evidence compatibility, rather than actual byte savings.

## Sources

- [Complete 70-case findings](residual-failure-results.md)
- [Source screenshot geometry audit](residual-missing-crop-protocol.md)
- [Pixel-level audit protocol](residual-pixel-protocol.md)
- [Identifier-retention results](identifier-baseline-results.md)
