from consts import *
from util import *


class Scale:
    def __init__(self, id):
        self.id = id
        self.root = consts.DEFAULT_SCALE_ROOT
        self.notes = ()
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

    def reset(self, scaler):
        # strip out invalid links
        self.links = tuple(link for link in self.links if link in scaler.scales)

    def get_note(self, i):
        if not self.notes:
            return self.root
        return self.root + self.notes[i]

    def next_note(self):
        if not self.notes:
            return self.root
        """
        return self.root + rnd.choice(self.notes)
        """
        # walk up the scale
        if self.cur >= len(self.notes):
            self.cur = 0
        rv = self.root + self.notes[self.cur]
        self.cur += 1
        return rv

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

    def check_scales(self):
        if len(self.scales) == 0:
            self.curScale = ''
        elif self.curScale not in self.scales:
            self.curScale = rnd.choice(self.scales.keys())

    def reset(self):
        self.nextChange = int(rnd.choice(self.changeTimes) * self.player.ppb)
        for sc in self.scales.itervalues():
            sc.reset(self)
        self.check_scales()

    def update(self, pulse):
        if pulse >= self.nextChange:
            self.nextChange = pulse + int(rnd.choice(self.changeTimes) * self.player.ppb)
            nextScale = self.scales[self.curScale].nextScale()
            #print 'Scale Change: %s -> %s; next change at %d'%(self.curScale, nextScale, self.nextChange)
            self.curScale = nextScale
            self.player.change_scale(self.scales[self.curScale])
        self.state = self.curScale

    def get_scale(self):
        self.check_scales()
        return self.scales[self.curScale].clone()

