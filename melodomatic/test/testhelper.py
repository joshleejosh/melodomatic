import sys, os.path
mydir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if mydir not in sys.path:
    sys.path.append(mydir)

from melodomatic import reader, midi, consts

def tokenize(s):
    s = s.replace('(',' ( ').replace(')', ' ) ')
    return s.strip().split()

def mkplayer(script, oldPlayer=None):
    parser = reader.Parser()
    lines = script.split('\n')
    pl = parser.make_player(lines, None, oldPlayer)
    pl.midi = midi.TestMidi()
    return pl

def setUp():
    pass

def tearDown():
    pass

