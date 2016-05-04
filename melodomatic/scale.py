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

    def degree_to_pitch(self, code):
        degree, octave, accidental = parse_degree(code)
        i = degree%len(self.intervals)
        o = octave + ((degree-1) // len(self.intervals))
        pitch = self.get_pitch(i - 1)
        pitch += 12 * o
        pitch += accidental
        return pitch

    def get_pitch(self, i):
        return self.pitches[i]

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

