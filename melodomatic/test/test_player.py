import unittest, random
import testhelper
import consts, generators

class PlayerTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr, cid=''):
        player = testhelper.mkplayer(scr)
        return player
 
    def test_duration(self):
        p = self.bindit(':PLAYER .bpm 120 .ppb 12')
        self.assertEqual(p.parse_duration('1'), (12, 12))
        self.assertEqual(p.parse_duration('-4'), (-48, -48))
        self.assertEqual(p.parse_duration('2b'), (24, 24))
        self.assertEqual(p.parse_duration('-3b'), (-36, -36))
        self.assertEqual(p.parse_duration('5p'), (5, 5))
        self.assertEqual(p.parse_duration('-7p'), (-7, -7))
        self.assertEqual(p.parse_duration(''), (0, 0))

        # Two values joined by a comma are duration & note hold time.
        self.assertEqual(p.parse_duration('1,.5'), (12, 6))
        self.assertEqual(p.parse_duration('2b,2b'), (24, 24))
        self.assertEqual(p.parse_duration('5p,3p'), (5, 3))
        self.assertEqual(p.parse_duration('0,0'), (0, 0))
        self.assertEqual(p.parse_duration(',0'), (0, 0))

        # hold cannot be greater than duration.
        self.assertEqual(p.parse_duration('1,13p'), (12, 12))
        self.assertEqual(p.parse_duration('-3,3'), (-36, -36))
        self.assertEqual(p.parse_duration(',2p'), (0, 0))

        p = self.bindit(':PLAYER .bpm 120 .ppb 8')
        self.assertEqual(p.parse_duration('2b'), (16, 16))
        self.assertEqual(p.parse_duration('5p'), (5, 5))
        self.assertEqual(p.parse_duration('1,.5'), (8, 4))
        self.assertEqual(p.parse_duration('2b,2b'), (16, 16))
        self.assertEqual(p.parse_duration('5p,3p'), (5, 3))
        self.assertEqual(p.parse_duration('-3b'), (-24, -24))

