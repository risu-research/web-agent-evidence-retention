# Original computation record

The confirmatory results came from the following public GitHub Actions run:

- Source commit: [`0f7f5a1c2f2110bfd8c2727ae6cac6f3c31ffd94`](https://github.com/risu-research/frb-exec-2609/commit/0f7f5a1c2f2110bfd8c2727ae6cac6f3c31ffd94)
- Run: [37231457813](https://github.com/risu-research/frb-exec-2609/actions/runs/37231457813), successful on October 4, 2026
- Source path: `jobs/j-4c9e-confirm/confirm.py`
- Original source blob SHA: `76110fb8cd01ab3a2e826975aa6e1d10ebbe29a6`

The fixed-action candidate-expansion sensitivity used:

- Source commit: [`bf968eef99c2ae93146d7732d2a2c1daca695943`](https://github.com/risu-research/frb-exec-2609/commit/bf968eef99c2ae93146d7732d2a2c1daca695943)
- Run: [37231485056](https://github.com/risu-research/frb-exec-2609/actions/runs/37231485056), successful on October 4, 2026
- Source path: `jobs/j-4c9e-audit/universe.py`
- Original source blob SHA: `a5c8773dee67caea2229fb71b925ecffdb087c03`

The migrated scripts keep the original sampling, compatibility, and calculation logic. The dataset queries now use the revisions recorded in the research protocol, instead of resolving the latest dataset revision when the script starts.

Both historical action artifact archives have expired. The submitted aggregate tables are preserved in `results/`. The checker validates a new confirmatory JSON summary against those reported aggregates after the full experiment runs.

The complete 600-action replay and 598-action candidate-expansion sensitivity both passed independently in [GitHub Actions run 45031621684](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45031621684) on November 22, 2026. See [the reproduction record](reproduction-2026-11-22.md) for the archived summaries, verified checksums, and exact environment.
