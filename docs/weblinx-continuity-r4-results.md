# Round 4 — Independent non-ID evidence and XPath anchor dependence

**Research status: source verification complete; independent logical-target identity remains unresolved.**

This study expands the pinned WebLINX original-source audits R1–R3D. The fixed follow-up population was set in the [R4 protocol](weblinx-continuity-r4-protocol.md) before loading the selected source HTML: all **8** captured-only XPath proxy matches, all **67** paired-success proxy matches, and all **11** original-source XPath anomalies. These 86 actions span 33 demonstrations.

Source dataset: `McGill-NLP/WebLINX-full`, revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. The first independent-channel source run retrieved **145/145 original named HTML files**. Its derived source outputs were reproduced byte-for-byte by a second full run.

## 1. The 75/75 native-ID comparison has a shared reference key

A separate [R4B exact-expression audit](weblinx-continuity-r4b-protocol.md) retrieved all 86 original recorded XPath strings and the original candidate's ordinary HTML `id` in memory.

Among the previously reported **75/75** captured-Replay XPath matches, **all 75** XPath strings have exactly the form `id("X")`, with no trailing path segment, and the `X` is precisely the original target's ordinary HTML `id`. The earlier proxy definition requires that same `id` to occur uniquely in the subsequent HTML. All 75 also satisfied that requirement in the raw HTML comparison.

Consequently, **the captured-XPath success count is determined by the proxy-label selection rule**. The 75/75 number is valid as a source-string/HTML consistency result. It supplies no independent demonstration of durable logical-element identity, browser-event delivery, or an advantage over a locator with a different root-ID generator.

The canonical DMR XPath's **67/75** source-proxy matches remain descriptive of whether the original absolute DOM path selected the element carrying the matching ordinary HTML `id` after page changes. The original paired **8/75** difference likewise describes two XPath representations under this constructed proxy criterion. Its earlier bootstrap interval quantifies variability among those selected demonstrations, with the same construct-dependence.

## 2. Blind corroboration without XPath, either ID or DOM position

To measure how much corroboration remained after removing the shared reference key, the R4 matcher received only source HTML tags, short descendant text, and selected semantic attributes. It excluded XPath, the ordinary HTML `id`, the WebLINX `data-webtasks-id`, DOM positions, CSS class, coordinates and labels indicating the original XPath outcome.

A source channel counted only if its exact normalized tag/value signature occurred once in the original HTML and once in the next HTML. After matching, the independently found next node was compared to the frozen site-native-ID proxy. Distinct corroborating families are text, test attribute, link destination, form name/type, and accessible label/placeholder. Contradictions and duplicate matches were counted, with no omitted cases.

| Independent non-ID evidence in the changed HTML | 8 captured-only cases | 67 paired-success cases | All 75 |
| --- | ---: | ---: | ---: |
| Two or more different semantic families uniquely choose the proxy | 3 | 19 | **22** |
| Exactly one semantic family uniquely chooses the proxy | 5 | 34 | **39** |
| No unique independent semantic family corroborates the proxy | 0 | 14 | **14** |
| Unique semantic source channel selects a different next node | 0 | 0 | **0** |
| **Total** | **8** | **67** | **75** |

The eight captured-only cases span five demonstrations. They all carry at least one matching non-ID semantic cue, and three have two or more different families agreeing. In the entire 75-case proxy sample, only **22/75** satisfy the stricter multiple-family criterion. Fourteen cases lack unique corroboration beyond the ordinary HTML `id`.

**Interpretation:** Semantic cues independently corroborate a subset of native-ID proxy links. Matching form attributes, visible text or link values can persist when the page is rerendered. Multiple cues improve evidential specificity, but attributes and text may also be repeated or reused by an application. Hence the strictest result is a candidate pool for external adjudication, rather than a newly verified ground-truth set.

## 3. Original-source action XPath anomalies (all eleven)

Of the original 600 recorded actions, **11** Replay XPath expressions selected a different or missing DOM node in the directly linked saved HTML (ten no-node outcomes, one other-node result). R3D identified seven cases with a missing root HTML `id` and four with an existing root that was an ancestor of the recorded target.

The R4 non-ID source-semantic audit found:

| Original HTML's non-ID semantic evidence for the recorded target | Original XPath anomaly cases |
| --- | ---: |
| At least one unique semantic channel identifies the target | **4** |
| No unique semantic channel available | **7** |
| Two or more independent semantic families identify the target | **0** |
| **Total** | **11** |

The follow-up R4B string audit found that six of the 11 recorded XPath expressions are terminal `id(...)` locators and five add path segments after the initial root ID. None of their root-ID arguments equals the target's own ordinary HTML `id`.

These are concrete differences between the recorded action expression and a later saved document. Source snapshot timing, browser DOM transformations and the extension's locator construction remain open explanations. No independent event-receiver trace exists for those 11 actions.

## 4. Reproducibility and decision gate

- [Frozen R4 protocol](weblinx-continuity-r4-protocol.md)
- [Independent-channel source code](../scripts/weblinx_continuity_r4.py)
- [Full R4 numerical casebook](../results/weblinx_continuity_r4_cases.csv)
- [R4 original aggregate result](../results/weblinx_continuity_r4_summary.json)
- [R4B exact terminal-ID protocol](weblinx-continuity-r4b-protocol.md)
- [R4B expression classifier](../scripts/weblinx_continuity_r4b.py)
- [R4B numeric casebook](../results/weblinx_continuity_r4b_cases.csv)
- [R4B original summary](../results/weblinx_continuity_r4b_summary.json)
- [R4 original source run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45058961877)
- [R4 independent replay](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45059119401)
- [R4B original lexical source run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45059246779)

The R4 source-run summary SHA-256 is `55b98569ecb625dc1c3f113eb95b2dfc8a62c7340a46e3668aec165490c7343d`, with per-action file `1ba4e6d6bdc0c5060f693a201bbe0d7696fef7ae27d89bc9f3da361eb271494d`.

The R4B original summary SHA-256 is `957fedbe94d53cc538dba340f1f8343d98b5a3dc9ea7d9f0f41e569c5a092f7e`, with per-action file `96845e26767d49356437a87c92bff03ef892986e2f422b06146ec9d785e34480`.

### What qualifies for the main manuscript?

The source consistency and stored-XPath dialect findings are defensible as measured facts. The previously described R3D 75/75 **relative durability** interpretation needs the present correction: the selected proxy is keyed by the same native ID as the captured locator. This change in evidential interpretation should precede any claim of a class jump.

Logical-element continuity and actual browser-action delivery still need labels from a truly independent source. A rigorous next step is a blinded, dual-adjudicator review of 8 discordant cases, multi-family-matching controls and hard negative controls, or an instrumented browser runtime that records the actual event path and resulting application state. The 14 source pairs lacking any independent non-ID semantic match should remain unadjudicated from HTML alone.

The public casebooks contain only demonstration/turn keys, numeric evidence coverage and categorical outcomes. Original URLs, site IDs, user text, exact XPath expressions and HTML remain with the pinned source dataset. No new Zenodo release or manuscript revision occurred during R4.
