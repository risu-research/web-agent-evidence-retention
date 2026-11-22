# Identifier-retention baseline protocol

## Question

For the 600-action frozen confirmatory WebLINX sample, measure the improvement in target identification when an execution log retains a locator alongside descriptive evidence.

## Frozen cohort

The action selection, 55-demonstration clustering, DMR candidate ranks, data revision, visual crop rules, and evidence compatibility calculations come directly from `scripts/reproduce_confirm.py`. The original summary is regenerated and its SHA-256 must match the earlier independent reproduction before the new results are accepted.

## Compared evidence

- **UID oracle:** Exact equality between the official positive candidate's UID and candidate UIDs. This measures the same-snapshot upper bound with the correct execution-time key retained. It also checks whether duplicate UID values occur within the candidate population.
- **WebLINX data-webtasks-id:** Exact attribute value retained in the candidate's published element description, separately from normal HTML IDs. Its availability and agreement with the official UID are recorded. Dataset instrumentation may supply this value.
- **XPath:** Exact string equality for the published `[[xpath]]` field, preserving spelling and path indices. A target with no published XPath is ineligible for XPath-only recovery.
- **HTML id:** Exact string equality for the published `id` attribute. The instrumented `data-webtasks-id` and other `data-*` attributes are excluded. Missing IDs in published candidates are counted as unavailable, with no inference about their presence in the original raw DOM.
- **Joint evidence:** Original text + semantic DOM + 64-bit pHash criterion, with Hamming distance at most four. Missing candidate visual evidence continues to preserve ambiguity.
- **Joint plus XPath / HTML id / both:** Intersect the original compatible-candidate set with the exact recorded locator values when present; use the original joint evidence when an identifier is unavailable.

The matching process compares candidates with the retained target attribute values. The positive label identifies the target for evaluation and supplies its recorded fields. Candidate scores, rank, and labels are excluded from the discriminator except for defining the candidate budget and identifying the ground-truth target.

## Outcome measures

For Top-10, Top-20, Top-50 and the entire published DMR candidate set: report target coverage, available-target count, unique recovery, conditional unique recovery among available targets, and collision count. Report paired improvements from the original 530/600 unique joint-evidence recoveries, specifically the count of the original 70 unresolved cases resolved with each locator. Use 5,000 demonstration-cluster bootstrap replicates (seed `2026112207`) for the paired full-set gains.

## Interpretation boundary

The experiment uses one frozen webpage state per action. XPath and element IDs are evaluated against the same recorded candidate representation. Persistence across changed pages, independent browser event evidence, and reliability after a page reload require separate longitudinal or runtime experiments.

An exact target UID identifies the desired element by construction when that element remains in the candidate set. The UID result is an upper-bound diagnostic, not a general-purpose reconstruction method. Candidate omission remains relevant for Top-K even with perfect identity evidence.

## Data handling

The script writes aggregate JSON and an action-level metrics CSV with demonstration keys, turn numbers, candidate ranks, availability flags and counts. It exports no literal XPath, HTML ID, element UID, page content, URL, screenshots, or participant dialogue. The original WebLINX data remain in the publisher's repository.
