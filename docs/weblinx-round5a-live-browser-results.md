# Round 5A — Live Chromium event recipient and actual application effects

**Status: real browser pilot complete; two complete reproducible runs.**

The [protocol](weblinx-continuity-r5a-protocol.md) fixed the two self-authored application layouts, twelve conditions and three locator methods before the first browser results. Two corrected full Chromium runs completed successfully and generated **byte-identical derived source files**. The [browser runner](../scripts/weblinx_round5_live_browser.py) is public.

## Experimental boundaries

This pilot runs genuine Playwright browser pointer inputs in Chromium 159.0.8154.6 under Python 3.11.18 and Playwright 1.65.2. The applications are deliberately controlled HTML fixtures with dummy records A and B. The first layout is a list; the second is a permission table. Both share application-handler logic. They are two distinct DOM layouts, **not independent external real-world applications**.

Each episode starts a fresh browser context. Target A is the declared intent. Three locators are compared:

- A source-positional first-button XPath;
- an XPath `id("target-A")`;
- a role+accessible-name locator for the intended A button.

There are twelve fixed mutation and handler conditions, including DOM reordering, native ID reassignment, node replacement, an overlay, disabled controls, a stopped bubbling event, a handler that makes no effect, target removal and duplicate accessible names. This yields **72 = 2 × 12 × 3** independently initialized episodes. The experiment does **not** re-execute WebLINX user actions or estimate field failures.

The measurement channels are deliberately separate:

1. The intended item and locator are fixed in the Python test before DOM mutation.
2. A document-capture listener, installed as the **first script** in the source document before the app script, records the actual trusted click's raw event target tag and first application item in the `composedPath()`.
3. A distinct application-level delegated click handler records the record it processed.
4. Application state and visible rendered output counters are independently read after the action and checked for agreement.

The last two readbacks are controlled by the fixture. This is a distinct observation channel, **not a separately administered authoritative server or user-visible production effect**.

## Measured source results

| Directly observed channel | A, intended | B, different | Overlay | No corresponding observation |
| --- | ---: | ---: | ---: | ---: |
| Trusted click event path | **42** | **6** | **6** | **18** |
| Application handler invoked for | **36** | **6** | – | **30** |
| Application state changed for | **30** | **6** | – | **36** |

Playwright operation status was `returned` in **54** episodes, `timeout` in **16**, and a reported Playwright error (ambiguous accessible name) in **2**. Of the 54 returned operations:

- **30** changed the intended A record;
- **6** changed a different B record;
- **18** made no state change.

The failures were deliberately created by the experimental conditions. Their fractions cannot be projected onto live sites or agents.

### Interpretable controls

| Condition (two layouts × three locators) | Verified outcome |
| --- | --- |
| Baseline | 6/6 intended A effects |
| Nested inner span | 6/6 intended A effects; event target is `SPAN`, effective composed path reaches A |
| DOM reorder before the action | 2/6 actions change B through positional XPath |
| Native ID reassigned to B | 2/6 actions change B through native-ID XPath |
| A removed before action | 2/6 actions change B through positional XPath; other four perform no action |
| Overlay with standard click | 6/6 time out, with no trusted click captured |
| Overlay with explicit `force=True` | 6/6 operations return; real trusted click reaches overlay; no app handler or state effect |
| A disabled | 6/6 time out, without trusted click |
| Handler intentionally leaves state unchanged | 6/6 operations return; A receives trusted click, handler runs, no state effect |
| Inner span stops propagation | 6/6 operations return; A receives trusted click, delegated handler does not run |
| A replaced with same native ID | 6/6 intended effects |
| Duplicate accessible button name | Two role-locator ambiguity errors; four other locators perform intended effect |

An ordinary successful Playwright operation return is insufficient to infer either intended action recipient or persistent state change. In particular, six episodes changed **B** and eighteen returned without effect.

A raw event target of `SPAN` need not be a wrong application receiver; its composed path can include the intended button. Conversely, a trusted event at the intended element does not guarantee that an application-level handler ran. Six `stop_bubble` episodes have that pattern. Six other episodes ran the intended application handler without changing the state. This separates **event, handler and effect** as distinct audit questions.

The overlay controls use Playwright's documented actionability checks. Standard locator clicks check that their target receives pointer events; an explicit `force` option bypasses the relevant check. These are normal Playwright capabilities. See [official actionability documentation](https://playwright.dev/docs/actionability) and [the Trace Viewer](https://playwright.dev/docs/trace-viewer).

## Measured retained log payload sizes

Each packet is compact sorted-key UTF-8 JSON; compressed figures use **per-episode zlib level 9**, with no cross-case deduplication. All packets contain the record's request. Later tiers add actual observed channels.

| Packet retained for 72 episodes | Raw UTF-8 bytes | Individually zlib-compressed bytes |
| --- | ---: | ---: |
| Request/intent only | **5,880** | **5,500** |
| Request + trusted event observer | **13,416** | **10,221** |
| Previous + actual app-handler item | **14,910** | **11,064** |
| Previous + pre/post state and rendered counter | **21,318** | **13,564** |

These are **real serialized packet bytes**, not theoretical estimates. They concern a tiny first-party test fixture and contain no screenshots, full DOM captures, executable audit verifier or external browser trace. They should not be equated with the much broader Playwright trace or the prior WebLINX retention cohort's byte totals.

In the fixed episodes, the event tier distinguishes actual pointer receiver, and a separate handler tier distinguishes delegated handler operation. The state-and-render tier distinguishes an intended event and handler from an actual state effect. The tiers align with the original paper's selective-retention question, now with independently recorded runtime *channels*.

## Reproducibility and validity

The initial browser automation was smoke-tested using `data:` navigation. A later attempt to use `set_content()` exposed an initialization bug: an observer attached to the previous `about:blank` document does not survive document replacement. Before the final R5 measurement, this was corrected by installing the standalone capture script **first in the actual fixture HTML document**. The [protocol documents the implementation correction](weblinx-continuity-r5a-protocol.md). The stable 72-case cohort and scoring rules remained unchanged.

The first two complete runs of the corrected source both passed every control and regenerated the same summary JSON, 72-row CSV, pinned environment list and SHA manifest **byte-for-byte**:

- [Corrected R5A full run 1](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45060903027)
- [Corrected R5A full run 2](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45060914497)
- [72 derived individual outcomes](../results/weblinx_round5a_browser_cases.csv)
- [Aggregate with actual byte counts](../results/weblinx_round5a_browser_summary.json)
- [Frozen source code](../scripts/weblinx_round5_live_browser.py)

SHA-256 of the final corrected source-run output:

- Summary JSON: `1196bc12db75aea9bfd4ced76a4894e34d12fda045ecd81e294de2934a8219cc`
- 72-case CSV: `190e3317de1f0702981dfc76ba91c705cb7cee7097845c69b57cc3d08ac2b7f0`

The numeric results are complete, including every failed action, and no third-party raw browser pages or sensitive browser profiles are released. Browser build and Playwright version are pinned. No new paper revision, GitHub release or Zenodo DOI was made.

## Next scientific gate

These are instrumented live browser interactions, **not independent production agent recordings**. R5B should acquire an externally maintained web application's authoritative server-side effect or task-level state, independently confirm its event recipient, and measure what minimum logs suffice to reconstruct the result. Compare explicitly with Playwright Trace, whose actionability information and DOM snapshots already form a substantial baseline. Only then can the project credibly argue for selective retention beyond a controlled fixture.
