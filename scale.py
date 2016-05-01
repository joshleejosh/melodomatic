import re
import consts, generators
from util import *

RE_DEGREE = re.compile('^\s*([-+]*)(\d+)([-+]*)\s*$')

# I represent an abstract degree in an arbitrary scale.
class ScaleDegree:
    def __init__(self, code):
        self.degree = 1
        self.octave = 0
        self.accidental = 0
        self.parse_code(code)

    def parse_code(self, code):
        m = RE_DEGREE.match(code)
        if not m:
            if consts.VERBOSE:
                print 'ERROR: Bad scale degree code "%s"'%code
            return
        g = m.groups()
        if g[0]:
            for c in g[0]:
                if c == '-':
                    self.octave -= 1
                elif c == '+':
                    self.octave += 1
        if g[1]:
            self.degree = int(g[1])
        if g[2]:
            for c in g[2]:
                if c == '-':
                    self.accidental -= 1
                elif c == '+':
                    self.accidental += 1

    def __str__(self):
        s = ''
        if self.octave < 0:
            for c in xrange(abs(self.octave)):
                s += '-'
        elif self.octave > 0:
            for c in xrange(self.octave):
                s += '+'
        s += str(self.degree)
        if self.accidental < 0:
            for c in xrange(abs(self.accidental)):
                s += '-'
        elif self.accidental > 0:
            for c in xrange(self.accidental):
                s += '+'
        return s

    # Get an actual pitch for this degree in the given scale.
    def get_pitch(self, scale):
        i = self.degree%len(scale.intervals)
        o = self.octave + ((self.degree-1) // len(scale.intervals))
        pitch = scale.get_pitch(i - 1)
        pitch += 12 * o
        pitch += self.accidental
        return pitch


# I represent a musical scale out of which notes are picked to produce melodies.
# I also know what other scales the ScaleChanger can transition to from me.
class Scale:
    def __init__(self, id):
        self.id = id
        self.root = consts.DEFAULT_SCALE_ROOT
        self.intervals = consts.DEFAULT_SCALE_INTERVALS
        self.pitches = tuple(self.root + i for i in self.intervals)
        self.linker, self.linkerLabel, self.linkerValues = generators.make_generator((self.id,))

    def dump(self):
        print 'SCALE %s:'%self.id
        print '    pitches = %s [%d + %s]'%(self.pitches, self.root, self.intervals)
        print '    links = %s'%self.linkerLabel

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

    def set_linker(self, data):
        if not data:
            data = (self.id,)
        g,d,v = generators.make_generator(data)
        if g:
            self.linker = g
            self.linkerLabel = d
            self.linkerValues = v

    def get_pitch(self, i):
        return self.pitches[i]

    def next_scale(self):
        return self.linker.next()

