# R7 — Reconstructed Playwright DOM snapshots versus selective evidence packets

**R7 first complete source run:** 48/48 real Django Admin action-plus-follow-through tasks; genuine Playwright Trace ZIPs; a separate browser event observer, read-only WSGI route wrapper, and independent SQLite connection. The [prospective protocol](weblinx-r7-dom-auditor-protocol.md) was fixed before inspecting actual R7 snapshots. The previous [R6 source](weblinx-r6-django-trace-results.md) and the independent Flaskr work remain unchanged.

## Primary result

The native Trace-only auditor inferred **all four scored outcomes correctly in all 48 cases** after the DOM snapshots were decoded. An independent per-evidence-tier packet auditor also answered all four correctly when given the full event, server and independent SQLite outcome packet.

| Audited question, 48 cases | Native Trace including reconstructed DOM | Event-only tier | Event+WSGI tier | Event+WSGI+SQL tier |
| --- | ---: | ---: | ---: | ---: |
| Q2. Visible row receiving the first trusted click, A/B/none | **48 correct** | 48 correct | 48 correct | 48 correct |
| Q3. Actual user-mutation server POST route, A/B/none | **48 correct** | 48 abstain | 48 correct | 48 correct |
| Q4. Actual stored row changed, A/B/none | **48 correct (UI inference)** | 48 abstain | 48 abstain | 48 correct (separate SQL readback) |
| Q5. First click returned or errored | **48 correct** | 48 correct | 48 correct | 48 correct |

Q1 is a distinct evidence-specific question: native Trace recorded a **literal first-click selector expression** in all 48 cases; the compact packet recorded the **locator category** in all 48. These levels of specificity differ, so they are not combined into one deceptive equality metric.

There are **no wrong answers and no abstentions** in the full native Trace DOM auditor on the four scored questions of these controlled trials. That is a meaningful positive result for the established Playwright Trace baseline, which we had previously evaluated only by explicit machine-readable action and network fields. There is no evidence in this experiment that extra event/SQL logging improves outcome classification accuracy for these specific Django workflows.

## The actual original DOM was decoded

A safe single-case [format probe](../scripts/weblinx_r7_trace_probe.py) observed that Playwright 1.65.2's `frame-snapshot` records store compact DOM node arrays, with unchanged subtrees referenced as `[[back, node-index]]`. The [DOM reader](../scripts/weblinx_r7_trace_dom_auditor.py) reconstructs these historical references using Playwright's postorder node indexing, parses the native Admin user table, and joins **source-listed, click-action, and final listed** DOM snapshots. It avoids raw-JSON substring searches.

On the **first** full original-source execution:

- **1,088 / 1,088** full or partial DOM snapshots reconstructed successfully;
- **14,825** historical subtree references resolved, **zero** unresolved;
- **847** Django admin user-list DOM snapshots recognized;
- **42** snapshots containing the original Playwright action-target marker recognized;
- **48** completed source tasks, with SQL effects **A:16**, **B:8**, **none:24**, matching the independent SQL measurements.

The Trace auditor sees only the raw ZIP and static, synthetic A/B user-ID mapping. It uses action snapshot target markers and native row text, with conservative inference for failed clicks and forced overlays. It compares the initial and final actual Django user-list DOM, including displayed first_name values and row deletions. It reads the native Trace network POSTs and before/after click action status. **It does not see the independent browser event callback, WSGI request log, SQL database or truth casebook during inference.**

The [packet auditor](../scripts/weblinx_r7_compare_auditors.py) receives only its allowed layer of actual event receiver, actual WSGI server route and/or committed SQLite readback. It has no Trace, DOM snapshots or results table during inference. The individual case answers are joined to the independent truth labels only after both auditors have produced their answers. All 48 cases, including action timeouts, ambiguity errors and no-op outcomes, are retained. The first baseline success conditions and no-effect standard overlays must pass before scoring.

This is a **deterministic code-based snapshot auditor** under frozen, dummy source labels. It is not a human observer experiment, an LLM-as-judge study, or a claim about natural agent error frequency. A blinded human trace-review task remains untested.

## What this does, and does not, prove

The earlier Round 6 audit found **no explicit authenticated `isTrusted` event record** and **no independent SQLite oracle inside the browser Trace**. Those statements remain correct. Round 7 demonstrates that an auditor can nonetheless **infer the same targets correctly** from Trace's native action markers, DOM snapshots, and network information for all 48 controlled Django tasks.

There is a clear difference between:

1. **Prediction/evidentiary reconstruction:** which row was clicked and which stored row probably changed, inferred from the browser's own Trace;
2. **Independent attestation:** a separate trusted browser-event observation and a new SQLite read after the application operation.

The two representations achieved **identical empirical classification results** on the frozen 48 cases but possess different evidence provenance. The retained packet's answers for the SQL question are simply the independent SQLite oracle included in the packet. Its perfect accuracy is therefore an expected property of its evidence, **not** a novel prediction algorithm or an independent validation set.

R7 is designed to detect the difference. It does not demonstrate a necessary accuracy improvement over Playwright Trace. It does show that provenance and measured audit-question-specific retention remain separate research dimensions. New experiments need **visually indistinguishable but server-divergent outcomes**, delayed external effects, or untrusted/incorrect UI feedback to measure when a browser Trace's accurate-looking state inference genuinely fails.

## Actual storage, with unequal information content

All packet sizes use canonical sorted-key compact JSON and **zlib level 9 per episode**, and include only the information needed for the declared questions. The native Trace size is its original ZIP size with DOM snapshots and network records. The first original full run measured:

| 48-case evidence retained | Real compressed bytes |
| --- | ---: |
| Request/intent packet | 3,670 |
| Request + event observation | 5,026 |
| Previous + WSGI server route | 5,734 |
| Previous + SQLite result | **7,290** |
| Native Playwright Trace with complete DOM snapshots | **1,655,362** |

The native Trace preserves much broader history, timing, DOM and network resources than the narrow question packet. Conversely, the packet has **additional privileged WSGI/DB observations** absent from native Trace. Storage differences here are **descriptive, not equal-function compression ratios**, and should not be cast as a general trace-cost advantage.

## Source controls and validity limitations

- External codebase: original unmodified Django Admin and `auth.User` at signed tag commit `4f382ca672f86dd4a1e4d071c91d0caad0e124b3`, version Django 5.2.12;
- Chromium 159.0.8154.6, Playwright 1.65.2, Python 3.11.18;
- fixed 48 conditions from R6, no selective exclusion;
- original R7 snapshot-format discovery and all sources/rules published;
- parser refuses to assert "no state change" from a lone DOM snapshot; separate initial and later tables are necessary;
- no screenshots of user activity, raw Trace ZIPs, browser cookies, account tokens, session files, raw HTML or unredacted selectors are exported;
- R6 earlier original invalid calibration runs documented in its protocol; R7 first valid blind source run is [45067176933](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45067176933).

Original R7 SHA-256:
- 48-case JSON summary `2a72e1fae82360ca0ef255a6e00cbc6895ed0772048b80c1ea0fde0a5efa749c`;
- 48-case full derived CSV `706fbd149da6de28fb62c28bb9d10dc531a1aff60022cb2e6e82fc6a604c77da`.

## Reproduction and artifact links

- [Fixed R7 protocol](weblinx-r7-dom-auditor-protocol.md)
- [Real DOM snapshot decoder](../scripts/weblinx_r7_trace_dom_auditor.py)
- [Blind auditor and actual Django runner](../scripts/weblinx_r7_compare_auditors.py)
- [Parser regression tests](../tests/test_weblinx_r7_trace_dom_auditor.py)
- [48 individual independent auditor verdicts](../results/weblinx_r7_DOM_vs_packets_48.csv)
- [Full counts, abstentions and actual byte costs](../results/weblinx_r7_DOM_vs_packets_summary.json)
- [Independent full-run reproducibility report](../results/weblinx_r7_independent_repeat.json)

The R7 results remain supplementary research evidence; main TRUSTMORE manuscript and Zenodo DOI remain unchanged pending review of construct validity and implications.
