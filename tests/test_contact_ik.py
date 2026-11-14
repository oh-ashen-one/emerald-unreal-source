import unittest
from tools.contact_ik import solve,length,sub,between,rotate
class ContactIKTests(unittest.TestCase):
    def test_reachable_contact_preserves_both_limb_lengths_and_bend_side(self):
        root=(0,0,0);joint=(3,4,0);end=(6,0,0);target=(4,3,2)
        elbow,hand=solve(root,joint,end,target)
        self.assertAlmostEqual(length(sub(elbow,root)),5,places=6)
        self.assertAlmostEqual(length(sub(hand,elbow)),5,places=6)
        self.assertLess(length(sub(hand,target)),1e-6)
        self.assertGreater(elbow[1],0)
    def test_unreachable_contact_clamps_without_stretching(self):
        elbow,hand=solve((0,0,0),(3,4,0),(6,0,0),(100,0,0))
        self.assertAlmostEqual(length(elbow),5,places=5)
        self.assertAlmostEqual(length(sub(hand,elbow)),5,places=5)
        self.assertLess(length(hand),10)
    def test_opposed_quaternion_alignment_is_finite_and_correct(self):
        out=rotate(between((1,0,0),(-1,0,0)),(1,0,0))
        self.assertLess(length(sub(out,(-1,0,0))),1e-6)
