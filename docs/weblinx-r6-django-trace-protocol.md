# R6 / Round 5C: second independent web application + Playwright Trace auditability

**Preregistered before the first R6 experimental browser run (November 22, 2026).** This is a separate controlled follow-up to the externally maintained Flaskr R5B experiment. R5B's 48+6 results are frozen and never retrospectively relabeled.

## Source and novelty boundary

Second application: the **standard Django admin user-management web application**, installed from the official Django distribution **5.2.12**, source-tag commit **`4f382ca672f86dd4a1e4d071c91d0caad0e124b3`** (`django/django` signed tag `5.2.12`). Use the original Django `django.contrib.admin` and `django.contrib.auth.models.User` model, default Django forms, routing and database operations. No Django backend, model, admin view, form or template changes. A small integration harness supplies Django's necessary settings, URL mapping, test admin account, two dummy user records, SQLite database and independent WSGI wrapper.

This is a **different web application framework, maintained by a different project** than Flaskr. Both experiments use our harness, local Chromium and synthetic DOM perturbations; the matrix is a controlled test, not a population sample of real-world failures.

## Fixed 48-case design

Cross **operations** `edit` (change one user's first_name via native Django admin form) and `delete` (delete a user through native Django admin change/delete/confirmation views), **locators** `positional`, `href_exact`, `contextual_row`, and **8 scenarios** `baseline`, `reorder`, `swap_href`, `remove_target`, `duplicate_context`, `overlay_standard`, `overlay_force`, `prevent_default`: 2 × 3 × 8 = **48 fresh browser episodes**.

All initial records A (`r6_a`) and B (`r6_b`) exist and are searched using Django's original admin user changelist (`/admin/auth/user/?q=r6_`). The intended record is always A. Two records are inserted for each episode using Django's native ORM; the independent readback uses **a new `sqlite3.connect`**, distinct from the browser and Django ORM.

The tested action is exactly one click on a user-change link. When the native Django change form opens, the harness follows through by submitting the original Django Save or Delete UI. Classify the **whole workflow's** committed SQL effect and separately retain which link received the click. A click by itself is not a DB-edit operation.

The eight DOM scenarios use browser-only DOM modifications. In `reorder` swap the visible rows; `swap_href` exchange the two native change-link `href` values; `remove_target` remove A's row; `duplicate_context` append an A-labeled row with a B destination (making contextual user A selection ambiguous); `overlay_standard` intercept the click with default actionability; `overlay_force` intercept with explicit force; `prevent_default` prevent navigation on the A link. Apply all scenarios to all locator/operation combinations with all failures retained. Django source stays untouched.

## Actual data layers and data-leakage controls

Independently log four different evidence sources:

- **Intent:** intended A and the predeclared locator and scenario.
- **Trusted browser receiver:** document-capture observer's `isTrusted` event target (raw element tag), ancestor admin table row username, and clicked link's current `href` record A/B. Installed through `context.add_init_script` before normal HTTP navigation, and relayed to a Python callback. Does not use or modify Django backend.
- **Server request:** external WSGI wrapper's actual method, user-change or user-delete route ID and response code. It does not infer which SQL effect occurred.
- **Persisted effect:** post-action separate SQLite connection re-reads both records' first_name/presence. A completed save/delete can change A, B or neither. Compare to the newly reloaded Django admin list for consistency.

No raw cookies, credentials, CSRF tokens, session storage, trace event payloads, third-party text or screenshots in published results.

## Real Playwright Trace audit, not a guessed baseline

Per episode, capture an authentic Playwright Trace ZIP with `snapshots=True`, `screenshots=False`, `sources=False`, including the initial audited click, follow-through form and navigation. **Parse the archive**, checking for a `.trace` file and `.network` records; collect observed event method counts, captured locator method/selector presence, network request methods/statuses, destination record IDs when a native admin change/delete POST is visible. Keep all parsing rules fixed before comparative results. Record actual ZIP bytes, action and network records and direct audit answers.

Predeclared audit questions (denominator all 48):
- **Q1: What locator was attempted?** Trace direct action params; request packet contains declared locator kind. Missing action evidence => abstain.
- **Q2: Which visible application row received an actual trusted click?** Explicit trusted browser event capture packet. A Trace click selector/DOM snapshot is a possible *inference* but is not an independent `isTrusted` recipient observation. Count Trace as `unverified` if no dedicated trusted event item record is present; do not assert that a human could never infer it from Trace.
- **Q3: Which server-side mutation route received a POST, if any?** Trace `.network` actual request URL/method and response when recorded, and independent WSGI route packet. A uniquely identified request is answerable; no recorded POST under a complete trace is a negative answer. For a failed or missing trace network stream => abstain; do not assume Trace always lacks network evidence.
- **Q4: Which SQLite record changed?** Independent post-commit SQLite readback (effect packet); Trace's network and DOM snapshots may indirectly suggest an effect but are not themselves an independently authenticated SQL-state record. Trace explicit authoritative answer is `unverified` unless actual SQL readback appears in Trace data; do not equate HTML redirect with a commit.
- **Q5: Did the initial Playwright locator operation return normally?** Trace after action with no error vs a captured action error; the source API status packet is known. Only count when trace event data explicitly gives it, else abstain.

To guard against **oracle leakage**, the Trace-only auditor takes **only the raw Trace ZIP**, fixed original A/B username mapping and static trial ID (no case outcome, WSGI logs or SQL), and emits per-question answer/evidence. The minimal-tier auditor takes only the corresponding packet tier, never the results table. The separate SQLite and WSGI oracle is joined **only after both evaluations are complete**.

## Compare actual storage with audit fidelity

For each case, measure actual trace ZIP bytes and independently compressed zlib-9 bytes for serialized tier packets `request`, `event`, `server`, `effect`. Each later tier includes the prior channel. Compare both **answer coverage** and **correctness among answered cases**, recording contradictions and abstention. A log with the DB oracle embedded has a privileged data source that Playwright Trace does not automatically contain: the experiment must explicitly say that the information difference comes from additional instrumentation, not clever compression.

The trace auditor is a **conservative machine-readable-field evaluator**, not a blinded human review of entire snapshots. That limitation is a condition of interpretation. We must not claim total human Trace unreadability.

## Replication and stage gates

Use Python 3.11, `Django==5.2.12`, `playwright==1.65.2`, Chromium pinned by Playwright. Re-run all 48 cases independently. Compare source/event/SQL results and audit verdicts exactly. Report actual trace ZIP size drift separately (trace may vary by runtime, timestamps). All original 48 episodes included.

Do not revise the TRUSTMORE manuscript or create a Zenodo DOI until source verification, trace parser correctness, and independent complete rerun pass. A next study on additional apps would be needed for cross-site generalization.

## Pre-valid-results harness corrections and rejected execution

The original run `45064250360` was rejected before analysis because the Django ORM attempted to seed test users inside the Playwright sync API's event-loop thread. User seeding now occurs through the **same native Django ORM** in an isolated non-async Python thread.

A subsequent complete initial test execution `45064424365` failed the **frozen baseline and overlay controls**. The harness had assumed the literal user-change `href` began with `/admin/auth/user/`, but the original admin markup can render relative native href values; the exact-`href` locator timed out even in baseline cases. The fixed-screen overlay also moved relative to page content when Playwright subsequently scrolled the click target into view. Those 48 invalid test outcomes are **excluded from scientific measurement**, but retained as failed setup run evidence.

Before any scientifically valid R6 result, the harness was corrected to (a) capture A's exact source-native original link `href` before DOM mutation and construct an exact-attribute CSS locator, and (b) scroll A's native link into view **before** placing a fixed-position overlay. These are corrections to experimental instrument validity, not changes to the frozen 2 × 3 × 8 matrix, the application source, the outcome oracle or the audit questions. The experiment must now be rerun in full, with all baseline A-commit and standard-overlay zero-commit cases passing before accepting results. Any further invalid run is likewise recorded and excluded from study statistics.

### Second control failure and final pointer-intercept correction

Runs `45064691419` and `45064708238` independently passed the baseline tests (6/6) and matched original recorded effect results but failed the overlay negative controls: the element-sized overlay did not reliably intercept clicks in the Django admin layout. These 48-case outputs are **invalid calibration data**, not eligible for publication as R6 results. The discrepancy was detected by the existing all-overlay zero-effect assertion.

Before the first valid study run, the overlay intervention was corrected to a **full-viewport fixed pointer shield**, with a DOM `elementFromPoint(10,10)` self-check after insertion. This is the same class of pointer-intercepting overlay specified in the original protocol. It is independent of link location, scrolling and Django CSS. Both standard and forced click outcomes remain measured empirically; standard overlay must have zero SQLite effect. All 48 original cells and underlying Django package remain fixed.
