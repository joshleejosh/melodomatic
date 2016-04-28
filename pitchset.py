import re
from consts import *
from util import *

RE_INTERVAL = re.compile('^\s*([-+]*)(\d+)([-+]*)\s*$')

# I represent an abstract pitch class in an arbitrary scale.
class PitchClass:
    def __init__(self, code):
        self.pclass = 1
        self.octave = 0
        self.accidental = 0
        self.parse_code(code)

    def parse_code(self, code):
        m = RE_INTERVAL.match(code)
        if not m:
            return
        g = m.groups()
        if g[0]:
            for c in g[0]:
                if c == '-':
                    self.octave -= 1
                elif c == '+':
                    self.octave += 1
        if g[1]:
            self.pclass = int(g[1])
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
        s += str(self.pclass)
        if self.accidental < 0:
            for c in xrange(abs(self.accidental)):
                s += '-'
        elif self.accidental > 0:
            for c in xrange(self.accidental):
                s += '+'
        return s


# I represent a set of pitch classes in arbitrary scale that can be played
# together in a nice way.  I produce pitches in some kind of order for a Voice
# to play as notes.
class PitchSet:
    def __init__(self, id):
        self.id = id
        self.codes = ["1",]
        self.pitches = [PitchClass("1")]
        self.order = 0

    def dump(self):
        print '%s: %s'%(self.id, ' '.join((str(i) for i in self.pitches)))

    def set_intervals(self, codes):
        self.codes = codes
        self.pitches = []
        for c in self.codes:
            self.pitches.append(PitchClass(c))

    def random_pitch(self, scale):
        pclass = rnd.choice(self.pitches)
        return self.get_pitch(pclass, scale)

    def ordered_pitch(self, scale):
        pclass = self.pitches[self.order]
        self.order += 1
        if self.order >= len(self.pitches):
            self.order = 0
        return self.get_pitch(pclass, scale)

    def get_pitch(self, pclass, scale):
        i = pclass.pclass
        o = pclass.octave
        while i > len(scale.intervals):
            i -= len(scale.intervals)
            o += 1
        pitch = scale.get_pitch(i - 1)
        pitch += 12 * o
        pitch += pclass.accidental
        return pitch


