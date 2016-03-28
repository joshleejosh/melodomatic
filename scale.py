from consts import *
from util import *


class Scale:
    def __init__(self, id):
        self.id = id
        self.root = consts.DEFAULT_SCALE_ROOT
        self.notes = consts.DEFAULT_SCALE_NOTES
        self.links = ()
        self.cur = 0

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.root, self.notes, self.links)

    def clone(self):
        rv = Scale(self.id)
        rv.root = self.root
        rv.notes = tuple(self.notes)
        rv.links = tuple(self.links)
        return rv

    def validate(self, scaler):
        if self.root < 0 or self.root > 127:
            self.root = DEFAULT_SCALE_ROOT
        if not self.notes:
            self.notes = consts.DEFAULT_SCALE_NOTES
        # strip out invalid links
        self.links = tuple(link for link in self.links if link in scaler.scales)

    def get_note(self, i):
        return self.root + self.notes[i]

    def next_note(self):
        # pick a random note
        return self.root + rnd.choice(self.notes)
        """
        # walk up the scale
        if self.cur >= len(self.notes):
            self.cur = 0
        rv = self.root + self.notes[self.cur]
        self.cur += 1
        return rv
        """

    def nextScale(self):
        if not self.links:
            return self.id
        return rnd.choice(self.links)

class ScaleChanger:
    def __init__(self, p):
        self.player = p
        self.state = ''
        self.scales = {}
        self.changeTimes = consts.DEFAULT_SCALE_CHANGE_TIMES
        self.curScale = ''
        self.nextChange = 0

    def dump(self):
        for sc in self.scales.itervalues():
            sc.dump()
        print 'Change Times: %s'%(self.changeTimes,)

    def validate(self):
        if not self.changeTimes:
            self.changeTimes = consts.DEFAULT_SCALE_CHANGE_TIMES
        for sc in self.scales.itervalues():
            sc.validate(self)
        self.validate_cur()

    def validate_cur(self):
        if len(self.scales) == 0:
            self.curScale = '' # that's okay, the player is going to fail and bail out next tick anyway.
        elif self.curScale not in self.scales:
            self.curScale = rnd.choice(self.scales.keys())

    def get_scale(self):
        self.validate_cur()
        return self.scales[self.curScale].clone()

    def update(self, pulse):
        if pulse >= self.nextChange:
            self.nextChange = pulse + int(rnd.choice(self.changeTimes) * self.player.ppb)
            if self.curScale:
                nextScale = self.scales[self.curScale].nextScale()
                #print 'Scale Change: %s -> %s; next change at %d'%(self.curScale, nextScale, self.nextChange)
                self.curScale = nextScale
                self.player.change_scale(self.scales[self.curScale])
        self.state = self.curScale

