import unittest
from . import testhelper

class VoiceGeneratorTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr):
        player = testhelper.mkplayer(scr)
        voice = player.voices[player.voiceOrder[0]]
        return player, voice
    def checkit(self, note, p, d, v):
        self.assertEqual(note.pitch, p)
        self.assertEqual(note.duration, d)
        self.assertEqual(note.velocity, v)
        #def f(n, p, d, v):
        #    print('        self.checkit(v.curNote, %d, %d, %d)'%(n.pitch, n.duration, n.velocity))

    def test_eq(self):
        _,v = self.bindit(':VOICE V .channel 2 .seed SEEDS .pitch 3 .duration 2 .velocity 57')
        _,w = self.bindit(':v V .ch 2 .seed SEEDS .p 3 .d 2 .v 57')
        self.assertEqual(v, w)
        _,x = self.bindit(':VOICE V .channel 2 .seed SEEDS .pitch 4 .duration 2 .velocity 57')
        self.assertNotEqual(v, x)

    def test_bad_voice(self):
        _,v = self.bindit(':v')
        self.assertEqual(v.id, 'DUMMY')
        _,v = self.bindit(':v V .')
        _,v = self.bindit(':v V .qwijybo')

        _,v = self.bindit(':v V')
        self.assertTrue(v.validate_generator())
        del v.parameters['PITCH']
        self.assertFalse(v.validate_generator())

        _,v = self.bindit(':v V')
        self.assertTrue(v.validate_generator())
        v.generator = None
        self.assertFalse(v.validate_generator())

    def test_bare(self):
        _,v = self.bindit("""
                :v V
                .seed SEEDS
                """)

        self.assertEqual(v.id, 'V')
        self.assertEqual(v.generator.name, 'MELODOMATIC')
        self.assertEqual(v.generator.voice, v)
        self.assertEqual(sorted(v.generator.parameters), ['DURATION', 'PITCH', 'TRANSPOSE', 'VELOCITY'])

    def test_melodomatic(self):
        _,v = self.bindit("""
                :v V .seed SEEDS .p 3 .d 2 .v 57
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        self.assertEqual(str(v.generator), '$MELODOMATIC')
        for i,val in enumerate(v.generator):
            self.checkit(val, 52, 24, 57)
            if i > 11:
                break

        _,v = self.bindit("""
                :v V
                .seed SEEDS
                .p 1 2 3 4
                .d 1 2 -1
                .v 48 56 64
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        self.checkit(next(v.generator),  1, 12,  0)
        self.checkit(next(v.generator), 52, 24, 56)
        self.checkit(next(v.generator), 48, 12, 48)
        self.checkit(next(v.generator), 48, 24, 64)
        self.checkit(next(v.generator), 52, 12, 48)
        self.checkit(next(v.generator), 53, 24, 64)
        self.checkit(next(v.generator), 53, 12, 64)
        self.checkit(next(v.generator),  1, 12,  0)
        self.checkit(next(v.generator),  1, 12,  0)
        self.checkit(next(v.generator),  1, 12,  0)
        self.checkit(next(v.generator), 48, 24, 64)

    def test_unscaled(self):
        # should be the same as in test_melodomatic, despite the different scale.
        _,v = self.bindit("""
                :v V $UNSCALED
                .seed SEEDS
                .n 48 50 52 53
                .d 1 2 -1
                .v 48 56 64
                :s S .r 62 .i 0 2 3 5 7 8 10 # D Minor
                :p .bpm 120 .ppb 12
                """)
        self.checkit(next(v.generator), 1, 12, 0)
        self.checkit(next(v.generator), 52, 24, 56)
        self.checkit(next(v.generator), 48, 12, 48)
        self.checkit(next(v.generator), 48, 24, 64)
        self.checkit(next(v.generator), 52, 12, 48)
        self.checkit(next(v.generator), 53, 24, 64)
        self.checkit(next(v.generator), 53, 12, 64)
        self.checkit(next(v.generator), 1, 12, 0)
        self.checkit(next(v.generator), 1, 12, 0)
        self.checkit(next(v.generator), 1, 12, 0)
        self.checkit(next(v.generator), 48, 24, 64)

    def test_unison(self):
        p,v = self.bindit("""
                :v V .seed SEEDS .p 1 2 3 4 .d 1 2 -1 .v 48 56 64
                :v U $unison .vo V .tr +12 .ve -8
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        u = p.voices['U']
        p.startup()
        p.update()
        self.checkit(v.curNote, 1, 12, 0)
        self.checkit(u.curNote, 13, 12, 0)

        p.pulse = 24
        p.update()
        self.checkit(v.curNote, 52, 24, 56)
        self.checkit(u.curNote, 64, 24, 48)

        p.pulse = 48
        p.update()
        self.checkit(v.curNote, 48, 12, 48)
        self.checkit(u.curNote, 60, 12, 40)

        p.pulse = 72
        p.update()
        self.checkit(v.curNote, 48, 24, 64)
        self.checkit(u.curNote, 60, 24, 56)

    def test_unison_bad_voice(self):
        # U is trying to follow a nonexistent voice
        p,v = self.bindit("""
                :v V .seed SEEDS .p 3 .d 2 .v 57
                :v U $unison .vo Q .tr +7 .ve +4
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        u = p.voices['U']
        p.startup()
        p.update()
        self.checkit(v.curNote, 52, 24, 57)
        self.checkit(u.curNote,  1,  1,  0)

    def test_unison_muted(self):
        # U is trying to follow a muted voice
        p,v = self.bindit("""
                :v V .seed SEEDS .p 3 .d 2 .v 57 .mute
                :v U $unison .vo V .tr +7 .ve +4
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        u = p.voices['U']
        p.startup()
        p.update()
        self.assertEqual(v.curNote, None)
        self.checkit(u.curNote,  1,  1,  0)

    def test_unison_pitch_range(self):
        # U is trying to follow a voice with an extreme pitch.
        # U's note will be out of range, so it will emit a rest instead.
        p,v = self.bindit("""
                :v V $UNSCALED .seed SEEDS .n 120 .d 2 .v 57
                :v U $unison .vo V .tr +12 .ve +4
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        u = p.voices['U']
        p.startup()
        p.update()
        self.checkit(v.curNote, 120, 24, 57)
        self.checkit(u.curNote,   1, 24,  0)

    def test_link(self):
        p,v = self.bindit("""
                :v V .seed SEEDS .p 1 2 3 4 .d 1 2 -1 .v 48 56 64 .mt 4 .ml W
                :v W .seed SEEDS .p 5 6 7 8 .d 7b     .v 56 64 72 .mt 4 .ml W .mute
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        w = p.voices['W']
        p.startup()
        p.update()
        self.assertFalse(v.mute)
        self.assertEqual(v.changeTime, 48)
        self.assertTrue(w.mute)

        p.pulse = 47
        p.update()
        self.assertFalse(v.mute)
        self.assertTrue(w.mute)

        p.tick()
        p.update()
        self.assertTrue(v.mute)
        self.assertFalse(w.mute)
        self.assertEqual(w.changeTime, 96)

        p.pulse = 95
        p.update()
        self.assertTrue(v.mute)
        self.assertFalse(w.mute)
        # W has an irregular note duration, so we can test that the voice
        # doesn't do an interrupting hard reset on self-transition.
        cn = w.curNote

        # self-(non-)transition: nothting should change but W's change time
        p.tick()
        p.update()
        self.assertTrue(v.mute)
        self.assertFalse(w.mute)
        self.assertEqual(w.changeTime, 144)
        self.assertEqual(w.curNote, cn)

    def test_solo(self):
        p,v = self.bindit("""
                :v V .seed SEEDS .p 1 .d 1 .v 96
                :v W .seed SEEDS .p 3 .d 1 .v 96 .solo
                :v X .seed SEEDS .p 5 .d 1 .v 96
                :s S .r 48 .i 0 2 4 5 7 9 11
                """)
        v = p.voices['V']
        w = p.voices['W']
        x = p.voices['X']
        p.startup()
        p.update()
        self.assertTrue(v.mute)
        self.assertFalse(w.mute)
        self.assertTrue(x.mute)

    # Solo and mute should cancel each other
    def test_mute_solo(self):
        p,v = self.bindit("""
                :v V .seed SEEDS .p 1 .d 1 .v 96
                :s S .r 48 .i 0 2 4 5 7 9 11
                """)
        v = p.voices['V']
        p.startup()
        p.update()
        self.assertFalse(v.mute)
        self.assertFalse(v.solo)
        v.set_solo(True)
        self.assertFalse(v.mute)
        self.assertTrue(v.solo)
        v.set_mute(False)
        self.assertFalse(v.mute)
        self.assertTrue(v.solo)
        v.set_mute(True)
        self.assertTrue(v.mute)
        self.assertFalse(v.solo)
        v.set_solo(False)
        self.assertTrue(v.mute)
        self.assertFalse(v.solo)
        v.set_solo(True)
        self.assertFalse(v.mute)
        self.assertTrue(v.solo)

