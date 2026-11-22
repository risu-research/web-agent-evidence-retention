# R5B-2: authentic Flaskr server validation with successful POST and zero SQL commits

Frozen 2026-11-22 **before running this six-case supplementary experiment**. Retain the original R5B-1 48-case source/results unchanged.

## Rationale

R5B-1 shows that source click recipients can differ from the actual edited/deleted SQL row, and that a successfully returned browser click can have no effect. However, all R5B-1 operations that submitted a server-side POST also committed a SQL change. To test whether an observed server POST is sufficient evidence of actual persistence, use Flaskr's own existing title-required validation, backed by the same independent SQLite oracle.

## Source and fixed six-case matrix

Unmodified official `pallets/flask` example `examples/tutorial/flaskr` at SHA `49943b5a94413a530761350f04e896f76e8d620e`. Pin Flask 3.1.2, Playwright 1.65.2, Chromium browser from the same Playwright release. Fresh server, SQLite database and browser context for each episode; dummy authenticated user and two posts A/B.

All episodes perform an **edit**, crossing locators (`positional`, `href_exact`, `contextual_role`) and page conditions (`baseline`, `reorder`): **3 × 2 = 6**. The first click visits a genuine Flaskr Edit page. On the edit form, remove the HTML `required` attribute from the title input **in the browser DOM only**, clear its value and submit the real Save form through trusted browser input. Flaskr's untouched `if not title` validation should reject the blank title on the server and return HTTP 200 with the flash message, without a SQL UPDATE or COMMIT for the post. The removal of the client-side attribute is intentionally a controlled input intervention. Do not call this a spontaneously occurring security or validation defect.

## Separate independent signals

Record (a) first trusted link click and its displayed source article, (b) actual Flaskr server GET edit route, (c) actual server POST edit route and HTTP response status, (d) whether a user-visible validation message appears, (e) a separate `sqlite3.connect` query proving both post rows still have their original titles/bodies after submission. These are different evidentiary stages. A network request accepted and processed by the app is not equivalent to a successful stored state change.

Trace baseline: actual Playwright context trace ZIP generated with `snapshots=True`, `screenshots=False`, `sources=False`. Record its exact ZIP bytes and number of trace and network records. Delete raw ZIP after measurement, publishing only derived counts.

## Required controls and interpretation

All six cases must have first link click status `returned`, exactly one source-route GET update request, exactly one genuine POST update with HTTP 200 and zero SQLite state changes. Both original Flaskr posts must remain visible on reloading the index. The expected server-side rejection is a *frozen fixture oracle* derived from the official source and independently checked by a real SQL query; a failure must be recorded, not omitted or corrected silently.

This is a single externally maintained educational app and six deliberately constructed validation-rejection cases. Their presence confirms a possible evidence distinction in this source; it does not estimate real-world frequency, other Flask applications' behavior or independent agent errors.

The experiment is an exploratory predeclared **follow-up** to R5B-1, not part of the original frozen 48-case matrix. Keep the six-case cohort separate. Compare results against independently repeated full runs and publish categorical records only.
