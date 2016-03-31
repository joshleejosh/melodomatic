import unittest
import consts, midi, reader, player, scale, voice

TEST_SCRIPT_EMPTY = ""

TEST_SCRIPT_DEGENERATE = """
:scale S
:voice V
"""

TEST_SCRIPT_SIMPLE = """
:scale S
48
0 4 7
:voice V
0
1 2 4
48 56 64
"""

# #########################################################
# Generate testable objects.

# Create a player with *testable* members, overriding specific values/method where necessary. 
def make_player(script):
    # replace random generators with safer stuff
    voice.Voice.make_pitch = _voice_make_pitch_iterate
    voice.Voice.make_duration = _voice_make_duration_iterate

    p = player.Player()
    reader.Parser().parse(script.splitlines(), p, None)
    p.midi = midi.TestMidi()
    for v in p.voices:
        v.velocity = 48 # default behavior is to init with a random velocity
    return p

def _voice_make_pitch_iterate(self):
    if not hasattr(self, 'curp'):
        self.curp = -1
    self.curp = (self.curp + 1)%len(self.scale.intervals)
    return self.scale.get_pitch(self.curp)

def _voice_make_duration_iterate(self):
    if len(self.durations) == 0:
        return consts.DEFAULT_VELOCITY
    if len(self.durations) == 1:
        return self.b2d(self.durations[0])
    if not hasattr(self, 'curd'):
        self.curd = -1
    self.curd = (self.curd + 1)%len(self.durations)
    return self.b2d(self.durations[self.curd])

# #########################################################
# Validate the test data above.

class ScriptTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_empty(self):
        player = make_player(TEST_SCRIPT_EMPTY)
        self.assertEqual(len(player.scaler.scales), 0)
        self.assertEqual(len(player.voices), 0)
        self.assertEqual(player.scaler.curScale, '')

    def test_degenerate(self):
        player = make_player(TEST_SCRIPT_DEGENERATE)
        self.assertEqual(len(player.voices), 1)
        self.assertEqual(player.voices[0].id, 'V')
        self.assertEqual(player.voices[0].offset, 0)
        self.assertEqual(player.voices[0].durations, ())
        self.assertEqual(player.voices[0].velocities, ())
        self.assertEqual(len(player.scaler.scales), 1)
        self.assertEqual(player.scaler.scales['S'].root, 60)
        self.assertEqual(player.scaler.scales['S'].intervals, (0,))
        self.assertEqual(player.scaler.scales['S'].links, ())
        self.assertEqual(player.scaler.curScale, 'S')

    def test_simple(self):
        player = make_player(TEST_SCRIPT_SIMPLE)
        self.assertEqual(len(player.scaler.scales), 1)
        self.assertEqual(player.scaler.scales['S'].root, 48)
        self.assertEqual(player.scaler.scales['S'].intervals, (0,4,7))
        self.assertEqual(player.scaler.curScale, 'S')
        self.assertEqual(len(player.voices), 1)
        self.assertEqual(player.voices[0].id, 'V')
        self.assertEqual(player.voices[0].offset, 0)
        self.assertEqual(player.voices[0].durations, (1,2,4))
        self.assertEqual(player.voices[0].velocities, (48,56,64))



