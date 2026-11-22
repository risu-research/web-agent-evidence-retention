# Pixel-level follow-up to the 70-case residual audit

This diagnostic supplements the previously frozen text/DOM/pHash collision taxonomy. It targets **only valid-crop competing candidates already accepted by pHash <= 4** within the 70 residual actions. The original sample and pHash/semantic matching rule stay fixed. The existing collision categories are preserved.

For each such candidate, compute a crop directly from the original WebLINX screenshot, using exactly the floor/ceil/clamp bounding-box rule in `crop_hash`. Compare the target's RGB crop with the competing crop in two ways:

1. **Exact RGB equality** requires equal dimensions and identical RGB pixel bytes. This can identify truly repeated crop images, including images at different locations.
2. **Normalized 32×32 RGB mean absolute error** resizes both crops using Pillow LANCZOS and reports mean absolute pixel difference on the 0–255 scale. Preserve it as a continuous diagnostic without defining an arbitrary threshold for perceptual equivalence.

Within the pHash-distance-zero matches, report how many are byte-identical and how many have different pixels. Report separate totals for competitors with distances one to four. Retain the original mutually exclusive `missing_visual_only`, `mixed_missing_and_valid`, and `valid_visual_matches` labels.

This calculation tests what pHash collisions mean at the pixel level. Even exact crop equality cannot prove that the two DOM elements perform the same operation. Full semantic identity, dynamic page changes, actual browser event delivery, and retained ancestor context are outside this test.

Source screenshots remain in WebLINX. Public outputs include de-identified per-case counts and normalized differences only; raw crop bytes, images, page text, attributes, and locator strings stay out of the repository.

The rerun must reproduce the existing confirmatory and identifier hashes, plus the 70-case category summary and its complete membership before its pixel extension is accepted.
