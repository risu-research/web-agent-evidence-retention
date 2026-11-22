"""Offline checks for measured evidence packets and exact crop bytes."""
import sys
import unittest
from pathlib import Path

import imagehash
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from storage_costs import (
    byte_sizes, decoded_matches, image_blob_measure, measure_action,
    packet_variants, packet_staged,
)


def sample_pixels():
    im=Image.new("RGB",(90,60),"white")
    for x in range(2,22):
        for y in range(2,22):
            im.putpixel((x,y),(200,30,30))
    for x in range(32,52):
        for y in range(2,22):
            im.putpixel((x,y),(20,20,170))
    return im


def item(im, uid, text, bbox, label=0):
    import math
    if bbox[2]<=2 or bbox[3]<=2:
        h=None
    else:
        x,y,w,hh=bbox
        h=imagehash.phash(im.crop((math.floor(x),math.floor(y),
                                   math.ceil(x+w),math.ceil(y+hh))).convert("RGB"),
                           hash_size=8)
    return {
        "uid":uid,"xpath":"/html/body/"+uid,"html_id":uid,
        "label":label,"rank":1,"text":text,"tag":"button","sem":(),
        "bbox":bbox,"phash":h,
    }


class CostTests(unittest.TestCase):
    def test_unique_text_is_first_stage(self):
        im=sample_pixels()
        target=item(im,"a","save",(2,2,20,20),1)
        other=item(im,"b","delete",(32,2,20,20))
        candidates=[target,other]
        variants,stage,sem=packet_variants(candidates,target,key=["demo",2])
        self.assertEqual(stage,"text")
        self.assertEqual(len(sem),1)
        for name in ("text","semantic","all_hashes","selective_hashes","staged","uid","xpath"):
            self.assertEqual(decoded_matches(variants[name]),[0])
            a,b=byte_sizes(variants[name])
            self.assertGreater(a,0)
            self.assertGreater(b,0)
        result=measure_action(candidates,target,im,1800,demo="demo",turn=2,
                              first_screenshot_reference=True)
        self.assertEqual(result["crop_png_n"],0)
        self.assertEqual(result["semantic_plus_crops_unique"],1)
        self.assertEqual(result["source_screenshot_new_bytes"],1800)

    def test_bbox_tier_after_joint_collision(self):
        im=sample_pixels()
        target=item(im,"a","save",(2,2,20,20),1)
        other=item(im,"b","save",(32,2,20,20))
        candidates=[target,other]
        variants,stage,_=packet_variants(candidates,target,key=["d",3])
        # Crops of constant color have identical pHash despite different RGB.
        self.assertEqual(stage,"bbox")
        self.assertEqual(decoded_matches(variants["staged"]),[0])
        self.assertEqual(decoded_matches(variants["xpath"]),[0])
        assert len(decoded_matches(variants["selective_hashes"]))==2
        result=measure_action(candidates,target,im,1800,demo="d",turn=3,
                              first_screenshot_reference=False)
        self.assertEqual(result["staged_level"],"bbox")
        self.assertEqual(result["staged_unique"],1)
        self.assertEqual(result["source_screenshot_new_bytes"],0)
        self.assertEqual(result["semantic_plus_crops_unique"],1)
        self.assertEqual(result["crop_png_n"],3)

    def test_xpath_fallback_with_same_box(self):
        im=sample_pixels()
        target=item(im,"a","save",(2,2,20,20),1)
        other=item(im,"b","save",(2,2,20,20))
        variants,stage,_=packet_variants([target,other],target,key=["d",4])
        self.assertEqual(stage,"xpath")
        self.assertEqual(decoded_matches(variants["staged"]),[0])
        self.assertEqual(decoded_matches(variants["all_hashes"]),[0,1])
        result=measure_action([target,other],target,im,1800,demo="d",turn=4,
                              first_screenshot_reference=False)
        self.assertEqual(result["semantic_plus_crops_unique"],0)
        self.assertEqual(result["crop_png_n"],3)

    def test_missing_crop_is_compatible(self):
        im=sample_pixels()
        target=item(im,"a","save",(2,2,20,20),1)
        missing=item(im,"b","save",(32,2,1,20))
        variants,stage,_=packet_variants([target,missing],target,key=["d",5])
        self.assertEqual(len(decoded_matches(variants["selective_hashes"])),2)
        self.assertEqual(stage,"bbox")
        result=measure_action([target,missing],target,im,1800,demo="d",turn=5,
                              first_screenshot_reference=False)
        self.assertEqual(result["missing_crop_competitors"],1)
        self.assertEqual(result["semantic_plus_crops_unique"],0)
        self.assertEqual(result["crop_png_n"],2)


if __name__=="__main__":
    unittest.main()
