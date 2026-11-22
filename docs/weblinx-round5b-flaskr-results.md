# Round 5B-1 — Real Flaskr browser actions with independently read SQLite effects

**Status:** First 48-case experiment fully executed, verified and archived. Second independent run and comparison described in the final provenance section after completion.

## Frozen third-party source

This experiment moves beyond the synthetic first-party R5A testbed. The application under test is the **unmodified Flaskr blog sample** maintained in the upstream [Pallets Flask repository](https://github.com/pallets/flask/tree/49943b5a94413a530761350f04e896f76e8d620e/examples/tutorial/flaskr), pinned to full commit `49943b5a94413a530761350f04e896f76e8d620e`. Flaskr is an educational third-party application whose real authenticated edit and delete handlers commit changes to a SQLite database.

The [R5B-1 protocol](weblinx-round5b-flaskr-protocol.md) was committed **before the first source experiment**. It specifies 48 trials, with two operations (edit and delete), three locator constructions (positional first Edit link, exact edit destination URL, contextual article heading), and eight browser-DOM conditions (baseline, reorder, swapped Edit links, remove original target, duplicated article heading, standard overlay, forced overlay, prevented default navigation).

The upstream Flaskr source templates, routes, backend validation and database schema remain unchanged. The independently written harness supplies dummy blog posts, a throwaway authenticated account and an isolated SQLite database to each episode. After loading the actual page, it may manipulate the **browser DOM only** under the fixed conditions. This is a controlled intervention in an authentic server-backed app, not an observation of naturally occurring website failures.

Environment: Python 3.11.18, Flask 3.1.2, Playwright 1.65.2, Chromium 159.0.8154.6.

## Measurement hierarchy

Each episode starts with two persistent original posts A and B, with A as the declared intention. The main audited action is a **single attempted click on an Edit link**.

The event observer uses a browser document-capture listener and `isTrusted` and records which article visually owns the link and where the link's `href` points. These are separate channels. A read-only external WSGI wrapper records the genuine HTTP route and method received by the unmodified Flaskr backend. If a native edit form opens, the harness follows through with the original app's Save or Delete form. A separate SQLite connection reads whether A or B was actually updated or deleted, and a newly rendered Flaskr index confirms the persisted state.

The final SQL effect depends on the **full click-plus-follow-through workflow**. It cannot be ascribed to the first link click alone. Each episode preserves the source event, server update route, follow-through operation, SQL effect and rendered index agreement separately.

## First complete results

| Outcome | Original 48 episodes |
| --- | ---: |
| Independent SQL readback: intended A changed | **16** |
| Independent SQL readback: different B changed | **8** |
| No SQLite row changed | **24** |
| **Total** | **48** |

There are 24 update trials and 24 delete trials. Each operation has eight intended A changes, four unintended B changes and twelve no-effect cases. Every recorded final rendered post list matches the separately queried database state.

Playwright's first-click API returned normally in **36** trials, timed out in **10**, and reported a locator error in **2**. Among the 36 returned clicks, **12** produced no SQLite effect after the declared workflow. The other 24 led to real server-side edit/delete POST requests and corresponding actual SQL commits.

| Controlled intervention | Intended A SQL effects | Other B SQL effects | No effects |
| --- | ---: | ---: | ---: |
| Baseline | 6 | 0 | 0 |
| DOM reordered before action | 4 | 2 | 0 |
| Edit-link `href` values exchanged | 2 | 4 | 0 |
| Intended article removed | 0 | 2 | 4 |
| Duplicate matching article heading | 4 | 0 | 2 |
| Standard pointer-blocking overlay | 0 | 0 | 6 |
| Forced click through pointer-blocking overlay | 0 | 0 | 6 |
| Default link navigation prevented | 0 | 0 | 6 |

The normal overlay led to timeouts. Forced clicks returned but had no server DB effect. Preventing navigation also produced returned clicks with no DB effect. The two contextual-locator ambiguity errors occurred in the duplicate-heading condition.

## Clicked page element differs from actual database effect

The source captured an actual trusted click on an **article's Edit link**. That article's title is a visible source-document attribute, separately from its link URL. The independently committed SQLite row belongs to the server route reached through that URL.

| Event link visually belongs to | SQL changes A | SQL changes B | No SQL change |
| --- | ---: | ---: | ---: |
| A | 14 | 4 | 6 |
| B | 2 | 4 | 0 |
| No article link received an event | 0 | 0 | 18 |
| **Total** | **16** | **8** | **24** |

**Four of eight actual wrong-row effects occurred after a trusted click on A's visible Edit link.** Conversely, **two intended A effects followed a click on the B article's link**. All six discrepancies occurred in the predeclared swapped-`href` condition. This directly demonstrates how a receiver-oriented audit and an application-state-oriented audit answer different questions.

For an auditor who regards the **visual article** of the click as the effect target, using only the event label would miss four of the eight B mutations and mistakenly flag two correct A mutations. An independent server destination and actual post-commit database readback resolve the distinction. The source HTTP request route is itself an observation, and a received POST or successful network status is not in general proof of a committed database mutation.

## Genuine serialized evidence and Playwright Trace baseline

Per-episode evidence packets were serialized as compact JSON and compressed independently using zlib level 9. The tiers add observed channels progressively. The following are **measured bytes over all 48 trials**, without global compression or deduplication.

| Evidence included | UTF-8 bytes | Per-episode zlib bytes |
| --- | ---: | ---: |
| Request and intended action | 5,090 | **4,286** |
| Request + actual trusted event recipient and link destination | 9,230 | **6,228** |
| Previous + observed actual server GET/POST route | 14,822 | **8,181** |
| Previous + separate committed SQLite effect and rendered index agreement | 18,638 | **10,123** |

For the very same 48 episodes, actual Playwright `context.tracing` generated **48 Trace ZIP files** with `snapshots=True`, `screenshots=False`, `sources=False`. Their original-run ZIP byte total is **343,784 bytes** and the reported median per episode is **8,093 bytes**. The trace archives contained **3,132 trace event records and 312 network records** in aggregate.

This trace is a **real existing baseline**, not a strawman minimal logger. Playwright stores action steps, DOM snapshots and network records. The trace ZIPs are larger than the compact source evidence packets, but their scope differs. A trace may contain details the purpose-built packet omits, and a trace network record can support different inferences from an independent SQLite readback. Therefore a factor-of-34 storage ratio between 343,784 Trace ZIP bytes and 10,123 compact effect-packet bytes is **descriptive of these configurations**; it is not a matched functional-sufficiency or general storage-efficiency result.

The original Playwright Trace ZIP files are deleted with per-episode temporary directories. They may contain dummy local login session and raw app snapshots, so they are **not copied to public GitHub or the archive**. The full trace-generation method and numeric count of its archived records remain reproducible in the published runner.

## Independence, limits and scientific relevance

The Flaskr implementation is third-party-maintained; its native authenticated web routes and SQL schema were retrieved from a fixed commit. Test accounts, posts, source DOM interventions and the observer are our own. The independent SQLite query is distinct from browser UI, server request interception and the Flaskr response. It is the authoritative stored-result evidence for this particular app.

This remains **one externally maintained sample application**, with controlled dummy data and deliberate DOM interventions. The two operations use related source routes in the same codebase. The 48 trials are an experimental matrix, not an independent sample of agent interactions or web application failures. No estimate of production incidence, independent-site generalization, event-recipient correctness of WebLINX's old recordings or any novel Playwright limitation follows from these numbers.

The contribution for the accepted manuscript is a concrete, directly verified distinction among recorded intention, browser receiver, server endpoint and committed application effect. This motivates evidence retention indexed by an **audit question**, with the indispensable caveat that existing Playwright Trace is an information-rich comparator.

## Reproduction and provenance

- [Frozen R5B-1 protocol](weblinx-round5b-flaskr-protocol.md)
- [Actual upstream Flaskr runner](../scripts/weblinx_round5b_flaskr.py)
- [48 casebook source results](../results/weblinx_round5b_flaskr_cases.csv)
- [Full aggregate, actual Trace bytes and upstream file hashes](../results/weblinx_round5b_flaskr_summary.json)
- [First complete 48-case source run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45062479226)
- [Pinned external Flaskr upstream](https://github.com/pallets/flask/tree/49943b5a94413a530761350f04e896f76e8d620e/examples/tutorial/flaskr)

First-run SHA-256:
- Summary JSON: `ca60140c7e54eabc1619558ea6f53740cb9b878dafb85e5465c9a0b118ca7c6e`
- Complete CSV: `c3959fd7a7867e434d3a35932a421343b8998f6f2dd0688ea042e3f608b858f3`

Do not report raw Playwright trace parity based on these SHA values. Independent browser trace files include timing and runtime-dependent records; their actual sizes are retained separately as descriptive measurements. The rerun compares the full 48 original categorical outcomes and purpose-built log packet fields exactly, and reports actual Trace ZIP byte variation.
