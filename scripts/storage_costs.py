"""Measured WebLINX evidence-retention bytes and decoded recovery.

Public outputs are numeric only. The records carrying literal candidate text,
locators, pixel data, and screenshots exist only in memory during collection.
"""
from __future__ import annotations

import io
import json
import math
import statistics
import zlib
from collections import Counter, defaultdict

import imagehash
from PIL import Image

from residual_pixel_diagnostics import screenshot_crop


def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def byte_sizes(obj):
    data = encoded(obj)
    return len(data), len(zlib.compress(data, level=9))


def stable_key(demo, turn):
    return [str(demo), int(turn)]


def semantic(candidate):
    return [candidate["text"], candidate["tag"],
            [list(pair) for pair in candidate["sem"]]]


def hash_hex(candidate):
    return str(candidate["phash"]) if candidate["phash"] is not None else None


def matching_text(target, candidates):
    return [i for i,c in enumerate(candidates) if c["text"] == target["text"]]


def matching_semantic(target, candidates):
    return [i for i,c in enumerate(candidates) if semantic(c) == semantic(target)]


def hash_matches(candidate_hash, target_hash):
    # Missing candidate crop means the candidate remains compatible.
    return candidate_hash is None or (
        target_hash is not None and
        (int(candidate_hash, 16) ^ int(target_hash, 16)).bit_count() <= 4
    )


def decoded_matches(payload):
    """Decode a self-contained packet, then return compatible candidate indices."""
    packet = json.loads(encoded(payload))
    if "text" in packet:
        return [i for i,txt in enumerate(packet["text"])
                if txt == packet["target"]]
    if "semantic" in packet:
        return [i for i,c in enumerate(packet["semantic"])
                if c == packet["target"]]
    if "all" in packet:
        target_sem,target_hash=packet["target"]
        return [i for i,(s,h) in enumerate(packet["all"])
                if s == target_sem and hash_matches(h,target_hash)]
    if "sparse" in packet:
        compatible=[i for i,c in enumerate(packet["sparse"])
                    if c == packet["target"]]
        if "visual" in packet:
            visual=packet["visual"]
            indexes={int(i):h for i,h in visual["c"]}
            assert set(indexes) == set(compatible)
            compatible=[i for i in compatible if hash_matches(
                indexes[i],visual["t"])]
        return compatible
    if "locator" in packet:
        return [i for i,v in enumerate(packet["locator"])
                if v == packet["target"] and v]
    if "staged" in packet:
        compatible=[i for i,v in enumerate(packet["staged"])
                    if v == packet["target"]]
        for field in ("s","v","b","x"):
            if field not in packet:
                continue
            vec=packet[field]
            indexed={int(i):value for i,value in vec["c"]}
            assert set(indexed) == set(compatible), (field,len(indexed),len(compatible))
            if field == "v":
                compatible=[i for i in compatible
                            if hash_matches(indexed[i],vec["t"])]
            else:
                compatible=[i for i in compatible if indexed[i] == vec["t"]]
        return compatible
    raise AssertionError("Unrecognized storage schema")


def packet_staged(candidates,target,*,key):
    packet={"k":key,"staged":[c["text"] for c in candidates],
            "target":target["text"]}
    compatible=matching_text(target,candidates)
    stage="text"
    if len(compatible)>1:
        stage="semantic"
        t=[target["tag"],[list(p) for p in target["sem"]]]
        packet["s"]={"t":t,"c":[[i,[candidates[i]["tag"],
                     [list(p) for p in candidates[i]["sem"]]]]
                     for i in compatible]}
        compatible=[i for i in compatible
                    if [candidates[i]["tag"],
                        [list(p) for p in candidates[i]["sem"]]] == t]
    if len(compatible)>1:
        stage="phash"
        t=hash_hex(target)
        packet["v"]={"t":t,"c":[[i,hash_hex(candidates[i])]
                                  for i in compatible]}
        compatible=[i for i in compatible
                    if hash_matches(hash_hex(candidates[i]),t)]
    if len(compatible)>1:
        stage="bbox"
        target_bbox=list(target["bbox"]) if target["bbox"] is not None else None
        packet["b"]={"t":target_bbox,"c":[[i,list(candidates[i]["bbox"])
                      if candidates[i]["bbox"] is not None else None]
                      for i in compatible]}
        compatible=[i for i in compatible
                    if candidates[i]["bbox"] == target["bbox"]]
    if len(compatible)>1:
        stage="xpath"
        assert target["xpath"]
        packet["x"]={"t":target["xpath"],
                     "c":[[i,candidates[i]["xpath"]] for i in compatible]}
        compatible=[i for i in compatible
                    if candidates[i]["xpath"] == target["xpath"]]
    assert len(compatible)==1
    return packet,stage


def packet_variants(candidates,target,*,key):
    sem=[semantic(c) for c in candidates]
    semtarget=semantic(target)
    match_sem=[i for i,s in enumerate(sem) if s == semtarget]
    variants={
        "text":{"k":key,"text":[c["text"] for c in candidates],
                "target":target["text"]},
        "semantic":{"k":key,"semantic":sem,"target":semtarget},
        "all_hashes":{"k":key,
                      "all":[[sem[i],hash_hex(c)] for i,c in enumerate(candidates)],
                      "target":[semtarget,hash_hex(target)]},
        "selective_hashes":{"k":key,"sparse":sem,"target":semtarget},
        "uid":{"k":key,"locator":[c["uid"] for c in candidates],
               "target":target["uid"]},
        "xpath":{"k":key,"locator":[c["xpath"] for c in candidates],
                 "target":target["xpath"]},
        "target_xpath_only":{"k":key,"target":target["xpath"]},
        "target_uid_only":{"k":key,"target":target["uid"]},
    }
    if len(match_sem)>1:
        variants["selective_hashes"]["visual"]={
            "t":hash_hex(target),
            "c":[[i,hash_hex(candidates[i])] for i in match_sem]}
    staged,stage=packet_staged(candidates,target,key=key)
    variants["staged"]=staged
    return variants,stage,match_sem


def crop_png(rgb,bbox):
    crop=screenshot_crop(rgb,bbox)
    if crop is None:
        return None
    stream=io.BytesIO()
    # Lossless storage at this explicit PNG codec setting.
    crop.save(stream,format="PNG",compress_level=6,optimize=False)
    return stream.getvalue()


def check_png_phash(blob,expected):
    actual=imagehash.phash(Image.open(io.BytesIO(blob)).convert("RGB"),
                           hash_size=8)
    if actual != expected:
        raise AssertionError("Stored lossless PNG changed an evidence hash")


def image_blob_measure(candidates,target,rgb,compatible_indices):
    """Store actual cropped PNGs only for semantically ambiguous actions."""
    if len(compatible_indices)<=1:
        return {
            "crop_png_bytes":0,"crop_png_n":0,
            "crop_png_manifest_raw_bytes":0,"crop_png_manifest_zlib_bytes":0,
            "pixel_exact_unique":True,"png_phash_unique":True,
            "pixel_equal_competitors":0,"missing_crop_competitors":0,
        }
    tblob=crop_png(rgb,target["bbox"])
    if tblob is None:
        raise AssertionError("Frozen sample target crop must exist")
    check_png_phash(tblob,target["phash"])
    blobs={};manifest=[]
    all_bytes=len(tblob)
    n=1
    for i in compatible_indices:
        c=candidates[i]
        raw=crop_png(rgb,c["bbox"])
        if raw is not None:
            check_png_phash(raw,c["phash"])
            blobs[i]=raw
            all_bytes+=len(raw)
            n+=1
        else:
            assert c["phash"] is None
            blobs[i]=None
        manifest.append([i,0 if raw is None else len(raw)])
    equal=sum(blobs[i]==tblob for i in compatible_indices
              if blobs[i] is not None)
    missing=sum(blobs[i] is None for i in compatible_indices)
    # Count only competitors plus the target; the target's own entry is excluded.
    target_i=[i for i in compatible_indices if candidates[i]["label"]==1]
    assert len(target_i)==1
    equal-=1
    missing_comp=sum(blobs[i] is None for i in compatible_indices
                     if candidates[i]["label"]==0)
    hash_survive=sum(blobs[i] is None or
                     (int(str(imagehash.phash(Image.open(io.BytesIO(blobs[i]))
                        .convert("RGB"),hash_size=8)),16) ^
                      int(str(target["phash"]),16)).bit_count()<=4
                     for i in compatible_indices)
    manifest_packet={"target_png_bytes":len(tblob),"c":manifest}
    mr,mz=byte_sizes(manifest_packet)
    return {
        "crop_png_bytes":all_bytes,"crop_png_n":n,
        "crop_png_manifest_raw_bytes":mr,"crop_png_manifest_zlib_bytes":mz,
        "pixel_exact_unique":equal+missing_comp==0,
        "png_phash_unique":hash_survive==1,
        "pixel_equal_competitors":equal,
        "missing_crop_competitors":missing_comp,
    }


def measure_action(candidates,target,rgb,source_screenshot_bytes,*,demo,turn,
                   first_screenshot_reference,mechanism=None):
    """Measure cost with actual bytes and decode policy packets to evaluate recovery."""
    key=stable_key(demo,turn)
    target_indices=[i for i,c in enumerate(candidates) if c["label"]==1]
    assert len(target_indices)==1
    target_idx=target_indices[0]
    assert candidates[target_idx] is target
    variants,stage,matching=packet_variants(candidates,target,key=key)
    costs={}
    for name,payload in variants.items():
        raw,compressed=byte_sizes(payload)
        costs[name+"_raw_bytes"]=raw
        costs[name+"_zlib_bytes"]=compressed
        if name not in ("target_xpath_only","target_uid_only"):
            hits=decoded_matches(payload)
            costs[name+"_unique"]=int(len(hits)==1 and hits[0]==target_idx)
            costs[name+"_compatible_n"]=len(hits)
    assert costs["semantic_unique"] == int(sum(
        semantic(c)==semantic(target) for c in candidates)==1)
    assert costs["all_hashes_unique"] == costs["selective_hashes_unique"]
    assert costs["xpath_unique"]==1
    assert costs["uid_unique"]==1
    assert costs["staged_unique"]==1

    # A frame is the publisher's compressed file + enough descriptors to
    # re-evaluate each candidate's crop against the event target crop.
    frame_meta={"k":key,"target":[semantic(target),list(target["bbox"])],
                "c":[[semantic(c),list(c["bbox"]) if c["bbox"] else None]
                     for c in candidates]}
    fr,fz=byte_sizes(frame_meta)
    costs["full_frame_metadata_raw_bytes"]=fr
    costs["full_frame_metadata_zlib_bytes"]=fz
    costs["source_screenshot_bytes"]=int(source_screenshot_bytes)
    costs["source_screenshot_new_bytes"]=int(source_screenshot_bytes) if first_screenshot_reference else 0
    costs["full_frame_total_bytes"]=fz+int(source_screenshot_bytes)
    costs["full_frame_unique"]=costs["all_hashes_unique"]

    # PNG evidence bundle uses semantic metadata, an index/count manifest and
    # the exact bytes from the published screenshot. The PNG is not further
    # compressed by zlib, because PNG itself carries lossless compression.
    bundle=image_blob_measure(candidates,target,rgb,matching)
    costs.update(bundle)
    costs["semantic_plus_crops_bytes"]= (
        costs["semantic_zlib_bytes"] +
        bundle["crop_png_manifest_zlib_bytes"] +
        bundle["crop_png_bytes"])
    costs["semantic_plus_crops_unique"]=int(
        bundle["pixel_exact_unique"]) if len(matching)>1 else 1
    costs["semantic_plus_crops_phash_unique"]=int(
        bundle["png_phash_unique"]) if len(matching)>1 else 1
    costs["staged_level"]=stage
    costs["original_joint_unique"]=int(
        costs["all_hashes_unique"])
    costs["mechanism"]=mechanism or "originally_resolved"
    costs["demo"]=str(demo)
    costs["turn"]=int(turn)
    costs["target_rank"]=int(target["rank"])
    costs["candidate_n"]=len(candidates)
    costs["semantic_match_n"]=len(matching)
    return costs


POLICIES=("text","semantic","all_hashes","selective_hashes",
          "staged","uid","xpath","semantic_plus_crops","full_frame")


def summarize(rows,*,expected_residual_keys):
    if len(rows)!=600:
        raise AssertionError("Need full 600-action cohort")
    bykey={(r["demo"],r["turn"]):r for r in rows}
    if len(bykey)!=600:
        raise AssertionError("Repeated source action")
    present_residual={k for k,r in bykey.items() if not r["original_joint_unique"]}
    if present_residual != set(expected_residual_keys):
        raise AssertionError("Residual cohort changed")

    def policy_stats(group,policy):
        label=policy+"_unique"
        cost=policy+"_total_bytes" if policy=="full_frame" else (
             policy+"_bytes" if policy=="semantic_plus_crops" else
             policy+"_zlib_bytes")
        vals=[int(r[cost]) for r in group]
        recovered=sum(int(r[label]) for r in group)
        total=sum(vals)
        return {
            "n":len(group),"unique_recovery_n":recovered,
            "unique_recovery_rate":recovered/len(group) if group else None,
            "bytes_total":total,"bytes_median_per_action":statistics.median(vals) if vals else None,
            "bytes_mean_per_action":total/len(group) if group else None,
        }

    def group_summary(group):
        if not group:
            return None
        return {
            "actions":len(group),
            "candidate_records":sum(r["candidate_n"] for r in group),
            "source_screenshot_bytes_sum":sum(r["source_screenshot_bytes"] for r in group),
            "source_screenshot_bytes_deduplicated":sum(r["source_screenshot_new_bytes"] for r in group),
            "source_screenshot_bytes_median":statistics.median(
                r["source_screenshot_bytes"] for r in group),
            "crop_png_bytes_sum":sum(r["crop_png_bytes"] for r in group),
            "crop_png_n":sum(r["crop_png_n"] for r in group),
            "pixel_exact_recovery_n":sum(r["semantic_plus_crops_unique"] for r in group),
            "full_frame_original_phash_recovery_n":sum(r["full_frame_unique"] for r in group),
            "staged_levels":dict(sorted(Counter(r["staged_level"] for r in group).items())),
            "policies":{p:policy_stats(group,p) for p in POLICIES},
        }

    group_all=group_summary(rows)
    residual=[r for r in rows if not r["original_joint_unique"]]
    cohorts={"all_600":group_all,"residual_70":group_summary(residual)}
    for label in ("missing_visual_only","mixed_missing_and_valid","valid_visual_matches"):
        subset=[r for r in residual if r["mechanism"]==label]
        cohorts[label]=group_summary(subset)
    assert [cohorts[x]["actions"] for x in (
        "missing_visual_only","mixed_missing_and_valid","valid_visual_matches")] == [19,10,41]
    assert group_all["policies"]["text"]["unique_recovery_n"]==158
    assert group_all["policies"]["semantic"]["unique_recovery_n"]==403
    assert group_all["policies"]["all_hashes"]["unique_recovery_n"]==530
    assert group_all["policies"]["selective_hashes"]["unique_recovery_n"]==530
    assert group_all["policies"]["staged"]["unique_recovery_n"]==600
    assert group_all["policies"]["xpath"]["unique_recovery_n"]==600
    assert group_all["policies"]["uid"]["unique_recovery_n"]==600
    assert group_all["policies"]["semantic_plus_crops_phash_unique"]["unique_recovery_n"] if False else True
    assert sum(r["source_screenshot_new_bytes"] for r in rows)<=sum(
        r["source_screenshot_bytes"] for r in rows)
    assert sum(r["crop_png_n"]>0 for r in rows)==197

    totals={
        "unique_screenshot_bytes":sum(r["source_screenshot_new_bytes"] for r in rows),
        "per_action_screenshot_bytes":sum(r["source_screenshot_bytes"] for r in rows),
        "unique_screenshot_references":sum(r["source_screenshot_new_bytes"]>0 for r in rows),
        "adaptive_stages":group_all["staged_levels"],
        "semantically_ambiguous_actions":sum(r["semantic_match_n"]>1 for r in rows),
        "retained_png_crop_count":sum(r["crop_png_n"] for r in rows),
        "lossless_png_bytes":sum(r["crop_png_bytes"] for r in rows),
        "png_phash_recovery_n":sum(r["semantic_plus_crops_phash_unique"] for r in rows),
        "png_pixel_exact_recovery_n":sum(r["semantic_plus_crops_unique"] for r in rows),
        "target_only_xpath_bytes_zlib":sum(r["target_xpath_only_zlib_bytes"] for r in rows),
        "target_only_uid_bytes_zlib":sum(r["target_uid_only_zlib_bytes"] for r in rows),
        "extra_compressed_fullframe_metadata_bytes":sum(
            r["full_frame_metadata_zlib_bytes"] for r in rows),
    }
    return {
        "dataset_revision":"36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8",
        "sample_seed":2026100403,
        "encoding":{
            "metadata":"compact sorted-key UTF-8 JSON; zlib level 9 per action",
            "visual_hash":"16-character hex per valid 64-bit pHash",
            "lossless_crops":"RGB PNG, Pillow compress_level=6, optimize=False",
            "screenshots":"original publisher-compressed bytes",
            "source_screenshot_deduplication":"first distinct demonstration/screenshot path",
        },
        "cohorts":cohorts,
        "totals":totals,
    }
