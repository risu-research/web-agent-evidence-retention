# R5B-1: External-maintained Flaskr with independent SQLite readback

Protocol frozen 2026-11-22 before the first R5B run. This is a **new prospective browser study**, separate from the 600 WebLINX source actions and the synthetic R5A 72-case experiment.

## Third-party application selection and provenance

Use the actual official Flask tutorial application **Flaskr**, from `pallets/flask`, `examples/tutorial/flaskr` at **Git commit `49943b5a94413a530761350f04e896f76e8d620e`**, checked before downloading. Its unmodified backend implements authenticated blog post reading, update and delete through native Flask routes backed by SQLite. Pin `Flask==3.1.2`, `playwright==1.65.2`, Python 3.11 and the corresponding Playwright Chromium browser. Do not patch Flaskr application code. The harness may create its own local SQLite database, test account, two dummy posts, the WSGI server and independent browser instrumentation.

The externally maintained Flaskr example is an actual third-party webapp with a real SQL commit, although it is an **educational example**, not a production deployment. Only one externally maintained app is evaluated in this stage. Our injected DOM mutations and dummy tasks are controlled interventions; do not describe them as naturally observed website failures.

## Frozen matrix: 48 independent episodes

Cross **two real app operations** (edit post, delete post) with **three user-requested link locators** and **eight predeclared webpage conditions**. Total **2 × 3 × 8 = 48** independently initialized browser+server+database episodes.

- Locator `positional`: first `article.post a.action` Edit link in source order.
- Locator `href_exact`: exact native `href` attribute to post A's `/<id>/update` route.
- Locator `contextual_role`: Edit link within the article whose title heading matches A.
- Conditions `baseline`, `reorder`, `swap_href`, `remove_target`, `duplicate_context`, `overlay_standard`, `overlay_force`, and `prevent_default`.

All target intents are **post A**, created later than B so A is first in the unmodified Flaskr index. The other post B is a distractor. Use only synthetic titles `R5B-A`, `R5B-B` and dummy post text. Users are registered through a test database, then login through the **original Flaskr login UI**. Independent source SQL seed records are not used as an alternative web route.

The eight DOM conditions are performed solely through local browser DOM modifications **after page load and before the audited first click**; the application backend and templates stay byte-identical to upstream. The `overlay_force` condition forces the click; all others use default Playwright actionability.

Each episode attempts the first Edit-link click once, recording the actual event target and server GET update navigation. If the original update page opens, the harness then performs the operation under test using Flaskr's **real form**: either fill the title and click Save, or click Delete and accept the native confirmation. If no edit page opens, the task ends as a no-effect outcome. The second UI action is explicitly a follow-through step, and its effects cannot be attributed to the first click alone.

## Independent observations and units

Record separately:

1. **Intent:** test's original post A, locator kind, and condition, fixed before UI mutation.
2. **Actual recipient:** browser document-capture `isTrusted` click with original first-link article heading and clicked `href`. The event observer is installed before page scripts using `context.add_init_script` on real HTTP navigation and emits to a Python callback. Do not equate an inner child event target with a different link.
3. **Server route:** record incoming server-side HTTP request method, route and status in an external WSGI wrapper, without modifying Flaskr view source. A network request and response are separate from a committed SQL effect.
4. **Authoritative effect:** open SQLite with a separate `sqlite3.connect` after the browser action; verify post A and B's stored IDs/title/body and whether a row was deleted; also compare the final HTML index. Classify effect on A, B, or none. An operation that returned successfully may still update B or do nothing.
5. **Playwright Trace baseline:** capture a per-episode standard `context.tracing` ZIP with `snapshots=True`, `screenshots=False`, `sources=False`, starting after login and including the audited click, subsequent form action and navigation. Measure actual compressed ZIP file bytes, trace resource member count, and trace-event count; preserve no raw cookie-containing trace in the public artifact. Baseline Trace is **not assumed** to lack evidence about the result: it records DOM snapshots, actions, and network activity. Whether it can independently authenticate the committed database state must be assessed as a separate question.

## Data and positive/negative controls

Only dummy local test data. Never use real accounts or external user sessions. Before the first audited click, verify SQL A and B exist in the expected state. After any DOM mutation but before action, confirm zero SQL changes. Then start or continue per-episode browser trace.

All non-overlaid baseline runs **must update/delete A**. For `reorder`, the first positional locator is expected to access B. For `swap_href`, event/article identity and HTTP route identity can disagree. For `overlay_standard`, no trusted click and no SQL change is expected; `overlay_force` may deliver a click to an overlay with no navigation or SQL change. The `prevent_default` intervention should allow an actual click event with no server update. The `duplicate_context` scenario is constructed to produce ambiguity only in the contextual heading-based locator; count all errors and no-effect outcomes. Do not silently discard unexpected outcomes.

Record all 48 episodes including failed or no-op operations. Use request-target, trusted event, WSGI route and independent SQL effect observations as distinct evidence layers. Report per-operation, per-locator, per-condition counts and actual serialized byte costs per episode. No claim of real-world frequency, third-party agent performance or reproducibility beyond this pinned app.

## Trace interpretation and privacy

Raw Playwright Trace includes snapshots and network information. Generate it locally for experimental comparison, inspect its archive structure, but publish only trace byte counts, record-type counts and schema-derived diagnostics. The original trace may contain local test cookies or session metadata. Do not publish raw traces or saved browser profiles.

The test data, Flask secret, user credentials and local HTTP port are throwaway. Published data must contain only fixed synthetic task IDs, app commit SHA, categorical results, anonymized server route categories, compact log byte sizes, original upstream source checksums and code. Literal login passwords, cookies and trace resources must remain inside the runner.

## Reproduction and decision criteria

Re-run the full 48-case experiment independently under the same pinned app and browser. Source/DB truth must be checked in a **separate SQLite connection** after the browser operation. Run regression tests for positive and negative controls and for safe CSV export. For trace sizes, report actual .zip byte length, with fixed snapshots/screenshots/sources options.

R5B-1 is successful only if there is a verified, independently read committed SQL effect and real browser event and network observations, with complete 48-case accountability. Generalization requires a second independent app or natural website trajectories. Trace-vs-minimal log *sufficiency* must not be inferred from filesize alone.
