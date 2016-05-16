import unittest, random
import testhelper
import consts, generators

class VoiceGeneratorTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr, vid=''):
        player = testhelper.mkplayer(scr)
        voice = player.voices[player.voiceOrder[0]]
        if vid:
            voice = player.voices[vid]
        return player, voice
    def checkit(self, note, p, d, v):
        self.assertEqual(note.pitch, p)
        self.assertEqual(note.duration, d)
        self.assertEqual(note.velocity, v)

    def test_eq(self):
        p,v = self.bindit(':VOICE V .channel 2 .seed SEEDS .pitch 3 .duration 2 .velocity 57')
        q,w = self.bindit(':v V .ch 2 .seed SEEDS .p 3 .d 2 .v 57')
        self.assertEqual(v, w)

    def test_bare(self):
        p,v = self.bindit("""
                :v V
                .seed SEEDS
                """)

        self.assertEqual(v.id, 'V')
        self.assertEqual(v.generator.name, 'MELODOMATIC')
        self.assertEqual(v.generator.voice, v)
        self.assertEqual(sorted(v.generator.parameters), ['DURATION', 'PITCH', 'TRANSPOSE', 'VELOCITY'])

    def test_melodomatic(self):
        p,v = self.bindit("""
                :v V .seed SEEDS .p 3 .d 2 .v 57
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        for i in xrange(11):
            self.checkit(v.generator.next(), 52, 24, 57)

        p,v = self.bindit("""
                :v V
                .seed SEEDS
                .p 1 2 3 4
                .d 1 2 -1
                .v 48 56 64
                :s S .r 48 .i 0 2 4 5 7 9 11
                :p .bpm 120 .ppb 12
                """)
        self.checkit(v.generator.next(), 48, 24, 64)
        self.checkit(v.generator.next(), 50, 24, 64)
        self.checkit(v.generator.next(), 52, 24, 56)
        self.checkit(v.generator.next(), 1, 12, 0)
        self.checkit(v.generator.next(), 53, 24, 64)
        self.checkit(v.generator.next(), 1, 12, 0)
        self.checkit(v.generator.next(), 1, 12, 0)
        self.checkit(v.generator.next(), 1, 12, 0)
        self.checkit(v.generator.next(), 50, 12, 64)
        self.checkit(v.generator.next(), 1, 12, 0)
        self.checkit(v.generator.next(), 1, 12, 0)



