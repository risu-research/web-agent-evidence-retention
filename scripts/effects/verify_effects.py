"""Offline verification of archived derived results and a separate finite SQLite model.
No browser trace, network access, or source database is required. Run from any directory.
"""
import csv,itertools,json,sqlite3,zlib
from pathlib import Path
from collections import Counter,defaultdict
D=Path(__file__).resolve().parents[2]/"results"/"effects"
U=["member_a","member_b"];P=["change_group","change_user"];G=[1,2]
UP=list(itertools.product(U,P)); UG=list(itertools.product(U,G)); GP=list(itertools.product(G,P))
METHODS=["pre_full_relationships","pre_candidates_alternative_bits","pre_candidates_alternative_list","post_effective_before_after","post_loss_list","post_universe_loss_bits","post_candidate_loss_bits","pre_predicted_loss_list"]
def enc(obj):return json.dumps(obj,separators=(",",":"),sort_keys=True).encode()
def decode(raw):
    v,i,t,ok,p=json.loads(raw);assert v==1 and i in range(8)
    if i in (0,1,2,7) and not ok:return set()
    if i==0:
        m,g,d=p;before=set(map(tuple,d));after=set(before)
        for u,h in m:
            for j,q in g:
                if h==j:
                    before.add((u,q))
                    if j!=t:after.add((u,q))
        return before-after
    if i==3:return set(map(tuple,p[0]))-set(map(tuple,p[1]))
    if i in (4,7):return set(map(tuple,p))
    a,b,x=p;c=list(itertools.product(a,b))
    if i==2:return set(c)-set(map(tuple,x))
    assert len(c)==len(x) and set(x)<=set("01")
    return {pair for pair,bit in zip(c,x) if bit==("0" if i==1 else "1")}
def margins(loss):
    return [len(loss), sorted(Counter(u for u,p in loss).items()),sorted(Counter(p for u,p in loss).items())]
def conflicts(buckets):
    return sum(len(v) for v in buckets.values() if len(set(v))>1)
def effective(c):
    return set(c.execute("SELECT u,p FROM direct UNION SELECT m.u,g.p FROM membership m JOIN grants g USING(g)"))
def finite():
    c=sqlite3.connect(":memory:")
    c.executescript("""PRAGMA foreign_keys=ON;
    CREATE TABLE groups(g INTEGER PRIMARY KEY);
    CREATE TABLE membership(u TEXT,g INTEGER REFERENCES groups(g) ON DELETE CASCADE,PRIMARY KEY(u,g));
    CREATE TABLE grants(g INTEGER REFERENCES groups(g) ON DELETE CASCADE,p TEXT,PRIMARY KEY(g,p));
    CREATE TABLE direct(u TEXT,p TEXT,PRIMARY KEY(u,p));""")
    buckets=defaultdict(list); totals=[[0,0,0] for _ in METHODS]
    for bits in itertools.product((0,1),repeat=12):
        m=[x for x,b in zip(UG,bits[:4]) if b];g=[x for x,b in zip(GP,bits[4:8]) if b];d=[x for x,b in zip(UP,bits[8:]) if b]
        c.execute("DELETE FROM groups");c.execute("DELETE FROM direct")
        c.executemany("INSERT INTO groups VALUES (?)",[(x,) for x in G])
        c.executemany("INSERT INTO membership VALUES (?,?)",m)
        c.executemany("INSERT INTO grants VALUES (?,?)",g)
        c.executemany("INSERT INTO direct VALUES (?,?)",d)
        pre=effective(c);members=sorted(u for u,h in m if h==1);perms=sorted(p for h,p in g if h==1);cand=list(itertools.product(members,perms))
        alt=set(c.execute("SELECT u,p FROM direct UNION SELECT m.u,g.p FROM membership m JOIN grants g USING(g) WHERE m.g<>1"))
        c.execute("DELETE FROM groups WHERE g=1");c.commit();post=effective(c);loss=pre-post
        assert loss==set(cand)-alt
        buckets[enc([members,perms,sorted(pre),margins(loss)])].append(tuple(sorted(loss)))
        payloads=[[m,g,d],[members,perms,"".join("1" if x in alt else "0" for x in cand)],[members,perms,sorted(set(cand)&alt)],[sorted(pre),sorted(post)],sorted(loss),[U,P,"".join("1" if x in loss else "0" for x in UP)],[members,perms,"".join("1" if x in loss else "0" for x in cand)],sorted(set(cand)-alt)]
        for i,p in enumerate(payloads):
            raw=enc([1,i,1,True,p]);z=zlib.compress(raw,9)
            assert decode(zlib.decompress(z))==loss
            if i in (0,1,2,7):assert decode(enc([1,i,1,False,p]))==set()
            totals[i][0]+=1;totals[i][1]+=len(raw);totals[i][2]+=len(z)
    assert conflicts(buckets)==22 and all(t[0]==4096 for t in totals)
    return {"worlds":4096,"ambiguous_with_both_margins":22,"conditional_false_flag_checks":16384,"methods":dict(zip(METHODS,totals))}
def native():
    data=json.loads((D/"group_permission_packets.json").read_text())
    assert len(data)==2 and all(x["native_gate"] for x in data)
    totals=[];n=0
    for rep in data:
        cases=rep["cases"];assert len(cases)==12
        size=[[0,0,0] for _ in METHODS];pre_groups=defaultdict(list);margin_groups=defaultdict(list);states=set()
        for case in cases:
            truth=set(map(tuple,case["truth"]));ps=case["packets"]
            for i,k in enumerate(METHODS[:7]):
                p=ps[k];raw=p["encoded"].encode();z=zlib.compress(raw,9)
                assert decode(zlib.decompress(z))==truth and len(raw)==p["bytes"] and len(z)==p["zlib_bytes"]
                assert set(map(tuple,p["decoded"]))==truth
                size[i][0]+=1;size[i][1]+=len(raw);size[i][2]+=len(z);n+=1
            _,_,target,ok,rel=json.loads(ps[METHODS[0]]["encoded"]);states.add(enc(rel))
            _,_,_,_,(members,perms,bits)=json.loads(ps[METHODS[1]]["encoded"])
            forecast=sorted(decode(ps[METHODS[1]]["encoded"]))
            raw=enc([1,7,target,ok,forecast]);z=zlib.compress(raw,9)
            assert decode(zlib.decompress(z))==truth
            size[7][0]+=1;size[7][1]+=len(raw);size[7][2]+=len(z)
            pre=json.loads(ps[METHODS[3]]["encoded"])[4][0]
            key=[target,members,perms,pre];t=tuple(sorted(truth))
            pre_groups[enc(key)].append(t);margin_groups[enc(key+[margins(truth)])].append(t)
        assert len(states)==9 and conflicts(pre_groups)==11 and conflicts(margin_groups)==2
        assert [x[1:] for x in size]==[[1450,888],[635,646],[906,687],[1518,742],[392,456],[912,828],[635,673],[392,456]]
        totals.append(size)
    assert totals[0]==totals[1]
    assert all(a["packets"]==b["packets"] for a,b in zip(data[0]["cases"],data[1]["cases"]))
    return {"source_packet_checks":n,"additional_predicted_checks":24,"assigned_conditions":12,"unique_grant_states":9,"methods_per_repeat":dict(zip(METHODS,totals[0])),"ambiguous_conditions_pre":11,"ambiguous_conditions_with_margins":2}
def diagnostic():
    data=json.loads((D/"group_trace_diagnostic.json").read_text());assert len(data)==2 and all(x["native_gate"] for x in data)
    core=[p for r in data for p in r["pairs"] if p["kind"] not in ("same_loss_control","visible_count_control")]
    assert len(core)==8 and all(p["same_three_dom"] and p["same_document_records"] and p["same_native_admin_log"] and p["same_pre_effective_all"] and p["lost_pairs_differ"] for p in core)
    a=[p["trace_decomposition"] for p in core]
    assert sum(x["aligned"] for x in a)==208 and sum(x["marker_normalized_aligned_equal"] for x in a)==208
    all_t=[p["trace_decomposition"] for r in data for p in r["pairs"]]
    assert sum(sum(x["unmatched"]) for x in all_t)==2
    assert sum(sum(x["response_body_missing"]) for x in all_t)==864
    assert sum(s["resource_schema"]["response_attachment_read"] for x in all_t for s in x["resource_schema"])==600
    assert all(not any("body" in v["fields_differ"] for v in x["network_projection_differences"].values()) for x in a)
    return {"aligned_core_pairs":208,"matched_after_csrf_normalization":208,"unmatched_snapshots":2,"referenced_bodies_read":600,"network_records_without_body":864}
def user_trace():
    with (D/"user_trace_cases.csv").open(newline="") as f:rows=list(csv.DictReader(f))
    assert len(rows)==48
    fields=[k for k in rows[0] if k.startswith("trace_Q") and k.endswith("_grade")]
    assert len(fields)==4 and all(x[k]=="correct" for x in rows for k in fields)
    assert sum(int(x["trace_DOM_snapshots_decoded"]) for x in rows)==1088
    return {"conditions":48,"correct":len(rows)*len(fields)}
if __name__=="__main__":
    print(json.dumps({"user_trace":user_trace(),"group_trace":diagnostic(),"native_packets":native(),"finite_model":finite()},indent=2))
