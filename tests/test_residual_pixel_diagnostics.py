"""Tests for exact crop RGB equality and pHash collision separation."""
import sys
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from residual_pixel_diagnostics import screenshot_crop,rgb_equal,normalized_rgb_mae,compare_residual_pixels


class FakeHash:
    def __init__(self,v):self.v=v
    def __sub__(self,other):return abs(self.v-other.v)


def item(uid,label,bbox):
    return {"uid":uid,"label":label,"text":"","tag":"button","sem":(),
            "bbox":bbox,"phash":FakeHash(0)}


class PixelTests(unittest.TestCase):
    def test_distinct_positions_same_pixels(self):
        im=Image.new("RGB",(42,20),"black")
        for x0 in (0,20):
            for x in range(x0,x0+10):
                for y in range(1,11):
                    im.putpixel((x,y),(100,20,180))
        t=item("target",1,(0,1,10,10))
        c=item("competitor",0,(20,1,10,10))
        out=compare_residual_pixels([t,c],t,im)
        self.assertEqual(out["exact_rgb_equal_competitors"],1)
        self.assertEqual(out["different_bbox_same_rgb_competitors"],1)
        self.assertEqual(out["same_phash_different_rgb_competitors"],0)
        self.assertEqual(out["minimum_normalized_rgb_mae"],0.0)

    def test_same_hash_different_pixels(self):
        im=Image.new("RGB",(42,20),"black")
        for x in range(0,10):
            for y in range(0,10):im.putpixel((x,y),(255,255,255))
        for x in range(20,30):
            for y in range(0,10):im.putpixel((x,y),(0,0,0))
        t=item("t",1,(0,0,10,10))
        c=item("c",0,(20,0,10,10))
        out=compare_residual_pixels([t,c],t,im)
        self.assertEqual(out["same_phash_same_rgb_competitors"],0)
        self.assertEqual(out["same_phash_different_rgb_competitors"],1)
        self.assertEqual(out["minimum_normalized_rgb_mae"],255)

    def test_invalid_and_identical_crop(self):
        im=Image.new("RGB",(30,30),"white")
        self.assertIsNone(screenshot_crop(im,(0,0,1,20)))
        a=screenshot_crop(im,(0,0,10,10))
        self.assertTrue(rgb_equal(a,a))
        self.assertEqual(normalized_rgb_mae(a,a),0.0)


if __name__=="__main__":
    unittest.main()
