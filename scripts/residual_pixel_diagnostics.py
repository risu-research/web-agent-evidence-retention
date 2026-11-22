"""Compare original RGB crops for competitors passing the pHash evidence criterion."""
from __future__ import annotations

from collections import Counter
from PIL import ImageChops, ImageStat, Image


def screenshot_crop(rgb, bbox):
    if bbox is None:
        return None
    import math
    x,y,w,h=bbox
    left=max(0,int(math.floor(x)))
    top=max(0,int(math.floor(y)))
    right=min(rgb.width,int(math.ceil(x+w)))
    bottom=min(rgb.height,int(math.ceil(y+h)))
    if right-left < 3 or bottom-top < 3:
        return None
    return rgb.crop((left,top,right,bottom)).convert("RGB")


def rgb_equal(a,b):
    return bool(a is not None and b is not None and
                a.size==b.size and a.tobytes()==b.tobytes())


def normalized_rgb_mae(a,b):
    if a is None or b is None:
        return None
    a=a.resize((32,32),resample=Image.Resampling.LANCZOS)
    b=b.resize((32,32),resample=Image.Resampling.LANCZOS)
    stat=ImageStat.Stat(ImageChops.difference(a,b))
    return sum(stat.mean)/3


def compare_residual_pixels(candidates,target,screenshot,*,threshold=4):
    """The caller has established a non-unique compatible target.

    Images are used in memory. Output is numeric only.
    """
    from residual_diagnostics import joint_compatible
    matching=[c for c in candidates if c["label"]==0 and
              joint_compatible(c,target,threshold)]
    valid=[c for c in matching if c["phash"] is not None]
    target_image=screenshot_crop(screenshot,target["bbox"])
    if target_image is None:
        raise AssertionError("Target crop absent despite valid pHash")
    equal=0
    identical_hash_equal_pixels=0
    identical_hash_different_pixels=0
    distinct_bbox_equal_pixels=0
    errs=[]
    for c in valid:
        cimg=screenshot_crop(screenshot,c["bbox"])
        if cimg is None:
            raise AssertionError("A valid pHash competitor lost its crop")
        same=rgb_equal(target_image,cimg)
        dist=int(c["phash"]-target["phash"])
        if same:equal+=1
        if dist==0 and same:identical_hash_equal_pixels+=1
        if dist==0 and not same:identical_hash_different_pixels+=1
        if same and c["bbox"] != target["bbox"]:
            distinct_bbox_equal_pixels+=1
        errs.append(normalized_rgb_mae(target_image,cimg))
    out={
        "pixel_valid_comparisons":len(valid),
        "exact_rgb_equal_competitors":equal,
        "same_phash_same_rgb_competitors":identical_hash_equal_pixels,
        "same_phash_different_rgb_competitors":identical_hash_different_pixels,
        "different_bbox_same_rgb_competitors":distinct_bbox_equal_pixels,
        "minimum_normalized_rgb_mae":round(min(errs),6) if errs else None,
        "median_normalized_rgb_mae":round(sorted(errs)[len(errs)//2],6) if errs else None,
        "maximum_normalized_rgb_mae":round(max(errs),6) if errs else None,
    }
    assert out["same_phash_same_rgb_competitors"] + out["same_phash_different_rgb_competitors"] == sum(
        int(c["phash"]-target["phash"])==0 for c in valid)
    return out


def summarize_pixel_cases(cases):
    if len(cases)!=70:
        raise AssertionError("Expected exactly 70 cases")
    keys=("pixel_valid_comparisons","exact_rgb_equal_competitors",
          "same_phash_same_rgb_competitors","same_phash_different_rgb_competitors",
          "different_bbox_same_rgb_competitors")
    total={k:sum(c[k] for c in cases) for k in keys}
    return {
        "case_n":70,
        "case_counts":{
            "any_exact_rgb_equal":sum(c["exact_rgb_equal_competitors"]>0 for c in cases),
            "any_hash0_but_different_pixels":sum(c["same_phash_different_rgb_competitors"]>0 for c in cases),
            "any_different_bbox_same_pixels":sum(c["different_bbox_same_rgb_competitors"]>0 for c in cases),
            "no_valid_competitor_crop":sum(c["pixel_valid_comparisons"]==0 for c in cases),
        },
        "competitor_counts":total,
        "mechanism_counts":dict(sorted(Counter(c["mechanism"] for c in cases).items())),
    }
