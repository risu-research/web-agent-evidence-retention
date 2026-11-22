# Actual storage cost and recoverability protocol

Frozen before inspecting new measurements on November 22, 2026.

## Study population and input

Use the same 600 actions from 55 WebLINX demonstrations and the pinned `McGill-NLP/WebLINX-full` source revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. Generate the same frozen confirmatory JSON, identifier JSON, 70-case residual JSON, and pixel audit from the unchanged code path, and verify exact hashes. Do not sample additional actions to improve reported results.

## What is counted

Storage cost is **actual encoded byte length**, measured from the source screenshot files, serialized evidence bytes, and generated lossless PNG crops. Each JSON packet is serialized as UTF-8 with sorted keys and compact separators. Report raw JSON bytes and `zlib.compress(..., level=9)` bytes **per action**, allowing random access. This is one explicit implementation of candidate-record storage, not a universal lower bound.

- Record the publisher's original compressed screenshot file byte size (PNG/JPEG/etc.) for each action, separately report repeated screenshot cost per action and the sum after deduplicating identical referenced screenshot paths. Deduplication keys are pinned source `demo/screenshot` identifiers. The screenshot is counted *in addition to* candidate descriptors.
- Descriptive evidence payloads contain candidate text and selected semantic attributes and an action-level target signature. Dataset ground-truth labels, target candidate index, candidate UID, and target identity are held only by the evaluator. Publishing them in the retrieval payload would leak the intended answer.
- A retained 64-bit pHash is encoded as a fixed 16-character hexadecimal string for a valid crop, or `null` for invalid or unavailable crops. This encoding reflects JSON storage overhead; eight-byte binary coding is possible but not the measurement in this experiment.
- Locator baselines serialize recorded XPath/UID values. These baselines test exact equality within the same WebLINX candidate snapshot. Compare self-contained `target + candidate-list` storage with `target-only` byte size and label the latter as an external-lookup dependency.
- For ambiguous actions, create real **lossless RGB PNG** files in memory for the target and its semantically compatible candidates; sum the actual PNG bytes. Include all valid semantically compatible candidates and explicit null markers for unavailable crops. Measure PNG bytes separately from descriptive payloads and from hashes. Exact RGB crop equality is a strict snapshot discriminator; report it as a diagnostic rather than validated replay reliability.
- For residual actions, also measure the cost of retaining the target's and competitors' bounding boxes, and the extra same-state locator records needed for any remaining collision. Keep each alternative's bytes separately identifiable.

## Policies and reconstruction

All policies reconstruct uniqueness by comparing a retained target signature to stored candidate signatures, without access to the ground-truth labels. Only after decoding does the evaluator compare the single matched candidate with the ground truth.

1. `text`: target text and all candidate texts.
2. `semantic`: target text/tag/semantic attributes and all candidate descriptions.
3. `all_hashes`: semantic descriptions plus 64-bit pHash for every candidate.
4. `selective_hashes`: semantic descriptions for all candidates, with target pHash and candidate pHashes stored **only when semantic matching has more than one candidate** and then only for the semantically compatible candidates. This is a working same-snapshot logger requiring image access during recording.
5. `staged`: candidate texts for every action; semantic attributes only for text-compatible candidates when text collides; pHash only for semantically compatible candidates when semantic evidence collides; target and competing bounding boxes only if joint evidence remains ambiguous; target and competing XPaths only if geometry is still ambiguous. This policy should achieve 600/600 only if the complete matching path is reproducibly shown. Record how many actions use each stage.
6. `uid` and `xpath`: self-contained exact-match locator references for the target and full candidate list, with candidate order preserved. Also report a target-only locator log separately; it assumes an external candidate index or browser snapshot and cannot be equated to a self-contained audit.
7. `full_screenshot`: original compressed screenshot file plus semantic candidate descriptors, candidate bounding boxes and target evidence geometry, allowing recomputation of pHash. Measure original screenshot media separately so baseline accounting stays transparent.
8. `semantic_plus_crops`: semantic candidate descriptors and lossless RGB PNG crops for target and semantically matching candidates only when semantic evidence collides. Report PNG bytes and reconstructed original pHash uniqueness, plus exact RGB uniqueness as a separate upper-bound discriminator.

## Three failure mechanisms

For the original 70 residual cases, group by the frozen classes `missing_visual_only` (19), `mixed_missing_and_valid` (10) and `valid_visual_matches` (41). Report actual screenshot bytes, candidate metadata bytes, sparse hash bytes, lossless crop bytes, bounding-box/locator escalation bytes, and reconstruction success after each stage. Report both totals and medians, and clarify that the 70 cases are post hoc failure classes within a fixed confirmatory cohort.

## Integrity and interpretation

Validate the exact 600/55 cohort, all 70 residual membership keys, the prior 530/600 joint and 600/600 XPath results, and the 19/10/41 mechanisms. Preserve each encoded payload only in volatile memory; publish numeric per-action byte counts, success flags and source demonstration/turn keys, aggregate JSON, tests, and source code. Source screenshots, raw HTML, page text and locator values remain with the original publisher.

Report uncompressed bytes, compressed packet bytes, and source image bytes with units and arithmetic. Compression is performed per action, so repeated records across actions are not deduplicated except in the separately marked screenshot-path analysis.

Costs are **retention bytes** from one specified logger schema. They exclude initial image acquisition, time spent finding the target, CPU for candidate hashing, encryption, filesystem block overhead, storage indexes, transport, privacy review, and evidence required to prove actual event delivery. Exact same-snapshot target identification is an evaluation property, not an independently authenticated execution trace.
