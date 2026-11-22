# Round 3D — Paired captured XPath vs source-canonical XPath

## Source, timing and scope

This is a **post-observation exploratory follow-up**, frozen after the Round 3C source-executed action XPath experiment. Its union cohort is fixed from the archived [600-row R3C action table](../results/weblinx_continuity_r3c_actions.csv):

- All **11** recorded-action XPath expressions that failed to identify the dataset-recorded target in the same source HTML.
- All **75** independently selected *site-native ID proxy* cases from byte-changed adjacent source HTML pages.

The sets have no overlapping actions, giving **86 unique source actions**. This study re-fetched **152 original HTML files** from `McGill-NLP/WebLINX-full` revision `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`. The original [predeclared R3D rules](weblinx-continuity-r3d-protocol.md) determine every classification.

## A. Recorded-action XPath mismatches on their own source HTML

Round 3C evaluated the 600 captured action XPath expressions on the **same** recorded HTML snapshot and found 589 selecting the expected source UID target, ten selecting no element and one selecting a different element.

All 11 anomalies use XPath's `id(...)` root expression. The focused source audit measured the root ID's presence:

| Original-source discrepancy mechanism | Cases |
| --- | ---: |
| Root site-native ID referenced by the action XPath absent from saved HTML | **7** |
| Root ID unique and present, with recorded target inside the root subtree, but full expression unresolved or selecting a different node | **4** |
| **Total original-source anomalies** | **11** |

This demonstrates a concrete difference between the recorded action expression and the directly linked HTML state. It does **not** establish that the browser delivered an incorrect event. The extension's event-time DOM and its retained page HTML might represent different moments or tree representations.

## B. Same-next-source comparison of two XPath generators

Within the 75 source-native-id continuity *proxies*, both original XPath expressions were executed against the **same next HTML**. A reconstruction is classified as a unique proxy match only if it selects the node carrying the original site-authored `id` uniquely in the second snapshot, with compatible tag and stable element attributes.

| Original locator | Selects site-native proxy on later HTML | Source cases |
| --- | ---: | ---: |
| Replay captured `action.arguments.element.xpath` | **75/75 (100%)** | 75 |
| DMR candidate `[[xpath]]`, canonical absolute source path | **67/75 (89.3%)** | 75 |

Paired outcomes: **67 both succeed, eight captured-action only, zero canonical-only, zero neither**. The canonical path selects no node in seven of the eight additional cases and uniquely selects a different node in one.

Of the 73 proxy cases with the same recorded URL hint, the captured action XPath resolves the proxy in **73/73**, compared with **66/73** for the canonical DMR XPath. The different-URL hint subset consists of two cases, with two vs one matches.

The canonical source XPath text changes between snapshots in 16 cases, but **eight of these still resolve the proxy when executed**. The other eight account for the paired difference. This is an important distinction: changed source XPath strings are not necessarily locator failures. Some original positional expressions can remain valid when the newly computed canonical XPath uses a different, but equivalent path.

The 75 proxy cases span 31 demonstrations; their original `id` values are site authored and not WebLINX-generated UIDs. However, a web app may reuse a native ID for a newly rendered node. The pair is an observational continuity proxy, not an independently adjudicated logical identity.

## C. Paired uncertainty and evidence scope

The observed captured-minus-canonical recovery difference is **8/75 = 10.7 percentage points**. Resampling all **31 demonstrations** as clusters with 5,000 fixed-seed bootstrap replicates gives a descriptive 95% interval of approximately **2.8–19.2 percentage points** (seed `2026112239`). This uncertainty is conditional on the original post hoc 75 proxy cases and their websites. It is not a population-wide browser-action accuracy result.

The combined R3 evidence changes the research question. There are at least two different exact XPath representations associated with one recorded action: 568 Replay action locators use a root `id(...)` syntax, and all 600 DMR candidate XPaths match the parser-computed absolute source path. The canonical source paths are exact in the original 600 snapshots; the captured action expressions have 11 source discrepancies. Among the 75 later-state site-native proxies, the captured expressions more often select the proxy. A broad claim that “XPath is robust” or “XPath fails when pages change” would conceal these generator and state differences.

We have **not** measured actual event delivery, independently adjudicated logical-element identity, or a verified incorrect-action rate. Before this result changes the main manuscript's conclusions, a source-independent target identity procedure and actual runtime trace comparison would be needed.

## Data and method

- [Fixed Round 3D post-observation protocol](weblinx-continuity-r3d-protocol.md)
- [R3C original source baseline](weblinx-continuity-r3c-results.md)
- [R3D source code](../scripts/weblinx_continuity_r3d.py)
- [86 selected action diagnostics](../results/weblinx_continuity_r3d_cases.csv)
- [Derived R3D aggregates](../results/weblinx_continuity_r3d_summary.json)
- [Demonstration-cluster paired bootstrap](../results/weblinx_continuity_r3d_cluster_bootstrap.json)
- [First full R3D run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45057674650)

Original-run SHA-256:
- `r3d_summary.json`: `66a8e5767d58a0fe6eb4c5560841c424202dbbeb6a7e6653eee25af06454a158`
- `r3d_selected_cases.csv`: `234352ddb7656d7f8d8f60a65f5222fc971f37a6dea0f1b983bfb6dc54646e61`

All public outputs are numeric. Original HTML, site IDs, source URLs, candidate UIDs and literal XPath strings remain at the original publisher's pinned source revision. Zenodo and the manuscript remain unchanged by this feasibility audit.
