import unittest
import player, scale, voice
import test_script

class VoiceTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_gen_note(self):
        player = test_script.make_player(test_script.TEST_SCRIPT_SIMPLE)
        v = player.voices[0]
        v.gen_note(13)
        self.assertEqual(len(v.queue), 2)
        self.assertEqual(v.queue[0], {'when':21, 'note':48, 'velocity':0})
        self.assertEqual(v.queue[1], {'when':13, 'note':48, 'velocity':48})
        v.gen_note(21)
        self.assertEqual(len(v.queue), 4)
        self.assertEqual(v.queue[2], {'when':37, 'note':52, 'velocity':0})
        self.assertEqual(v.queue[3], {'when':21, 'note':52, 'velocity':48})
        v.gen_note(37)
        self.assertEqual(len(v.queue), 6)
        self.assertEqual(v.queue[4], {'when':69, 'note':55, 'velocity':0})
        self.assertEqual(v.queue[5], {'when':37, 'note':55, 'velocity':48})

    def test_play(self):
        player = test_script.make_player(test_script.TEST_SCRIPT_SIMPLE)
        v = player.voices[0]
        v.gen_note(13)
        v.gen_note(21)
        v.gen_note(37)
        v.play(0) # too early, don't do anything
        self.assertEqual(len(v.queue), 6)
        self.assertEqual(len(player.midi.buffer), 0)
        v.play(13)
        self.assertEqual(len(v.queue), 5)
        self.assertEqual(tuple(e['when'] for e in v.queue), (21, 37, 21, 69, 37))
        self.assertEqual(tuple(e['velocity'] for e in v.queue), (0,0,48,0,48))
        self.assertEqual(len(player.midi.buffer), 1)
        v.play(20) # short by one, should nop
        self.assertEqual(len(v.queue), 5)
        self.assertEqual(len(player.midi.buffer), 1)
        v.play(21)
        self.assertEqual(len(v.queue), 3)
        self.assertEqual(tuple(e['when'] for e in v.queue), (37, 69, 37))
        self.assertEqual(tuple(e['velocity'] for e in v.queue), (0,0,48))
        self.assertEqual(len(player.midi.buffer), 3)
        v.play(38) # over by one, should catch late messages
        self.assertEqual(len(v.queue), 1)
        self.assertEqual(tuple(e['when'] for e in v.queue), (69,))
        self.assertEqual(tuple(e['velocity'] for e in v.queue), (0,))
        self.assertEqual(len(player.midi.buffer), 5)
        # check the order of messages
        self.assertEqual(tuple(m.note for m in player.midi.buffer), (48,48,52,52,55))
        self.assertEqual(tuple(m.velocity for m in player.midi.buffer), (48,0,48,0,48))

    def test_offset(self):
        script = """
            :scale S
            40
            0 4 7
            :voice V
            5
            """
        player = test_script.make_player(script)
        v = player.voices[0]
        v.gen_note(0)
        self.assertEqual(v.queue[0]['note'], 45)
        self.assertEqual(v.queue[1]['note'], 45)

    def test_change_velocity(self):
        script = """
            :scale S
            :voice V
            0
            2
            48
            """
        player = test_script.make_player(script)
        voice = player.voices[0]
        # bad value
        voice.velocity = 33
        self.assertEqual(voice.change_velocity(), 48)
        # if there's only one value, it should never change
        self.assertEqual(voice.change_velocity(), 48)

        script = """
            :scale S
            :voice V
            0
            2
            48 64
            """
        player = test_script.make_player(script)
        voice = player.voices[0]
        # if there are two values, it should ping pong between them
        voice.velocity = 48
        self.assertEqual(voice.change_velocity(), 64)
        self.assertEqual(voice.change_velocity(), 48)
        self.assertEqual(voice.change_velocity(), 64)
        self.assertEqual(voice.change_velocity(), 48)

        # if there are three+ values, it should randomly walk, but whenever it hits an edge, turn around
        script = """
            :scale S
            :voice V
            0
            2
            48 56 64
            """
        player = test_script.make_player(script)
        voice = player.voices[0]
        voice.velocity = 48
        self.assertEqual(voice.change_velocity(), 56)
        for i in xrange(100):
            vel = voice.change_velocity()
            if vel == 64:
                self.assertEqual(voice.change_velocity(), 56)
            elif vel == 48:
                self.assertEqual(voice.change_velocity(), 56)
            else:
                self.fail('bad velocity %d'%vel)


    def test_harmony(self):
        script = """
            :scale S
            40
            0 2 4 5 7 9 11
            :voice V
            0
            2
            48 56 64
            :harmony Ho
            V
            -12
            0
            -8
            :harmony Hs
            V
            0
            2
            8
            :harmony Hn
            V
            0
            -3
            -4
            """
        player = test_script.make_player(script)
        voice = player.voices[0]
        harmo = player.voices[1]
        harms = player.voices[2]
        harmn = player.voices[2]
        voice.gen_note(0)
        self.assertEqual(voice.queue[-1], {'when':0, 'note':40, 'velocity':48})
        # one octave down
        self.assertEqual(harmo.queue[-1], {'when':0, 'note':28, 'velocity':40})
        # 2 steps up on the scale's interval list
        self.assertEqual(harms.queue[-1], {'when':0, 'note':44, 'velocity':56})


