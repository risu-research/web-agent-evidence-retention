# R8 prospective protocol: browser-equivalent episodes with divergent persisted effects

**Design fixed before any R8 live browser execution, November 22, 2026.**

## Scientific question

Can two executions of an unmodified externally maintained web app produce the same *observed browser trajectory* and Playwright Trace audit answers while differing in a database effect not included in that trajectory? This follow-up builds on the R7 finding of 48/48 correct outcomes using actual reconstructed DOM snapshots. R7's 48 cases and results remain frozen.

This is a controlled **observation-boundary demonstration**, not a frequency estimate or a newly discovered Django vulnerability. The extra write is deliberately inserted by a disclosed experiment-only server wrapper, after the original Django response has been computed. Its purpose is to test which evidence source can resolve a specified server-side question. Only trace-observable equality can be claimed, never bit-for-bit equality of raw traces from fresh sessions.

## Original application and independent effect

- Application: upstream Django 5.2.12, normal `django.contrib.admin` user change/delete forms, auth model and SQLite schema, with the same source verification and R6 setup. No Django source, admin form, model, or template changes.
- A is the intended dummy user `r6_a`. B is the other dummy user `r6_b`. The original admin user changelist shows username, first name, last name, email and staff status, but not B's `last_login`.
- The native browser action changes or deletes A through the original Django admin UI. An experiment-only WSGI boundary observes the successful POST to A after the upstream app returns its response. The wrapper then runs a separate SQLite UPDATE on B's `last_login` before returning that response to the browser. In **control**, the UPDATE binds NULL, preserving B's original NULL value. In **shadow**, the same UPDATE binds a fixed synthetic date. The wrapper uses the same SQL statement and route for both modes.
- The browser never receives a mode flag, backend-SQL values, or a special fixture endpoint. Both cases use independent fresh server, browser context and SQLite file; no shared browser cache or stale trace data.
- The hidden state is checked by a separate fresh read-only SQLite connection after final browser navigation. It is never read by the Trace-only auditor.

## Fixed design and ordering

Two native operations (edit A first_name; delete A) × three already tested R6 link locators (positional, exact original href, contextual user row) × two server modes (control, shadow) = **12 executions, six predeclared matched pairs**. Each pair contains both server modes; reverse mode order on alternating pairs. No original R7 DOM perturbations are added, so the source GUI workflow is normal. The value used to edit A is fixed across all modes.

First run a separate smoke validation to ensure that all six control cases change/delete A, the six shadow cases do the same, the injected B mutation is triggered exactly once per shadow case, and there are no unexpected writes. Reject the full run as an **instrument failure** if any gate fails; report the failed run. Do not exclude individual pairs.

## Predeclared audit views and questions

**T: native Playwright Trace-only.** Receive only a genuine per-episode Trace ZIP recorded from before the initial user-list navigation through the final user-list navigation, and a static A/B ID mapping. Run the **unchanged R7 DOM decoder and trace auditor** to answer Q1 locator, Q2 clicked row, Q3 mutation POST target, Q4 visible-record effect, Q5 click status. Additional Q6 asks whether B's `last_login` changed. For Q6 the conservative auditor must abstain absent a verified value in its accessible evidence. Inspect the original `.trace`, `.network` and decoded DOM, not a simulated trace or fabricated transcript. Never pass backend mode, server observer, SQL or truth CSV to this auditor.

**P: selective evidence packet.** Receive the recorded request/event/server facts plus the independent post-commit SQLite readback, including explicit before/after comparison of B's `last_login`. This privileged extra DB observation is the mechanism under test. Score Q6 from the actual database readback, never from the mode assignment or expected result.

**Independent evaluation.** After both auditors have produced predictions, join them to a separate SQLite oracle. Report Q6 as correct/wrong/abstain. R7 Q1–Q5 are diagnostic controls; Q6 is the new discriminating question.

## Equivalence gates

For each control–shadow pair, compare independently recorded:
1. initial and final **pixel screenshots** of the browser-rendered user list (SHA-256, exact decoded bytes), with no screenshots archived publicly;
2. Django-visible user-list rows/first_name values before and after, using the unmodified R7 source DOM reader;
3. original Trace-only R7 Q1–Q5 answers and reconstructed DOM decoder success;
4. ordered normalized method, route and response-status sequence parsed from the real `.network` records.

Same source app / browser / UI conditions are required. Since sessions, CSRF tokens, port numbers, timing, trace internal IDs, DOM input values and network metadata vary between fresh executions, raw Trace ZIP byte equality is neither expected nor claimed. The normalized network comparison deliberately excludes these unstable values; its precise fields must be disclosed. Pixels and visible rows must match exactly to accept a pair, and both modes must have an actual authorized Django POST. A failed gate yields an inconclusive pair, never fabricated equality.

## Key scientific interpretation

A browser-only observer cannot prove a hidden post-commit B-column value based on an observed trajectory that omits that value. The paired results seek to empirically demonstrate this identifiability limit using original UI traces. The full selective packet can distinguish the pair only because it receives a **new, privileged independent SQLite observation**. It should not be characterized as better inference over identical inputs, nor generalized to all Playwright Traces, production systems, or malicious server behavior. This follow-up measures the scope of observational evidence and effect-level accountability.

## Provenance, publication and repeatability

Keep source files and exact script under version control. Preserve category-level case results, per-pair equality flags, trace-snapshot counts, byte sizes and a SHA-256 manifest. Raw Trace ZIPs, screenshots, cookies, synthetic login secrets, CSRF and raw HTML stay in disposable directories and are deleted after each case. Run a second complete independent execution, compare all stable outputs, and disclose any differences. Retain the prior manuscript and Zenodo DOI unchanged pending review of construct validity and replication.
