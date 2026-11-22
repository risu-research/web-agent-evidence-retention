# Why 70 recorded targets remained ambiguous

## Scope and reproducibility

The analysis uses the frozen 600-action, 55-demonstration WebLINX confirmatory sample, with the original candidate records, replay-to-screenshot mapping, semantic DOM signature and 64-bit pHash threshold of four. The 70 cases are the actions with two or more candidate elements compatible with all three retained evidence types. They are evidence-reconstruction ambiguities in the released DMR candidate population.

The [complete 70-case run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45035439394) passed on November 22, 2026. The outputs for the original 600-action study and the earlier identifier baseline matched their archived SHA-256 values. The 70 cases span 33 demonstrations, and their membership agrees with the original confirmatory action rows.

## Three observed collision mechanisms

| Evidence mechanism | Cases | Share of 70 |
| --- | ---: | ---: |
| At least one valid visual competitor, with no missing competitor crops | 41 | 58.6% |
| Only competitors with missing visual crops | 19 | 27.1% |
| Both missing-crop and valid visual competitors | 10 | 14.3% |
| **Total** | **70** | **100%** |

The 70 cases contain 308 fully compatible *competing* candidates. Of those, 84 have missing visual crops. The other 224 have valid crop hashes compatible with the target: 161 at pHash Hamming distance zero and 63 at distances one through four.

In the 19 missing-crop-only cases, available crop evidence distinguishes the target from all competitors with computable hashes. Retaining missing-crop competitors as possible targets is essential to the conservative matching rule. The ten mixed cases retain at least one valid visual competitor as well.

## Text and semantic attributes

- 63 of the 70 ambiguous targets have blank text.
- Among all 600 actions, blank targets have 63/390 (16.15%) residual ambiguity, versus 7/210 (3.33%) for nonblank targets. The descriptive risk ratio is 4.85.
- The difference in residual rates is 12.82 percentage points; a 5,000-replicate demonstration-cluster bootstrap yields a 95% interval of 7.86 to 18.07 percentage points.
- Target tags in the 70 cases include 44 `div`, nine `span`, five `i`, three `svg` and two `path` records. The remaining seven cases use other tags.
- A standard accessibility role is absent in the released candidate representation for 69 of the 70 targets. All 29 cases involving a missing competing crop have blank target text.

These attributes were read from the released candidate descriptions. Additional context may exist in the original page or an agent's execution trace.

## Spatial and perceptual collisions

- At least one non-overlapping competing bounding box appears in 53/70 cases.
- An exactly identical pHash at a different bounding box appears in 25/70 cases.
- At least one competing candidate has exactly the same bounding box as the target in 17/70 cases.
- The target bounding box is unique among the published candidates in 49/70 cases.
- A stricter pHash threshold of zero uniquely resolves seven of the 70 cases; 63 remain ambiguous.

A matching pHash over two separate screen regions measures a collision of that image representation. Direct RGB-pixel comparisons are reported separately in the [pixel-inspection protocol](residual-pixel-protocol.md).

## Direct RGB-pixel audit

A second successful [GitHub Actions run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45035686194) reconstructed the same 70 actions from the pinned WebLINX screenshots. It repeated the original 600-action analysis and the identifier baseline with matching output hashes, and preserved the first 70-case category summary and casebook byte for byte.

All 224 valid-crop competing candidates were compared against their targets using the exact cropped RGB pixels, then separately with a 32×32 normalized mean absolute RGB difference.

| Competing-candidate mechanism | Number | Relationship to target |
| --- | ---: | --- |
| Missing or invalid visual crop | 84 | A crop comparison is unavailable |
| Exact RGB crop pixels | 92 | Valid crop, pHash distance 0, identical pixel bytes |
| Same pHash, different RGB crop pixels | 69 | Valid crop, pHash distance 0, different pixel bytes |
| pHash distance 1–4 | 63 | Valid crop and a near, distinct hash |
| **Total** | **308** | |

Among the 161 candidates with identical pHash values, 92 (57.1%) have byte-identical crop pixels and 69 (42.9%) contain different pixels. Sixty-five of the exact pixel repetitions occur at different bounding boxes. At the action level, 34/70 cases contain an exactly repeated RGB crop, 14/70 have at least one hash-zero competitor with different RGB pixels, and 17/70 contain repeated crop pixels at different positions.

Two concrete examples show different mechanisms:

- `vhzkvri`, turn 18: a blank `i` element competes with 23 candidates at separate bounding boxes. All 23 competitors have the same pHash and exactly the same cropped RGB pixels as the target.
- `jlzucpt`, turn 21: a blank `span` has 29 valid competing candidates. Of 26 competitors with identical pHash, eleven have exactly the same RGB pixels and fifteen differ at the pixel level. The other three candidates lie within pHash distance 1–4. Every competitor occupies a separate, nonoverlapping bounding box.
- `vcptmwr`, turn 15: a nonblank `a` element remains ambiguous against two separate candidate crops at pHash distances 1–4. Both crops contain RGB pixels different from the target.
- `zjkuqip`, turn 27: eleven competing candidates have unavailable visual crops, leaving twelve candidate matches including the target.

The pixel comparison separates genuinely repeated crop images from the information loss caused by pHash. Identical cropped pixels at two locations also indicate where preserving a larger context region or element ancestry may be useful. These are direct observations from the released screenshot snapshots; the usefulness of any new logging policy remains a separate experiment.

See the [pixel audit design](residual-pixel-protocol.md), [archived pixel summary](../results/residual_70_pixel_summary_2026-11-22.json), and [complete 70-row pixel diagnostics](../results/residual_70_pixel_cases_2026-11-22.csv). The latter include crop equality indicators and normalized RGB difference statistics, with source images retained at the original publisher.

## Multiplicity and candidate ranks

The median residual case has four compatible candidates including the true target. The range is two to 30. Twenty-six cases have exactly two. The 70 target ranks are distributed as follows: 29 in Top-10, ten in ranks 11–20, eight in 21–50, eleven in 51–100, and twelve after 100. This emphasizes the distinction between candidate coverage and evidence discrimination: a case may experience both, depending on the candidate budget.

## Representative reproducible cases

The following descriptions refer to public WebLINX demonstration keys and turn indices. Every label and count comes from the redacted action-level casebook.

| Demonstration / turn | Mechanism | Observed distinguishing facts |
| --- | --- | --- |
| `jlzucpt` / 21 | Valid visual matches | Blank `span`; 30 matching candidates, 29 competing regions, 26 with identical pHash and three with distance 1–4; all 29 competitors occupy disjoint bounding boxes |
| `vhzkvri` / 18 | Valid visual matches | Blank `i`; 24 matching candidates, 23 competitors with identical pHash, all at disjoint bounding boxes |
| `zjkuqip` / 27 | Missing visual only | Blank `div`; twelve matching candidates, eleven competitors with unavailable visual crops |
| `dalipxa` / 33 | Mixed | Blank `div`; 13 matching candidates, eleven valid competing crop hashes and one missing crop; target at published candidate rank 364 |
| `vcptmwr` / 15 | Valid visual matches | Nonblank `a` element; three matching candidates, two valid competing hashes at pHash distances 1–4; both at disjoint screen positions |
| `bjqwbbx` / 66 | Mixed | Blank `div`; eight matching candidates, six competitors with missing visual crops and one with a matching valid crop |

The original screenshots and source candidate records can be inspected through the pinned WebLINX dataset revision specified in the [protocol](residual-failure-protocol.md). This table records diagnostic facts for specific cases without publishing their page text, literal element identifiers, or screenshots.

## Implications for the paper

The evidence-level residuals divide into missing visual evidence and collisions between retained evidence signatures. Repeated blank-text elements and sparse semantic attributes occur frequently in these cases. The pixel-level comparison tests how often matching perceptual hashes represent identical crop pixels.

The earlier identifier-retention study recovered all 600 targets when it preserved the published same-state XPath. The present findings therefore apply to logs that retain the studied text, semantic DOM and crop-hash representations without the exact execution-time locator. A separate runtime audit would be needed to test how a recorded XPath relates to the element that actually received a browser event or to the page after later changes.

## Source and audit files

- [Frozen categories and reporting rules](residual-failure-protocol.md)
- [Reproduction script](../scripts/residual_casebook.py)
- [Evidence diagnostics](../scripts/residual_diagnostics.py)
- [Machine-readable summary](../results/residual_70_summary_2026-11-22.json)
- [Complete redacted 70-case CSV](../results/residual_70_cases_2026-11-22.csv)
- [Complete pixel-level 70-case CSV](../results/residual_70_pixel_cases_2026-11-22.csv)
- [Pixel-level aggregate summary](../results/residual_70_pixel_summary_2026-11-22.json)
- [Full run and redacted 70-row casebook](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45035439394)
- `residual_summary.json` SHA-256: `a141e76d34b11a9dd63828293dd8cc06fc96d4aaf3292ec1ef4293bdc041e05b`
- `residual_70_cases.csv` SHA-256: `a1d603af041fc5dd27a52f6c4e46a29b2761a6cb5ea3fbdf801fa8485302a5e3`

The action-level CSV contains the 70 public demonstration keys, turn indices, count comparisons, crop availability, tag categories, bounding-box overlap and perceptual-hash diagnostics. Its export schema excludes literal URLs, element identifiers, text and media.
