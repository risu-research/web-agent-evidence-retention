# Round 3C — evaluating recorded XPath expressions in original DOM snapshots

**Frozen after observing the R3A recording-format mismatch and before evaluating any recorded XPath expression.** Follow-up is exploratory. Source population remains exactly the 600 action/turn keys in the 55 demonstrations and the same frozen original WebLINX revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. R3A exposed that the 600 Replay action XPath strings differ literally from the DMR candidate XPath, though the latter equals the corresponding source DOM computed XPath for all 600. Literal equality of XPath strings is therefore a **serialization test**, not an element identity test.

## Procedure

1. Re-fetch the same replay, positive candidate, and directly recorded HTML source files. Verify the original R3A 600 UID/DMR/HTML concordance from first principles. Preserve 600 unique (demonstration, turn) keys.
2. For each original Replay `action.arguments.element.xpath`, parse/evaluate the expression against the *recorded source DOM*. With the same pinned `lxml` parser as Round 2, categorize the expression as a root-ID-function locator (`id(...)`), absolute path, double-slash path or other. Never export literal XPath, site URL, source HTML or user content.
3. A successful expression matches exactly one actual DOM node, whose computed source XPath equals the independently located UID target node's source XPath. Track zero-node result, multiple-node results, a single different node, parse/evaluation error, or unrecognized expression separately. The UID target is the source dataset's own recorded target, not an independent runtime event recipient.
4. Evaluate the **same exact action XPath string** on the next browser observation's directly recorded HTML where available. Count changed/unchanged HTML pairs, empty, single and multiple results. A returned node at the same position is syntactic continuity only.
5. Separately, for the fixed **75 R3B site-native-id continuity proxy candidates**, classify the next expression's result as selecting the proxy node, a different node, no node, multiple nodes or evaluation error. Report the same-URL-hint subgroup separately. This site-native identifier is a plausible matching proxy, not an adjudicated logical identity label.
6. Report null cases when the next HTML is unavailable, changed URL, or the source record fails selection. Never silently filter or substitute later browser states. Neither side may use a browser execution action or webpage modification.

All comparisons are output as numeric counts and public demonstration/turn keys. Preserve source hashes, no raw locator values. Record exact provenance, unit tests and independent repeat output hashes. Any apparent mismatch on the later page is a **changed-snapshot locator observation**, never an observed wrong click or an independently proven logical-target error.

## Decision gate

If the recorded XPath dialect can be evaluated reliably and nontrivial changed-snapshot differences exist in the site-native proxy cohort, use that cohort only to prioritize blinded independent target adjudication. The true XPath persistence accuracy remains unmeasured until adjudication and dynamic browser execution are established.
