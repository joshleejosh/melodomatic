from consts import *
from util import *

# I represent a set of pitches that can be played together.
# I produce pitches in some kind of order for a Voice to play as notes.
class Scale:
    def __init__(self, id):
        self.id = id
        self.root = consts.DEFAULT_SCALE_ROOT
        self.intervals = consts.DEFAULT_SCALE_INTERVALS
        self.links = ()
        self.cur = 0

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.root, self.intervals, self.links)

    def validate(self, scaler):
        if self.root < 0 or self.root > 127:
            self.root = DEFAULT_SCALE_ROOT
        if not self.intervals:
            self.intervals = consts.DEFAULT_SCALE_INTERVALS
        # strip out invalid links
        self.links = tuple(link for link in self.links if link in scaler.scales)

    def clone(self):
        rv = Scale(self.id)
        rv.root = self.root
        rv.intervals = tuple(self.intervals)
        rv.links = tuple(self.links)
        return rv

    # for the given pitch, reverse engineer which interval in my set it indexes to.
    def pitch_to_interval(self, p):
        try:
            return self.intervals.index(p - self.root)
        except ValueError:
            return -1

    def get_pitch(self, i):
        return self.root + self.intervals[i]

    def next_pitch(self):
        # pick a random note
        return self.root + rnd.choice(self.intervals)
        """
        # walk up the scale
        print self.cur, len(self.intervals)
        rv = self.root + self.intervals[self.cur]
        self.cur = (self.cur + 1)%len(self.intervals)
        return rv
        """

    def nextScale(self):
        if not self.links:
            return self.id
        return rnd.choice(self.links)


# I am responsible for knowing about all the available Scales and shifting
# between them at appropriate times.  When I change Scales, the Player will
# propogate the change to all the Voices.
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


