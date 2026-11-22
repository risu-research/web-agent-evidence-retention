# Round 3D — focused anomaly attribution and paired XPath dialect comparison

Exploratory audit plan frozen November 22, 2026 **after** observing the R3C action-XPath results.

## Fixed follow-up populations

- Original-source discrepancy cohort: **all 11** original action records where recorded action XPath evaluation did not uniquely select the UID-identified source target (ten `no_node`, one `unique_other_node`). Identified solely by published R3C numeric records.
- Site-native continuity proxy cohort: **all 75** changed-HTML transitions with a unique ordinary HTML `id` and compatible static attributes in both states, as fixed by the earlier R3B protocol and independently listed by R3C. Exactly 73 have the same recorded URL hint.

Select the union of these fixed cohorts **before fetching any HTML** for this follow-up. No subset chosen by the performance of a new comparator.

## Original-action discrepancy audit (11)

On the original directly named source HTML and using the same source parser, classify the start of recorded action XPath as `id(...)`, absolute or other. For root-ID XPath, parse its literal ID argument *in memory* and record whether that site-authored ID exists zero, one or multiple times in original HTML; whether its referenced node is an ancestor of the UID target node; and whether the complete action XPath selects no node or a different node. Record only categorical and numerical indicators. A missing root ID or an outdated relative step is a possible **source expression inconsistency**. It does not establish that a browser click went to the wrong element.

## Paired comparison (75)

Evaluate **two original XPath representations** against the *next directly recorded source HTML*: (a) action `action.arguments.element.xpath`; (b) DMR canonical candidate `[[xpath]]` computed from original source. Declare success only when exactly one selected next-state node equals the independently selected **site-native-id proxy** node. Count no-node, unique other-node, multiple-node, invalid expressions separately; stratify by same/different recorded URL hint and initial computed XPath changed/unchanged. The proxy itself remains unadjudicated. Report paired recovery and disagreements, not causal execution error.

Never expose exact locator values, ordinary site ids, URLs or page content in artifacts. Read only 11+75 source action keys from the official 600-action casebook; preserve all selected keys and record any missing evidence.

## Scientific gate

Distinguish a difference in XPath *generator* from a proven loss of a logical target. A useful next experiment requires blinded identity judgments or an authoritative site event trace before quantifying incorrect action outcomes.
