"""Controlled Django Admin user-row browser fixtures and independent observations."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import zipfile
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from wsgiref.simple_server import make_server, WSGIRequestHandler

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

OUT=Path("out_round6")
PIN="4f382ca672f86dd4a1e4d071c91d0caad0e124b3"
VERSION="5.2.12"
PLAYWRIGHT="1.65.2"
OPS=("edit","delete")
LOCATORS=("positional","href_exact","contextual_row")
CONDITIONS=("baseline","reorder","swap_href","remove_target",
            "duplicate_context","overlay_standard","overlay_force",
            "prevent_default")
TIMEOUT_MS=850
USERNAME={"A":"r6_a","B":"r6_b"}
CAPTURE=r"""(() => {
  document.addEventListener("click", e => {
    if (!e.isTrusted) return;
    const path=e.composedPath();
    const a=path.find(n=>n && n.tagName==="A" &&
                          n.closest && n.closest("#result_list"));
    if (!a) return;
    const tr=a.closest("tr");
    const rowName=tr?.querySelector(".field-username a")?.textContent?.trim() || "";
    const dest=new URL(a.getAttribute("href"),location.href).pathname;
    window.__r6_capture({trusted:true,raw_tag:String(e.target.tagName||""),
                         row_name:rowName,destination:dest});
  },true);
})();"""

MUTATE=r"""({condition}) => {
 const body=document.querySelector("#result_list tbody");
 if(!body)throw Error("Admin user result table not found");
 const trs=Array.from(body.querySelectorAll("tr"));
 const getname=tr=>tr.querySelector(".field-username a")?.textContent?.trim();
 const a=trs.find(tr=>getname(tr)==="r6_a");
 const b=trs.find(tr=>getname(tr)==="r6_b");
 if(!a || !b) throw Error("Both Django source user rows required");
 const la=a.querySelector(".field-username a");
 const lb=b.querySelector(".field-username a");
 if(condition==="reorder")body.insertBefore(b,a);
 if(condition==="swap_href"){
   const h=la.getAttribute("href");
   la.setAttribute("href",lb.getAttribute("href"));
   lb.setAttribute("href",h);
 }
 if(condition==="remove_target")a.remove();
 if(condition==="duplicate_context"){
   const clone=a.cloneNode(true);
   clone.querySelector(".field-username a").setAttribute(
     "href",lb.getAttribute("href"));
   body.appendChild(clone);
 }
 if(condition==="overlay_standard" || condition==="overlay_force"){
   // A full-viewport pointer intercept is insensitive to responsive
   // layout, CSS and automatic scrolling during Playwright actionability.
   const cover=document.createElement("div");
   cover.id="r6-cover";
   Object.assign(cover.style,{
     position:"fixed",inset:"0",width:"100vw",height:"100vh",
     zIndex:"2147483647",pointerEvents:"auto",
     background:"rgba(0,0,0,0.14)"
   });
   document.documentElement.appendChild(cover);
   if (document.elementFromPoint(10,10)!==cover)
     throw Error("Pointer interception fixture failed");
 }
 if(condition==="prevent_default")
   la.addEventListener("click",e=>e.preventDefault(),false);
}"""

def matrix():
    return [(o,l,c) for o in OPS for l in LOCATORS for c in CONDITIONS]


def init_django(template_path):
    from django.conf import settings
    settings.configure(
        DEBUG=False, SECRET_KEY="R6-disposable-local-test-key",
        ALLOWED_HOSTS=["localhost","127.0.0.1"],
        ROOT_URLCONF=__name__,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3",
                              "NAME":str(template_path)}},
        INSTALLED_APPS=[
            "django.contrib.admin","django.contrib.auth",
            "django.contrib.contenttypes","django.contrib.sessions",
            "django.contrib.messages","django.contrib.staticfiles"],
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware"],
        TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates",
                    "DIRS":[],"APP_DIRS":True,
                    "OPTIONS":{"context_processors":[
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages"]}}],
        STATIC_URL="/static/",
        USE_TZ=True, TIME_ZONE="UTC", LANGUAGE_CODE="en-us",
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField")
    import django
    django.setup()
    from django.urls import path
    from django.contrib import admin
    globals()["urlpatterns"]=[path("admin/",admin.site.urls)]
    from django.core.management import call_command
    call_command("migrate",interactive=False,verbosity=0)
    from django.db import connections
    connections.close_all()


def switch_database(path):
    from django.conf import settings
    from django.db import connections
    connections.close_all()
    settings.DATABASES["default"]["NAME"]=str(path)
    connections.databases["default"]["NAME"]=str(path)


def create_initial_users(dbfile):
    # Playwright's synchronous Python API owns an asyncio event loop on its
    # calling thread. Django deliberately rejects sync ORM calls in that
    # thread. Run the unchanged ORM seeding in a different, non-async thread.
    from concurrent.futures import ThreadPoolExecutor
    switch_database(dbfile)
    def seed_using_original_django_orm():
        from django.contrib.auth.models import User
        from django.db import connections
        try:
            User.objects.create_superuser(
                username="rootoperator",email="root@fixture.test",
                password="r6-private-temp-password")
            a=User.objects.create_user(username="r6_a",password="random-dummy",
                                       first_name="Seed-A",email="a@fixture.test")
            b=User.objects.create_user(username="r6_b",password="random-dummy",
                                       first_name="Seed-B",email="b@fixture.test")
            return {"A":a.pk,"B":b.pk}
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(seed_using_original_django_orm).result()


def sql_state(dbfile,ids):
    # Explicit separate SQLite connection, no Django ORM.
    with sqlite3.connect(dbfile,timeout=15) as conn:
        rows=conn.execute(
            "SELECT id,username,first_name FROM auth_user WHERE id IN (?,?)",
            (ids["A"],ids["B"])).fetchall()
    index={r[0]:(r[1],r[2]) for r in rows}
    return {k:index.get(v) for k,v in ids.items()}


class NoLog(WSGIRequestHandler):
    def log_message(self,fmt,*args):
        pass


class WSGIBoundary:
    def __init__(self,app):
        self.app=app
        self.events=[]
        self.lock=threading.Lock()
    def __call__(self,environ,start_response):
        path=environ.get("PATH_INFO","")
        method=environ.get("REQUEST_METHOD","")
        match=re.fullmatch(
            r"/admin/auth/user/(\d+)/(change|delete)/",path)
        route="user_"+match.group(2) if match else "other"
        pk=int(match.group(1)) if match else 0
        def capture(status,headers,exc_info=None):
            with self.lock:
                self.events.append({
                    "method":method,"route":route,"pk":pk,
                    "status":int(status.split()[0])})
            return start_response(status,headers,exc_info)
        return self.app(environ,capture)
    def snapshot(self):
        with self.lock:return list(self.events)


def route_id(path,ids):
    match=re.search(r"/admin/auth/user/(\d+)/(?:change|delete)/",path or "")
    if not match:return "none"
    pk=int(match.group(1))
    return "A" if pk==ids["A"] else "B" if pk==ids["B"] else "other"


def locator(page,method,ids):
    if method=="positional":
        return page.locator("#result_list tbody tr .field-username a").first
    if method=="href_exact":
        # Django's own admin can render a relative change-link href.
        # Read the exact source-native attribute from the ORIGINAL A row
        # before the intervention and retain that unchanged locator.
        source_row=page.locator("#result_list tbody tr").filter(
            has=page.get_by_role("link",name="r6_a",exact=True))
        exact_href=source_row.locator(".field-username a").get_attribute("href")
        if not exact_href:
            raise AssertionError("Native Django A change link has no href")
        return page.locator(
            '#result_list tbody tr .field-username a'
            f'[href={json.dumps(exact_href)}]')
    if method=="contextual_row":
        return page.locator("#result_list tbody tr").filter(
            has=page.get_by_role("link",name="r6_a",exact=True)
        ).locator(".field-username a")
    raise AssertionError("unknown locator")


def trace_parse(p,ids):
    """Receive only the raw Trace ZIP and STATIC record IDs.

    Produces no judgments from WSGI, event callback, SQL, or the outcome CSV.
    Extracts directly represented action and network observations only.
    """
    events=[]; net=[]; files=[]
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None:raise AssertionError("corrupt trace")
        names=z.namelist()
        for name in names:
            if name.endswith(".trace"):
                files.append(name)
                for line in z.read(name).splitlines():
                    try: events.append(json.loads(line))
                    except (json.JSONDecodeError,ValueError):pass
            elif name.endswith(".network"):
                for line in z.read(name).splitlines():
                    try:net.append(json.loads(line))
                    except (json.JSONDecodeError,ValueError):pass
    if not files:raise AssertionError("trace missing record file")
    # Playwright trace is JSONL, event type "before"/"after" or network
    # resource-snapshot, not a raw CDP event-recipient observer.
    methods=Counter(str(e.get("method","")) for e in events
                    if e.get("type")=="before")
    clicks=[e for e in events if e.get("type")=="before"
            and e.get("method")=="click"]
    after={e.get("callId"):e for e in events
           if e.get("type")=="after" and e.get("callId") is not None}
    first=clicks[0] if clicks else None
    expression=first.get("params",{}).get("selector") if first else None
    # Do not store the original selector string (may contain page content).
    selector_status="present" if isinstance(expression,str) and expression else "absent"
    if not first:
        first_status="unavailable"
    elif first.get("callId") in after:
        final=after[first["callId"]]
        first_status="error" if final.get("error") else "returned"
    else:first_status="unavailable"
    post_records=[]
    get_records=[]
    net_types=Counter()
    for e in net:
        net_types[str(e.get("type",""))]+=1
        snap=e.get("snapshot",{})
        if not isinstance(snap,dict):continue
        request=snap.get("request",{})
        if not isinstance(request,dict):continue
        path=urlparse(request.get("url","")).path
        method=request.get("method","")
        val=route_id(path,ids)
        if method=="POST" and val!="none":
            post_records.append(val)
        if method=="GET" and val!="none":
            get_records.append(val)
    return {
        "zip_bytes":p.stat().st_size,
        "trace_lines":len(events),"network_lines":len(net),
        "network_type_names":dict(net_types),
        "click_before_events":len(clicks),
        "first_click_selector":selector_status,
        "first_click_status":first_status,
        "first_click_record_is_observed_trusted_event":False,
        "trace_POST_routes":post_records,
        "trace_GET_routes":get_records,
        "trace_POST_route_unique":(
            post_records[0] if len(post_records)==1 else
            "none" if len(post_records)==0 else "ambiguous"
        ),
        "member_count":len(names),
    }


def packet_bytes(obj):
    s=json.dumps(obj,sort_keys=True,ensure_ascii=False,
                 separators=(",",":")).encode("utf-8")
    return len(s),len(zlib.compress(s,9))


def episode(browser,base_db,op,loc,cond,idx):
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    with tempfile.TemporaryDirectory(prefix="r6_django_") as work:
        root=Path(work)
        db=root/"db.sqlite3"
        shutil.copy2(base_db,db)
        ids=create_initial_users(db)
        before=sql_state(db,ids)
        assert before["A"]==("r6_a","Seed-A")
        assert before["B"]==("r6_b","Seed-B")
        wrapped=WSGIBoundary(get_wsgi_application())
        server=make_server("127.0.0.1",0,wrapped,
                           handler_class=NoLog)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base=f"http://127.0.0.1:{server.server_port}"
        context=browser.new_context(viewport={"width":1350,"height":920})
        events=[]
        context.expose_binding("__r6_capture",lambda _source,data:events.append(data))
        context.add_init_script(CAPTURE)
        page=context.new_page()
        try:
            page.goto(base+"/admin/login/?next=/admin/auth/user/",wait_until="load")
            page.locator("#id_username").fill("rootoperator")
            page.locator("#id_password").fill("r6-private-temp-password")
            page.locator('input[type="submit"]').click()
            if page.locator("#id_username").count():
                raise AssertionError("Django admin login failed")
            events.clear()
            trace=root/"trace.zip"
            context.tracing.start(screenshots=False,snapshots=True,sources=False)
            listing="/admin/auth/user/?q=r6_"
            page.goto(base+listing,wait_until="load")
            links=page.locator("#result_list tbody tr .field-username a")
            if links.count()!=2:
                raise AssertionError("Django user changelist is not exactly A/B")
            source_names=links.all_text_contents()
            if [s.strip() for s in source_names]!=["r6_a","r6_b"]:
                raise AssertionError("Initial Django list ordering changed")
            chosen=locator(page,loc,ids)
            if cond in ("overlay_standard","overlay_force"):
                # A fixed overlay only covers the target if the original
                # link has already been scrolled into the viewport. Avoid
                # Playwright's later automatic scrolling moving the page
                # underneath a fixed-position blocker.
                row_A=page.locator("#result_list tbody tr").filter(
                    has=page.get_by_role("link",name="r6_a",exact=True))
                row_A.locator(".field-username a").scroll_into_view_if_needed()
            page.evaluate(MUTATE,{"condition":cond})
            if sql_state(db,ids)!=before:
                raise AssertionError("DOM intervention changed stored data")
            start_requests=len(wrapped.snapshot())
            status="returned"
            try:
                chosen.click(force=cond=="overlay_force",
                             timeout=TIMEOUT_MS)
            except PWTimeout:
                status="timeout"
            except Exception:
                status="playwright_error"
            page.wait_for_timeout(25)
            first_event=next((e for e in events if e.get("trusted")),{})
            clicked_row=(
                "A" if first_event.get("row_name")=="r6_a" else
                "B" if first_event.get("row_name")=="r6_b" else "none"
            )
            clicked_dest=route_id(first_event.get("destination",""),ids)
            change_page=route_id(urlparse(page.url).path,ids)
            followed="none"
            if change_page in ("A","B") and page.locator("#id_first_name").count():
                if op=="edit":
                    page.locator("#id_first_name").fill(f"R6-EDIT-{idx:02d}")
                    page.locator('input[name="_save"]').click()
                    followed="posted_edit"
                else:
                    page.locator("a.deletelink").click()
                    # Native Django admin Delete confirmation. Only one
                    # submitted confirmation input in the deletion form.
                    page.locator('form input[type="submit"]').first.click()
                    followed="posted_delete"
                page.wait_for_timeout(40)
            got=sql_state(db,ids)
            changed=[k for k in ("A","B") if got[k]!=before[k]]
            if len(changed)>1:raise AssertionError("multiple rows changed")
            effect=changed[0] if changed else "none"
            if effect!="none":
                if op=="delete" and got[effect] is not None:
                    raise AssertionError("Django deletion has not committed")
                if op=="edit" and (got[effect] is None or
                        got[effect][1]!=f"R6-EDIT-{idx:02d}"):
                    raise AssertionError("Wrong stored update")
            # Source-verification: re-query UI for BOTH original test
            # users after the SQL readback; renamed first_name keeps username.
            page.goto(base+listing,wait_until="load")
            final_links=[x.strip() for x in page.locator(
                "#result_list tbody tr .field-username a").all_text_contents()]
            should=[k for k in ("r6_a","r6_b") if
                    got["A" if k=="r6_a" else "B"] is not None]
            if sorted(final_links)!=sorted(should):
                raise AssertionError("Rendered Django list and database differ")
            context.tracing.stop(path=str(trace))
            trace_eval=trace_parse(trace,ids)
            incoming=wrapped.snapshot()[start_requests:]
            change_posts=[e for e in incoming if
                          e["method"]=="POST" and e["route"] in
                          ("user_change","user_delete")]
            record_post=(
                "A" if change_posts and change_posts[0]["pk"]==ids["A"] else
                "B" if change_posts and change_posts[0]["pk"]==ids["B"] else
                "none"
            )
            if effect!="none" and not change_posts:
                raise AssertionError("Stored effect without server POST")
            server_post=record_post
            if trace_eval["trace_POST_route_unique"]!=server_post:
                raise AssertionError(
                    "Trace network POST is inconsistent with WSGI server")
            record={
                "case":idx,"operation":op,"locator":loc,"condition":cond,
                "intended":"A","first_click_status":status,
                "first_click_trusted_count":len(events),
                "first_click_row":clicked_row,"first_click_href_record":clicked_dest,
                "first_click_raw_tag":str(first_event.get("raw_tag","none")),
                "first_navigation_record":change_page,
                "followthrough":followed,
                "WSGI_mutation_POST_count":len(change_posts),
                "WSGI_mutation_POST_record":server_post,
                "sqlite_effect_record":effect,
                "sqlite_A_exists":int(got["A"] is not None),
                "sqlite_B_exists":int(got["B"] is not None),
                "sqlite_changed_rows":len(changed),
                "render_matches_SQL":1,
                "event_row_differs_from_effect":int(
                    effect!="none" and clicked_row!=effect),
                "returned_click_without_SQL_effect":int(
                    status=="returned" and effect=="none"),
                "trace_zip_bytes":trace_eval["zip_bytes"],
                "trace_event_lines":trace_eval["trace_lines"],
                "trace_network_lines":trace_eval["network_lines"],
                "trace_member_count":trace_eval["member_count"],
                "trace_click_before_count":trace_eval["click_before_events"],
                "trace_first_click_selector":trace_eval["first_click_selector"],
                "trace_first_click_status":trace_eval["first_click_status"],
                "trace_server_POST_record":trace_eval["trace_POST_route_unique"],
                "trace_event_trusted_target_explicit":0,
                "trace_SQL_commit_explicit":0,
            }
            req={"intended":"A","op":op,"loc":loc,"cond":cond,
                 "returned":status}
            evt={**req,"trusted":int(bool(first_event)),
                 "row":clicked_row,"href_to":clicked_dest,
                 "raw_tag":record["first_click_raw_tag"]}
            server_packet={**evt,"server_post":server_post,
                           "server_POST_count":len(change_posts)}
            effect_packet={**server_packet,"sqlite_effect":effect,
                           "A_exists":record["sqlite_A_exists"],
                           "B_exists":record["sqlite_B_exists"]}
            for label,value in [("request",req),("event",evt),
                                ("server",server_packet),("effect",effect_packet)]:
                raw,compressed=packet_bytes(value)
                record[label+"_bytes"]=raw
                record[label+"_zlib_bytes"]=compressed
            # A conservative auditor scores only explicit fields from
            # the parsed archive; it is not supplied with this result.
            return record
        finally:
            context.close()
            server.shutdown()
            thread.join(timeout=3)
            server.server_close()
            connections.close_all()


def report(rows,django_version,browser_version,source_checks):
    assert len(rows)==48
    assert len({(r["operation"],r["locator"],r["condition"])
                for r in rows})==48
    def group(x):
        return {
            "n":len(x),
            "effects":dict(sorted(Counter(r["sqlite_effect_record"]
                                           for r in x).items())),
            "click_status":dict(sorted(Counter(r["first_click_status"]
                                                for r in x).items())),
            "wrong_B":sum(r["sqlite_effect_record"]=="B" for r in x),
            "returned_no_effect":sum(r["returned_click_without_SQL_effect"] for r in x),
            "event_row_vs_SQL_mismatch":sum(r["event_row_differs_from_effect"] for r in x),
        }
    return {
        "source":"Django 5.2.12 unmodified django.contrib.admin and auth.User",
        "upstream_tag_commit":PIN,
        "upstream_source_sha256":source_checks,
        "runtime":{"python":sys.version.split()[0],"django":django_version,
                   "playwright":PLAYWRIGHT,"chromium":browser_version},
        "predeclared_cases":{"operations":list(OPS),"locators":list(LOCATORS),
                             "conditions":list(CONDITIONS),"count":48},
        "total":group(rows),
        "by_operation":{k:group([r for r in rows if r["operation"]==k]) for k in OPS},
        "by_locator":{k:group([r for r in rows if r["locator"]==k]) for k in LOCATORS},
        "by_condition":{k:group([r for r in rows if r["condition"]==k]) for k in CONDITIONS},
        "bytes":{
            label:{
                "raw_utf8":sum(r[label+"_bytes"] for r in rows),
                "zlib_per_case":sum(r[label+"_zlib_bytes"] for r in rows)
            } for label in ("request","event","server","effect")
        },
        "trace":{
            "zip_total_bytes":sum(r["trace_zip_bytes"] for r in rows),
            "zip_median_bytes":sorted(r["trace_zip_bytes"] for r in rows)[24],
            "trace_record_count":sum(r["trace_event_lines"] for r in rows),
            "network_record_count":sum(r["trace_network_lines"] for r in rows),
            "first_click_selector_present_n":sum(
                r["trace_first_click_selector"]=="present" for r in rows),
            "first_click_result_present_n":sum(
                r["trace_first_click_status"]!="unavailable" for r in rows),
            "server_POST_record_correct_n":sum(
                r["trace_server_POST_record"]==r["WSGI_mutation_POST_record"]
                for r in rows),
        },
        "oracle_sources":{
            "trusted_receiver":"independent capture listener",
            "server_route":"read-only WSGI boundary wrapper",
            "stored_effect":"separate native sqlite3.connect",
            "trace":"original Playwright context.tracing ZIP",
        },
        "raw_trace_published":False,
        "sql_state_not_present_as_trace_oracle":True,
        "second_independent_project":True,
        "synthetic_DOM_interventions":True,
        "production_web_agent_error_rate":False,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    import django
    with tempfile.TemporaryDirectory(prefix="r6_master_") as dirname:
        root=Path(dirname)
        template=root/"base.sqlite3"
        init_django(template)
        import django.contrib.auth.admin, django.contrib.admin.options
        checks={
            "django/contrib/auth/admin.py":hashlib.sha256(
                Path(django.contrib.auth.admin.__file__).read_bytes()).hexdigest(),
            "django/contrib/admin/options.py":hashlib.sha256(
                Path(django.contrib.admin.options.__file__).read_bytes()).hexdigest()
        }
        result=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                version=browser.version
                for n,(op,loc,cond) in enumerate(matrix(),1):
                    result.append(episode(browser,template,op,loc,cond,n))
                    if n%8==0:
                        print("R6_COMPLETE",n,"/",48,flush=True)
            finally:browser.close()
        final=report(result,django.get_version(),version,checks)
        with (OUT/"r6_django_48.csv").open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(result[0]))
            writer.writeheader();writer.writerows(result)
        (OUT/"r6_django_summary.json").write_text(
            json.dumps(final,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("R6_SUMMARY",json.dumps(final,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
