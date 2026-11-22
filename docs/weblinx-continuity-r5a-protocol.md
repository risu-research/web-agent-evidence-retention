# Round 5A — predeclared live-browser recipient and effect pilot

Frozen 2026-11-22 **before first R5 browser run**. This is a separate prospective, controlled browser experiment after the frozen R1–R4 WebLINX source-only audit.

## Question

For an actual trusted browser click, how often do four observed facts disagree?

1. **Request:** the tool's declared intended application item and locator expression;
2. **Event:** a document-capture listener's trusted `click` event target and composed path;
3. **Handler:** an independently implemented application-level delegated click handler, logging the item for which it ran;
4. **Effect:** separate readback of application state and rendered counter values after the action.

Preserve these channels separately. A browser event's `target` can be an icon nested inside a button; a composed path containing the intended button is a different observation. Handler invocation is different from a successful state change. A tool command returning successfully is different from both.

## Fixture and cohort

Two explicitly synthetic, controlled first-party applications, designed before evaluation: (i) a two-record action list (`list`, development), and (ii) a distinct permission table layout (`table`, layout holdout). The second is a layout holdout, **not an external real-world website or independently collected task corpus**. Both have two persistent application records, A (intended) and B (distractor), initially unmodified. Their visible counters start at zero.

Predeclared 12 mutation or handler conditions, crossed with three locator methods for each app:

- `baseline`: original visible buttons, no mutation;
- `nested_icon`: a nested span fills the intended button, so raw event target differs from effective button;
- `reorder`: B is moved before A after locator capture, changing the first positional button;
- `reuse_id`: the native ID `target-A` is reassigned from A to B before clicking;
- `rerender_same_id`: the intended button is replaced with a new DOM node using the same ID;
- `overlay_standard`: a pointer-intercepting overlay covers A, ordinary Playwright click;
- `overlay_force`: the same interception with Playwright's explicit `force=True` click;
- `disabled`: A becomes disabled;
- `handler_no_effect`: the delegated app handler runs for A but intentionally makes no state change;
- `stop_bubble`: an inner child stops propagation before the delegated app handler;
- `target_removed`: A is removed after locator capture;
- `duplicate_accessible_name`: both buttons expose the same accessible name.

Locators: `positional` = source first action button, `native_id` = an XPath `id("target-A")` expression, `accessible_role` = a role+name locator for A. Always choose A as the intended item. Cross product **12 × 3 × 2 = 72** independent browser episodes. Fresh browser context and new source HTML for each episode. All clicks use the real browser input mechanism through Playwright locator actions. No `dispatch_event` or synthetic JS `.click()` is used to create an outcome.

Frozen case order: app, scenario, locator in the above order; no selective exclusion after seeing results. The evaluation app and all scenarios are defined in source before any run. The same measurement rules and conditions apply to both.

## Independent signals and classification

Install the document-capture observer as the first `<script>` in each newly created fixture document, before application code. Count only `isTrusted` click events. It records the original event target's tag and the nearest path node's application item key. This observer never calls the application handler.

A separate app handler runs at document bubble phase, logs its executed item, and updates in-memory state plus rendered counters. The two counters and two state values are read back separately. If the click is stopped at its inner target before bubbling, capture may exist without a handler.

Each episode has exactly one attempted click. The intended application key is fixed in test configuration prior to page mutation. Observe status (`returned` or sanitized error type), trusted event count, event path item, handler item, independent before/after state delta, independent rendered-counter delta, and agreement between state and rendering. Record zero events, intercepted events, wrong-recipient effects, handler-without-effect, and protected failures as separate categories. Do not treat a nested raw `span` event target as a wrong-action target when the composed path and app handler identify A.

Assert fixture invariant: no unintended state mutation before the click; no state/render readback divergence; never count a programmatic JS click as a trusted event.

## Baselines and limits

Compare Playwright's **standard actionability checks** with explicit force actions. Standard Playwright checks visibility, stability and ability to receive pointer events; its Trace Viewer stores DOM snapshots and action logs. Neither the generic trace nor the test script is assumed to be an independent audit oracle until actually compared against a separately observed event and effect.

This is a controlled test of evidence channel sufficiency and failure taxonomy. It **does not** measure production-site error frequency, external agent success, security enforcement, user impact or previously recorded WebLINX action delivery.

## Reproducibility and publication

Pin `playwright==1.65.2` and its Chromium browser revision; store exact Python and browser version in results. Save the complete 72-row numeric casebook, aggregate, fixed fixture and runner source, and source SHA-256. Publish **no** browser profile, screenshot of external sites, Playwright trace containing third-party user content, network credentials, or internal unpublished research. The two fixtures use dummy data only.

Freeze the protocol and source before running the table-layout holdout. Do not tune parameters from evaluation outcomes. Re-run the complete experiment independently; compare exact aggregated results, allow browser-version metadata to be pinned.

## Advancement criteria

R5A succeeds scientifically if all 72 episodes execute and separately report all four channels, including clean negative controls. Whether any given failure is observed is an empirical result, including zero wrong-action deliveries. Further R5B should compare the minimum retained evidence and measured bytes for answering distinct audit questions, with Playwright Trace as an explicit baseline and at least one genuinely independent external application or instrumented codebase before making generalization claims.

## Instrumentation implementation note

During the initial local Chromium smoke test (before any successful R5 result), we found that replacing the about:blank document with `page.set_content()` drops capture listeners installed on the previous document. The standalone observer is now installed as the first script **in the actual new fixture DOM**, before the application script. The declared four evidence channels, 72 episodes, locator set, mutations and scoring rules are unchanged. This correction prevents false missing-event observations from a test harness lifetime bug; an initial run that predates this fix cannot qualify as a scientific result. All production runs must use the corrected source and be repeated independently.
