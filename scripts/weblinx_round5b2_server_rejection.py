"""R5B-2: original Flaskr server accepts an HTTP POST but rejects a blank
post title and commits no SQL update.

Six frozen, separate browser episodes verify real third-party validation,
a genuine browser event, a real Flask endpoint response, and a separately
opened SQLite connection proving that the stored state did not change.
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from weblinx_round5b_flaskr import (
    BASE,OUT as MAIN_OUT,UPSTREAM_SHA,PLAYWRIGHT_VERSION,FLASK_VERSION,
    CAPTURE_JS,MUTATE_JS,inspect_upstream,start_flaskr,db_rows,
    chosen_locator,route_identity,trace_features
)

OUT=Path("out_round5b2")
LOCATORS=("positional","href_exact","contextual_role")
SCENARIOS=("baseline","reorder")
OPERATIONS=("edit_blank_title",)


def cases():
    return [(locator,cond) for locator in LOCATORS for cond in SCENARIOS]


def episode(browser,locator_kind,condition,index):
    with tempfile.TemporaryDirectory(prefix="r5b2_server_") as tmpdirname:
        temp=Path(tmpdirname)
        database=temp/"flaskr.sqlite"
        server,thread,requests,ids=start_flaskr(database)
        url=f"http://127.0.0.1:{server.server_port}"
        context=browser.new_context(viewport={"width":1300,"height":920})
        seen=[]
        def first_click(_source,event):
            if isinstance(event,dict):seen.append(dict(event))
        context.expose_binding("__r5b_emit_capture",first_click)
        context.add_init_script(CAPTURE_JS)
        page=context.new_page()
        try:
            page.goto(url+"/auth/login",wait_until="load")
            page.get_by_label("Username").fill("r5b-test-user")
            page.get_by_label("Password").fill("r5b-test-pass")
            page.locator('input[type="submit"][value="Log In"]').click()
            page.wait_for_url(url+"/")
            original=db_rows(database,ids)
            assert original["A"]["title"]=="R5B-A"
            assert original["B"]["title"]=="R5B-B"
            seen.clear()
            trace_path=temp/"trace.zip"
            context.tracing.start(screenshots=False,snapshots=True,sources=False)
            page.goto(url+"/",wait_until="load")
            subject=chosen_locator(page,locator_kind,ids)
            page.evaluate(MUTATE_JS,{"condition":condition,
                                    "a":ids["A"],"b":ids["B"]})
            assert db_rows(database,ids)==original
            first_status="returned"
            try:
                subject.click(timeout=950)
            except Exception as exc:
                first_status="click_error_"+type(exc).__name__
            page.wait_for_timeout(30)
            original_clicks=list(seen)
            original_event=original_clicks[0] if original_clicks else {}
            entered=route_identity(urlparse(page.url).path,ids)
            if first_status!="returned" or entered not in ("A","B"):
                raise AssertionError("R5B-2 frozen first-click gate failed")
            # Deliberate HTML-only client validation removal. The upstream
            # Flaskr Python handler remains unchanged, and performs its own
            # "Title is required." check after genuine form POST.
            field=page.get_by_label("Title")
            field.evaluate("node => node.removeAttribute('required')")
            field.fill("")
            old_sql=db_rows(database,ids)
            assert old_sql==original
            before=len(requests.snapshot())
            page.locator('input[type="submit"][value="Save"]').click()
            page.wait_for_timeout(50)
            server_post=requests.snapshot()[before:]
            posts=[r for r in server_post
                   if r["method"]=="POST" and r["route"]=="post_update"]
            if len(posts)!=1:
                raise AssertionError("Expected real POST to upstream validation")
            db_after=db_rows(database,ids)
            if db_after!=original:
                raise AssertionError("Rejected Flaskr title unexpectedly committed SQL")
            flash_messages=page.locator(".flash").all_text_contents()
            rejected_by_page=any("Title is required." in x for x in flash_messages)
            if not rejected_by_page:
                raise AssertionError("Official Flaskr validation flash missing")
            if posts[0]["status"]!=200:
                raise AssertionError("Expected real Flaskr rejection page 200")
            # Verify new index still renders original stored state.
            page.goto(url+"/",wait_until="load")
            visible=[x.strip() for x in page.locator("article.post h1").all_text_contents()]
            if sorted(visible)!=["R5B-A","R5B-B"]:
                raise AssertionError("App output and independent SQLite mismatch")
            context.tracing.stop(path=str(trace_path))
            trace=trace_features(trace_path)
            return {
                "case":index,
                "operation":"edit_blank_title",
                "locator":locator_kind,
                "condition":condition,
                "intended":"A",
                "first_click_status":first_status,
                "first_click_trusted_count":len(original_clicks),
                "first_click_article":(
                    "A" if original_event.get("link_article_title")=="R5B-A"
                    else "B" if original_event.get("link_article_title")=="R5B-B"
                    else "none"),
                "first_click_href_record":route_identity(
                    original_event.get("link_href_path",""),ids),
                "server_edit_route_record":entered,
                "server_edit_POST_count":len(posts),
                "server_edit_POST_status":posts[0]["status"],
                "server_side_validation_message":int(rejected_by_page),
                "sql_rows_changed_count":sum(db_after[k]!=original[k]
                                             for k in ("A","B")),
                "sql_A_unchanged":int(db_after["A"]==original["A"]),
                "sql_B_unchanged":int(db_after["B"]==original["B"]),
                "browser_render_matches_SQL":1,
                "playwright_trace_zip_bytes":trace["zip_bytes"],
                "playwright_trace_records":trace["trace_record_lines"],
                "playwright_trace_network_records":trace["network_record_lines"],
            }
        finally:
            try:context.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()


def summarize(rows,source_hashes,browser_version):
    assert len(rows)==6
    return {
        "study":"R5B-2 verified server POST with validation rejection and zero committed SQL changes",
        "source":"pallets/flask examples/tutorial/flaskr",
        "source_commit":UPSTREAM_SHA,
        "source_file_checksums":source_hashes,
        "environment":{"python":sys.version.split()[0],
                        "flask":FLASK_VERSION,
                        "playwright":PLAYWRIGHT_VERSION,
                        "chromium":browser_version},
        "six_case_matrix":{"locators":list(LOCATORS),
                           "conditions":list(SCENARIOS)},
        "total_cases":len(rows),
        "first_click_results":dict(sorted(Counter(
            r["first_click_status"] for r in rows).items())),
        "post_response_codes":dict(sorted(Counter(
            r["server_edit_POST_status"] for r in rows).items())),
        "server_POST_count_total":sum(r["server_edit_POST_count"] for r in rows),
        "server_POST_with_no_SQL_commit":sum(
            r["server_edit_POST_count"]==1 and
            r["sql_rows_changed_count"]==0 for r in rows),
        "flash_validation_n":sum(r["server_side_validation_message"] for r in rows),
        "all_SQL_A_unchanged":all(r["sql_A_unchanged"] for r in rows),
        "all_SQL_B_unchanged":all(r["sql_B_unchanged"] for r in rows),
        "trace_zip_total_bytes":sum(r["playwright_trace_zip_bytes"] for r in rows),
        "trace_record_lines":sum(r["playwright_trace_records"] for r in rows),
        "trace_network_records":sum(r["playwright_trace_network_records"] for r in rows),
        "real_external_app_backend_unchanged":True,
        "actual_independent_SQLite_reads":True,
        "server_validation_rejection_controlled":True,
        "raw_trace_archives_published":False,
        "new_corpus_independent_of_R5B1":False
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source_hashes=inspect_upstream()
    path=str(BASE.absolute())
    if path not in sys.path:sys.path.insert(0,path)
    trials=cases()
    assert len(trials)==6
    rows=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            version=browser.version
            for i,(method,condition) in enumerate(trials,1):
                rows.append(episode(browser,method,condition,i))
                print("R5B2_EPISODE",i,"/",len(trials),flush=True)
        finally:
            browser.close()
    report=summarize(rows,source_hashes,version)
    with (OUT/"r5b2_server_rejections_6.csv").open("w",newline="",
                                                encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (OUT/"r5b2_server_rejection_summary.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R5B2_SUMMARY",json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
