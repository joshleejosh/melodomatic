import os, unittest, random, tempfile
import testhelper
import consts, generators

class PlayerTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr, op=None):
        player = testhelper.mkplayer(scr, oldPlayer=op)
        return player

    def test_valid(self):
        p = self.bindit('')
        self.assertFalse(p.is_valid())
        p.startup()
        self.assertFalse(p.midi.opened)
        p = self.bindit(':v V')
        self.assertFalse(p.is_valid())
        p = self.bindit(':s S')
        self.assertFalse(p.is_valid())
        p = self.bindit(""":v V
                           :s S""")
        self.assertTrue(p.is_valid())
        p.startup()
        self.assertTrue(p.midi.opened)
        p.shutdown()
        self.assertFalse(p.midi.opened)

    def test_start_scale(self):
        p = self.bindit(""":v V
                           :s S .r 60
                           :s T .r 62
                           :p .start_scale T
                           """)
        self.assertTrue(p.is_valid())
        self.assertEqual(p.startScale, 'T')
        p.startup()
        self.assertEqual(p.curScale.id, 'T')


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
        self.assertEqual(p.parse_duration(',2p'), (0, 0))

        # can't have a postive hold with negative duration.
        self.assertEqual(p.parse_duration('-3,3'), (-36, -36))
        # Can't have a negative hold with a positive duration.
        self.assertEqual(p.parse_duration('1,-6p'), (12, 12))

        # fractional pulse is a no-no, gets thrown away
        self.assertEqual(p.parse_duration('1.2p'), (0,0))

        p = self.bindit(':PLAYER .bpm 120 .ppb 8')
        self.assertEqual(p.parse_duration('2b'), (16, 16))
        self.assertEqual(p.parse_duration('5p'), (5, 5))
        self.assertEqual(p.parse_duration('1,.5'), (8, 4))
        self.assertEqual(p.parse_duration('2b,2b'), (16, 16))
        self.assertEqual(p.parse_duration('5p,3p'), (5, 3))
        self.assertEqual(p.parse_duration('-3b'), (-24, -24))

        self.assertEqual(p.parse_duration('dfafdasd'), (0, 0))

    def test_transfer(self):
        pass
        p = self.bindit(""":v V .p 1 3 5 .d 1 2 .v 64 72
                           :s S .r 60
                           :s T .r 62
                           :c C .ra 32 .cid 7 .cval 40
                           :p .start_scale T .seed SEEDY
                           """)
        q = self.bindit(""":v V .p 1 3 5 .d 1 2 .v 64 72
                           :s S .r 60
                           :s T .r 62
                           :c C .ra 32 .cid 7 .cval 40
                           :p .start_scale T .seed SEEDY
                           """)
        # voices and scales are equivalent but not the same instance.
        self.assertNotEqual(id(q.voices['V']), id(p.voices['V']))
        self.assertEqual(q.voices['V'], p.voices['V'])
        self.assertNotEqual(id(q.scales['S']), id(p.scales['S']))
        self.assertEqual(q.scales['S'], p.scales['S'])
        self.assertNotEqual(id(q.scales['T']), id(p.scales['T']))
        self.assertEqual(q.scales['T'], p.scales['T'])
        self.assertNotEqual(id(q.controls['C']), id(p.controls['C']))
        self.assertEqual(q.controls['C'], p.controls['C'])

        for i in xrange(4):
            p.update()
            p.pulse += 1
        q.transfer_state(p)
        self.assertEqual(q.pulse, 4)
        self.assertEqual(id(q.voices['V']), id(p.voices['V']))
        self.assertEqual(id(q.scales['S']), id(p.scales['S']))
        self.assertEqual(id(q.scales['T']), id(p.scales['T']))
        self.assertEqual(id(q.controls['C']), id(p.controls['C']))

        # Change S scale, should not copy when transferred
        for i in xrange(4):
            q.update()
            q.pulse += 1
        r = self.bindit(""":v V .p 1 3 5 .d 1 2 .v 64 72
                           :s S .r 59
                           :s T .r 62
                           :c C .ra 32 .cid 7 .cval 40
                           :p .start_scale T .seed SEEDY
                           """, op=q)
        self.assertEqual(r.pulse, 8)
        self.assertEqual(id(r.voices['V']), id(q.voices['V']))
        self.assertNotEqual(id(r.scales['S']), id(q.scales['S']))
        self.assertEqual(id(r.scales['T']), id(q.scales['T']))
        self.assertEqual(id(r.controls['C']), id(q.controls['C']))

    def test_macro(self):
        p = self.bindit("""
            !define FOO 1 2 3
            :v V .p 1 .v 64 .d @FOO 4
        """)
        self.assertEqual(str(p.voices['V'].parameters['DURATION']), '$RANDOM (\'1\', \'2\', \'3\', \'4\')')

    def test_vis_window(self):
        p = self.bindit(':p .visualization_window 6p')
        self.assertEqual(p.visualizationWindow, 6)

    def test_bad_labels(self):
        p = self.bindit("""
            :v V
            :QWIJYBO
            :s S
            .root 60
            .phlebotenum 32
            .intervals 0 2 4 5 7 9 11
        """)
        self.assertEqual(len(p.voices), 1)
        self.assertEqual(len(p.scales), 1)
        self.assertEqual(p.scales['S'].intervals, (0, 2, 4, 5, 7, 9, 11))

