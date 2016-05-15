import sys, os.path
mydir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if mydir not in sys.path:
    sys.path.append(mydir)

import reader

def tokenize(s):
    s = s.replace('(',' ( ').replace(')', ' ) ')
    return s.strip().split()

def mkplayer(script):
    parser = reader.Parser()
    lines = script.split('\n')
    pl = parser.make_player(lines, None, None)
    return pl

def setUp():
    pass

def tearDown():
    pass

