# Runtime evidence and permission-loss reproduction

This extension is built on the frozen WebLINX artifact v1.0.0. It adds the experiments used in Section IX and Tables VIII–IX of the revised paper. All data here concern synthetic users in local databases; no real account information is needed.

## Offline check

From the repository root with Python 3.11:

```bash
python scripts/verify_paper_artifact.py
python scripts/effects/verify_effects.py
```

The first command verifies archived WebLINX results. The second independently decodes the archived packet payloads, recomputes the eighth (pre-predicted loss list) encoding, verifies the collision partitions and runs 4,096 actual SQLite deletions in an independently constructed finite model. The finite model is not additional browser data. Packet sizes are compact UTF-8 JSON and zlib level 9 per condition, including identifiers, method/version, target ID and success flag. The decoder check with a false success flag is a model check, not a failed browser run.

## Actual browser rerun

Use a fresh virtual environment, Python 3.11, and a Linux Chromium environment. Install:

```bash
python -m pip install -r requirements-effects.txt
python -m playwright install --with-deps chromium
python scripts/effects/django_user_trace.py
python scripts/effects/group_trace_diagnostic.py
mv out_permission_loss out_trace_diagnostic
python scripts/effects/group_permission_packets.py
```

Repeat in a fresh process, using a different output directory or moving the generated directories before rerunning. The user-row study uses a matrix of 48 edit/delete and locator conditions with controlled browser-side DOM interventions. The group deletion study uses unmodified upstream Django Admin and ordinary seeded grant relations, no DOM intervention. It has six pairs, 12 assigned conditions across nine initial grant-relation states, with two repetitions. Each group script independently verifies SQLite truth, Django permission decisions and protected-form GET transitions. The trace diagnostic and packet comparison are distinct experiments. Raw traces/databases exist in temporary directories only.

## Claims and source records

| Paper result | Included record | Original source run |
| --- | --- | --- |
| 48 user-edit/delete conditions; four Trace answers correct | user_trace_cases.csv, user_trace_summary.json | [first](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45067176933), [repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45067470635) |
| Table VIII: equal marginal loss counts, swapped user/permission loss pairs; aligned DOM and body diagnostics | group_trace_diagnostic.json | [diagnostic](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45748941364) |
| Table IX: seven native packet encodings and actual permission loss sets, two repeats | group_permission_packets.json | [native packet run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45749386174) |
| Eighth predicted loss list and finite-model 4,096 worlds (22 ambiguous with both margins) | verify_effects.py | independent offline computation |

Files in results/effects/group_*.json are exact parsed result objects from the corresponding completed source-job log lines, not copies of the entire CI ZIP. Source scripts were extracted from the frozen workflow commits 4e3f06e86761fca99bee2946489741b7423e2b94 and 01616d7fe7df308ad80d35f0117d0c7d2cac3c2d; imports and output names were adapted for a standalone directory. The 48-case scripts are from the same pinned source tree.

## Interpretation

The core pairs agree on selected normalized DOM/document HTTP and administrator-log fields, not entire Trace ZIPs. The final diagnostic aligns 208 core DOM pairs; two additional snapshots are unmatched; 600 referenced bodies were recovered and 864 network records lack a body reference or inline body. The first row experiment infers observed state from UI; the independent SQL and protected-form measurements are separate evidence. The predicted loss list is conditional on successful deletion and stable other grants. The observed list depends on actual before/after observations. Acquisition, authentication, attribution under concurrency and validation costs are outside this storage comparison. The cohort is deliberately constructed; its collision counts are not population error rates.

No raw Trace, screenshot, browser session, local database, real user identifiers, or private editing history is distributed. The WebLINX rights boundary and original MIT license remain unchanged.
