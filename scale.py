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
        self.linker, self.linkerLabel, self.linkerValues = generators.make_generator((self.id,))

    def dump(self):
        print 'SCALE %s:'%self.id
        print '    root = %d'%self.root
        print '    intervals = %s'%str(self.intervals)
        print '    links = %s'%self.linkerLabel

    def set_linker(self, data):
        if not data:
            data = (self.id,)
        g,d,v = generators.make_generator(data)
        if g:
            self.linker = g
            self.linkerLabel = d
            self.linkerValues = v

    def validate(self, scaler):
        if self.root < 0 or self.root > 127:
            self.root = DEFAULT_SCALE_ROOT
        if not self.intervals:
            self.intervals = consts.DEFAULT_SCALE_INTERVALS
        # strip out invalid links
        self.links = tuple(link for link in self.links if link in scaler.scales)

    # for the given pitch, reverse engineer which interval in my set it indexes to.
    # returns -1 if it can't figure something out.
    def pitch_to_interval(self, p):
        try:
            return self.intervals.index(p - self.root)
        except ValueError:
            return -1

    def get_pitch(self, i):
        return self.root + self.intervals[i]

    def next_scale(self):
        return self.linker.next()

