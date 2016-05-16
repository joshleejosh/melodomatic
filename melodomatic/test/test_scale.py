import unittest, random
import testhelper
import consts, generators

class ScaleTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr, sid=''):
        player = testhelper.mkplayer(scr)
        sc = player.scales[player.scaleOrder[0]]
        if sid:
            sc = player.scales[sid]
        return player, sc
 
    def test_eq(self):
        p,s = self.bindit(':SCALE TheScale .seed SEEDY .root 59 .intervals 0 1 3 5 6 8 10 .duration 12')
        q,t = self.bindit(':s TheScale .se SEEDY .r 59 .i 0 1 3 5 6 8 10 .d 12')
        self.assertEqual(s, t)
        r,u = self.bindit(':s THESCALE .se SEEDY .p 59 60 62 64 65 67 69 .d 12')
        self.assertNotEqual(s, u)
        self.assertNotEqual(t, u)
        r,u = self.bindit(':s TheScale .se SEEDY .p 59 60 62 64 65 67 69 .d 12')
        self.assertEqual(s, u)
        self.assertEqual(t, u)


