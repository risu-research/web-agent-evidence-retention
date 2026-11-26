# Runtime evidence and permission-loss reproduction

The experiments in Section IX and Tables VIII–IX use synthetic users in local Django databases. This guide covers the browser runs, the evidence records and the independent finite-model check.

## Offline check

From the repository root with Python 3.11:

```bash
python scripts/verify_paper_artifact.py
python scripts/effects/verify_effects.py
```

The first command verifies archived WebLINX results. The second independently decodes the archived packet payloads, recomputes the eighth (pre-predicted loss list) encoding, verifies the collision partitions and runs 4,096 actual SQLite deletions in an independently constructed finite model. The finite model enumerates possible grant relations separately from the browser experiments. Packet sizes are compact UTF-8 JSON and zlib level 9 per condition, including identifiers, method/version, target ID and success flag. False success flags are tested in the model.

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

Repeat in a fresh process, using a different output directory or moving the generated directories before rerunning. The user-row study uses a matrix of 48 edit/delete and locator conditions with controlled browser-side DOM interventions. The group deletion study uses unmodified upstream Django Admin and grant relations seeded in the database before the action. The group pages and deletion handler use the upstream implementation. It has six pairs, 12 assigned conditions across nine initial grant-relation states, with two repetitions. Each group script independently verifies SQLite truth, Django permission decisions and protected-form GET transitions. The trace diagnostic and packet comparison are distinct experiments. Raw traces/databases exist in temporary directories only.

## Claims and source records

| Paper result | Included record | Original source run |
| --- | --- | --- |
| 48 user-edit/delete conditions; four Trace answers correct | user_trace_cases.csv, user_trace_summary.json | [first](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45067176933), [repeat](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45067470635) |
| Table VIII: equal marginal loss counts, swapped user/permission loss pairs; aligned DOM and body diagnostics | group_trace_diagnostic.json | [diagnostic](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45748941364) |
| Table IX: seven native packet encodings and actual permission loss sets, two repeats | group_permission_packets.json | [native packet run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45749386174) |
| Eighth predicted loss list and finite-model 4,096 worlds (22 ambiguous with both margins) | verify_effects.py | independent offline computation |

The files in `results/effects/group_*.json` contain the parsed result objects emitted by the completed source jobs. Source scripts were extracted from the frozen workflow commits 4e3f06e86761fca99bee2946489741b7423e2b94 and 01616d7fe7df308ad80d35f0117d0c7d2cac3c2d; imports and output names were adapted for a standalone directory. The 48-case scripts are from the same pinned source tree.

## Interpretation

The comparison covers selected normalized DOM, document HTTP and administrator-log fields. The diagnostic aligns 208 core DOM pairs. Two additional snapshots remain unmatched. It recovers 600 referenced bodies, and 864 network records contain neither a body reference nor an inline body. The first row experiment infers observed state from UI; the independent SQL and protected-form measurements are separate evidence. The predicted loss list is conditional on successful deletion and stable other grants. The observed list depends on actual before/after observations. Acquisition, authentication, attribution under concurrency and validation costs are outside this storage comparison. The collision counts describe the constructed conditions.

The distributed outputs contain synthetic identifiers, decoded evidence records and numeric diagnostics. Raw traces, screenshots, sessions and local databases are temporary files. See the repository license and WebLINX dataset terms.
