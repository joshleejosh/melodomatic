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
        self.root = consts.DEFAULT_SCALE_ROOT
        self.intervals = consts.DEFAULT_SCALE_INTERVALS
        self.pitches = tuple(self.root + i for i in self.intervals)
        self.linker, self.linkerLabel = generators.bind_generator((self.id,), self.player)

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
        g,d = generators.bind_generator(data, self.player)
        if g:
            self.linker = g
            self.linkerLabel = d

    def parse_degree(self, code):
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

        i = degree%len(self.intervals)
        o = octave + ((degree-1) // len(self.intervals))
        pitch = self.get_pitch(i - 1)
        pitch += 12 * o
        pitch += accidental
        return pitch

    def get_pitch(self, i):
        return self.pitches[i]

    def next_scale(self):
        return str(self.linker.next())

