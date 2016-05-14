import re
import consts, generators
from util import *

RE_DEGREE = re.compile('^\s*([-+]*)(\d+)([-+]*)\s*$')

# I represent a musical scale out of which notes are picked to produce melodies.
# I also know what other scales the ScaleChanger can transition to from me.
class Scale:
    def __init__(self, id, player):
        self.id = id
        self.player = player
        self.rng = random.Random()
        self.set_seed(self.player.rng.random())
        self.root = consts.DEFAULT_SCALE_ROOT
        self.intervals = consts.DEFAULT_SCALE_INTERVALS
        self.pitches = tuple(self.root + i for i in self.intervals)
        self.set_durationer([])
        self.set_linker([])
        self.pulse = 0
        self.changeTime = 0
        self.status = ''

    def dump(self):
        print 'SCALE %s:'%self.id
        print '    seed %s'%self.rngSeed
        print '    pitches = %s [%d + %s]'%(self.pitches, self.root, self.intervals)
        print '    duration = %s'%self.durationerLabel
        print '    links = %s'%self.linkerLabel

    def set_seed(self, sv):
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def set_root(self, r):
        self.root = r
        if self.root and self.intervals:
            self.pitches = tuple(i + self.root for i in self.intervals)

    def set_intervals(self, ia):
        self.intervals = ia
        if self.root and self.intervals:
            self.pitches = tuple(i + self.root for i in self.intervals)

    def set_pitches(self, pa):
        self.pitches = pa
        self.root = self.pitches[0]
        self.intervals = tuple(p - self.root for p in self.pitches)

    def set_durationer(self, data):
        if not data:
            data = (str(consts.DEFAULT_SCALE_CHANGE_TIME),)
        g,d = generators.bind_generator(data, self)
        if g:
            self.durationer = g
            self.durationerLabel = d
        
    def set_linker(self, data):
        if not data:
            data = (self.id,)
        g,d = generators.bind_generator(data, self)
        if g:
            self.linker = g
            self.linkerLabel = d

    def begin(self, pulse):
        self.pulse = pulse
        self.changeTime = self.pulse + self.player.parse_duration(self.durationer.next())
        self.status = self.id
        #if consts.VERBOSE:
        #    print 'Begin scale %s at %d, next change at %d'%(self.id, self.pulse, self.changeTime)

    def update(self, pulse):
        self.status = ''
        self.pulse = pulse
        if self.pulse >= self.changeTime:
            n = str(self.linker.next())
            self.player.change_scale(n)

    def get_pitch(self, i):
        return self.pitches[i]

    # -----------------------------------------------------
    # pitch arithmetic

    def degree_to_pitch(self, code):
        degree, octave, accidental = self.parse_code(code)
        pitch = self.get_pitch(degree - 1)
        pitch += 12 * octave
        pitch += accidental
        return pitch

    # Make sure degree is within the range of this scale, and adjust octave
    # accordingly.
    def parse_code(self, code):
        d, o, a = parse_degree(code)
        while d > len(self.intervals):
            d -= len(self.intervals)
            o += 1
        return (d, o, a)

    # join a degree and octave into single degree offset, with the tonic at 0.
    # So for codes: --2 -1 -5 -7 1 3 5 7 8 +4
    # You get:      -13 -7 -3 -1 0 2 4 6 7 10
    def join_degree(self, degree, octave):
        rv = degree - 1
        rv += octave * len(self.intervals)
        return rv

    # Take a degree offset (probably produced from join_degree) and split it
    # into (normalized) degree and octave.
    def split_degree(self, d):
        octave = d // len(self.intervals)
        degree = d % len(self.intervals) + 1
        return (degree, octave)


def parse_degree(code):
    code = code.strip()
    degree = 1
    octave = 0
    accidental = 0

    i = 0
    while i < len(code):
        if code[i] == '-':
            octave -= 1
        elif code[i] == '+':
            octave += 1
        else:
            break
        i += 1

    dbuf = ''
    while i < len(code):
        if code[i].isdigit():
            dbuf += code[i]
        else:
            break
        i += 1
    degree = int(dbuf)

    while i < len(code):
        if code[i] == '-':
            accidental -= 1
        elif code[i] == '+':
            accidental += 1
        else:
            break
        i += 1
    
    return (degree, octave, accidental)


def format_degree(degree, octave, accidental):
    rv = ''
    for i in xrange(abs(octave)):
        if octave < 0:
            rv += '-'
        else:
            rv += '+'
    rv += str(degree)
    for i in xrange(abs(accidental)):
        if accidental < 0:
            rv += '-'
        else:
            rv += '+'
    return rv


