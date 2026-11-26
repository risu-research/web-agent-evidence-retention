"""Native group deletion: compare evidence packets against observed permission loss."""
import sys, json, re, hashlib, tempfile, shutil, threading, sqlite3, zlib, zipfile
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
from wsgiref.simple_server import make_server
import django_user_fixture as r6
from trace_dom_reader import read_raw, SnapshotDecoder, Node
from playwright.sync_api import sync_playwright
from django.contrib.staticfiles.handlers import StaticFilesHandler

PAIRS=("backup_group_equal_pre","direct_grant_equal_pre","two_members_equal_pre","same_loss_control","visible_count_control","equal_marginals_two_permissions")
def seed(db,kind,variant):
    from django.contrib.auth.models import User,Group,Permission
    from django.db import connections
    r6.switch_database(db)
    root=User.objects.create_superuser("operator","operator@example.invalid","local-dummy-only")
    a=User.objects.create_user("member_a",password="local-dummy",is_staff=True)
    b=User.objects.create_user("member_b",password="local-dummy",is_staff=True)
    target=Group.objects.create(name="target_group")
    backup=Group.objects.create(name="backup_group")
    perm=Permission.objects.get(content_type__app_label="auth",content_type__model="user",codename="change_user")
    target.permissions.add(perm)
    backup.permissions.add(perm)
    # B's direct grant is fixed in the first two pairs. Both users always have
    # change_user before deletion. The alternate relationship is moved A -> B.
    if kind=="backup_group_equal_pre":
        target.user_set.add(a)
        b.user_permissions.add(perm)
        backup.user_set.add(a if variant==0 else b)
    elif kind=="direct_grant_equal_pre":
        target.user_set.add(a)
        backup.user_set.add(b)
        (a if variant==0 else b).user_permissions.add(perm)
    elif kind=="two_members_equal_pre":
        target.user_set.add(a,b)
        backup.user_set.add(a if variant==0 else b)
    elif kind=="same_loss_control":
        target.user_set.add(a)
        b.user_permissions.add(perm)
        if variant==0: backup.user_set.add(a)
        else: a.user_permissions.add(perm)
    elif kind=="visible_count_control":
        a.user_permissions.add(perm)
        b.user_permissions.add(perm)
        if variant==1: target.user_set.add(a)
    elif kind=="equal_marginals_two_permissions":
        q=Permission.objects.get(content_type__app_label="auth",content_type__model="group",codename="change_group")
        target.permissions.add(q)
        target.user_set.add(a,b)
        # Identical membership and permission counts, swapped direct grant endpoints.
        (a if variant==0 else b).user_permissions.add(perm)
        (b if variant==0 else a).user_permissions.add(q)
    else: raise AssertionError(kind)
    ids={"target":target.pk,"permission":perm.pk,"backup":backup.pk}
    connections.close_all()
    return ids
def truth(db,ids):
    with sqlite3.connect(db) as con:
        grants=con.execute("""
        SELECT u.username FROM auth_user u
        WHERE u.username IN ('member_a','member_b') AND (
          EXISTS(SELECT 1 FROM auth_user_user_permissions p WHERE p.user_id=u.id AND p.permission_id=?)
          OR EXISTS(SELECT 1 FROM auth_user_groups g JOIN auth_group_permissions p ON p.group_id=g.group_id
          WHERE g.user_id=u.id AND p.permission_id=?))
        ORDER BY u.username""",(ids["permission"],ids["permission"])).fetchall()
        memberships=con.execute("SELECT u.username FROM auth_user_groups g JOIN auth_user u ON g.user_id=u.id WHERE g.group_id=? ORDER BY u.username",(ids["target"],)).fetchall()
        effective_pairs=con.execute("""
          SELECT u.username,p.codename FROM auth_user u CROSS JOIN auth_permission p
          WHERE u.username IN ('member_a','member_b') AND p.codename IN ('change_user','change_group')
          AND p.content_type_id IN (SELECT id FROM django_content_type WHERE app_label='auth' AND model IN ('user','group'))
          AND (EXISTS(SELECT 1 FROM auth_user_user_permissions x WHERE x.user_id=u.id AND x.permission_id=p.id)
          OR EXISTS(SELECT 1 FROM auth_user_groups g JOIN auth_group_permissions x ON g.group_id=x.group_id WHERE g.user_id=u.id AND x.permission_id=p.id))
          ORDER BY u.username,p.codename
        """).fetchall()
        exists=con.execute("SELECT COUNT(*) FROM auth_group WHERE id=?",(ids["target"],)).fetchone()[0]
        group_permissions=con.execute("SELECT p.codename FROM auth_group_permissions g JOIN auth_permission p ON p.id=g.permission_id WHERE g.group_id=? ORDER BY p.codename",(ids["target"],)).fetchall()
    return {"granted":[x[0] for x in grants],"target_members":[x[0] for x in memberships],"target_exists":exists,"target_permissions":[x[0] for x in group_permissions],"target_id":ids["target"],"effective_pairs":effective_pairs}
def native_permissions(db):
    from concurrent.futures import ThreadPoolExecutor
    def worker():
        from django.contrib.auth.models import User
        from django.test import Client
        from django.db import connections
        try:
            observed={}
            for name in ("member_a","member_b","operator"):
                user=User.objects.get(username=name)
                permission=user.has_perm("auth.change_user")
                client=Client(HTTP_HOST="localhost")
                client.force_login(user)
                res=client.get(f"/admin/auth/user/{user.pk}/change/")
                from django.contrib.auth.models import Group
                backup=Group.objects.get(name="backup_group")
                group_res=client.get(f"/admin/auth/group/{backup.pk}/change/")
                observed[name]={"has_perm":permission,"change_form_status":res.status_code,"all_permissions":sorted(user.get_all_permissions()),"group_form_status":group_res.status_code,"has_group_perm":user.has_perm("auth.change_group")}
                client.logout()
            return observed
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(worker).result()
def native_log(db):
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT user_id,content_type_id,object_id,object_repr,action_flag,change_message FROM django_admin_log ORDER BY id").fetchall()
def alternative_packet(db,ids):
    with sqlite3.connect(db) as conn:
        rows=conn.execute("""
          SELECT u.username, p.codename,
          EXISTS(SELECT 1 FROM auth_user_user_permissions x WHERE x.user_id=u.id AND x.permission_id=p.id)
          OR EXISTS(SELECT 1 FROM auth_user_groups g JOIN auth_group_permissions x ON x.group_id=g.group_id
                    WHERE g.user_id=u.id AND g.group_id<>? AND x.permission_id=p.id)
          FROM auth_user_groups m JOIN auth_user u ON m.user_id=u.id
          JOIN auth_group_permissions gp ON gp.group_id=m.group_id
          JOIN auth_permission p ON p.id=gp.permission_id
          WHERE m.group_id=? ORDER BY u.username,p.codename
        """,(ids["target"],ids["target"])).fetchall()
    return rows
# same question, same identifier encoding, same episode envelope.
# Each complete packet carries version, numeric method ID, target identity,
# independently verified deletion success and its method-specific payload.
# Pre-state packets are conditional predictions; post-state packets are observations.
METHODS={0:"pre_full_relationships",1:"pre_candidates_alternative_bits",2:"pre_candidates_alternative_list",
         3:"post_effective_before_after",4:"post_loss_list",5:"post_universe_loss_bits",
         6:"post_candidate_loss_bits"}
def relationship_packet(db):
    with sqlite3.connect(db) as con:
        membership=con.execute("""
          SELECT u.username,g.id FROM auth_user_groups m JOIN auth_user u ON u.id=m.user_id
          JOIN auth_group g ON g.id=m.group_id WHERE u.username IN ('member_a','member_b')
          ORDER BY u.username,g.id
        """).fetchall()
        grants=con.execute("""
          SELECT g.id,p.codename FROM auth_group_permissions x JOIN auth_group g ON g.id=x.group_id
          JOIN auth_permission p ON p.id=x.permission_id JOIN django_content_type t ON t.id=p.content_type_id
          WHERE t.app_label='auth' AND p.codename IN ('change_user','change_group')
          ORDER BY g.id,p.codename
        """).fetchall()
        direct=con.execute("""
          SELECT u.username,p.codename FROM auth_user_user_permissions x JOIN auth_user u ON u.id=x.user_id
          JOIN auth_permission p ON p.id=x.permission_id JOIN django_content_type t ON t.id=p.content_type_id
          WHERE u.username IN ('member_a','member_b') AND t.app_label='auth' AND p.codename IN ('change_user','change_group')
          ORDER BY u.username,p.codename
        """).fetchall()
    return [membership,grants,direct]
def decode_packet(blob):
    version,method,target,committed,payload=json.loads(blob)
    assert version==1 and method in METHODS
    if method in (0,1,2) and not committed:return []
    if method==0:
        membership,grants,direct=payload
        full={(u,p) for u,g in membership for h,p in grants if g==h}|set(map(tuple,direct))
        remaining={(u,p) for u,g in membership for h,p in grants if g==h and g!=target}|set(map(tuple,direct))
        result=full-remaining
    elif method in (1,2,5,6):
        members,perms,data=payload
        candidates=[(u,p) for u in members for p in perms]
        if method==2:result=set(candidates)-set(map(tuple,data))
        else:
            assert len(data)==len(candidates) and set(data)<={"0","1"}
            result={pair for pair,bit in zip(candidates,data) if bit==("0" if method==1 else "1")}
    elif method==3:result=set(map(tuple,payload[0]))-set(map(tuple,payload[1]))
    elif method==4:result=set(map(tuple,payload))
    return sorted(result)
def observed_effective(native):
    return sorted((u,p) for u in ("member_a","member_b") for p in ("change_group","change_user") if "auth."+p in native[u]["all_permissions"])
def build_packets(target,pre,alt,rel,native_before,native_after,committed):
    members=pre["target_members"];perms=pre["target_permissions"]
    candidates=[(u,p) for u in members for p in perms]
    alternatives={(u,p) for u,p,has in alt if has}
    assert set(candidates)=={(u,p) for u,p,has in alt}
    actual_before=observed_effective(native_before)
    actual_after=observed_effective(native_after)
    actual_loss=sorted(set(actual_before)-set(actual_after))
    # Include the identity dictionary in every bitmap; no free out-of-band dictionary.
    users=["member_a","member_b"];permissions=["change_group","change_user"]
    universe=[(u,p) for u in users for p in permissions]
    assert set(actual_loss)<=set(candidates)
    payloads={
      0:rel,
      1:[members,perms,"".join("1" if x in alternatives else "0" for x in candidates)],
      2:[members,perms,sorted(alternatives)],
      3:[actual_before,actual_after],
      4:actual_loss,
      5:[users,permissions,"".join("1" if x in actual_loss else "0" for x in universe)],
      6:[members,perms,"".join("1" if x in actual_loss else "0" for x in candidates)]}
    packets={}
    for method,payload in payloads.items():
        raw=json.dumps([1,method,target,committed,payload],separators=(",",":"),sort_keys=True).encode()
        compressed=zlib.compress(raw,9)
        # Auditor receives only decoded packet bytes, no database or oracle.
        result=decode_packet(zlib.decompress(compressed))
        assert result==decode_packet(raw)
        packets[METHODS[method]]={"encoded":raw.decode(),"bytes":len(raw),"zlib_bytes":len(compressed),"decoded":result}
    return packets
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def normalize(s,base):
    s=s.replace(base,"http://localhost")
    # CSRF form values only, preserving all other fields.
    s=re.sub(r'(name="csrfmiddlewaretoken" value=")[A-Za-z0-9]+(")',r'\1CSRF\2',s)
    s=re.sub(r'("csrfmiddlewaretoken"\s+value=")[A-Za-z0-9]+(")',r'\1CSRF\2',s)
    return s
def node_value(node,base):
    if isinstance(node,str):return normalize(node,base)
    if not isinstance(node,Node):return None
    attrs={k:normalize(str(v),base) for k,v in node.attrs.items()}
    if attrs.get("name")=="csrfmiddlewaretoken":
        for k in ("value","__playwright_value__"):
            if k in attrs:attrs[k]="CSRF"
    return [node.name,attrs,[node_value(c,base) for c in node.children]]
INTERNAL={}
def trace_projection(events,net,snapshots,trace,base):
    # Compare exact decoded trees with only predeclared treatment of CSRF/origin;
    # Playwright marker values are a distinct diagnostic tier, never silently erased.
    calls={e.get("callId"):i for i,e in enumerate(x for x in events if x.get("type")=="before")}
    def targetnorm(x):
        if isinstance(x,str):return x
        if not isinstance(x,list) or len(x)!=3:return x
        tag,attrs,children=x
        attrs=dict(attrs)
        if "__playwright_target__" in attrs:
            val=attrs["__playwright_target__"]
            attrs["__playwright_target__"]=calls.get(val,val)
        return [tag,attrs,[targetnorm(ch) for ch in children]]
    csrf_inventory=Counter()
    def csrf_check(node):
        if not isinstance(node,Node):return
        attrs=node.attrs
        if "__playwright_value_" in attrs:
            if node.name.upper()=="INPUT" and attrs.get("name")=="csrfmiddlewaretoken" and attrs.get("type","").lower()=="hidden":
                raw=str(attrs.get("__playwright_value_",""))
                native=str(attrs.get("value",""))
                if raw==native and re.fullmatch(r"[A-Za-z0-9]{64}",raw):
                    csrf_inventory["hidden_csrf_runtime_matches_native_masked_token"]+=1
                else:csrf_inventory["hidden_csrf_runtime_other"]+=1
            else:csrf_inventory["other_input_runtime_value"]+=1
        for child in node.children:csrf_check(child)
    def csrf_norm(x):
        if isinstance(x,str):return x
        if not isinstance(x,list) or len(x)!=3:return x
        tag,attrs,children=x
        attrs=dict(attrs)
        if tag.upper()=="INPUT" and attrs.get("name")=="csrfmiddlewaretoken" and attrs.get("type","").lower()=="hidden" and attrs.get("value")=="CSRF" and re.fullmatch(r"[A-Za-z0-9]{64}",str(attrs.get("__playwright_value_",""))):
            attrs["__playwright_value_"]="CSRF"
        return [tag,attrs,[csrf_norm(ch) for ch in children]]
    snaps=[]
    for meta,node in snapshots:
        csrf_check(node)
        original=node_value(node,base)
        key=[calls.get(meta.get("callId"),"unmapped"),meta.get("phase"),meta.get("snapshotName","").split("@")[0],urlsplit(meta.get("frameUrl","")).path]
        snaps.append((key,original,csrf_norm(targetnorm(original))))
    def normobj(obj):
        if isinstance(obj,str):return normalize(obj,base)
        if isinstance(obj,list):return [normobj(x) for x in obj]
        if isinstance(obj,dict):return {k:normobj(v) for k,v in obj.items()}
        return obj
    actions=[]
    for e in events:
        if e.get("type")=="before":
            actions.append([e.get("class"),e.get("method"),e.get("apiName"),normobj(e.get("params"))])
    resources=[]; schema=Counter(); content_keys=Counter(); response_keys=Counter(); post_keys=Counter()
    with zipfile.ZipFile(trace) as z:
        names=set(z.namelist()); schema["zip_resource_members"]=sum(n.startswith("resources/") for n in names)
        for entry in net:
            st=entry.get("snapshot",{})
            req=st.get("request",{}); res=st.get("response",{})
            if not req:continue
            url=urlsplit(req.get("url",""))
            post=req.get("postData") or {}
            postsha=post.get("_sha1") or post.get("sha1") or post.get("_file")
            postname=str(postsha) if str(postsha).startswith("resources/") else "resources/"+str(postsha)
            posttext=post.get("text") or ""
            source="inline" if posttext else "none"
            if postsha:
                if postname in names:
                    posttext=z.read(postname).decode("utf-8",errors="strict")
                    source="attached"
                else:source="missing_attachment"
            if "application/x-www-form-urlencoded" in post.get("mimeType",""):
                fields=parse_qsl(posttext,keep_blank_values=True)
                if not fields and post.get("params"):
                    fields=[(x["name"],x["value"]) for x in post["params"]]
                    source="params_only"
                fields=[(k,"CSRF" if k=="csrfmiddlewaretoken" else v) for k,v in fields]
                if req.get("method")=="POST":
                    assert fields and source!="missing_attachment","POST form not recovered"
            elif posttext:fields=[("opaque_body_sha256",digest(posttext))]
            else:fields=[]
            def headers(raw):
                result=[]
                for h in raw:
                    name=h["name"].lower(); value=h.get("value","")
                    if name=="host" and value==urlsplit(base).netloc:value="localhost"
                    value=normalize(value,base)
                    if name in ("cookie","set-cookie"):
                        value=re.sub(r"(?i)(\b(?:csrftoken|sessionid)=)[^;\s]+",r"\1TOKEN",value)
                    result.append((name,value))
                return sorted(result)
            content=res.get("content") or {}
            content_keys.update(content.keys());response_keys.update(res.keys());post_keys.update(post.keys())
            sha=content.get("_sha1") or content.get("sha1") or content.get("_file")
            name=str(sha) if str(sha).startswith("resources/") else "resources/"+str(sha)
            body="missing"; b=None
            if sha:
                schema["response_attachment_reference"]+=1
                if name in names:b=z.read(name);schema["response_attachment_read"]+=1
                else:schema["response_attachment_not_found"]+=1
            elif isinstance(content.get("text"),str) and content["text"]:
                if content.get("encoding")=="base64":
                    import base64
                    b=base64.b64decode(content["text"],validate=True)
                else:b=content["text"].encode("utf-8")
                schema["response_inline_read"]+=1
            else:schema["response_no_body_reference_or_inline"]+=1
            if b is not None:
                if "html" in str(content.get("mimeType","")):
                    body=digest(normalize(b.decode("utf-8",errors="strict"),base))
                else:body=hashlib.sha256(b).hexdigest()
            resources.append({"key":[req.get("method"),url.path,url.query],
                              "status":res.get("status"),"form":fields,"body":body,"post_source":source,
                              "request_headers":headers(req.get("headers",[])),"response_headers":headers(res.get("headers",[])),
                              "request_header_names":sorted(h["name"].lower() for h in req.get("headers",[])),
                              "response_header_names":sorted(h["name"].lower() for h in res.get("headers",[]))})
    return {"snapshots":snaps,"actions":actions,"resources":resources,"csrf_inventory":dict(csrf_inventory),"resource_schema":dict(schema),"content_keys":dict(content_keys),"response_keys":dict(response_keys),"post_keys":dict(post_keys)}
def compare_trace(left,right):
    # Preserve unequal sequence and distinguish same-state duplicates from changes.
    a,b=left["snapshots"],right["snapshots"]
    aa=[(json.dumps(k,sort_keys=True),digest(n)) for k,_,n in a]
    bb=[(json.dumps(k,sort_keys=True),digest(n)) for k,_,n in b]
    # Match by call ordinal/phase/page first, not by expected truth.
    ka=[x[0] for x in aa];kb=[x[0] for x in bb]
    matcher=SequenceMatcher(None,ka,kb,autojunk=False)
    diff=Counter(); examples={}; unmatched=[0,0]; aligned=0; equal=0; raw_equal=0
    def note(kind,path,left,right):
        diff[kind]+=1
        if kind not in examples:
            # Never publish literal text, attributes, cookies, or tokens.
            examples[kind]={"path":path,"left_sha256":digest(left),"right_sha256":digest(right)}
    def compare(x,y,path):
        if x==y:return
        if isinstance(x,str) and isinstance(y,str):
            note("text_value",path,x,y);return
        if not isinstance(x,list) or not isinstance(y,list) or len(x)!=3 or len(y)!=3:
            note("node_type",path,x,y);return
        if x[0]!=y[0]:note("tag",path,x[0],y[0]);return
        tag,ax,cx=x;_,ay,cy=y
        for k in sorted(set(ax)|set(ay)):
            if ax.get(k)!=ay.get(k):note("attribute:"+tag+":"+k,path,ax.get(k),ay.get(k))
        if len(cx)!=len(cy):note("child_count:"+tag,path,len(cx),len(cy))
        for i,(u,v) in enumerate(zip(cx,cy)):compare(u,v,path+"/"+tag+"["+str(i)+"]")
    for op,i,j,k,l in matcher.get_opcodes():
        if op=="equal":
            for ix,iy in zip(range(i,j),range(k,l)):
                aligned+=1
                if a[ix][1]==b[iy][1]:raw_equal+=1
                if a[ix][2]==b[iy][2]:equal+=1
                else:compare(a[ix][2],b[iy][2],"root")
        else:unmatched[0]+=j-i;unmatched[1]+=l-k
    # Compare full network projection (ordered and multiset); record every divergent path/status/body.
    def key(r):return json.dumps(r["key"])
    def netdiff(a,b):
        ax=defaultdict(list);bx=defaultdict(list)
        for r in a:ax[key(r)].append(r)
        for r in b:bx[key(r)].append(r)
        out={}
        for k in sorted(set(ax)|set(bx)):
            if ax[k]!=bx[k]:
                out[k]={"counts":[len(ax[k]),len(bx[k])],
                        "status":[[r["status"] for r in ax[k]],[r["status"] for r in bx[k]]],
                        "fields_differ":[f for f in ("status","form","body","post_source","request_header_names","response_header_names","request_headers","response_headers") if [r[f] for r in ax[k]]!=[r[f] for r in bx[k]]],
                        "header_value_differences":{f:sorted({name for r in ax[k]+bx[k] for name,value in r[f] if [[v for n,v in row[f] if n==name] for row in ax[k]]!=[[v for n,v in row[f] if n==name] for row in bx[k]]}) for f in ("request_headers","response_headers")}}
        return out
    return {"snapshot_counts":[len(a),len(b)],"aligned":aligned,"raw_aligned_equal":raw_equal,
            "csrf_inventory":[left["csrf_inventory"],right["csrf_inventory"]],
            "resource_schema":[{k:side[k] for k in ("resource_schema","content_keys","response_keys","post_keys")} for side in (left,right)],
            "marker_normalized_aligned_equal":equal,"unmatched":unmatched,"node_diff_counts":dict(diff),"redacted_diff_examples":examples,
            "marker_normalized_snapshot_hash_sets_equal":set(x[1] for x in aa)==set(x[1] for x in bb),
            "action_records_equal":left["actions"]==right["actions"],
            "network_record_counts":[len(left["resources"]),len(right["resources"])],
            "post_body_sources":[dict(Counter(r["post_source"] for r in side["resources"] if r["key"][0]=="POST")) for side in (left,right)],
            "response_body_missing":[sum(r["body"]=="missing" for r in side["resources"]) for side in (left,right)],
            "network_ordered_projection_equal":left["resources"]==right["resources"],
            "network_projection_differences":netdiff(left["resources"],right["resources"])}
def episode(browser,db,ids,kind,variant):
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    r6.switch_database(db)
    before=truth(db,ids)
    native_before=native_permissions(db)
    alt=alternative_packet(db,ids)
    rel=relationship_packet(db)
    server=make_server("127.0.0.1",0,StaticFilesHandler(get_wsgi_application()),handler_class=r6.NoLog)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    base=f"http://127.0.0.1:{server.server_port}"
    ctx=browser.new_context(viewport={"width":1350,"height":920})
    p=ctx.new_page()
    try:
        p.goto(base+"/admin/login/?next=/admin/auth/group/")
        p.locator("#id_username").fill("operator")
        p.locator("#id_password").fill("local-dummy-only")
        p.locator('input[type=submit]').click()
        p.locator("#result_list").wait_for()
        trace=db.parent/"trace.zip"
        ctx.tracing.start(screenshots=True,snapshots=True,sources=False)
        docs=[]
        doc_records=[]
        def capture_docs():
            for res in docs[:]:
                req=res.request
                fields=parse_qsl(req.post_data or "",keep_blank_values=True)
                fields=[(k,"CSRF" if k=="csrfmiddlewaretoken" else v) for k,v in fields]
                body=normalize(res.text(),base) if res.status==200 and "text/html" in res.headers.get("content-type","") else ""
                doc_records.append([req.method,urlsplit(req.url).path,urlsplit(req.url).query,res.status,fields,digest(body)])
            docs.clear()
        p.on("response",lambda res:docs.append(res) if res.request.resource_type=="document" else None)
        p.goto(base+"/admin/auth/group/",wait_until="load")
        row=p.locator("#result_list tbody tr").filter(has=p.get_by_role("link",name="target_group",exact=True))
        assert row.count()==1
        before_dom=normalize(p.content(),base)
        capture_docs()
        row.locator('input[type=checkbox]').check()
        p.locator('select[name=action]').select_option("delete_selected")
        p.locator('button[name=index]').click()
        p.locator('input[name=post]').wait_for(state="attached")
        confirm_dom=normalize(p.content(),base)
        capture_docs()
        confirmation=p.locator("#content").inner_text()
        # Native confirmation must show target, but membership endpoints may not be displayed.
        assert "target_group" in confirmation
        p.locator('form input[type=submit]').last.click()
        p.locator("#result_list").wait_for()
        assert p.get_by_role("link",name="target_group",exact=True).count()==0
        final_dom=normalize(p.content(),base)
        capture_docs()
        ctx.tracing.stop(path=trace)
        events,net=read_raw(trace)
        decoder=SnapshotDecoder(); decoded=[]; snapshot_records=[]
        for event in events:
            if event.get("type")=="frame-snapshot":
                s=event.get("snapshot",{})
                if s.get("isMainFrame"):
                    root=decoder.decode(s)
                    if root is not None:
                        decoded.append(digest(node_value(root,base)))
                        snapshot_records.append((s,root))
        trace_audit=trace_projection(events,net,snapshot_records,trace,base)
        # Internal detailed projections live only in process memory until paired comparison.
        INTERNAL[(kind,variant)]=trace_audit
        assert decoder.ref_failures==0 and decoder.decoded>0
        after=truth(db,ids)
        native_after=native_permissions(db)
        log=native_log(db)
        assert before["target_exists"]==1 and after["target_exists"]==0
        assert after["target_members"]==[]
        lost=sorted(set(before["granted"])-set(after["granted"]))
        native_lost=sorted(k for k,v in native_before.items() if k!="operator" and v["has_perm"] and not native_after[k]["has_perm"])
        http_lost=sorted(k for k,v in native_before.items() if k!="operator" and v["change_form_status"]==200 and native_after[k]["change_form_status"]==403)
        assert all((v["change_form_status"]==200)==v["has_perm"] and v["change_form_status"] in (200,403) for obs in (native_before,native_after) for v in obs.values())
        assert all(sorted(k for k,v in obs.items() if k!="operator" and v["has_perm"])==state["granted"] for obs,state in ((native_before,before),(native_after,after)))
        assert lost==native_lost==http_lost==sorted(row[0] for row in alt if row[1]=="change_user" and not row[2])
        lost_pairs=sorted(set(before["effective_pairs"])-set(after["effective_pairs"]))
        native_pairs=sorted((u,p) for u in ("member_a","member_b") for p in ("change_user","change_group") if "auth."+p in native_before[u]["all_permissions"] and "auth."+p not in native_after[u]["all_permissions"])
        http_pairs=sorted((u,p) for u in ("member_a","member_b") for p,k in (("change_user","change_form_status"),("change_group","group_form_status")) if native_before[u][k]==200 and native_after[u][k]==403)
        assert all(v["group_form_status"] in (200,403) and (v["group_form_status"]==200)==v["has_group_perm"] for obs in (native_before,native_after) for v in obs.values())
        assert lost_pairs==native_pairs==http_pairs==sorted((u,p) for u,p,has in alt if not has)
        packets=build_packets(ids["target"],before,alt,rel,native_before,native_after,after["target_exists"]==0)
        assert all(v["decoded"]==lost_pairs for v in packets.values())
        margins=[len(lost_pairs),sorted(Counter(u for u,p in lost_pairs).items()),sorted(Counter(p for u,p in lost_pairs).items())]
        assert len(log)==1 and log[0][3]=="target_group" and log[0][4]==3
        log_projection=log[0]
        return {"kind":kind,"variant":variant,"before":before,"after":after,"lost":lost,
                "dom_hashes":[digest(before_dom),digest(confirm_dom),digest(final_dom)],
                "confirmation_hash":digest(confirmation),"lost_pairs":lost_pairs,"margins":margins,"packets":packets,
                "native_before":native_before,"native_after":native_after,"native_lost":native_lost,"http_lost":http_lost,"alternative_packet":alt,"native_admin_log":log_projection,
                "confirmation_mentions_members":[n for n in ("member_a","member_b") if n in confirmation],
                "document_records":doc_records,"decoded_snapshot_count":decoder.decoded,
                "decoded_unique_hashes":sorted(set(decoded)),"trace_bytes":trace.stat().st_size,
                "snapshot_failures":decoder.ref_failures,
                "effect_packet_bytes":len(zlib.compress(json.dumps({"before":before,"after":after},sort_keys=True,separators=(",",":")).encode(),9))}
    finally:
        ctx.close();server.shutdown();server.server_close();t.join(timeout=3)
        connections.close_all()
def main():
    import django
    out=Path("out_permission_loss");out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); template=root/"template.sqlite3"
        r6.init_django(template)
        prepared=[]
        for kind in PAIRS:
            for variant in (0,1):
                d=root/f"{kind}-{variant}";d.mkdir()
                db=d/"db.sqlite3";shutil.copy2(template,db)
                ids=seed(db,kind,variant);prepared.append((db,ids,kind,variant))
        rows=[]
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            for db,ids,kind,variant in prepared:
                row=episode(browser,db,ids,kind,variant);rows.append(row)
                print("CASE",kind,variant,"pre",row["before"]["granted"],"post",row["after"]["granted"],"lost",row["lost"],"native",row["native_lost"],"http",row["http_lost"],"packet",row["alternative_packet"],"decoded",row["decoded_snapshot_count"],flush=True)
            browser.close()
        pairs=[]
        for kind in PAIRS:
            a,b=[x for x in rows if x["kind"]==kind]
            pairs.append({"kind":kind,"same_three_dom":a["dom_hashes"]==b["dom_hashes"],
                          "same_confirmation":a["confirmation_hash"]==b["confirmation_hash"],
                          "trace_decomposition":compare_trace(INTERNAL[(kind,0)],INTERNAL[(kind,1)]),
                          "same_loss_margins":a["margins"]==b["margins"],
                          "lost_pairs":[a["lost_pairs"],b["lost_pairs"]],
                          "lost_pairs_differ":a["lost_pairs"]!=b["lost_pairs"],
                          "same_pre_effective_all":a["native_before"]==b["native_before"],
                          "same_pre_target_members":a["before"]["target_members"]==b["before"]["target_members"],
                          "same_pre_target_permissions":a["before"]["target_permissions"]==b["before"]["target_permissions"],
                          "same_target_id":a["before"]["target_id"]==b["before"]["target_id"],
                          "pre_grants": [a["before"]["granted"],b["before"]["granted"]],
                          "alt_packet_differs":a["alternative_packet"]!=b["alternative_packet"],
                          "same_native_admin_log":a["native_admin_log"]==b["native_admin_log"],
                          "native_http_agreement":all(x["lost"]==x["native_lost"]==x["http_lost"] for x in (a,b)),
                          "same_document_records":a["document_records"]==b["document_records"],
                          "same_all_decoded_snapshot_hash_set":a["decoded_unique_hashes"]==b["decoded_unique_hashes"],
                          "lost_different":a["lost"]!=b["lost"],"lost":[a["lost"],b["lost"]],
                          "member_names_in_confirmation":[a["confirmation_mentions_members"],b["confirmation_mentions_members"]]})
        totals={}
        for method in METHODS.values():
            packets=[x["packets"][method] for x in rows]
            totals[method]={"raw":sum(p["bytes"] for p in packets),"zlib":sum(p["zlib_bytes"] for p in packets),
              "min_zlib":min(p["zlib_bytes"] for p in packets),"max_zlib":max(p["zlib_bytes"] for p in packets),
              "correct":sum(p["decoded"]==x["lost_pairs"] for p,x in zip(packets,rows))}
        # Compare collisions using only independently observed evidence projections.
        fields={
          "target_and_native_log":lambda x:[x["before"]["target_id"],x["native_admin_log"]],
          "target_members_permissions_pre_effective":lambda x:[x["before"]["target_id"],x["before"]["target_members"],x["before"]["target_permissions"],x["before"]["effective_pairs"]],
          "pre_effective_plus_loss_margins":lambda x:[x["before"]["target_id"],x["before"]["target_members"],x["before"]["target_permissions"],x["before"]["effective_pairs"],x["margins"]]}
        ambiguity={}
        for label,project in fields.items():
            buckets=defaultdict(list)
            for x in rows:buckets[digest(project(x))].append(x)
            ambiguous=[b for b in buckets.values() if len({digest(x["lost_pairs"]) for x in b})>1]
            ambiguity[label]={"observed_ambiguous_episodes":sum(map(len,ambiguous)),"observed_conflicting_classes":len(ambiguous),"distinct_records":len(buckets)}
        result={"django":django.get_version(),"cases":rows,"pairs":pairs,"packet_totals":totals,"observed_collision":ambiguity,
                "gate":"Three equal-pre native collisions, same-loss negative control and visible-count positive control.",
                "native_gate":all(all(p[k] for k in ("same_three_dom","same_document_records","same_native_admin_log","native_http_agreement","same_pre_effective_all","same_pre_target_members","same_pre_target_permissions","same_target_id","lost_different","alt_packet_differs")) for p in pairs[:3]) and all(pairs[3][k] for k in ("same_three_dom","same_document_records","same_native_admin_log","same_pre_effective_all","same_pre_target_members","same_pre_target_permissions","same_target_id")) and not pairs[3]["lost_different"] and not pairs[3]["alt_packet_differs"] and not pairs[4]["same_confirmation"] and pairs[4]["same_pre_effective_all"] and all(pairs[5][k] for k in ("same_three_dom","same_document_records","same_native_admin_log","same_pre_effective_all","same_pre_target_members","same_pre_target_permissions","same_target_id","same_loss_margins","lost_pairs_differ","alt_packet_differs"))}
        (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True))
        print("PERMISSION_PACKET_RESULT",json.dumps({"native_gate":result["native_gate"],"packet_totals":totals,"observed_collision":ambiguity,"cases":[{"kind":x["kind"],"variant":x["variant"],"truth":x["lost_pairs"],"packets":x["packets"],"trace_bytes":x["trace_bytes"]} for x in rows]},sort_keys=True),flush=True)
        assert result["native_gate"],"Native permission-loss comparison failed"
        assert all(v["correct"]==len(rows) for v in totals.values())
if __name__=="__main__":main()
