# R6 — A second independent web application and a real Playwright Trace audit

> **Round 7 DOM-reconstruction follow-up (November 22, 2026).** The earlier 0/48 Trace counts below refer only to **explicit independent `isTrusted` receiver and SQLite-oracle records**. A subsequent [actual DOM snapshot auditor](weblinx-r7-dom-auditor-results.md) reconstructed Playwright's compact DOM snapshots and predicted both the clicked row and eventual SQL-effect label correctly in **all 48 fixed Django cases**. Its answers were independently verified against the native event and SQLite measurements, then exactly reproduced in a second complete execution. This materially strengthens the Playwright Trace baseline. Browser-visible inference and independent event/SQL attestation remain different evidence sources.

**Scientific status:** Complete fixed 48-case Django admin experiment, two independent source runs, real Trace ZIP parsing, all five questions scored; no main-paper or Zenodo changes.

## Original source and preregistration

The previously published [Flaskr R5B study](weblinx-round5b-flaskr-results.md) uses an externally maintained Flask application. R6 uses the **standard Django Admin user-management application** and Django's original `django.contrib.auth.models.User`, developed and maintained by a different project. Django is pinned to **5.2.12** and to signed upstream tag commit `4f382ca672f86dd4a1e4d071c91d0caad0e124b3`. The runner's source workflow downloads the exact upstream `django/contrib/auth/admin.py` and `django/contrib/admin/options.py` files and verifies byte-for-byte agreement with the installed Django distribution.

The Django admin model, backend routes, forms, views and templates were **not patched**. The test harness sets up a disposable Django project, installs standard Django admin/auth middleware and templates, creates three dummy accounts and two audit target user rows in SQLite, and runs the original application with a WSGI server.

The [R6 source protocol](weblinx-r6-django-trace-protocol.md) froze the experimental matrix and audit questions before any browser trial: **two operations** (native user edit and delete), **three first-link locators** (positional, original `href` exact, contextual row), and **eight browser-only DOM conditions** (baseline, row reorder, href swap, target removal, duplicate labeled row, standard pointer blocker, forced pointer blocker and prevented default navigation). The intended account is A, with B as a distractor. Every episode has a fresh database, server and Chromium context.

This is **48 designed tests**, not a natural frequency sample. The main click opens Django's original change form, and the harness follows through with the real Save or Delete confirmation form. The final SQL effect is attributed to the entire click-plus-form workflow.

### Integrity corrections before publication

R6 encountered three instrumentation problems before any valid source result: (1) Django ORM seeding cannot run on Playwright's sync event-loop thread, (2) native Django admin user links can use relative `href` attributes, and (3) an element-sized fixed overlay can move relative to the clicked element during scrolling. The first failed run `45064250360` was blocked during setup. Runs `45064424365`, `45064691419` and `45064708238` failed the preregistered baseline or overlay negative controls and were rejected. These invalid runs were excluded **before scientific result acceptance**.

The harness now seeds through Django's original ORM in a dedicated synchronous Python worker thread, reads the unmodified A link's exact `href` from the initial browser DOM before mutation, and uses a full-viewport pointer shield verified by `elementFromPoint`. This leaves all 48 originally fixed cases, source code, actions, SQL oracle and audit questions unchanged. The first two **control-passing** independent source runs are [45064967915](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45064967915) and [45064981005](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45064981005).

## Two independent original-app experiments

| Workflow's authoritative effect | Flaskr R5B, 48 controlled trials | Django R6, 48 controlled trials |
| --- | ---: | ---: |
| Intended A record updated/deleted | **16** | **16** |
| Wrong B record updated/deleted | **8** | **8** |
| No stored change | **24** | **24** |
| First click returned normally, but no stored effect | **12** | **12** |
| Trusted event's visible record differs from eventual stored record | **6** | **6** |

In the R6 source runs, the first Playwright click returned in 36 cases, timed out in ten, and encountered locator ambiguity in two. Baseline conditions succeeded 6/6, normal pointer-overlay conditions made zero changes 6/6, and explicit forced overlay clicks returned but made zero changes 6/6.

The same outcome counts in Flaskr and Django arise from the **same preconstructed test matrix and deliberate interventions**, applied to independent web frameworks. They replicate the failure mechanisms under distinct backend implementations; they are not two independent random samples of production errors.

The externally captured trusted event belonged to a visible A row in 24 cases, B in six and no source row in eighteen. In six href-swap cases the visible event row and authoritative changed SQL account differed:

| Trusted click's visible row | DB A changed | DB B changed | No change |
| --- | ---: | ---: | ---: |
| A | 14 | **4** | 6 |
| B | **2** | 4 | 0 |
| No source-row click recorded | 0 | 0 | 18 |

A raw trusted click receiver is a real observation of a browser event, but it does not by itself identify the data record that a link's destination or eventual server POST modifies.

## Raw Playwright Trace parsing was performed

For every one of the 48 Django episodes, the harness recorded a genuine Playwright `context.tracing` ZIP with `snapshots=True`, `screenshots=False`, and `sources=False`. It **opened the ZIP** and parsed `.trace` JSONL action records and `.network` request records while the ZIP existed locally. It then destroyed the ZIP with the disposable episode directory. Raw trace resources and local login cookies are absent from this public artifact.

The Trace parser has access only to that original ZIP and static A/B record-ID mappings. It does not receive the WSGI event list, separate SQLite state or the final outcome table. The WSGI and SQL measurements are joined later for validation.

First successful Django run:
- **48/48** first clicked selector expressions are present in direct Trace action parameters.
- **48/48** first-click return/error states are recoverable from the before/after action stream, and all **48/48** match the Playwright API-level outcome.
- **48/48** direct Trace network POST classifications (A, B, none) match independently observed Django WSGI HTTP request routes.
- **9,040** Trace action/snapshot/log records and **3,785** network records were parsed across all 48 ZIPs.

This verifies that Playwright **already captures** meaningful selection, action-status and network-routing evidence. It must be treated as a strong comparator, not a deficient baseline by assumption.

## Five independently defined audit questions

The [auditor implementation](../scripts/weblinx_r6_audit_matrix.py) compares five direct-evidence questions, preserving abstention and the distinction between observed proof and inference.

| Question | Trace directly records the answer | Supplementary evidence channel |
| --- | ---: | ---: |
| Q1. Which click selector was invoked? | **48/48**, exact expression retained in trace | 48/48, compact request stores locator kind |
| Q2. Which visible row received an actual `isTrusted` click? | **0/48 explicitly authenticated event rows** | 48/48 observer records event row or verifies no such event |
| Q3. Which user mutation route received a POST, if any? | **48/48 correct**, compared with actual WSGI | 48/48 actual WSGI log |
| Q4. Which account was independently proven changed in SQLite? | **0/48 explicit SQLite oracle records** | 48/48 new `sqlite3.connect` readback |
| Q5. Did first Playwright locator action return or error? | **48/48 correct**, compared with API result | 48/48 recorded API result |

**Scope of the zeroes:** Standard Trace snapshots and action records may support reconstruction of a visible UI state or an inferred click recipient. This study uses a **strict direct-source criterion** for trusted events and independently authenticated stored SQL. It does not conduct blinded human review of Trace screenshots or a complete reconstruction of all DOM snapshot references. Hence zero explicit `isTrusted` records and zero independent SQL oracle records are **not** general claims that a reviewer could learn nothing about those questions from a Trace.

The additional SQL evidence comes from a **privileged readback** unavailable to an ordinary browser-only trace. It would be misleading to attribute the information difference to better compression alone.

## Actual evidence retention bytes

Each compressed packet is compact JSON, independently zlib-compressed at level 9 per episode. The progressively retained packets append observed event, then WSGI server, then independent SQLite effect. Both Trace totals are real compressed ZIP files measured for the **identical 48 episodes within each app**.

| App and evidence packet | Measured compressed bytes across 48 |
| --- | ---: |
| Flaskr intent/request packet | **4,286** |
| Flaskr + trusted event | **6,228** |
| Flaskr + server request | **8,181** |
| Flaskr + SQLite result | **10,123** |
| Flaskr full Playwright Trace ZIP baseline | **343,784** |
| Django intent/request packet | **3,909** |
| Django + trusted event | **5,153** |
| Django + server request | **6,286** |
| Django + SQLite result | **7,334** |
| Django full Playwright Trace ZIP baseline | **1,651,341** |

These packet/trace byte sizes are **not functionally equivalent**. Playwright Trace retains extensive DOM snapshots, logs, network details and selectors beyond the five narrow questions. The purpose-built packets add authoritative server and SQL observations unavailable in a browser-only trace. The measured sizes are descriptive of these exact configurations and support an audit-question-specific recording policy, not a claim of matched functionality or universal performance.

## Independent full rerun

Both control-passing Django runs regenerated all 48 categorical event/WSGI/SQL outcomes and byte sizes of the small JSON evidence packets exactly. Reproducibility was checked by [the independent run comparison code](../scripts/weblinx_r6_compare.py), with every per-action field compared except actual Trace ZIP byte count and trace/network line volumes.

The **first run** generated 1,651,341 total Trace ZIP bytes, 9,040 trace records and 3,785 network records. The independent **second run** generated 1,655,144 ZIP bytes, 9,161 trace records and 3,834 network records. Both had direct Trace/WSGI POST concordance **48/48**. All real outcomes were unchanged. Trace byte and record count variability remains in the released reproducibility report.

## Reproduction and interpretation

- [Frozen R6 protocol, including rejected calibration runs](weblinx-r6-django-trace-protocol.md)
- [Pinned Django source and full live browser runner](../scripts/weblinx_r6_django_trace.py)
- [First valid 48-case raw-Trace-derived source output](../results/weblinx_r6_django_cases.csv)
- [Original source checksums, counters and packet sizes](../results/weblinx_r6_django_summary.json)
- [Five-question independent-answer audit](../results/weblinx_r6_audit_matrix.json)
- [All 48 audit-question verdicts](../results/weblinx_r6_audit_cases.csv)
- [Independent two-run source comparison](../results/weblinx_r6_independent_repeat.json)
- [Successful original Django full run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45064967915)
- [Successful independent complete repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45064981005)
- [Earlier Flaskr first-app source results](weblinx-round5b-flaskr-results.md)

The public records contain only synthetic case IDs, source pinned code/versions, numeric result categories, task condition labels and byte measurements. Upstream framework sources are downloaded from their official repository. No original user data, website cookies, raw browser Trace ZIPs, or unredacted DOM content are published.

### Scientific gate

R6 now completes a **second external maintained codebase** with real browser events, real server handling, independent SQL effect proof and authentic Playwright Trace inspection. The five-question study shows both what native Trace already captures and what additional event/SQL observation buys. A matched **blinded human or reference reconstruction of Trace DOM snapshots**, plus a new web app or natural trajectories, would be necessary for broader claims about minimal sufficient evidence and human audit capability. Until then, preserve the accepted manuscript's core same-state evidence results and treat R5B/R6 as source-grounded supplementary studies.
