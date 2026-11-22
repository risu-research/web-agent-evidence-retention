# R5B-2 — Real Flaskr POST accepted by HTTP layer, zero SQLite commits

**Six-case server-side validation control.** This supplementary study was frozen in the [R5B-2 protocol](weblinx-round5b2-server-rejection-protocol.md) after the original R5B-1 48-case study. It is a separate prospective negative-control cohort in the **same external maintained application**, the official Flaskr example from `pallets/flask` at pinned Git commit `49943b5a94413a530761350f04e896f76e8d620e`.

The original Flaskr source validates update titles on the server. When a submitted title is empty, Flaskr flashes `Title is required.`, returns HTTP 200 with the edit form, and leaves SQLite unchanged. This is the application's documented and source-verified validation pathway. The harness removes the **browser input's HTML `required` attribute** in the loaded page immediately before submission, allowing a real browser POST with an empty title. No server handler, database schema, template file or application validation rule is patched.

## Original six-case result

Three link locators (positional, exact edit URL and contextual article heading) crossed with two DOM conditions (baseline and order-swapped) yield six independent browser contexts, servers and SQLite files. In all six:

- The first Edit-link click was real, trusted and returned normally;
- The original Flaskr edit form opened through a real GET route;
- The original Save form submitted an empty title through a genuine **POST** request;
- The Flaskr server returned **HTTP 200** with its existing validation message;
- A separate SQLite connection found **zero changes** to either stored post A or B;
- Reloading the Flaskr index confirmed that the visible original posts matched the database.

The positional locator in the reordered-page condition opened post B's original Flaskr edit page. It also submitted an invalid title that failed server validation. Thus the correct persistence claim is zero SQL changes for both original rows, including when the first link selected B.

The first complete run recorded **six POST responses, all status 200, and zero committed changes**. Its genuine Playwright Trace ZIPs (snapshots enabled, screenshots and code sources disabled) totaled **53,512 bytes**, with 498 trace records and 48 network records. Raw Trace archives were destroyed after measurement and are not released.

| Independent observation | Cases |
| --- | ---: |
| Trusted browser first click returned | **6/6** |
| Actual Flaskr edit POST recorded | **6/6** |
| Edit POST received HTTP status 200 | **6/6** |
| Flaskr native validation message rendered | **6/6** |
| Independent SQLite A or B change | **0/6** |

This negative control directly addresses one limitation of R5B-1: an HTTP request being received and answered by the app does not necessarily mean that the requested data mutation took effect. Request logs, event logs and browser Trace can show the request and response; an independent SQL readback establishes the stored result for this app.

The controlled removal of an HTML input constraint is an explicit test intervention. The server's native validation behavior is unchanged. These six negative cases are not sampled from real agent traffic and must remain separate from the original 48-case matrix.

## Source and reproducibility

- [Frozen source protocol](weblinx-round5b2-server-rejection-protocol.md)
- [Unmodified upstream Flaskr commit](https://github.com/pallets/flask/tree/49943b5a94413a530761350f04e896f76e8d620e/examples/tutorial/flaskr)
- [Source-linked real browser runner](../scripts/weblinx_round5b2_server_rejection.py)
- [Six numeric cases](../results/weblinx_round5b2_rejection_cases.csv)
- [Source hashes, response counts and Trace byte metrics](../results/weblinx_round5b2_rejection_summary.json)
- [First complete source run](https://github.com/risu-research/web-agent-evidence-retention/actions/runs/45063079721)
- [Source experiment comparison](../scripts/weblinx_round5b2_compare.py)

Original-run SHA-256:
- Derived summary JSON `a0dbc1fbddb16bc8ef17959428d20443761c32695cfea1e5eef354d91a7190f6`
- Six derived numeric cases CSV `7f3fab73f08ccfd6df670cfd5ba7847a766faa8fb0aad0b10d3a8621b1569084`

The original source hashes of `flaskr/blog.py`, `schema.sql` and all relevant HTML templates are retained in the numeric summary. No user accounts, cookies, literal session IDs, real text, screenshots, or raw Trace ZIPs are exported.

The principal R5B-1 dataset remains exactly 48 cases. R5B-2 adds six separate server-rejection negative controls. A future evaluation should use at least one different maintained web application and a separate action/effect reference for independent generalization.
