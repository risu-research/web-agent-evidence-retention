# R8B prospective correction: transactional network equivalence

**Fixed November 22, 2026 before any R8B source execution.** This is a separately labeled prospective experiment, following the failed full-equivalence calibration in R8. R8 and all its failed CI runs remain published as negative calibration history. The underlying 12 cases, original Django app, real browser execution, unmodified R7 auditor, SQL oracle, screenshots and pixel-gate remain unchanged.

## Reason for a new, separately frozen rule

R8 required exact ordered equality of every native Playwright Trace network request whose path began `/admin/`. This included the page's auxiliary `GET /admin/jsi18n/` translation resource. The third calibration run (ID 45068961921) found a pair with an auxiliary translation GET returning native Trace status `-1` in one execution and `200` in the other. Both runs had the same user-facing pixel screenshots, native DOM A/B list, account POST, A outcome and independently measured B hidden side-effect difference. The resource cancellation is an actual Trace observable and **must remain disclosed**. An R8 failing pair is not retrospectively passed.

## R8B corrected equivalence scope, frozen before its source results

Use the identical 2 operations × 3 original locators × 2 server modes = 12 episodes / 6 pairs. Each episode creates fresh SQLite, WSGI server and Chromium context, and runs the genuine unmodified Django Admin A edit or delete workflow. The post-commit B last_login controlled server-side test mutation is unchanged.

Retain every prior R8 strict equality gate **except** the network comparison, which is refined as follows.

- **Transactional network projection:** take the original native `.network` records and retain all `(HTTP method, normalized URL path, native response status)` entries whose path is the admin user's changelist `/admin/auth/user/` or a user record edit/delete route matching `^/admin/auth/user/[0-9]+/(change|delete)/$`. Require exact ordered equality of this complete transactional subsequence within each pair, including responses for the normal Django POST and all list refreshes.
- **Auxiliary network observation:** separately record whether other `/admin/` native Trace network entries differ, with counts, route identities and response statuses. These differences are reported, never claimed to be absent. Auxiliary canceled requests therefore do not silently disappear from the result.
- **Pixels:** require exact SHA-256 equality of the pre-action and final-browser user-list screenshots. No screenshot pixels leave the disposable runner.
- **Native DOM:** require exact equality of initial and final extracted A/B rows and the unchanged original R7 Q1–Q5 answers. The R7 DOM decoder must resolve all references.
- **Backend oracle:** each genuine POST must result in the native authorized A effect; the two modes must have different B last_login outcomes observed by independent SQLite. The SQL reading and mode assignment must remain hidden from the Trace-only auditor.

The transactional projection is smaller than the full native network trace, and its limitations must be visible in every publication. It tests equivalence of the **causally relevant browser/HTTP sequence and visible outcome**, never bitwise or complete-network equality of raw ZIPs.

## Scoring and independent repeat

Q6 asks whether B's hidden `last_login` changed. The unchanged R7 Trace reader answers Q1–Q5; a conservative browser-only answer to Q6 is `abstain` because this field is absent from the captured browser workflow. The independently observed SQL packet answers Q6 from before/after source values. Join auditor predictions to SQL truth afterward. All six pairs must pass all corrected equivalence gates, including transactional network order; one failure invalidates the complete experiment. Report auxiliary request differences, byte costs and independent second full execution. A human auditor, a production error-rate inference, and a general claim of Trace inferiority remain beyond scope.

The original R8 strict failed run IDs are 45068631082, 45068796349, 45068811353 and 45068961921. Keep them as explicit calibration evidence. Leave the main manuscript and Zenodo unchanged pending the new prospective result.
