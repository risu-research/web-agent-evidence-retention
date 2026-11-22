"""R8: actual original-Django browser traces with a hidden server-side effect.

The contrast is disclosed and synthetic. The original Django app, User model,
forms and templates are unchanged. R7 Trace auditor sees *only* the native
raw Playwright Trace and public dummy ID mapping. Independent SQL readback is
joined after both auditors have answered. No raw traces/screenshots exported.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
import threading
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from wsgiref.simple_server import make_server

import weblinx_r6_django_trace as r6
from weblinx_r7_trace_dom_auditor import (
    trace_auditor, read_raw, SnapshotDecoder, rows_from_admin_snapshot
)

OUT = Path("out_round8")
OPS = ("edit", "delete")
LOCATORS = ("positional", "href_exact", "contextual_row")
MODES = ("control", "shadow")
STAMP = "2026-01-01 00:00:00"
NEW_FIRST = "R8-COMMON"
LISTING = "/admin/auth/user/?q=r6_"


def paired_matrix():
    """The six pairs are predeclared; execution order alternates."""
    units = [(op, loc) for op in OPS for loc in LOCATORS]
    return [(i, op, loc, mode)
            for i, (op, loc) in enumerate(units, 1)
            for mode in (MODES if i % 2 else MODES[::-1])]


def B_last_login(dbfile, ids):
    """Independent SQLite connection, never Django ORM or browser state."""
    with sqlite3.connect(dbfile, timeout=20) as db:
        result = db.execute(
            "SELECT last_login FROM auth_user WHERE id=?", (ids["B"],)
        ).fetchone()
    if result is None:
        raise AssertionError("Missing B user in independent SQL read")
    return result[0]


class PostCommitShadowWSGI:
    """Experiment-only response-transparent WSGI boundary.

    For both variants one SQL UPDATE is issued on B after the upstream native
    Django POST produces its response. The bound value is NULL in control,
    the fixed timestamp in shadow. No HTTP response content is modified.
    """
    def __init__(self, app, dbfile, ids, mode):
        if mode not in MODES:
            raise ValueError("invalid mode")
        self.app = app
        self.dbfile = Path(dbfile)
        self.ids = ids
        self.mode = mode
        self.attempts = 0
        self.events = []
        self.lock = threading.Lock()

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "")
        path = environ.get("PATH_INFO", "")
        status = []
        def wrapped_start(code, headers, exc_info=None):
            status.append(int(code.split()[0]))
            return start_response(code, headers, exc_info)
        response = self.app(environ, wrapped_start)
        match = re.fullmatch(r"/admin/auth/user/(\d+)/(change|delete)/", path)
        selected = (method == "POST" and match is not None
                    and int(match.group(1)) == self.ids["A"])
        if selected and status and status[0] in (302, 303):
            # The normal admin writes A. This separate *test wrapper* writes B.
            # Both modes follow the identical SQL execution path.
            with sqlite3.connect(self.dbfile, timeout=20) as db:
                cursor = db.execute(
                    "UPDATE auth_user SET last_login=? WHERE id=?",
                    (STAMP if self.mode == "shadow" else None, self.ids["B"])
                )
                if cursor.rowcount != 1:
                    raise AssertionError("Shadow boundary failed to update B")
                db.commit()
            with self.lock:
                self.attempts += 1
        if match:
            with self.lock:
                self.events.append({
                    "method": method,
                    "target": "A" if int(match.group(1)) == self.ids["A"]
                              else "B" if int(match.group(1)) == self.ids["B"]
                              else "other",
                    "operation": match.group(2),
                    "status": status[0] if status else None
                })
        return response


def source_dom_projection(trace_path):
    """Parse authentic R7 compact DOM and native network in the raw ZIP.

    The network projection has only HTTP method, normalized path and status
    for /admin/ requests. No session, token, query, time, port, or body.
    It is an explicitly lossy, stable projection, not raw Trace equality.
    """
    trace, network = read_raw(trace_path)
    decoder = SnapshotDecoder()
    rows = []
    for item in trace:
        if item.get("type") != "frame-snapshot":
            continue
        snap = item.get("snapshot", {})
        if not snap.get("isMainFrame"):
            continue
        tree = decoder.decode(snap)
        if urlparse(snap.get("frameUrl", "")).path == "/admin/auth/user/":
            values = rows_from_admin_snapshot(tree)
            if values is not None:
                rows.append(values)
    if decoder.ref_failures:
        raise AssertionError("Unresolved original Playwright DOM references")
    if len(rows) < 2:
        raise AssertionError("Insufficient actual changelist snapshots")
    # Initial and final fully reconstructed admin list. Independent SQL
    # truth is intentionally not consulted here.
    initial = next((r for r in rows if set(r) == {"A", "B"}), None)
    if initial is None:
        raise AssertionError("Missing complete initial DOM")
    network_projection = []
    for rec in network:
        snap = rec.get("snapshot", {})
        if not isinstance(snap, dict):
            continue
        req, res = snap.get("request", {}), snap.get("response", {})
        if not isinstance(req, dict) or not isinstance(res, dict):
            continue
        path = urlparse(req.get("url", "")).path
        if path.startswith("/admin/"):
            network_projection.append([
                req.get("method"), path, res.get("status")
            ])
    return {
        "initial_rows": initial,
        "final_rows": rows[-1],
        "network_projection": network_projection,
        "snapshots_decoded": decoder.decoded,
        "refs_resolved": decoder.ref_count,
        "ref_failures": decoder.ref_failures,
    }


def browser_image_hash(page):
    """Pixel-level rendered UI gate, screenshot bytes destroyed immediately."""
    page.evaluate("window.scrollTo(0,0)")
    page.evaluate("() => document.fonts.ready")
    return hashlib.sha256(page.screenshot(
        animations="disabled", full_page=False
    )).hexdigest()


def packet_auditor(packet):
    """Q6 is read from independently observed before/after SQLite values."""
    if ("before_B_last_login" not in packet or
            "after_B_last_login" not in packet):
        return "abstain"
    before, after = packet["before_B_last_login"], packet["after_B_last_login"]
    return "changed" if before != after else "unchanged"


def trace_hidden_effect_auditor(trace_path, ids):
    """Conservative additional question to the unchanged R7 auditor.

    Browser DOM and HTTP requests alone contain no independently verified
    last_login post-commit value in this predeclared observed trajectory.
    Return abstain. This does not purport to make a probabilistic prediction.
    """
    unchanged_r7 = trace_auditor(trace_path, ids)
    projection = source_dom_projection(trace_path)
    return unchanged_r7, projection, "abstain"


def safe_packet_size(before, after):
    # Disclose byte costs as question-specific compressed packet sizes.
    packet = {"source": "independent_sqlite_readback",
              "B_last_login_before": before,
              "B_last_login_after": after,
              "B_hidden_changed": before != after}
    raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
    return len(raw), len(zlib.compress(raw, 9))


def one_episode(browser, source_db, pair, op, loc, mode):
    from django.core.wsgi import get_wsgi_application
    with tempfile.TemporaryDirectory(prefix="r8_django_") as directory:
        base = Path(directory)
        dbfile = base / "source.sqlite3"
        shutil.copy2(source_db, dbfile)
        ids = r6.create_initial_users(dbfile)
        before = r6.sql_state(dbfile, ids)
        before_b = B_last_login(dbfile, ids)
        if before_b is not None:
            raise AssertionError("B last_login must begin NULL")
        if before["A"] != ("r6_a", "Seed-A") or before["B"] != ("r6_b", "Seed-B"):
            raise AssertionError("Unexpected upstream Django fixture")
        backend = PostCommitShadowWSGI(get_wsgi_application(), dbfile, ids, mode)
        server = make_server("127.0.0.1", 0, backend, handler_class=r6.NoLog)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        ctx = browser.new_context(viewport={"width": 1350, "height": 920})
        callbacks = []
        ctx.expose_binding("__r6_capture",
                           lambda _source, event: callbacks.append(event))
        ctx.add_init_script(r6.CAPTURE)
        page = ctx.new_page()
        try:
            page.goto(base_url + "/admin/login/?next=/admin/auth/user/",
                      wait_until="load")
            page.locator("#id_username").fill("rootoperator")
            page.locator("#id_password").fill("r6-private-temp-password")
            page.locator('input[type="submit"]').click()
            if page.locator("#id_username").count():
                raise AssertionError("Native Django admin login failed")
            callbacks.clear()
            native_trace = base / "original_trace.zip"
            ctx.tracing.start(screenshots=False, snapshots=True, sources=False)
            page.goto(base_url + LISTING, wait_until="load")
            links = page.locator("#result_list tbody tr .field-username a")
            if [x.strip() for x in links.all_text_contents()] != ["r6_a", "r6_b"]:
                raise AssertionError("Original user list changed")
            selected = r6.locator(page, loc, ids)
            screenshot_before = browser_image_hash(page)
            selected.click(timeout=r6.TIMEOUT_MS)
            if op == "edit":
                if not page.locator("#id_first_name").count():
                    raise AssertionError("Native change form unavailable")
                page.locator("#id_first_name").fill(NEW_FIRST)
                page.locator('input[name="_save"]').click()
            else:
                page.locator("a.deletelink").click()
                page.locator('form input[type="submit"]').first.click()
            page.goto(base_url + LISTING, wait_until="load")
            screenshot_after = browser_image_hash(page)
            ctx.tracing.stop(path=str(native_trace))

            # The Trace analyst gets the original ZIP only, while it exists.
            trace_answer, projection, q6_t = trace_hidden_effect_auditor(
                native_trace, ids
            )
            event = next((e for e in callbacks if e.get("trusted")), None)
            packet = {
                "first_click_event_row": (
                    event.get("row_name") if event else None
                ),
                "server_routes": backend.events,
                "before_B_last_login": before_b,
                "after_B_last_login": B_last_login(dbfile, ids),
            }
            q6_p = packet_auditor(packet)

            # Only *after* both auditors answered, independently read truth.
            after = r6.sql_state(dbfile, ids)
            after_b = B_last_login(dbfile, ids)
            q6_truth = "changed" if before_b != after_b else "unchanged"
            if backend.attempts != 1:
                raise AssertionError("Exactly one native POST follow-through required")
            if after["B"] != before["B"]:
                raise AssertionError("Unexpected visible mutation to B")
            if op == "edit" and (after["A"] is None or
                                 after["A"][1] != NEW_FIRST):
                raise AssertionError("Django native edit A did not commit")
            if op == "delete" and after["A"] is not None:
                raise AssertionError("Django native delete A did not commit")
            if not event or event.get("row_name") != "r6_a":
                raise AssertionError("First trusted click did not reach A")
            if trace_answer["q2_visible_receiver_inferred"] != "A":
                raise AssertionError("Original R7 Trace auditor lost A click")
            if trace_answer["q3_actual_POST_route"] != "A":
                raise AssertionError("Original R7 Trace auditor lost A POST")
            if trace_answer["q4_UI_effect_inferred"] != "A":
                raise AssertionError("Original R7 Trace auditor lost A effect")
            if trace_answer["q5_first_click_status"] != "returned":
                raise AssertionError("Original first-click success control failed")
            if q6_p != q6_truth:
                raise AssertionError("Packet-only auditor disagrees with SQL oracle")
            if q6_truth != ("changed" if mode == "shadow" else "unchanged"):
                raise AssertionError("Post-commit manipulation control failed")
            raw_bytes, zipped_bytes = safe_packet_size(before_b, after_b)
            data = {
                "pair": pair, "operation": op, "locator": loc, "mode": mode,
                "q1_selector": trace_answer["q1_selector_present"],
                "q2_click": trace_answer["q2_visible_receiver_inferred"],
                "q3_POST": trace_answer["q3_actual_POST_route"],
                "q4_UI_effect": trace_answer["q4_UI_effect_inferred"],
                "q5_first_click_status": trace_answer["q5_first_click_status"],
                "q6_trace": q6_t, "q6_packet": q6_p,
                "q6_truth": q6_truth,
                "snapshot_count": projection["snapshots_decoded"],
                "resolved_refs": projection["refs_resolved"],
                "unresolved_refs": projection["ref_failures"],
                "native_trace_zip_bytes": native_trace.stat().st_size,
                "pixel_before_sha256": screenshot_before,
                "pixel_after_sha256": screenshot_after,
                "initial_visible_rows": projection["initial_rows"],
                "final_visible_rows": projection["final_rows"],
                "network_projection": projection["network_projection"],
                "server_POST_count": backend.attempts,
                "packet_raw_bytes": raw_bytes,
                "packet_zlib9_bytes": zipped_bytes,
                "B_before_NULL": before_b is None,
                "B_after_nonNULL": after_b is not None,
            }
            return data
        finally:
            ctx.close()
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=4)


def compare_pair(a, b):
    """Reject apparent equality if *any* agreed observed field differs."""
    if {a["mode"], b["mode"]} != set(MODES):
        raise AssertionError("A pair must have both modes")
    fields = [
        "operation", "locator", "q1_selector", "q2_click",
        "q3_POST", "q4_UI_effect", "q5_first_click_status",
        "q6_trace", "pixel_before_sha256", "pixel_after_sha256",
        "initial_visible_rows", "final_visible_rows",
        "network_projection", "unresolved_refs", "server_POST_count"
    ]
    verdict = {key: a[key] == b[key] for key in fields}
    return verdict


def run():
    import django
    from playwright.sync_api import sync_playwright
    cases = paired_matrix()
    if len(cases) != 12 or len(set(cases)) != 12:
        raise AssertionError("R8 prospective matrix mutated")
    OUT.mkdir(parents=True, exist_ok=True)
    episodes = []
    with tempfile.TemporaryDirectory(prefix="r8_master_") as root:
        template = Path(root) / "template.sqlite3"
        r6.init_django(template)
        with sync_playwright() as play:
            browser = play.chromium.launch(headless=True)
            try:
                browser_version = browser.version
                for pair, op, loc, mode in cases:
                    episodes.append(one_episode(browser, template,
                                                pair, op, loc, mode))
                    print("R8_NATIVE_TRACE_EPISODE", len(episodes),
                          "/", len(cases), flush=True)
            finally:
                browser.close()
    pair_details = []
    for pair in range(1, 7):
        a, b = [x for x in episodes if x["pair"] == pair]
        tests = compare_pair(a, b)
        pair_details.append({
            "pair": pair,
            "operation": a["operation"], "locator": a["locator"],
            "equivalent": all(tests.values()), "gates": tests,
            "q6_truth_divergent": a["q6_truth"] != b["q6_truth"],
            "q6_trace_indistinguishable": a["q6_trace"] == b["q6_trace"],
            "q6_packet_distinguishable": a["q6_packet"] != b["q6_packet"],
        })
    verdicts = Counter(x["q6_truth"] for x in episodes)
    if verdicts != {"changed": 6, "unchanged": 6}:
        raise AssertionError("Expected controlled hidden-effect balance")
    if not all(x["equivalent"] and x["q6_truth_divergent"] and
               x["q6_trace_indistinguishable"] and
               x["q6_packet_distinguishable"] for x in pair_details):
        diagnostic = {
            "status":"INVALID_CALIBRATION_EQUIVALENCE_GATE",
            "pair_details":pair_details,
            "unapproved_cases":len(episodes),
            "raw_traces_exported":False,
        }
        (OUT / "r8_equivalence_diagnostics.json").write_text(
            json.dumps(diagnostic, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        print("R8_EQUIVALENCE_GATE_FAILED",
              json.dumps(diagnostic,sort_keys=True),flush=True)
        raise AssertionError("R8 strict browser-equivalence gate failed")
    report = {
        "experiment": "R8 genuine Django browser Trace, response-transparent shadow B SQL",
        "protocol": "docs/weblinx-r8-server-divergence-protocol.md",
        "application": "upstream unmodified Django admin auth.User",
        "Django_version": django.get_version(),
        "Playwright_version": r6.PLAYWRIGHT,
        "chromium_version": browser_version,
        "cases": len(episodes), "matched_pairs": len(pair_details),
        "equivalent_pairs": sum(x["equivalent"] for x in pair_details),
        "pairs_with_distinct_SQL_effect": sum(x["q6_truth_divergent"]
                                               for x in pair_details),
        "trace_Q6": dict(Counter(x["q6_trace"] for x in episodes)),
        "packet_Q6_correct": sum(x["q6_packet"] == x["q6_truth"]
                                  for x in episodes),
        "pair_details": pair_details,
        "snapshot_totals": {
            "decoded": sum(x["snapshot_count"] for x in episodes),
            "resolved_refs": sum(x["resolved_refs"] for x in episodes),
            "failures": sum(x["unresolved_refs"] for x in episodes),
        },
        "bytes": {
            "actual_trace_ZIP_total": sum(x["native_trace_zip_bytes"]
                                          for x in episodes),
            "q6_independent_SQL_packet_zlib9_total": sum(
                x["packet_zlib9_bytes"] for x in episodes),
        },
        "raw_trace_published": False,
        "raw_screenshots_published": False,
        "harness_constructed_side_effect": True,
        "production_bug_or_failure_rate": False,
        "raw_trace_equality_claimed": False,
        "audit_with_blinded_humans": False,
    }
    # Export only category labels, byte counts, equality flags and hashes.
    # SHA-256 of synthetic UI screenshot images is non-reversible; no pixels.
    export_cols = [
        "pair", "operation", "locator", "mode",
        "q1_selector", "q2_click", "q3_POST", "q4_UI_effect",
        "q5_first_click_status", "q6_trace", "q6_packet", "q6_truth",
        "snapshot_count", "resolved_refs", "unresolved_refs",
        "native_trace_zip_bytes", "pixel_before_sha256", "pixel_after_sha256",
        "server_POST_count", "packet_raw_bytes", "packet_zlib9_bytes",
        "B_before_NULL", "B_after_nonNULL"
    ]
    with (OUT / "r8_12_source_cases.csv").open(
            "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=export_cols)
        writer.writeheader()
        for e in episodes:
            writer.writerow({key: e[key] for key in export_cols})
    (OUT / "r8_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R8_ALL_PAIRS_VALID", json.dumps(report, sort_keys=True),
          flush=True)


if __name__ == "__main__":
    run()
