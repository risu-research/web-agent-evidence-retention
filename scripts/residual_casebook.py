import io,json,math,random,re,statistics,time
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image
import imagehash
from residual_diagnostics import analyze_residual, summary_of_cases
from huggingface_hub import HfApi,hf_hub_download
import weblinx as wl

SEED=2026100403
TARGET=600
OVERSAMPLE=750
MAX_PER_DEMO=14
PHASH_T=4
PHASH_TS=(0,4,8,12)
WORKERS=6
KS=(10,20,50)
RAW=Path("wl_confirm"); OUT=Path("out_confirm"); OUT.mkdir(exist_ok=True)
WS=re.compile(r"\s+")
FIELD=re.compile(r"\[\[([a-zA-Z_]+)\]\]\s*(.*?)(?=(?:\[\[[a-zA-Z_]+\]\])|\Z)",re.S)
KV=re.compile(r"""([:\w-]+)\s*=\s*(['"])(.*?)\2""",re.S)
NUM=re.compile(r"""(x|y|width|height)\s*=\s*(-?\d+(?:\.\d+)?)""")

def norm(x,lim=240): return WS.sub(" ",str(x or "")).strip().lower()[:lim]
def parse_bbox(s):
    d={k:float(v) for k,v in NUM.findall(str(s or ""))}
    if all(k in d for k in ("x","y","width","height")) and d["width"]>2 and d["height"]>2:
        return (d["x"],d["y"],d["width"],d["height"])
    return None
def parse_doc(doc,uid):
    f={}
    for fm in FIELD.finditer(str(doc or "")): f[fm.group(1).lower()]=norm(fm.group(2),2000)
    attrs={k.lower():norm(v,160) for k,_,v in KV.findall(f.get("attributes",""))}
    sem=tuple((k,attrs.get(k,"")) for k in ("role","type","name","aria-label","title","placeholder","alt","href","value") if attrs.get(k))
    return {"uid":str(uid),"tag":norm(f.get("tag",""),40),"text":norm(f.get("text",""),240),"sem":sem,"bbox":parse_bbox(f.get("bbox",""))}

def locator_fields(doc):
    """Extract recorded locator fields without using the target label or a raw DOM lookup."""
    fields = {m.group(1).lower(): m.group(2).strip()
              for m in FIELD.finditer(str(doc or ""))}
    attrs = {k.lower(): v.strip()
             for k, _, v in KV.findall(fields.get("attributes", ""))}
    return {
        "xpath": fields.get("xpath", "").strip(),
        "html_id": attrs.get("id", "").strip(),
        "webtasks_id": attrs.get("data-webtasks-id", "").strip(),
    }


def is_joint_compatible(candidate, target):
    return (candidate["text"] == target["text"]
            and (candidate["tag"], candidate["sem"]) == (target["tag"], target["sem"])
            and (candidate["phash"] is None or
                 candidate["phash"] - target["phash"] <= PHASH_T))


def measure_identifier_action(candidates, target):
    out = {
        "xpath_available": int(bool(target["xpath"])),
        "html_id_available": int(bool(target["html_id"])),
        "webtasks_id_available": int(bool(target["webtasks_id"])),
        "webtasks_id_equals_uid": int(bool(target["webtasks_id"]) and
                                       target["webtasks_id"] == target["uid"]),
        "missing_candidate_xpath": sum(not c["xpath"] for c in candidates),
        "missing_candidate_html_id": sum(not c["html_id"] for c in candidates),
    }
    for k in (10, 20, 50, "all"):
        key = str(k)
        subset = candidates if k == "all" else [c for c in candidates if c["rank"] <= k]
        compatible = [c for c in subset if is_joint_compatible(c, target)]
        out[key + "_present"] = int(any(c["label"] == 1 for c in subset))
        out[key + "_joint_n"] = len(compatible)
        out[key + "_uid_n"] = sum(c["uid"] == target["uid"] for c in subset)
        for field in ("xpath", "html_id", "webtasks_id"):
            out[key + "_" + field + "_n"] = (
                sum(c[field] == target[field] for c in subset)
                if target[field] else None
            )
            out[key + "_joint_" + field + "_n"] = (
                sum(c[field] == target[field] for c in compatible)
                if target[field] else len(compatible)
            )
        out[key + "_joint_both_n"] = sum(
            (not target["xpath"] or c["xpath"] == target["xpath"]) and
            (not target["html_id"] or c["html_id"] == target["html_id"])
            for c in compatible
        )
    return out

def raw_get(repo_path,sha,optional=False):
    dest=RAW/repo_path
    if dest.exists() and dest.stat().st_size>0:return dest
    dest.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://huggingface.co/datasets/McGill-NLP/WebLINX-full/resolve/{sha}/{quote(repo_path,safe='/')}?download=true"
    last=None
    for a in range(8):
        try:
            r=requests.get(url,stream=True,timeout=(25,180))
            if r.status_code==404 and optional:return None
            if r.status_code==429:time.sleep(min(45,2*(a+1)**2));continue
            r.raise_for_status(); tmp=dest.with_suffix(dest.suffix+".part")
            with open(tmp,"wb") as h:
                for chunk in r.iter_content(1024*1024):
                    if chunk:h.write(chunk)
            tmp.replace(dest);return dest
        except Exception as e:last=e;time.sleep(min(30,2**a))
    if optional:return None
    raise RuntimeError(f"fetch failed {repo_path}: {last}")
def crop_hash(im,b):
    if b is None:return None
    x,y,w,h=b;L=max(0,int(math.floor(x)));T=max(0,int(math.floor(y)))
    R=min(im.width,int(math.ceil(x+w)));B=min(im.height,int(math.ceil(y+h)))
    if R-L<3 or B-T<3:return None
    return imagehash.phash(im.crop((L,T,R,B)).convert("RGB"),hash_size=8)
def rate(rs,p): return sum(1 for r in rs if p(r))/len(rs) if rs else float("nan")
def metric(rs,key):
    vs=[r[key] for r in rs]
    return {"n":len(vs),"unique_rate":sum(v==1 for v in vs)/len(vs),"collision_rate":sum(v>1 for v in vs)/len(vs),
            "median":statistics.median(vs),"p90":sorted(vs)[max(0,math.ceil(.9*len(vs))-1)]}
def bootstrap(rows,reps=5000):
    by=defaultdict(list)
    for r in rows:by[r["demo"]].append(r)
    demos=sorted(by);rng=random.Random(2026100404); vals=defaultdict(list)
    for _ in range(reps):
        rs=[r for __ in demos for r in by[rng.choice(demos)]]
        b=[r for r in rs if r["blank"]]; n=[r for r in rs if not r["blank"]]
        q={"text_unique":rate(rs,lambda r:r["text_n"]==1),
           "visual_unique":rate(rs,lambda r:r["visual_n"]==1),
           "joint_unique":rate(rs,lambda r:r["joint_n"]==1),
           "semantic_unique":rate(rs,lambda r:r["textdom_n"]==1),
           "visual_escalation":rate(rs,lambda r:r["textdom_n"]>1),
           "blank_text_unique":rate(b,lambda r:r["text_n"]==1),
           "nonblank_text_unique":rate(n,lambda r:r["text_n"]==1),
           "blank_visual_unique":rate(b,lambda r:r["visual_n"]==1),
           "nonblank_visual_unique":rate(n,lambda r:r["visual_n"]==1),
           "blank_joint_unique":rate(b,lambda r:r["joint_n"]==1),
           "nonblank_joint_unique":rate(n,lambda r:r["joint_n"]==1)}
        q["text_inversion_gap"]=q["nonblank_text_unique"]-q["blank_text_unique"]
        for k,v in q.items():
            if not math.isnan(v):vals[k].append(v)
    b=[r for r in rows if r["blank"]];n=[r for r in rows if not r["blank"]]
    point={"text_unique":rate(rows,lambda r:r["text_n"]==1),"visual_unique":rate(rows,lambda r:r["visual_n"]==1),
           "joint_unique":rate(rows,lambda r:r["joint_n"]==1),"semantic_unique":rate(rows,lambda r:r["textdom_n"]==1),
           "visual_escalation":rate(rows,lambda r:r["textdom_n"]>1),
           "blank_text_unique":rate(b,lambda r:r["text_n"]==1),"nonblank_text_unique":rate(n,lambda r:r["text_n"]==1),
           "blank_visual_unique":rate(b,lambda r:r["visual_n"]==1),"nonblank_visual_unique":rate(n,lambda r:r["visual_n"]==1),
           "blank_joint_unique":rate(b,lambda r:r["joint_n"]==1),"nonblank_joint_unique":rate(n,lambda r:r["joint_n"]==1)}
    point["text_inversion_gap"]=point["nonblank_text_unique"]-point["blank_text_unique"]
    out={}
    for k,v in point.items():
        a=sorted(vals[k]);out[k]={"estimate":v,"ci95":[a[math.floor(.025*(len(a)-1))],a[math.ceil(.975*(len(a)-1))]]}
    return {"unit":"demo","reps":reps,"demo_n":len(demos),"metrics":out}

raw_sha="36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8"
cand_path=hf_hub_download("McGill-NLP/WebLINX-full","candidates/test_iid.jsonl",repo_type="dataset",revision=raw_sha)

# Pass 1: official target-turn population, with no top-K conditioning.
# Freeze only groups with exactly one positive target; ambiguous/multi-positive groups
# are excluded before sampling rather than becoming post-hoc compute skips.
target_lists=defaultdict(list);group_sizes=Counter()
with open(cand_path,encoding="utf-8") as h:
    for line in h:
        z=json.loads(line);key=(str(z["demo_name"]),int(z["turn_index"]));group_sizes[key]+=1
        if int(z.get("label",0))==1:
            target_lists[key].append({"demo":key[0],"turn":key[1],"uid":str(z["uid"]),"rank":int(z["rank"])})
targets=[vs[0] for key,vs in target_lists.items() if len(vs)==1]
ambiguous_target_groups=sum(len(vs)!=1 for vs in target_lists.values())

by=defaultdict(list)
for r in targets:by[r["demo"]].append(r)
rng=random.Random(SEED); demos=sorted(by);rng.shuffle(demos);chosen=[]
for d in demos:
    g=by[d][:];rng.shuffle(g);chosen.extend(g[:MAX_PER_DEMO])
    if len(chosen)>=OVERSAMPLE:break
chosen=chosen[:OVERSAMPLE];chosen_keys={(r["demo"],r["turn"]) for r in chosen}

# Pass 2: collect only selected official records, dropping repeated query text.
records=defaultdict(list)
with open(cand_path,encoding="utf-8") as h:
    for line in h:
        z=json.loads(line);key=(str(z["demo_name"]),int(z["turn_index"]))
        if key in chosen_keys:
            records[key].append({"uid":str(z["uid"]),"doc":z["doc"],"rank":int(z["rank"]),"label":int(z.get("label",0))})

# Map replay turns to frozen screenshots.
for d in sorted({r["demo"] for r in chosen}):
    raw_get(f"demonstrations/{d}/replay.json",raw_sha)
    raw_get(f"demonstrations/{d}/metadata.json",raw_sha,optional=True)
    raw_get(f"demonstrations/{d}/form.json",raw_sha,optional=True)
replays={}
for d in sorted({r["demo"] for r in chosen}):
    replays[d]=wl.Replay.from_demonstration(wl.Demonstration(d,base_dir=RAW/"demonstrations"))
mapped=[];map_skips=Counter()
for r in chosen:
    try:
        turn=replays[r["demo"]][r["turn"]]
        if not turn.has_screenshot():replays[r["demo"]].assign_screenshot_to_turn(turn)
        ss=(turn.get("state") or {}).get("screenshot")
        if ss:mapped.append({**r,"screenshot":ss})
        else:map_skips["no_screenshot"]+=1
    except Exception as e:map_skips[type(e).__name__]+=1
sample=mapped[:TARGET]
paths=sorted(set(f'demonstrations/{r["demo"]}/screenshots/{r["screenshot"]}' for r in sample))
fail=Counter()
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    fut={ex.submit(raw_get,p,raw_sha):p for p in paths}
    for f in as_completed(fut):
        try:f.result()
        except Exception as e:fail[type(e).__name__]+=1

rows=[];skips=Counter();case_rows=[]
for i,r in enumerate(sample,1):
    key=(r["demo"],r["turn"]);recs=records[key]
    sp=RAW/f'demonstrations/{r["demo"]}/screenshots/{r["screenshot"]}'
    if not sp.exists():skips["missing_screen"]+=1;continue
    try:
        with Image.open(sp) as im:
            im=im.convert("RGB"); cs=[]
            for z in recs:
                c=parse_doc(z["doc"],z["uid"]);c.update(locator_fields(z["doc"]));c["rank"]=z["rank"];c["label"]=z["label"];c["phash"]=crop_hash(im,c["bbox"]);cs.append(c)
    except Exception as e:skips["image_"+type(e).__name__]+=1;continue
    ts=[c for c in cs if c["label"]==1]
    if len(ts)!=1:skips["target_count"]+=1;continue
    t=ts[0]
    if t["phash"] is None:skips["target_no_hash"]+=1;continue
    row={"demo":r["demo"],"turn":r["turn"],"target_rank":r["rank"],"candidate_n":len(cs),"blank":int(t["text"]=="")}
    row["text_n"]=sum(c["text"]==t["text"] for c in cs)
    row["dom_n"]=sum((c["tag"],c["sem"])==(t["tag"],t["sem"]) for c in cs)
    row["textdom_n"]=sum(c["text"]==t["text"] and (c["tag"],c["sem"])==(t["tag"],t["sem"]) for c in cs)
    row["visual_n"]=sum(c["phash"] is None or (c["phash"]-t["phash"])<=PHASH_T for c in cs)
    row["joint_n"]=sum(c["text"]==t["text"] and (c["tag"],c["sem"])==(t["tag"],t["sem"]) and (c["phash"] is None or (c["phash"]-t["phash"])<=PHASH_T) for c in cs)
    row["candidate_visual_valid_n"]=sum(c["phash"] is not None for c in cs)
    row["textdom_missing_visual_n"]=sum(c["text"]==t["text"] and (c["tag"],c["sem"])==(t["tag"],t["sem"]) and c["phash"] is None for c in cs)
    for pt in PHASH_TS:
        row[f"visual_t{pt}_n"]=sum(c["phash"] is None or (c["phash"]-t["phash"])<=pt for c in cs)
        row[f"joint_t{pt}_n"]=sum(c["text"]==t["text"] and (c["tag"],c["sem"])==(t["tag"],t["sem"]) and (c["phash"] is None or (c["phash"]-t["phash"])<=pt) for c in cs)
    for k in KS:
        sub=[c for c in cs if c["rank"]<=k]
        present=r["rank"]<=k
        row[f"k{k}_present"]=int(present)
        if present:
            row[f"k{k}_joint_n"]=sum(c["text"]==t["text"] and (c["tag"],c["sem"])==(t["tag"],t["sem"]) and (c["phash"] is None or (c["phash"]-t["phash"])<=PHASH_T) for c in sub)
    row.update(measure_identifier_action(cs,t))
    audit=analyze_residual(cs,t,demo=r["demo"],turn=r["turn"],target_rank=r["rank"])
    if audit is not None:
        assert audit["joint_match_n"] == row["joint_n"]
        assert audit["semantic_match_n"] == row["textdom_n"]
        case_rows.append(audit)
    rows.append(row)
    if i%100==0:print("CONFIRM_PROCESSED",i)

blank=[r for r in rows if r["blank"]];nonblank=[r for r in rows if not r["blank"]]
sizes=[r["candidate_n"] for r in rows]
rankpop=[r["rank"] for r in targets]
def bootstrap_phash(rows,reps=5000):
    by=defaultdict(list)
    for r in rows: by[r["demo"]].append(r)
    demos=sorted(by); rng=random.Random(2026100405)
    vals={str(pt):{"visual":[],"joint":[]} for pt in PHASH_TS}
    for _ in range(reps):
        rs=[r for __ in demos for r in by[rng.choice(demos)]]
        for pt in PHASH_TS:
            vals[str(pt)]["visual"].append(rate(rs,lambda r,pt=pt:r[f"visual_t{pt}_n"]==1))
            vals[str(pt)]["joint"].append(rate(rs,lambda r,pt=pt:r[f"joint_t{pt}_n"]==1))
    out={}
    for pt in PHASH_TS:
        p=str(pt); out[p]={}
        for name in ("visual","joint"):
            a=sorted(vals[p][name])
            est=rate(rows,lambda r,pt=pt,name=name:r[f"{name}_t{pt}_n"]==1)
            out[p][name]={"estimate":est,"ci95":[a[math.floor(.025*(len(a)-1))],a[math.ceil(.975*(len(a)-1))]]}
    return {"unit":"demo","reps":reps,"demo_n":len(demos),"metrics":out}

phash_sensitivity={}
for pt in PHASH_TS:
    phash_sensitivity[str(pt)]={
      "overall":{
        "visual":metric(rows,f"visual_t{pt}_n"),
        "joint":metric(rows,f"joint_t{pt}_n")},
      "blank":{
        "visual":metric(blank,f"visual_t{pt}_n"),
        "joint":metric(blank,f"joint_t{pt}_n")},
      "nonblank":{
        "visual":metric(nonblank,f"visual_t{pt}_n"),
        "joint":metric(nonblank,f"joint_t{pt}_n")}
    }
phash_bootstrap=bootstrap_phash(rows)

summary={
 "raw_sha":raw_sha,
 "population":{"target_turns":len(targets),"ambiguous_target_groups_excluded":ambiguous_target_groups,"demo_n":len(by),
   "target_rank_coverage":{str(k):sum(x<=k for x in rankpop)/len(rankpop) for k in KS}},
 "sampling":{"oversampled":len(chosen),"mapped":len(mapped),"requested":TARGET,"analyzed":len(rows),
   "demo_n":len(set(r["demo"] for r in rows)),"map_skips":dict(map_skips),"compute_skips":dict(skips),"fetch_failures":dict(fail),
   "sample_target_rank_coverage":{str(k):sum(r["target_rank"]<=k for r in rows)/len(rows) for k in KS}},
 "candidate_universe":{"median":statistics.median(sizes),"p90":sorted(sizes)[max(0,math.ceil(.9*len(sizes))-1)],"min":min(sizes),"max":max(sizes)},
 "all_universe":{"text":metric(rows,"text_n"),"dom":metric(rows,"dom_n"),"textdom":metric(rows,"textdom_n"),"visual":metric(rows,"visual_n"),"joint":metric(rows,"joint_n"),
   "visual_escalation_rate":rate(rows,lambda r:r["textdom_n"]>1)},
 "protocol_audit":{
   "candidate_total":sum(r["candidate_n"] for r in rows),
   "candidate_visual_valid_total":sum(r["candidate_visual_valid_n"] for r in rows),
   "candidate_visual_valid_rate":sum(r["candidate_visual_valid_n"] for r in rows)/sum(r["candidate_n"] for r in rows),
   "actions_with_any_missing_candidate_visual":sum(r["candidate_visual_valid_n"]<r["candidate_n"] for r in rows),
   "actions_with_semantic_match_missing_visual":sum(r["textdom_missing_visual_n"]>0 for r in rows)
 },
 "strata":{
   "blank":{"n":len(blank),"text":metric(blank,"text_n"),"visual":metric(blank,"visual_n"),"joint":metric(blank,"joint_n"),"textdom":metric(blank,"textdom_n")},
   "nonblank":{"n":len(nonblank),"text":metric(nonblank,"text_n"),"visual":metric(nonblank,"visual_n"),"joint":metric(nonblank,"joint_n"),"textdom":metric(nonblank,"textdom_n")}},
 "bootstrap":bootstrap(rows),
 "phash_threshold":PHASH_T,
 "phash_sensitivity":phash_sensitivity,
 "phash_sensitivity_bootstrap":phash_bootstrap,
 "topk_unconditional":{str(k):{
    "target_present_rate":rate(rows,lambda r,k=k:r["target_rank"]<=k),
    "joint_unique_over_all_actions":sum((r["target_rank"]<=k and r.get(f"k{k}_joint_n")==1) for r in rows)/len(rows),
    "joint_unique_conditional_present":rate([r for r in rows if r["target_rank"]<=k],lambda r,k=k:r.get(f"k{k}_joint_n")==1)
 } for k in KS}
}
def jd(o):
    if hasattr(o,"item"):return o.item()
    raise TypeError(type(o).__name__)
(OUT/"confirm_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True,default=jd))
print("CONFIRM_SUMMARY",json.dumps(summary,sort_keys=True,default=jd))


# The original confirmatory summary above is retained unchanged. Identifier baselines
# use only the locator fields present in the published ranked candidate records.
import csv

ID_OUT = Path("out_identifier")
ID_OUT.mkdir(exist_ok=True)
BASELINES = (
    "joint", "uid", "xpath", "html_id", "webtasks_id",
    "joint_xpath", "joint_html_id", "joint_webtasks_id", "joint_both",
)

def recovered(r, key, baseline):
    count = r[key + "_" + baseline + "_n"]
    return bool(r[key + "_present"] and count == 1)

def identifier_bootstrap(rows, reps=5000):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["demo"]].append(row)
    demos = sorted(grouped)
    rng = random.Random(2026112207)
    names = (
        "all_joint", "all_uid", "all_xpath", "all_html_id",
        "all_joint_xpath", "all_joint_html_id", "all_joint_both",
        "10_joint", "10_uid", "10_joint_xpath", "10_joint_html_id", "10_joint_both"
    )
    values = {name: [] for name in names}
    for _ in range(reps):
        sample_rows = [r for _ in demos for r in grouped[rng.choice(demos)]]
        for name in names:
            key, baseline = name.split("_", 1)
            values[name].append(sum(recovered(r,key,baseline) for r in sample_rows)
                                / len(sample_rows))
    out = {}
    for name in names:
        vs = sorted(values[name])
        key,baseline = name.split("_",1)
        out[name] = {
            "estimate":sum(recovered(r,key,baseline) for r in rows)/len(rows),
            "ci95":[vs[math.floor(.025*(reps-1))],vs[math.ceil(.975*(reps-1))]]
        }
    for label, new_name, old_name in (
        ("gain_joint_xpath", "all_joint_xpath", "all_joint"),
        ("gain_joint_html_id", "all_joint_html_id", "all_joint"),
        ("gain_joint_both", "all_joint_both", "all_joint"),
    ):
        vs = sorted(a-b for a,b in zip(values[new_name], values[old_name]))
        out[label] = {
            "estimate":out[new_name]["estimate"] - out[old_name]["estimate"],
            "ci95":[vs[math.floor(.025*(reps-1))],vs[math.ceil(.975*(reps-1))]]
        }
    return {"unit":"demonstration","reps":reps,"demo_n":len(demos),"metrics":out}

baseline_summary = {}
for k in ("10", "20", "50", "all"):
    subset = [r for r in rows if r[k+"_present"]]
    baseline_summary[k] = {
        "n":len(rows),
        "target_present_count":len(subset),
        "coverage":len(subset)/len(rows),
        "baselines":{}
    }
    for name in BASELINES:
        availability = {
            "xpath":"xpath_available",
            "html_id":"html_id_available",
            "webtasks_id":"webtasks_id_available",
        }.get(name)
        eligible = ([r for r in subset if r[availability]] if availability
                    else subset)
        successes = sum(recovered(r,k,name) for r in rows)
        baseline_summary[k]["baselines"][name] = {
            "recovered":successes,
            "end_to_end_rate":successes/len(rows),
            "conditional_on_target_presence":successes/len(subset) if subset else None,
            "eligible_targets":len(eligible),
            "conditional_on_available_and_present":successes/len(eligible) if eligible else None,
            "remaining_collisions_on_present_and_available":
                sum(r[k+"_"+name+"_n"] > 1 for r in eligible),
        }

def count_where(predicate):
    return sum(bool(predicate(r)) for r in rows)

cohort_summary = {
    "target_xpath_available": count_where(lambda r: r["xpath_available"]),
    "target_html_id_available": count_where(lambda r: r["html_id_available"]),
    "target_webtasks_id_available": count_where(lambda r: r["webtasks_id_available"]),
    "target_webtasks_id_equals_uid": count_where(lambda r: r["webtasks_id_equals_uid"]),
    "joint_residual": count_where(lambda r: r["all_joint_n"] > 1),
    "joint_residual_resolved_xpath": count_where(
        lambda r: r["all_joint_n"] > 1 and r["all_joint_xpath_n"] == 1),
    "joint_residual_resolved_html_id": count_where(
        lambda r: r["all_joint_n"] > 1 and r["all_joint_html_id_n"] == 1),
    "joint_residual_resolved_both": count_where(
        lambda r: r["all_joint_n"] > 1 and r["all_joint_both_n"] == 1),
    "missing_candidate_xpath_total":sum(r["missing_candidate_xpath"] for r in rows),
    "missing_candidate_html_id_total":sum(r["missing_candidate_html_id"] for r in rows),
}
metrics = {
    "protocol":"frozen-confirmatory-sample-2026100403",
    "raw_sha":raw_sha,
    "cohort_n":len(rows),
    "demo_n":len(set(r["demo"] for r in rows)),
    "candidate_population":"released DMR candidate records",
    "field_provenance":{
        "uid":"official DMR record uid (dataset-ground-truth equality oracle)",
        "xpath":"literal [[xpath]] string in the released candidate doc",
        "html_id":"literal id attribute in released candidate doc, excluding data-webtasks-id",
        "webtasks_id":"recorded data-webtasks-id, dataset instrumented locator",
    },
    "cohort":cohort_summary,
    "by_candidate_budget":baseline_summary,
    "cluster_bootstrap":identifier_bootstrap(rows),
}
assert len(rows) == 600 and cohort_summary["joint_residual"] == 70
assert baseline_summary["all"]["baselines"]["joint"]["recovered"] == 530
assert baseline_summary["10"]["baselines"]["joint"]["recovered"] == 415
assert baseline_summary["all"]["baselines"]["uid"]["recovered"] == 600

with (ID_OUT/"identifier_action_metrics.csv").open("w",newline="",encoding="utf-8") as out:
    columns=["demo","turn","target_rank","candidate_n","blank","text_n","textdom_n","joint_n"]
    columns += ["xpath_available","html_id_available","webtasks_id_available",
                "webtasks_id_equals_uid","missing_candidate_xpath","missing_candidate_html_id"]
    for k in ("10","20","50","all"):
        columns.extend([k+"_"+field for field in (
            "present","joint_n","uid_n","xpath_n","html_id_n","webtasks_id_n",
            "joint_xpath_n","joint_html_id_n","joint_webtasks_id_n","joint_both_n")])
    writer=csv.DictWriter(out,fieldnames=columns,extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
(ID_OUT/"identifier_summary.json").write_text(json.dumps(metrics,indent=2,sort_keys=True))
print("IDENTIFIER_SUMMARY",json.dumps(metrics,sort_keys=True))


# Residual collision audit. The confirmatory and identifier summaries above are
# regenerated byte for byte from their original frozen implementations.
RES_OUT=Path("out_residual")
RES_OUT.mkdir(exist_ok=True)
assert len(case_rows)==70
summary70=summary_of_cases(case_rows,rows)
summary70["protocol"]="frozen-confirmatory-2026100403-residual-20261122"
summary70["dataset_sha"]=raw_sha
summary70["comparison"]={
    "confirmatory_total":len(rows),
    "original_joint_success":sum(r["joint_n"]==1 for r in rows),
    "residual_count":sum(r["joint_n"]>1 for r in rows),
    "identifier_xpath_success":sum(r["all_xpath_n"]==1 for r in rows),
}
assert summary70["comparison"] == {
    "confirmatory_total":600,"original_joint_success":530,
    "residual_count":70,"identifier_xpath_success":600,
}
with (RES_OUT/"residual_70_cases.csv").open("w",newline="",encoding="utf-8") as fh:
    writer=csv.DictWriter(fh,fieldnames=list(case_rows[0]))
    writer.writeheader()
    writer.writerows(case_rows)
(RES_OUT/"residual_summary.json").write_text(
    json.dumps(summary70,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print("RESIDUAL_SUMMARY",json.dumps(summary70,sort_keys=True))
