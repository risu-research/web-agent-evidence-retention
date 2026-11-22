# R8B: matched visible browser outcomes with different committed server effects

**Scientific status: two independent full original Django/Playwright runs passed the separately frozen R8B protocol, November 22, 2026.** The original strict R8 calibration attempts remain failed and visible. No main-paper or Zenodo changes.

## Source and design

R7 found that decoding full Playwright DOM snapshots permitted correct browser-based inference of all 48 original Django workflow outcomes. R8B asks a narrower follow-up: what happens when a server effect is outside the observed browser trajectory?

The genuine upstream Django 5.2.12 Admin user-management view, forms and `auth.User` model are unchanged. A test-only WSGI response-boundary wrapper executes a second raw SQLite UPDATE on dummy user B after Django has handled an authorized native edit or delete POST for user A. Both modes issue the same SQL statement on B's `last_login` column. **Control** binds the initial NULL; **shadow** binds a fixed synthetic date. The standard user-list page displays A and B usernames and first names, including the authorized A effect, but does not display B's `last_login`.

Six matched pairs cross two native A operations (edit/delete) and the three R6/R7 tested locators (positional, original href exact, contextual row). Each pair executes control and shadow on separate fresh servers, browsers and SQLite databases. The source Trace auditor receives only the actual original Playwright Trace ZIP and static A/B IDs. The selective packet auditor receives a separately measured pre/post SQLite B value. Independent SQL truth is joined after both auditors emit answers.

The [original strict R8 protocol](weblinx-r8-server-divergence-protocol.md) compared the complete ordered `/admin/` network sequence including translation-resource requests. Its calibration runs 45068631082, 45068796349, 45068811353 and 45068961921 were **not scientifically accepted**. Investigating their network records revealed an auxiliary `GET /admin/jsi18n/` sometimes completed with status 200 and sometimes was canceled with native status -1 during navigation. The [separately prospective R8B protocol](weblinx-r8b-transactional-protocol.md) therefore compares the ordered user-list and user-edit/delete transactional HTTP sequence, while separately reporting the auxiliary request differences. A rare form-navigation race in an initial R8B attempt was corrected by waiting for the original native edit form to become visible. This is disclosed as an instrument calibration. A complete R8B run with the earlier timing code also passed; the two published source runs use the same calibrated code.

## Two verified complete executions

| Verification item | Original complete R8B run | Independent complete R8B rerun |
| --- | ---: | ---: |
| Genuine original Django browser episodes | 12 | 12 |
| Matched control/shadow pairs | 6 | 6 |
| Pairs with identical before/after rendered screenshot SHA-256 hashes | 6/6 | 6/6 |
| Pairs with identical initial/final A/B native user-list DOM | 6/6 | 6/6 |
| Pairs with identical ordered user-list/edit/delete HTTP transaction records | 6/6 | 6/6 |
| Pairs with equal **entire** ordered `/admin/` network projection | 5/6 | 4/6 |
| Pairs with differing independent SQLite B field effect | 6/6 | 6/6 |
| Full R7 Trace auditor Q2 (clicked row A), Q3 (mutation POST A), Q4 (visible A effect), Q5 (click returned) | 12/12 each | 12/12 each |
| Trace-only Q6 (hidden B `last_login` effect) | 12 abstain | 12 abstain |
| Separate SQLite packet Q6 | 12/12 correct | 12/12 correct |
| Successfully decoded real Playwright DOM snapshots | 316 | 320 |
| Historical DOM subtree references resolved | 6,578 | 6,619 |
| Decoder failures | 0 | 0 |
| Original native Trace ZIP byte totals | 484,202 | 482,830 |

The first full R8B run's 12 Q6-specific SQLite observation packets totaled **1,242 compressed bytes** (canonical JSON, zlib level 9 per episode). This narrow value packet holds an independently recorded field missing from the browser's observed workflow. The Trace and packet preserve *different scopes of information*, so their sizes are descriptive and not a same-function compression benchmark.

The two verified full runs were:

- [Original completed source run 45069326392](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45069326392).
- [Independent completed source run 45069329684](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45069329684).

Both source artifact SHA-256 manifests were checked before publication. Their **16 stable categorical fields across each of 12 cases** were compared pairwise, giving **zero disagreements in 192 field comparisons**. Snapshot counts, compressed Trace byte sizes and auxiliary network timing were allowed to vary and have been reported as such.

## What the contrast demonstrates

For every control/shadow pair, the tested before/after visible page pixels, source A/B list cells, R7 Trace audit answers and relevant account HTTP transaction sequence agreed. Both variants completed the authorized A effect. Only the shadow branch caused an additional B `last_login` state difference, confirmed through a fresh independent SQLite connection.

The R7 auditor continues to infer A's visible effect correctly. For the new question, whether B's hidden value was changed, its conservative browser-only policy **abstains**. The full packet answers from its separate SQL sensor. On the disclosed relevant browser/HTTP projection, a deterministic function must produce the same answer in both branches despite the branches' different truth values. This is an empirical constructed counterexample to relying on that projection alone for the additional server-side question.

The comparison does **not** show that the entire raw Trace ZIP archives are byte-identical. Raw session tokens, timing, request cancellations and trace-internal IDs can differ. The original R8 strict result was accordingly rejected, and R8B reports the auxiliary translation-resource differences explicitly. A human auditor, a statistical timing classifier over raw traces, and an adversary who can browse B's separate admin edit page were not tested.

The hidden extra effect is deliberately introduced by the disclosed independent test wrapper, not discovered as a vulnerability or naturally occurring Django behavior. The six pairs are constructed tests with deterministic ground truth, not samples for estimating production error rates. A selective packet's advantage on Q6 follows from access to the independently measured DB field. It is an advantage of **additional trusted observation**, not better prediction from equal evidence.

## Reproduction and public integrity

- [R8 strict source protocol](weblinx-r8-server-divergence-protocol.md) and [its exact native runner](../scripts/weblinx_r8_server_divergence.py)
- [Separately frozen R8B protocol](weblinx-r8b-transactional-protocol.md) and [the corrected transactional comparator](../scripts/weblinx_r8b_transactional.py)
- [Original R7 full DOM Trace reader](../scripts/weblinx_r7_trace_dom_auditor.py)
- [R8 tests](../tests/test_weblinx_r8_server_divergence.py) and [R8B comparator tests](../tests/test_weblinx_r8b_transactional.py)
- [Original complete 12-case derived audit results](../results/weblinx_r8b_transactional_12_cases.csv)
- [Full source summary, all equivalence gates and auxiliary network differences](../results/weblinx_r8b_transactional_summary.json)
- [Independent rerun, 16-field equality audit and both SHA-256 manifests](../results/weblinx_r8b_independent_repeat.json)

The source-run manifest and result-file SHA-256 values are in the independent-repeat JSON. Raw source Trace ZIPs, screenshots, cookies, synthetic test credentials and raw DOM snapshots were used in the ephemeral runs and not uploaded.

**Research implication:** This controlled pair establishes a boundary between browser-observed effects and independently attested server changes. It complements R7's positive Trace finding. Incorporation into the main manuscript requires a careful distinction between constructed observation gaps, naturally occurring effects, and the incremental value of retaining a purpose-selected independent source. No manuscript or Zenodo DOI changes have been made.
