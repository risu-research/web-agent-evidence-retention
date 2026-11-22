# R4B recorded XPath terminal-root audit

Declared 2026-11-22 after the R4 source-semantic results. Exploratory follow-up on the **same exact 86 source actions** from `results/weblinx_continuity_r4_cases.csv` only. Preserve that file's original digest before analysis.

In R4, all 75 site-native-ID proxy cases showed the captured action XPath's root `id(...)` referred to the **target node itself** and the ID remained unique in next HTML. R4B distinguishes a full `id(...)` expression with no trailing XPath steps from an expression that only begins with `id(...)`.

Retrieve Replay `action.arguments.element.xpath` for all original keys, along with the DMR target's ordinary HTML id. For every recorded XPath, report: root-ID expression present, root value equals DMR ordinary id, expression **ends immediately after** the closing `) ` (ignoring whitespace), expression includes an additional path or function suffix, or other XPath grammar. Reuse recorded source checks from R4 instead of inventing a cross-state identity label.

This compares string syntax and source-native id reuse only. If all 75 captured XPath expressions are precisely `id("target-id")`, the earlier 75/75 source-native-id proxy comparison is deterministic given the proxy-selection rule, and this must be explicitly reported. If some contain suffixes, preserve the exact counts and investigate separately. The 11 original-source anomalies remain in the analysis and are never reclassified as executed browser failures.

Publish only categorical counts and public action keys, never the raw `id` values, XPath strings, page HTML or URLs. The group selection is fixed by the SHA-verified 86-case R4 artifact. No independent same-element ground truth or receiver-event trace is available.
