"""R5B: actual external-maintained Flaskr app, trusted browser events and
authoritative SQLite commit/readback. All HTML templates/views originate
unchanged from pallets/flask at one frozen upstream commit.

48 fixed episodes: 2 operations x 3 locators x 8 browser DOM interventions.
Each has a fresh app factory, server, SQLite database and browser context.
Raw Playwright trace archives are inspected locally but never exported.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import threading
import time
import zlib
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright,TimeoutError as BrowserTimeout
from werkzeug.serving import make_server,WSGIRequestHandler
from werkzeug.security import generate_password_hash

UPSTREAM_SHA="49943b5a94413a530761350f04e896f76e8d620e"
PLAYWRIGHT_VERSION="1.65.2"
FLASK_VERSION="3.1.2"
BASE=Path(".r5b_upstream")
OUT=Path("out_round5b")
OPERATIONS=("edit","delete")
LOCATORS=("positional","href_exact","contextual_role")
CONDITIONS=(
    "baseline","reorder","swap_href","remove_target",
    "duplicate_context","overlay_standard","overlay_force","prevent_default"
)
TIMEOUT_MS=950
DB_NAMES=("R5B-A","R5B-B")

# Python callback is outside the app; the installed browser listener runs
# before page-authored handlers and does not block or mutate the click.
CAPTURE_JS=r"""(() => {
 document.addEventListener("click",e=>{
   if(!e.isTrusted)return;
   const path=e.composedPath();
   const link=path.find(n=>n && n.tagName==="A" && n.classList?.contains("action"));
   const article=link?.closest("article.post");
   const title=article?.querySelector("h1")?.textContent?.trim()||"";
   const route=link?new URL(link.getAttribute("href"),location.href).pathname:"";
   const data={
     trusted:true,
     raw_target_tag:String(e.target?.tagName||""),
     link_article_title:title,
     link_href_path:route,
     has_edit_link:!!link
   };
   window.__r5b_emit_capture(data);
 },true);
})();"""

MUTATE_JS=r"""({condition,a,b}) => {
  const cards=Array.from(document.querySelectorAll("article.post"));
  const mainA=cards.find(n=>n.querySelector("h1")?.textContent?.trim()==="R5B-A");
  const mainB=cards.find(n=>n.querySelector("h1")?.textContent?.trim()==="R5B-B");
  if(!mainA || !mainB)throw Error("Original Flaskr posts missing");
  const linkA=mainA.querySelector("a.action");
  const linkB=mainB.querySelector("a.action");
  if(!linkA || !linkB)throw Error("Original Edit link missing");
  if(condition==="reorder"){
    mainA.parentNode.insertBefore(mainB,mainA);
  }
  if(condition==="swap_href"){
    const first=linkA.getAttribute("href");
    linkA.setAttribute("href",linkB.getAttribute("href"));
    linkB.setAttribute("href",first);
  }
  if(condition==="remove_target"){
    mainA.remove();
  }
  if(condition==="duplicate_context"){
    const cloned=mainA.cloneNode(true);
    cloned.querySelector("a.action").setAttribute("href","/"+b+"/update");
    mainA.parentNode.appendChild(cloned);
  }
  if(condition==="overlay_standard" || condition==="overlay_force"){
    const rect=linkA.getBoundingClientRect();
    const blocker=document.createElement("div");
    blocker.setAttribute("data-r5b-overlay","1");
    Object.assign(blocker.style,{
      position:"fixed",left:rect.left+"px",top:rect.top+"px",
      width:rect.width+"px",height:rect.height+"px",
      zIndex:"999999",background:"rgba(0,0,0,0.15)",pointerEvents:"auto"
    });
    document.body.appendChild(blocker);
  }
  if(condition==="prevent_default"){
    linkA.addEventListener("click",e=>e.preventDefault(),false);
  }
}"""


def fixed_cases():
    return [(op,loc,cond) for op in OPERATIONS
            for loc in LOCATORS for cond in CONDITIONS]


class QuietHTTP(WSGIRequestHandler):
    def log(self,typ,message,*args):
        pass


class ExternalRequestAudit:
    """WSGI boundary only; the upstream app route function is unmodified."""
    def __init__(self,application):
        self.application=application
        self.log=[]
        self.lock=threading.Lock()

    def __call__(self,environ,start_response):
        request_method=environ.get("REQUEST_METHOD","")
        path=environ.get("PATH_INFO","")
        route_match=re.fullmatch(r"/(\d+)/(update|delete)",path)
        if route_match:
            route=f"post_{route_match.group(2)}"
            post=int(route_match.group(1))
        elif path=="/":
            route="index";post=0
        elif path.startswith("/auth/"):
            route="auth";post=0
        else:
            route="other";post=0
        def audited_start(status,headers,exc_info=None):
            with self.lock:
                self.log.append({
                    "method":request_method,
                    "route":route,"post_id":post,
                    "status":int(status.split()[0])
                })
            return start_response(status,headers,exc_info)
        return self.application(environ,audited_start)

    def snapshot(self):
        with self.lock:
            return [dict(x) for x in self.log]


def inspect_upstream():
    assert BASE.is_dir()
    required=[
        "flaskr/__init__.py","flaskr/blog.py","flaskr/auth.py",
        "flaskr/db.py","flaskr/schema.sql",
        "flaskr/templates/blog/index.html",
        "flaskr/templates/blog/update.html",
        "flaskr/templates/auth/login.html",
    ]
    checks={}
    for item in required:
        p=BASE/item
        if not p.is_file():raise FileNotFoundError(p)
        checks[item]=hashlib.sha256(p.read_bytes()).hexdigest()
    return checks


def db_rows(db_path,ids):
    with sqlite3.connect(db_path,timeout=5) as conn:
        rows=conn.execute(
            "SELECT id,title,body,author_id FROM post ORDER BY id").fetchall()
    observed={r[0]:{"title":r[1],"body":r[2],"author_id":r[3]} for r in rows}
    return {k:observed.get(v) for k,v in ids.items()}


def start_flaskr(db_path):
    # Official upstream files from frozen checkout.
    from flaskr import create_app
    from flaskr.db import init_db
    app=create_app({
        "TESTING":False,
        "DATABASE":str(db_path),
        "SECRET_KEY":"R5B-only-disposable-fixture-key",
    })
    with app.app_context():
        init_db()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
          "INSERT INTO user(username,password) VALUES (?,?)",
          ("r5b-test-user",generate_password_hash("r5b-test-pass",
                                                 method="pbkdf2:sha256:1000")))
        author=int(conn.execute(
            "SELECT id FROM user WHERE username=?",("r5b-test-user",)
        ).fetchone()[0])
        # A is guaranteed to precede B on source Flaskr's date-descending index.
        conn.execute(
          "INSERT INTO post(author_id,created,title,body) VALUES(?,?,?,?)",
          (author,"2026-11-22 19:05:00","R5B-A","Dummy body A"))
        a=int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.execute(
          "INSERT INTO post(author_id,created,title,body) VALUES(?,?,?,?)",
          (author,"2026-11-21 19:05:00","R5B-B","Dummy body B"))
        b=int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()
    app_audit=ExternalRequestAudit(app.wsgi_app)
    app.wsgi_app=app_audit
    server=make_server("127.0.0.1",0,app,threaded=True,
                       request_handler=QuietHTTP)
    worker=threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    return server,worker,app_audit,{"A":a,"B":b}


def chosen_locator(page,kind,ids):
    if kind=="positional":
        return page.locator("article.post a.action").first
    if kind=="href_exact":
        return page.locator(f'article.post a.action[href="/{ids["A"]}/update"]')
    if kind=="contextual_role":
        article=page.locator("article.post").filter(
            has=page.get_by_role("heading",name="R5B-A",exact=True))
        return article.get_by_role("link",name="Edit",exact=True)
    raise AssertionError("Invalid frozen locator")


def route_identity(path,ids):
    match=re.fullmatch(r"/(\d+)/(?:update|delete)",path or "")
    if match:
        p=int(match.group(1))
        return "A" if p==ids["A"] else "B" if p==ids["B"] else "other"
    return "none"


def encode_bytes(packet):
    raw=json.dumps(packet,sort_keys=True,ensure_ascii=False,
                   separators=(",",":")).encode("utf-8")
    return len(raw),len(zlib.compress(raw,9))


def trace_features(trace_file):
    if not trace_file.is_file() or trace_file.stat().st_size==0:
        raise AssertionError("Playwright baseline trace missing")
    with zipfile.ZipFile(trace_file) as z:
        items=z.namelist()
        if not any(x.endswith(".trace") for x in items):
            raise AssertionError("Playwright Trace missing .trace events")
        if z.testzip() is not None:raise AssertionError("Invalid Playwright trace zip")
        # Count actual archived record lines, without serializing their data.
        trace_lines=sum(
            len(z.read(k).splitlines()) for k in items if k.endswith(".trace")
        )
        network_lines=sum(
            len(z.read(k).splitlines()) for k in items if k.endswith(".network")
        )
        resource_files=sum("/resources/" in k for k in items)
        return {
          "zip_bytes":trace_file.stat().st_size,
          "trace_file_members":sum(k.endswith(".trace") for k in items),
          "network_file_members":sum(k.endswith(".network") for k in items),
          "trace_record_lines":trace_lines,
          "network_record_lines":network_lines,
          "resource_files":resource_files,
        }


def episode(browser,op,locator_kind,condition,n,source_hash):
    with tempfile.TemporaryDirectory(prefix="r5b_flaskr_") as dirname:
        tmp=Path(dirname)
        db=tmp/"flaskr.sqlite"
        server,worker,requests,ids=start_flaskr(db)
        base=f"http://127.0.0.1:{server.server_port}"
        context=browser.new_context(viewport={"width":1300,"height":920},
                                    accept_downloads=False)
        captured=[]
        def capture(_source,payload):
            if isinstance(payload,dict):
                captured.append(dict(payload))
        context.expose_binding("__r5b_emit_capture",capture)
        context.add_init_script(CAPTURE_JS)
        page=context.new_page()
        try:
            page.goto(base+"/auth/login",wait_until="load")
            page.get_by_label("Username").fill("r5b-test-user")
            page.get_by_label("Password").fill("r5b-test-pass")
            page.locator('input[type="submit"][value="Log In"]').click()
            page.wait_for_url(base+"/")
            initial_db=db_rows(db,ids)
            assert initial_db["A"]["title"]=="R5B-A"
            assert initial_db["B"]["title"]=="R5B-B"
            captured.clear()
            before_requests=len(requests.snapshot())
            tracepath=tmp/"trace.zip"
            context.tracing.start(screenshots=False,snapshots=True,
                                  sources=False)
            page.goto(base+"/",wait_until="load")
            target_link=chosen_locator(page,locator_kind,ids)
            page.evaluate(MUTATE_JS,{"condition":condition,
                                    "a":ids["A"],"b":ids["B"]})
            assert db_rows(db,ids)==initial_db, "DOM change altered server DB"
            # only one tested first-link click per episode
            status="returned"
            try:
                target_link.click(force=(condition=="overlay_force"),
                                  timeout=TIMEOUT_MS)
            except BrowserTimeout:
                status="timeout"
            except Exception:
                status="playwright_error"
            # Capture callback is asynchronous across the browser<->Python
            # bridge; flush before we choose any follow-through action.
            page.wait_for_timeout(30)
            first_clicks=list(captured)
            capture_first=first_clicks[0] if first_clicks else {}
            # First-click route outcome is observed from real navigation;
            # server WSGI records are an additional independent channel.
            path=urlparse(page.url).path
            accessed=route_identity(path,ids)
            follow="no_edit_page"
            if accessed in ("A","B") and page.locator(
                    'input[type="submit"][value="Delete"]').count()==1:
                if op=="edit":
                    page.get_by_label("Title").fill(f"R5B-EDIT-{n:02d}")
                    page.locator('input[type="submit"][value="Save"]').click()
                    follow="posted_edit"
                else:
                    page.on("dialog",lambda dialog:dialog.accept())
                    page.locator('input[type="submit"][value="Delete"]').click()
                    follow="posted_delete"
                page.wait_for_url(base+"/")
            page.wait_for_timeout(30)
            result_db=db_rows(db,ids)
            changed=[]
            for key in ("A","B"):
                if result_db[key]!=initial_db[key]:
                    changed.append(key)
            if len(changed)>1:raise AssertionError("Multiple SQL rows mutated")
            db_effect=changed[0] if changed else "none"
            if db_effect!="none":
                if op=="delete" and result_db[db_effect] is not None:
                    raise AssertionError("Delete did not remove record")
                if op=="edit" and (
                    result_db[db_effect] is None or
                    result_db[db_effect]["title"]!=f"R5B-EDIT-{n:02d}"):
                    raise AssertionError("Unexpected SQL update value")
            page.goto(base+"/",wait_until="load")
            visible_titles=page.locator("article.post h1").all_text_contents()
            expected_titles=[r["title"] for r in result_db.values() if r is not None]
            final_display_equal=sorted(s.strip() for s in visible_titles)==sorted(
                expected_titles)
            if not final_display_equal:
                raise AssertionError("Server-backed index differs from SQL readback")
            context.tracing.stop(path=str(tracepath))
            trace=trace_features(tracepath)
            server_records=requests.snapshot()[before_requests:]
            first_update_gets=[r for r in server_records
                               if r["method"]=="GET" and r["route"]=="post_update"]
            app_mutations=[r for r in server_records if
                           r["method"]=="POST" and
                           r["route"] in ("post_update","post_delete")]
            if db_effect!="none" and not app_mutations:
                raise AssertionError("SQL change has no app POST request")
            if first_clicks and not capture_first.get("trusted",False):
                raise AssertionError("Untrusted browser click received")
            event_article=(
                "A" if capture_first.get("link_article_title")=="R5B-A" else
                "B" if capture_first.get("link_article_title")=="R5B-B" else
                "other" if capture_first.get("link_article_title") else
                "none")
            event_href=route_identity(capture_first.get("link_href_path",""),ids)
            result={
               "case":n,"operation":op,"locator":locator_kind,
               "condition":condition,"intended_record":"A",
               "first_click_status":status,
               "first_click_trusted_count":len(first_clicks),
               "first_click_raw_tag":capture_first.get("raw_target_tag","none"),
               "first_click_article":event_article,
               "first_click_href_record":event_href,
               "server_update_GET_A_count":sum(
                   r["post_id"]==ids["A"] for r in first_update_gets),
               "server_update_GET_B_count":sum(
                   r["post_id"]==ids["B"] for r in first_update_gets),
               "server_app_post_count":len(app_mutations),
               "server_app_post_record":(
                   route_identity(
                       f"/{app_mutations[0]['post_id']}/update",ids)
                   if app_mutations else "none"),
               "followthrough":follow,
               "sqlite_effect_record":db_effect,
               "sqlite_A_exists":int(result_db["A"] is not None),
               "sqlite_B_exists":int(result_db["B"] is not None),
               "rendered_matches_SQL":int(final_display_equal),
               "db_rows_changed_count":len(changed),
               "click_returned_no_DB_effect":int(status=="returned" and
                                                db_effect=="none"),
               "event_article_differs_from_SQL_effect":int(
                    db_effect!="none" and event_article!=db_effect),
               "wrong_SQL_record_effect":int(db_effect=="B"),
               "trace_zip_bytes":trace["zip_bytes"],
               "trace_event_lines":trace["trace_record_lines"],
               "trace_network_lines":trace["network_record_lines"],
               "trace_resource_files":trace["resource_files"],
               "trace_member_files":trace["trace_file_members"]+
                                    trace["network_file_members"],
            }
            # Tier sizes are actual serialized, per-episode fixed compact JSON.
            request_packet={"operation":op,"locator":locator_kind,
                            "condition":condition,"target":"A","status":status}
            event_packet={**request_packet,
                          "trusted_clicks":len(first_clicks),
                          "event_article":event_article,
                          "event_href_record":event_href,
                          "event_raw_tag":result["first_click_raw_tag"]}
            network_packet={**event_packet,
                            "server_update_GET_A_count":result["server_update_GET_A_count"],
                            "server_update_GET_B_count":result["server_update_GET_B_count"],
                            "server_app_post_count":len(app_mutations),
                            "server_app_post_record":result["server_app_post_record"]}
            effect_packet={**network_packet,
                           "sqlite_effect_record":db_effect,
                           "A_exists":result["sqlite_A_exists"],
                           "B_exists":result["sqlite_B_exists"],
                           "rendered_matches_SQL":int(final_display_equal)}
            for label,packet in [
                ("request",request_packet),("event",event_packet),
                ("server",network_packet),("effect",effect_packet)
            ]:
                size,compressed=encode_bytes(packet)
                result[label+"_bytes"]=size
                result[label+"_zlib_bytes"]=compressed
            return result
        finally:
            try:context.close()
            finally:
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()


def aggregate(rows,source_checks,browser_version):
    if len(rows)!=48 or len({(r["operation"],r["locator"],r["condition"])
                              for r in rows})!=48:
        raise AssertionError("Incomplete 48-case source cohort")
    def stats(items):
        counts=lambda k:dict(sorted(Counter(r[k] for r in items).items()))
        return {
            "n":len(items),"sqlite_effect_counts":counts("sqlite_effect_record"),
            "click_status_counts":counts("first_click_status"),
            "event_article_counts":counts("first_click_article"),
            "server_mutating_post_count":sum(r["server_app_post_count"]>0
                                             for r in items),
            "wrong_SQL_effects":sum(r["wrong_SQL_record_effect"] for r in items),
            "returned_clicks_without_SQL_effect":sum(
                r["click_returned_no_DB_effect"] for r in items),
            "mismatched_event_article_and_SQL_effect":sum(
                r["event_article_differs_from_SQL_effect"] for r in items)
        }
    totals=stats(rows)
    totals["bytes_by_evidence_tier"]={
        prefix:{
            "sum_utf8_bytes":sum(r[prefix+"_bytes"] for r in rows),
            "sum_zlib_per_episode_bytes":sum(r[prefix+"_zlib_bytes"] for r in rows)
        }
        for prefix in ("request","event","server","effect")
    }
    totals["playwright_trace_zip_total_bytes"]=sum(
        r["trace_zip_bytes"] for r in rows)
    totals["playwright_trace_zip_median_bytes"]=sorted(
        r["trace_zip_bytes"] for r in rows)[len(rows)//2]
    totals["playwright_trace_action_event_lines"]=sum(
        r["trace_event_lines"] for r in rows)
    totals["playwright_trace_network_lines"]=sum(
        r["trace_network_lines"] for r in rows)
    return {
        "experiment":"Round5B external upstream Flaskr server-backed browser and SQL pilot",
        "upstream":"pallets/flask examples/tutorial/flaskr",
        "upstream_commit":UPSTREAM_SHA,
        "upstream_original_file_sha256":source_checks,
        "environment":{"python":sys.version.split()[0],
                       "playwright":PLAYWRIGHT_VERSION,
                       "flask":FLASK_VERSION,
                       "browser":"Chromium",
                       "browser_version":browser_version},
        "fixed_conditions":{"operations":list(OPERATIONS),
                            "locators":list(LOCATORS),
                            "conditions":list(CONDITIONS)},
        "total":totals,
        "by_operation":{op:stats([r for r in rows if r["operation"]==op])
                        for op in OPERATIONS},
        "by_condition":{cond:stats([r for r in rows if r["condition"]==cond])
                        for cond in CONDITIONS},
        "by_locator":{loc:stats([r for r in rows if r["locator"]==loc])
                      for loc in LOCATORS},
        "actual_browser_inputs":True,
        "source_app_unmodified":True,
        "independent_authoritative_SQLite_readback":True,
        "real_user_website_tasks":False,
        "real_agent_trajectories":False,
        "only_one_external_app":True,
        "raw_playwright_traces_published":False,
        "trace_sufficiency_independently_adjudicated":False,
        "all_episode_results_preserved":True
    }


def main():
    source_checks=inspect_upstream()
    if str(BASE.absolute()) not in sys.path:
        sys.path.insert(0,str(BASE.absolute()))
    OUT.mkdir(parents=True,exist_ok=True)
    cases=fixed_cases()
    assert len(cases)==48
    result=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            version=browser.version
            for i,(op,loc,condition) in enumerate(cases,1):
                row=episode(browser,op,loc,condition,i,source_checks)
                result.append(row)
                if i%8==0:print("R5B_COMPLETED_CASES",i,len(cases),flush=True)
        finally:
            browser.close()
    report=aggregate(result,source_checks,version)
    with (OUT/"round5b_flaskr_actions_48.csv").open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(result[0]))
        wr.writeheader();wr.writerows(result)
    (OUT/"round5b_flaskr_summary.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("R5B_SUMMARY",json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
