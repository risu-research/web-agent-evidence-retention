# Reproduction protocol

## Data and sample

- Dataset: `McGill-NLP/WebLINX-full`
- Frozen revision: `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`
- Ranked candidates: `candidates/test_iid.jsonl`
- Clean population: 1,422 turns with exactly one positive DMR candidate across 99 demonstrations; 16 ambiguous groups excluded before sampling
- Confirmatory sample: seed `2026100403`, 14 actions maximum per demonstration, reserve of 750, first 600 mapped actions, 55 demonstrations
- All-candidate set: every released DMR candidate for a sampled turn (not the entire raw DOM)

## Evidence

Text is lowercase, whitespace-normalized visible text. Semantic DOM uses the tag and `role`, `type`, `name`, `aria-label`, `title`, `placeholder`, `alt`, `href`, and `value`. Visual evidence uses the screenshot crop at the published candidate bounding box and 64-bit pHash. The main visual compatibility threshold is Hamming distance <= 4; sensitivity thresholds are 0, 4, 8, and 12. A missing candidate visual crop remains compatible, preserving ambiguity.

A target is uniquely recoverable when exactly one candidate remains compatible with its retained evidence. Top-K end-to-end recovery requires the target to appear within K and be uniquely identifiable there.

## Output checks

The confirmatory script writes `out_confirm/confirm_summary.json`, including representation rates, top-K coverage and recovery, sampling diagnostics, sensitivity results, and 5,000 demonstration-cluster bootstrap iterations. Check it against the frozen counts with `python scripts/verify_results.py out_confirm/confirm_summary.json`.

The reported cascade has 158 actions resolved by text, 245 additionally by semantic DOM, 197 escalated to visual evidence, 127 recovered at that stage, and 70 unresolved.

The separate `reproduce_universe.py` experiment uses the earlier top-10-conditioned action set to test sensitivity to candidate-set size. Its 598 analyzed actions are separate from the final 600-action headline sample.
