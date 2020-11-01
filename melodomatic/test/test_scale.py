import unittest, random
from . import testhelper
from .. import consts, generators

class ScaleTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr):
        player = testhelper.mkplayer(scr)
        sc = player.scales[player.scaleOrder[0]]
        return player, sc
 
    def test_eq(self):
        # two separate instances with equivalent state are equal.
        # parent player doesn't count for equality. That's kind of the point!
        p,s = self.bindit(':SCALE TheScale .seed SEEDY .root 59 .intervals 0 1 3 5 6 8 10 .move_time 12')
        q,t = self.bindit(':s TheScale .se SEEDY .r 59 .i 0 1 3 5 6 8 10 .mt 12')
        self.assertEqual(s, t)
        # ID is case sensitive
        r,u = self.bindit(':s THESCALE .se SEEDY .p 59 60 62 64 65 67 69 .mt 12')
        self.assertNotEqual(s, u)
        self.assertNotEqual(t, u)
        # specifying pitch instead of root+intervals can still be equal
        r,u = self.bindit(':s TheScale .se SEEDY .p 59 60 62 64 65 67 69 .mt 12')
        self.assertEqual(s, u)
        self.assertEqual(t, u)

    def test_bad(self):
        p,s = self.bindit(':s')
        self.assertEqual(s.id, 'DUMMY')

    def test_link(self):
        p,s = self.bindit("""
        :sc S .se seedx .root 59 .intervals 0 1 3 5 6 8 10 .move_time 4 .move_link T
        :sc T .se seedy .root 64 .intervals 0 1 3 5 7 8 10 .mt 5 .ml S T
        :v V
        :p .ppb 8
        """)
        t = p.scales['T']

        p.startup()
        self.assertEqual(s.pulse, 0)
        self.assertEqual(s.changeTime, 32)
        self.assertEqual(p.pulse, 0)
        self.assertEqual(p.curScale, s)

        p.pulse = 31
        p.update()
        self.assertEqual(s.pulse, 31)
        self.assertEqual(p.curScale, s)

        p.tick()
        p.update()
        self.assertEqual(p.curScale, t)
        self.assertEqual(s.pulse, 32)
        self.assertEqual(t.pulse, 32)
        self.assertEqual(t.changeTime, 72)

        p.pulse = 71
        p.update()
        self.assertEqual(s.pulse, 32)
        self.assertEqual(t.pulse, 71)
        self.assertEqual(p.curScale, t)

        p.tick()
        p.update()
        self.assertEqual(p.curScale, s) # coinflipped

