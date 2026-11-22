"""Regression checks for the 70-case residual evidence audit."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from residual_diagnostics import analyze_residual,bbox_iou,joint_compatible,rank_band


class FakeHash:
    def __init__(self,value):
        self.value=value
    def __sub__(self,other):
        return abs(self.value-other.value)


def candidate(uid,phash=0,bbox=(0,0,12,12),label=0,blank=True):
    return {
        "uid":uid, "label":label,"rank":1,"text":"" if blank else "delete",
        "tag":"button", "sem":(),"bbox":bbox,
        "phash":None if phash is None else FakeHash(phash),
        "html_id":"","xpath":"/html/button"
    }


def audit(*competitors):
    target=candidate("target",label=1)
    cases=[target]+list(competitors)
    return analyze_residual(cases,target,demo="demo",turn=10,target_rank=1)


class DiagnosticTests(unittest.TestCase):
    def test_evidence_with_single_target_has_no_residual(self):
        self.assertIsNone(audit())

    def test_missing_visual_only(self):
        x=audit(candidate("other",phash=None))
        self.assertEqual(x["mechanism"],"missing_visual_only")
        self.assertEqual(x["missing_visual_competitor_n"],1)
        self.assertEqual(x["strict_phash_0_joint_match_n"],2)
        self.assertEqual(x["strict_phash_0_resolves"],0)

    def test_valid_equal_hash_with_different_position(self):
        x=audit(candidate("other",phash=0,bbox=(100,100,12,12)))
        self.assertEqual(x["mechanism"],"valid_visual_matches")
        self.assertEqual(x["equal_phash_competitor_n"],1)
        self.assertEqual(x["equal_phash_different_bbox_n"],1)
        self.assertEqual(x["disjoint_bbox_competitor_n"],1)
        self.assertEqual(x["strict_phash_0_joint_match_n"],2)

    def test_near_hash_with_matching_bbox(self):
        x=audit(candidate("other",phash=3))
        self.assertEqual(x["mechanism"],"valid_visual_matches")
        self.assertEqual(x["near_phash_competitor_n"],1)
        self.assertEqual(x["same_bbox_competitor_n"],1)
        self.assertEqual(x["strict_phash_0_joint_match_n"],1)
        self.assertEqual(x["strict_phash_0_resolves"],1)

    def test_mixed(self):
        x=audit(candidate("one",phash=None),candidate("two",phash=3))
        self.assertEqual(x["mechanism"],"mixed_missing_and_valid")
        self.assertEqual(x["joint_match_n"],3)
        self.assertEqual(x["strict_phash_0_joint_match_n"],2)

    def test_nonmatching_text_removed(self):
        target=candidate("target",label=1)
        bad=candidate("bad",phash=None,blank=False)
        self.assertFalse(joint_compatible(bad,target))
        self.assertIsNone(analyze_residual([target,bad],target,demo="x",turn=1,target_rank=1))

    def test_iou_and_rank(self):
        self.assertEqual(bbox_iou((0,0,10,10),(0,0,10,10)),1)
        self.assertEqual(bbox_iou((0,0,10,10),(20,20,10,10)),0)
        self.assertAlmostEqual(bbox_iou((0,0,10,10),(5,0,10,10)),1/3)
        self.assertEqual([rank_band(r) for r in [1,10,11,20,21,50,51,100,101]],
                         ["01-10","01-10","11-20","11-20","21-50",
                          "21-50","51-100","51-100","101+"])


if __name__=="__main__":
    unittest.main()
