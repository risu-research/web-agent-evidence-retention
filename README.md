# Web-Agent Evidence Retention

Reproducibility code for **What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention** (TRUSTMORE 2026).

The study measures whether the target of a recorded web-agent action appears in the candidates available for later review and whether the retained text, semantic DOM, and visual evidence distinguish it from competing elements.

The confirmatory analysis uses 600 WebLINX actions from 55 demonstrations. With the top 10 DMR candidates, target coverage was 70.83% and end-to-end recovery was 69.17%. Joint evidence over the full released candidate sets uniquely identified 88.33% of targets.

## Camera-ready manuscript reproduction

Start with the [paper-to-code reproduction guide](docs/PAPER_REPRODUCTION.md), which maps every numbered paper table to its exact archived result, script, and successful full-data source run. The [offline artifact validator](scripts/verify_paper_artifact.py) checks the headline counts, 600 action-level storage records, the DMR-versus-Replay XPath distinction, and bootstrap point estimates without downloading data.

```bash
python scripts/verify_paper_artifact.py
```

The official WebLINX-full data remain with the publisher. The dataset has a [CC BY-NC-SA 4.0 license and additional terms](docs/DATASET_TERMS.md), separate from the MIT license for original code in this repository. Published outputs contain derived numeric and categorical records, without raw HTML, screenshots, sessions, or literal XPath values.

R5–R8B browser-runtime work is preserved here as exploratory extensions. The camera-ready paper's main quantitative tables use the frozen 600-action WebLINX cohort and the separately identified 598-action sensitivity study.

For the final archival package, use the [reviewed public release boundary](docs/RELEASE_REVIEW.md) to exclude raw source material and unrelated exploratory runs.

## Reproduce

Use Python 3.11 in a clean working directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
python scripts/reproduce_confirm.py
python scripts/verify_results.py out_confirm/confirm_summary.json
```

On Windows, activate the environment with `.venv\Scripts\activate`.

The confirmatory script downloads the official ranked candidates, replay files, and screenshots for the frozen dataset revision. It reconstructs the sample, compares evidence representations, and calculates clustered bootstrap intervals. The download is substantial.

The earlier fixed-action candidate-expansion analysis can be run separately:

```bash
python scripts/reproduce_universe.py
python scripts/verify_universe.py out_audit/universe_summary.json
```

That analysis uses an earlier, top-10-conditioned sample. Its results belong to a separate sensitivity test.

## Contents

- `scripts/reproduce_confirm.py`: final 600-action confirmatory analysis
- `scripts/reproduce_universe.py`: fixed-action candidate-expansion sensitivity
- `scripts/verify_results.py` and `scripts/verify_universe.py`: compare newly generated summaries with the frozen results
- `results/`: published aggregate reference tables
- `docs/protocol.md`: fixed data and experiment definitions
- `docs/provenance.md`: links to the original computation commits and successful runs

The frozen 600-action results and the separate 598-action sensitivity were independently rerun on clean GitHub runners. The successful source runs and their checksums are linked below.

## Source data

WebLINX is hosted by its original publisher. The scripts download the necessary records. Local raw data and generated outputs stay outside the versioned source tree.

The historical experiments were independently rerun on November 22, 2026. The resulting summaries and environment are preserved in [the reproduction record](docs/reproduction-2026-11-22.md). Machine-readable software citation metadata is now in [CITATION.cff](CITATION.cff). A permanent archive DOI will be added only after the final release is reviewed.

## Identifier retention baseline

The same 600 actions were tested with retained element identifiers. Within the published candidate sets, a stored DMR candidate `[[xpath]]` uniquely identifies all 600 targets; the original text, semantic DOM and visual evidence identifies 530. The conventional HTML `id` appears in 122 target descriptions and uniquely identifies 121. Exact UID matching gives the same-snapshot upper bound.

See [the baseline results](docs/identifier-baseline-results.md) and [the frozen method](docs/identifier-baseline-protocol.md). The script runs as:

```bash
python scripts/identifier_baseline.py
```

The script also writes an action-level metrics CSV with no literal locator strings. Its `out_confirm/confirm_summary.json` must match the original confirmatory experiment.

## Residual collision audit

The original joint-evidence experiment left 70 of 600 actions with multiple compatible targets. A complete action-level audit found 41 cases with valid visual-hash collisions, 19 cases with unavailable competing visual crops, and ten cases with both. In those cases, 308 competing candidates survived the original evidence rule.

Direct RGB-crop comparisons further separated 92 pixel-identical competitors from 69 candidates with equal perceptual hashes but different pixels. Another 63 had pHash distances from one to four; 84 lacked usable crops. Source-geometry checks traced those 84 crops to 41 boxes with a dimension of two pixels or less and 43 boxes clipped below three pixels within the screenshot. These categories account for every competing candidate.

The [full 70-case findings](docs/residual-failure-results.md), [frozen classification rules](docs/residual-failure-protocol.md), [pixel audit method](docs/residual-pixel-protocol.md), and [redacted case-level CSV](results/residual_70_pixel_cases_2026-11-22.csv) are available in this repository. The computation can be repeated with:

```bash
python scripts/residual_casebook.py
python scripts/residual_pixel_casebook.py
```

Both scripts use the frozen 600-action sample and reproduce the original confirmatory and locator-baseline results before producing the additional diagnostics.

## Measured retention cost

A full replay measured the actual encoded sizes of candidate text, semantic DOM, 64-bit pHash, exact same-state locators, the publisher's compressed screenshots, and generated lossless PNG element crops. Recovery was checked by decoding each retained record across the same 600 actions.

Adding pHash only where semantic evidence is ambiguous takes **792,980 bytes** and identifies **530/600** targets. A text → semantic → pHash → bounding box → XPath record takes **862,427 bytes** and identifies **600/600** within the frozen candidate snapshots. A complete candidate XPath list with the recorded target XPath takes **621,808 bytes** and also identifies all 600.

The selective lossless-crop variant takes **309,543,191 bytes** and identifies **545/600**. Original compressed screenshots plus candidate descriptions and box coordinates take **206,275,510 bytes** using the original pHash recovery rule.

The [full measured results](docs/storage-cost-results.md), [frozen comparison protocol](docs/storage-cost-protocol.md), and [600-action numeric measurement table](results/storage_cost_600_actions_2026-11-22.csv) retain the exact costs and their interpretation.

```bash
python scripts/storage_cost_casebook.py
```

The code retrieves source images from the original publisher and exports derived numeric records. The Zenodo release remains scheduled for the final artifact audit.

## Consecutive-state source verification

The [R1 source inventory](docs/weblinx-continuity-r1-results.md) independently retrieved the 55 original WebLINX demonstration replays underlying the frozen 600-action cohort. There were 1,125 adjacent browser-state pairs with directly recorded HTML on both sides. The protocol fixed 165 source pairs, three from each demonstration, before inspecting their HTML bytes.

The [R2 source verification](docs/weblinx-continuity-r2-results.md) retrieved 233 pinned HTML files and parsed all 165 pairs. Twenty-six pairs contained identical HTML bytes despite different filenames. In 139 byte-changed pairs, 84 contained at least one identical XPath mapped to a different dataset UID. This also occurred in 34 of 88 byte-changed pairs with the same recorded URL hint.

These values measure syntactic changes between real recorded DOM snapshots. Neither dataset UID repetition nor a stable-looking XPath is an independently verified cross-state logical-element label. The next experiment requires independent target linkage before estimating incorrect identification or browser execution outcomes.

Both R1 and R2 were fully repeated with byte-identical artifacts. The public source scripts are:

```bash
python scripts/weblinx_continuity_r1.py
# Use its pinned 165-pair CSV as out_continuity_r1/source_pairs_frozen.csv
python scripts/weblinx_continuity_r2.py
```

The R1/R2 workflows, complete numeric casebooks, original replay digests, and immutable source revision are retained in this repository. No release or Zenodo DOI was issued.

## Round 4: native-ID reference overlap and independent semantic evidence

The [Round 4 audit](docs/weblinx-continuity-r4-results.md) identified a critical validity constraint on the R3C/R3D source-proxy experiment. In all **75** previously reported native-ID proxy matches, the captured Replay XPath is precisely `id("target-html-id")` with no suffix, and the proxy criterion requires the same ordinary HTML `id` to be unique in the next snapshot. Accordingly **75/75 captured XPath matches follow by construction**, and the earlier 8/75 difference from the canonical DMR absolute XPath is a **source-proxy comparison**, not independently measured logical-element robustness.

A [blinded non-ID source matcher](scripts/weblinx_continuity_r4.py) then checked original vs next HTML using only unique text, link destinations, form metadata, test fields and accessible labels. Within those same 75 cases, **22** had two or more separate matching semantic families, **39** had one, and **14** had none; no unique non-ID channel pointed to a conflicting node. All eight previous generator-disagreement cases had non-ID corroboration (three multi-family, five single-family). The separate 11 original action XPath source discrepancies had four uniquely descriptive source targets and seven without a unique non-ID cue.

These findings assess source evidence and construct dependence. The next validity gate remains independently adjudicated target identity or instrumented browser event-delivery records. No manuscript, GitHub release or Zenodo DOI was created as part of the Round 4 audit.

## Recorded action provenance and XPath generator comparison

[Round 3](docs/weblinx-continuity-r3-results.md) rechecked the same 600 original candidate targets against Replay action-element annotations and directly recorded HTML. All 600 target UIDs agreed with the Replay action element and resolved to exactly one element in their source HTML. The DMR candidate XPath equaled the parser-generated source XPath in all 600 actions.

The action-element XPath used a different representation: 568 of 600 began with an XPath `id(...)` function. Executing the actual captured expressions on the original HTML selected the recorded element in **589** actions, selected no node in ten and a different node in one. The [focused source audit](docs/weblinx-continuity-r3d-results.md) traced seven mismatches to absent root IDs and four to a present root whose full path failed.

The next-source audit included 560 directly linked HTML files and 413 changed-page pairs. Among 75 **site-native-id continuity proxies**, original captured action XPath expressions selected the proxy in **75/75** next snapshots; the DMR canonical XPath selected it in **67/75**. The 75 proxies span 31 demonstrations. This comparison is exploratory and does not supply independent logical-element ground truth or actual browser event delivery.

See the [captured-expression study](docs/weblinx-continuity-r3c-results.md), [paired generator audit](docs/weblinx-continuity-r3d-results.md) and [cluster uncertainty](results/weblinx_continuity_r3d_cluster_bootstrap.json). Original source records and executable scripts remain pinned. The manuscript and Zenodo release were left unchanged.

## Round 5A: observed browser event delivery and effects

The [Round 5A live-browser study](docs/weblinx-round5a-live-browser-results.md) completed 72 actual trusted Chromium clicks across **two controlled first-party fixture layouts**, twelve frozen mutation or handler scenarios, and three locator styles. The source protocol was fixed before the successful browser results. All 72 numeric records and their serialized-byte totals were independently repeated byte-for-byte.

**30/72** episodes changed the intended fixture record, **six** changed the wrong record and **36** made no state change. These conditions were intentionally balanced to include engineered failures; this is **not** an agent-production error-rate estimate. Of 54 returned Playwright operations, six changed the wrong record and eighteen returned with no state change. Separate document-capture, application-handler and state/render readbacks explain the differences, including nested-event targets and bypassed actionability with forced clicks.

The experiment measured compact event and effect log payloads: **5,500 bytes** for request-only and **13,564 bytes** for request+trusted-event+handler+state/render log packets over all 72 episodes, with per-episode zlib level 9 compression. These packets are not equivalent in coverage to a Playwright Trace.

- [Frozen and amended source protocol](docs/weblinx-continuity-r5a-protocol.md)
- [Complete results and interpretation](docs/weblinx-round5a-live-browser-results.md)
- [Actual Chromium experiment runner](scripts/weblinx_round5_live_browser.py)
- [72 verified episodes](results/weblinx_round5a_browser_cases.csv)
- [Results and bytes summary](results/weblinx_round5a_browser_summary.json)
- [Successful full run 1](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45060903027)
- [Successful full run 2](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45060914497)

The applications are synthetic testbeds and the second is a layout holdout; the experiment does not re-execute WebLINX recordings or measure a real externally maintained application's authoritative effects. Future work must compare an external app/event or server-state oracle and a real Playwright Trace. No Zenodo DOI or paper revision was made during R5A.

## Round 5B: externally maintained Flaskr with independent SQLite effects

The [Round 5B-1 report](docs/weblinx-round5b-flaskr-results.md) uses the original **Flaskr** blog application maintained by [Pallets Flask](https://github.com/pallets/flask/tree/49943b5a94413a530761350f04e896f76e8d620e/examples/tutorial/flaskr), pinned at Git commit `49943b5a94413a530761350f04e896f76e8d620e`. The backend source is unchanged. The harness runs 48 independent authenticated browser sessions, Flask server instances and SQLite databases, crossing two genuine post operations, three locator methods and eight controlled DOM interventions.

In 48 operations, the separately read committed database outcome was **A changed 16, B changed eight, neither changed 24**. Twelve Playwright first-click operations returned normally despite no stored effect. Crucially, among eight wrong-B database effects, four followed a trusted click on the visible A article's Edit link, because source article identity and link destination can differ. Two correct A effects followed a click on the visible B article's link. Browser event, server route and committed database effect therefore answer different questions.

The same 48 episodes were captured using genuine Playwright Trace ZIPs with DOM snapshots and network records. Measured baseline Trace ZIPs totaled **343,784 bytes**; purpose-built request+event+server+SQLite-effect packets totaled **10,123 bytes** when each was zlib-compressed independently. The information coverage differs, so the size ratio is descriptive rather than a matched evidence-equivalence claim.

Two full external Flaskr source runs matched all 48 action/SQL outcomes across **31 comparable fields**. Trace ZIP byte totals changed slightly across runs (**343,784** and **343,294**), and this source variation is retained separately from result reproducibility.

A distinct [six-case Flaskr server-validation negative control](docs/weblinx-round5b2-server-rejection-results.md) used the real original Flaskr title-required check. **Six genuine HTTP POST requests received HTTP 200 with the validation message and left SQLite entirely unchanged.** The server source remained unmodified, and only the browser's client-side `required` constraint was removed for this controlled test.

- [R5B-1 pinned protocol](docs/weblinx-round5b-flaskr-protocol.md)
- [R5B-1 source code](scripts/weblinx_round5b_flaskr.py)
- [Full 48-case SQL-linked casebook](results/weblinx_round5b_flaskr_cases.csv)
- [R5B-1 complete results and actual Trace byte metrics](results/weblinx_round5b_flaskr_summary.json)
- [R5B-1 independent repeat comparator](scripts/weblinx_round5b_compare.py)
- [R5B-2 protocol](docs/weblinx-round5b2-server-rejection-protocol.md)
- [R5B-2 source code](scripts/weblinx_round5b2_server_rejection.py)
- [Six original server rejection cases](results/weblinx_round5b2_rejection_cases.csv)

These are controlled interventions on one genuine externally maintained educational application. They establish distinguishable evidence channels and actual authoritative SQL effects, without yielding a real-world agent error frequency or a general conclusion about the adequacy of Playwright's existing Trace. Raw Trace ZIPs and dummy login sessions are not released. These browser-runtime findings remain exploratory and outside the current paper's primary candidate-recovery tables; no new DOI was issued for them.

## R6: second independent Django web application and actual Trace audit

A second [third-party maintained web app](docs/weblinx-r6-django-trace-results.md) now replicates the R5B experimental taxonomy on **unmodified Django Admin user management**, pinned to Django 5.2.12 and official source commit `4f382ca672f86dd4a1e4d071c91d0caad0e124b3`. The complete study executes **48 native user edit/delete tasks** in new SQLite databases, WSGI server instances and real Chromium contexts. Django uses a distinct framework and codebase from the earlier Flaskr app.

Both 48-case experiments found **16 intended stored effects, eight other-record effects and 24 no-change outcomes** under the deliberately imposed conditions. These are controlled interventions, not real-world failure rates. In each codebase, six cases differed between the visually clicked row and the actual database row affected. All validated source actions and actual SQLite changes were independently reproduced.

The [direct parsed-Trace audit](results/weblinx_r6_audit_matrix.json) scored **five evidence questions** across all 48 Django trials. Actual Playwright Trace recorded the attempted selector, first-click return/error result and server POST route in **48/48**, with **48/48 exact agreement** against independent API and WSGI observations for the latter two. Native Trace does not itself contain an independent `isTrusted` receiver observer or a separate SQLite-state oracle; compact event and SQL readback packets recorded those respective facts. Trace DOM snapshots can support human inference and were not exhaustively decoded in the conservative machine-readable-field audit.

The two complete Django runs recorded source SQL and audit outcomes identically, including all 48 cases across **36 nonvolatile categorical and packet-size fields**. Actual Trace ZIP size varied: **1,651,341 bytes** and **1,655,144 bytes**; the first run's request+event+server+SQL compact packets totaled **7,334 bytes** compressed per-episode. This is a descriptive comparison of **different information scopes**, not an equal-function compression claim.

- [Frozen R6 protocol and all excluded calibration attempts](docs/weblinx-r6-django-trace-protocol.md)
- [Full R6 scientific results](docs/weblinx-r6-django-trace-results.md)
- [Django runner including original Trace ZIP JSONL parsing](scripts/weblinx_r6_django_trace.py)
- [Original 48 Django casebook](results/weblinx_r6_django_cases.csv)
- [Original aggregate and source hashes](results/weblinx_r6_django_summary.json)
- [Five-question strict direct-evidence analysis](results/weblinx_r6_audit_matrix.json)
- [Independent full rerun comparison](results/weblinx_r6_independent_repeat.json)

All synthetic test material and derived categorical data are public. The original browser Trace ZIP files, disposable credentials and sessions are not distributed. The independent runtime repetitions remain separately documented; no new DOI was issued for these experiments.

## R7: real DOM snapshot auditor against selective evidence tiers

The [R7 frozen blind auditor study](docs/weblinx-r7-dom-auditor-results.md) **reconstructed the original Playwright DOM snapshots**, including historical subtree references, before comparing independent server/SQLite truth. The [actual source decoder](scripts/weblinx_r7_trace_dom_auditor.py) reads native `frame-snapshot` node arrays and prior-node references rather than guessing from plain Trace JSON. The source viewer recovered 1,088/1,088 DOM snapshots and 14,825 historical subtree references with zero parsing failures in its original full 48-case Django study.

This changed the earlier **Round 6 strict explicit-evidence** interpretation: with real DOM reconstruction, a **Trace-only** auditor inferred the visible clicked user row and ultimate changed SQL-row label correctly in **48/48**, matching native independent event and SQLite truth for this controlled app. Trace's native network POST route and Playwright first-click status were likewise correct **48/48**. Selective event, server and DB packets also answered all questions correctly when given the necessary actual observations.

The **two full source-execution repetitions** agreed on all 48 case results and 50 stable categorical fields per case, with zero disagreements. The two actual browser Trace ZIP sets used 1,655,362 and 1,654,963 bytes. The original first run's request/event/server/SQL packet used 7,290 bytes compressed in total (zlib level 9 per case). These different artifacts carry different information scopes; the size contrast is descriptive, not an equal-function compression claim.

**Critical distinction:** The reconstructed Trace predicts the database effect **from final browser DOM state**. A separate SQLite query in the retained effect packet records the actual committed state. Those yield the same answers in R7's 48 deliberately controlled tasks, but their source provenance and evidentiary guarantees differ. The 48-case experiment does not demonstrate an accuracy advantage for selective evidence over full native Playwright Trace, nor does it include blinded human reviewers or production agent error-rate evidence.

- [Full R7 result and implications](docs/weblinx-r7-dom-auditor-results.md)
- [Actual raw Trace DOM decoder](scripts/weblinx_r7_trace_dom_auditor.py)
- [Independent auditor runner](scripts/weblinx_r7_compare_auditors.py)
- [Individual original 48-case predictions and truth](results/weblinx_r7_DOM_vs_packets_48.csv)
- [All 5 question-category scores and actual byte costs](results/weblinx_r7_DOM_vs_packets_summary.json)
- [Independent 48-case/50-field repeat comparison](results/weblinx_r7_independent_repeat.json)

These exploratory runtime measurements are kept separate from the camera-ready paper's quantitative tables. No archival DOI was issued for this experiment.


## R8B: browser-equivalent workflows with different hidden server effects

The [R8B prospectively corrected paired experiment](docs/weblinx-r8b-transactional-results.md) follows R7's finding that reconstructing full Playwright DOM snapshots lets a Trace-only auditor correctly infer all 48 original Django outcomes. R8B tests a distinct, predeclared question: whether a browser observer can attest a *server-side field never shown in the observed workflow*.

Using the **original unmodified Django 5.2.12 Admin** forms, the harness completes real edit/delete operations on dummy user A. An explicitly disclosed experimental WSGI boundary issues a separate after-response SQL update to dummy user B's **non-displayed** `last_login` field. The control updates it to its original NULL; the paired shadow mode writes a fixed synthetic timestamp. Both modes issue the same SQL statement and leave the native A operation unchanged.

Across **six matched pairs (12 original browser episodes)**, pre/post screenshot pixels, reconstructed initial/final A/B list DOM, the R7 Trace auditor's Q1–Q5 answers and the ordered **account-related HTTP transaction** records agreed. An independent SQLite connection detected the hidden B effect difference in **all six pairs**. For the new Q6, the conservative Trace-only auditor abstained on all 12 episodes, and the independently observed SQLite effect packet answered all 12 correctly. A second full original-app execution reproduced all verdicts, with **zero differences in 16 stable fields per case (192 paired field checks)**, and zero DOM decoder failures.

This is a **constructed observation-boundary test**, not a naturally occurring Django bug or an observed production error rate. The packet succeeds because it retains an additional privileged SQL observation. The **entire raw Trace ZIPs are not identical**: Django auxiliary translation-resource requests varied (full `/admin/` network projection equal in 5/6 pairs and 4/6 pairs across the two runs), and those differences remain reported. The earlier stricter R8 full-network equivalence calibration **failed** and was preserved as failed evidence. R8B was separately preregistered before its validated source runs. This result complements R7's strong Trace baseline.

Research sources: [R8 strict failed calibration protocol](docs/weblinx-r8-server-divergence-protocol.md), [R8B prospectively frozen protocol](docs/weblinx-r8b-transactional-protocol.md), [full R8B results and limitations](docs/weblinx-r8b-transactional-results.md), [original browser and SQL runner](scripts/weblinx_r8_server_divergence.py), [R8B network comparator](scripts/weblinx_r8b_transactional.py), [12 verified case outcomes](results/weblinx_r8b_transactional_12_cases.csv), [source aggregate](results/weblinx_r8b_transactional_summary.json), and [two-run SHA-256 and stable-field comparison](results/weblinx_r8b_independent_repeat.json).

This controlled server-effect experiment is retained as an exploratory extension, outside the camera-ready paper's numerical tables. No archival DOI was issued for this round.
