# Round 3C — Captured XPath expressions on original and next HTML

The fixed population is the original 600 WebLINX actions in 55 demonstrations. This study followed the source-provenance [Round 3A/B result](weblinx-continuity-r3-results.md) using the protocol frozen **after** discovering that the action XPath strings differ from the canonical DMR XPath. All HTML was fetched from `McGill-NLP/WebLINX-full` at revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.

> **Validity correction from Round 4.** Every one of the 75 source-native-id proxy cases has a Replay locator whose full syntax is exactly `id("target HTML id")`. Because the proxy is also selected using that preserved HTML ID, its 75/75 Replay locator match follows by construction. See [Round 4](weblinx-continuity-r4-results.md) for a blinded test that excludes both IDs and both XPath representations.

## The XPath dialect matters

Of the 600 captured `action.arguments.element.xpath` expressions, 568 start with an XPath `id(...)` function and 32 are absolute source paths. The DMR candidate `[[xpath]]` string equals the `lxml` source XPath for all 600 targets. **All 600 action XPath strings differ literally from the canonical DMR XPath**, but literal string inequality does not mean that two expressions select different source elements.

Evaluating each captured action XPath against the **exact original recorded HTML** produces:

| XPath result on original HTML | Actions |
| --- | ---: |
| Selects the recorded UID target as its only element | **589** |
| Selects no DOM element | 10 |
| Selects one different DOM element | 1 |
| Multiple nodes, invalid XPath, or other | 0 |
| **Total** | **600** |

All eleven mismatches use the `id(...)` expression dialect. The eleven-case source-expression audit is a separate post-observation follow-up. This is a mismatch between recorded source expression and recorded source snapshot; the browser click recipient was not independently observed.

The original DMR candidate UID, Replay action element UID and the source HTML target are aligned for 600/600, and the DMR XPath equals the computed HTML XPath for 600/600. The source-consistency baseline therefore remains intact.

## Applying the same captured XPath to the next recorded HTML

Of 600 original actions, 560 have a directly recorded next HTML source. When the **unchanged original captured XPath** is evaluated in that later snapshot:

| Next-source XPath evaluation | Actions |
| --- | ---: |
| Exactly one DOM element found | 458 |
| No DOM element found | 102 |
| Next source HTML unavailable | 40 |
| Multiple or invalid result | 0 |
| **Total** | **600** |

Among the 458 unique next-state matches, 432 have the same WebLINX UID as the original target and 26 have a different or missing UID. A selected next node with the same source UID is a **syntactic link across recorded states**. It is not an independently adjudicated logical-element match.

The **75 R3B site-native-id proxy cases** are the stricter supplementary subset where the same ordinary HTML `id` appears uniquely in two byte-distinct documents with a compatible tag and stable attributes. The captured action XPath selects that native-id proxy node in **75/75 cases**, including 73 cases with the same recorded URL hint. Notably, this includes the 16 cases where the old canonical DMR XPath differs from the proxy node's computed XPath in the next state.

These source-level observations indicate that an action XPath built from a stable root ID can survive some source path changes better than a fully absolute generated DOM XPath. **The next comparison must execute both XPath generators on the same 75 source pairs**, with the same proxy-based outcome definition. The proxy can still refer to a newly rendered site element, so a genuine identity or browser-execution success rate remains unavailable.

## Consequences for the accepted manuscript

The present result is relevant to experimental validity: an explicit, executable action locator and a canonical candidate XPath represent **different recorded evidence artifacts** even when they describe the same source target. The 11 original-source discrepancies and 102 next-source empty lookups are concrete observations, with source provenance attached. Their interpretation depends on the originating XPath generator and event-time DOM semantics.

Current results **do not imply** 11 clicks were incorrect or 102 future actions would have failed. They mark places where a later auditor needs additional source or execution evidence.

## Original verification and reproducibility

- [Frozen follow-up protocol](weblinx-continuity-r3c-protocol.md)
- [Executable XPath evaluator](../scripts/weblinx_continuity_r3c.py)
- [600-row derived source evaluation](../results/weblinx_continuity_r3c_actions.csv)
- [Exact aggregate result](../results/weblinx_continuity_r3c_summary.json)
- [First successful full run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45057156651)
- [Independent second full run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45057539929)

Both runs regenerated their summary JSON and 600-row casebook byte for byte, with fixed source revisions and deterministic definitions.

- SHA-256 `r3c_summary.json`: `39ebd980e586d277c9d9c9f6c9e5eefdbcc127cc1b895f86531809b9890c2d0d`
- SHA-256 `r3c_action_xpath_600.csv`: `3b7b48d0dcec1f681ee3ffb4888533c76ec524cbb30130c08d493deef5add71b`

Public outputs contain numeric and categorical diagnostics only. No page HTML, original element locator, user text, screenshot or account detail is published.
