# Measured storage cost and target recovery

November 22, 2026. The calculation uses the same frozen 600 WebLINX actions from 55 demonstrations, with the official dataset at revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.

The source screen files, candidate records and ground truth were read again. Every storage policy creates a real encoded evidence packet and then decodes it to identify the target. The original confirmatory, identifier and 70-case audit outputs matched their recorded SHA-256 values.

## Full-cohort costs

All byte counts below are actual output lengths under the [fixed recording protocol](storage-cost-protocol.md). JSON is serialized as compact UTF-8 and compressed independently for each action using zlib level 9. Source screenshots retain their publisher-supplied compressed format. Crop images use lossless RGB PNG at compress_level 6.

| Stored representation | Bytes across 600 actions | Identified targets |
| --- | ---: | ---: |
| Text and target text | 267,898 | 158 (26.3%) |
| Text, element tag and semantic attributes | 701,966 | 403 (67.2%) |
| Semantic attributes and pHash for every candidate | 1,670,040 | 530 (88.3%) |
| Semantic attributes with pHash only after semantic collision | 792,980 | 530 (88.3%) |
| Escalating text → semantic attributes → pHash → bounding box → XPath | 862,427 | 600 (100%) |
| Full self-contained target and candidate XPath list | 621,808 | 600 (100%) |
| Full self-contained target and candidate UID list | 1,794,620 | 600 (100%) |
| Semantic attributes and lossless PNG crops on ambiguous actions | 309,543,191 | 545 (90.8%) |
| Publisher screenshot file and candidate semantic/bounding-box descriptors | 206,275,510 | 530 (88.3%) under original pHash rule |

The screenshot archive includes 204,723,458 original screen-file bytes and 1,552,052 compressed candidate and target metadata bytes. The 600 actions reference **546 distinct screenshots**. Counting each unique screenshot file once yields 186,931,927 bytes in screen images and **188,483,979 bytes** including the per-action metadata.

The full-frame cost includes target and candidate bounding boxes. The 530/600 figure uses the original text/DOM/pHash matching criterion for a controlled comparison. Adding exact bounding-box matching after pHash ambiguity resolves 53 additional cases, giving 583/600 for that additional same-state matching criterion. The pixels in the original screenshot also permit exact RGB comparisons, whose separate resolution rate is shown by the lossless-crop experiment.

The lossless-crop policy captured **9,242 actual PNG blobs** across the 197 actions requiring visual evidence. The PNG images themselves occupy **308,794,163 bytes**. The policy includes both a target evidence crop and the corresponding candidate crop. The remainder of the 309,543,191-byte total contains metadata and crop manifests. Deduplicating repeated crop content could reduce storage, but this is the measured undeduplicated implementation.

## Decision stages

The self-contained adaptive record uses the first level that uniquely distinguishes its target:

| Last necessary field | Actions |
| --- | ---: |
| Text | 158 |
| Semantic DOM | 245 |
| pHash | 127 |
| Bounding box | 53 |
| XPath | 17 |
| **Total** | **600** |

This policy stores more evidence only when the previous level is ambiguous in the collected snapshot. Against the semantic-plus-selective-pHash policy, it retains 70 more uniquely identified targets for 69,447 additional total bytes across the whole cohort (8.76% more storage).

For target-only locator records, where the candidate list would need to be available elsewhere, the compressed measurements are **50,556 bytes for the event XPath** and **34,665 bytes for the event UID** across 600 actions. Those two totals depend on a separately retained candidate index or screenshot and are distinct from the self-contained comparisons above.

## Three failure mechanisms

The original 70 residual actions comprise 19 cases with only unavailable competitor crops, ten mixed cases, and 41 cases with valid competing crop hashes.

| Original mechanism | Actions | Semantic + selective pHash bytes | Lossless crop policy bytes | Lossless crop policy recoveries | Adaptive policy bytes | Adaptive recoveries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Missing visual only | 19 | 33,486 | 51,808,735 | 0 | 43,129 | 19 |
| Missing and valid visual competitors | 10 | 24,486 | 30,436,718 | 0 | 31,558 | 10 |
| Valid visual competitors only | 41 | 52,707 | 51,530,808 | 15 | 70,680 | 41 |
| **Total** | **70** | **110,679** | **133,776,261** | **15** | **145,367** | **70** |

Under the adaptive policy, all 19 missing-crop-only cases resolve through bounding boxes. The mixed cases require bounding boxes in three actions and XPath in seven. The valid-crop cases require bounding boxes in 31 actions and XPath in ten.

The lossless PNG criterion resolves 15 of the original 70 cases by requiring identical target and candidate RGB crop pixels. All 15 are also recovered by the bounding-box tier. The actual image data provide no incremental uniquely resolved action after retaining the exact same-state bounding box and the fallback XPath under this measured evaluation.

## Interpretation

- Sparse pHash retention saves 877,060 bytes (52.5%) against recording pHash for every candidate, with identical 530/600 recovery.
- Full PNG crops require 309.5 MB for 545/600 unique matches. The original compressed screenshots plus descriptor metadata require 206.3 MB and can be reused across actions.
- In the 19 missing-crop-only cases, the lossless crop policy stores 51.8 MB and recovers none. The original clipping and minimum-crop rules leave those competing candidates unresolved.
- Exact same-snapshot XPath matching identifies every target and uses less space than the adaptive protocol in this dataset. The implication is strongest for systems able to collect and retain reliable event-time locators.
- The 70-case audit remains a useful characterization of ambiguity under the restricted descriptive-evidence representation. The observed savings and target recovery refer to that fixed representation and candidate collection.

## Measurement boundaries

The numbers are byte counts of a specified recorder schema. Candidate order is retained implicitly in each packet; target labels and correct-candidate indices are used only during evaluation. The exact event-time target's signature is available to the hypothetical logger. Metadata is compressed per action, without cross-action string deduplication.

The experiment measures target uniqueness in the frozen WebLINX candidate snapshot. A valid XPath can identify one candidate in that snapshot. Demonstrating that a browser actually delivered the event to that candidate, or that the path remains valid after page changes, requires an execution trace and a separate experiment.

Image encoding and retention have distinct roles. Exact PNG pixels can support later visual review, and perceptual hashes preserve compact matching signatures. Cryptographic integrity, audit provenance, human review, privacy requirements and authorized access are separate operational considerations.

Costs exclude initial screenshot acquisition, processor time, network transfer, storage indexing, encryption and object-store metadata. The original media remain on WebLINX; only derived sizes, outcomes and reproducibility code are retained in this repository.

## Files and verification

- [Frozen cost protocol](storage-cost-protocol.md)
- [Byte-accounting and decoder implementation](../scripts/storage_costs.py)
- [Full 600-action executable study](../scripts/storage_cost_casebook.py)
- [Original 600-action measured summary](../results/storage_cost_summary_2026-11-22.json)
- [Complete numeric 600-action cost table](../results/storage_cost_600_actions_2026-11-22.csv)
- [Successful first independent computation](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45045751574)

Original runner-produced SHA-256 values:
- `storage_cost_summary.json`: `fa28e1b7981642ce4d8cb20d879129bf90cb4e5cbfbb531f018e7ff7ff549465`
- `storage_cost_600_actions.csv`: `1a7459d7a9fa1f81c1c4855ec85634db282e0ae9697e960eea030e1cb8741145`

No GitHub release or Zenodo DOI is created during this measurement stage.
