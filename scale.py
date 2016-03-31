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

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.root, self.intervals, self.links)

    def validate(self, scaler):
        if self.root < 0 or self.root > 127:
            self.root = DEFAULT_SCALE_ROOT
        if not self.intervals:
            self.intervals = consts.DEFAULT_SCALE_INTERVALS
        # strip out invalid links
        self.links = tuple(link for link in self.links if link in scaler.scales)

    # for the given pitch, reverse engineer which interval in my set it indexes to.
    def pitch_to_interval(self, p):
        try:
            return self.intervals.index(p - self.root)
        except ValueError:
            return -1

    def get_pitch(self, i):
        return self.root + self.intervals[i]

    def random_pitch(self):
        return self.root + rnd.choice(self.intervals)

    def next_scale(self):
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
        self.set_next_change(self.player.pulse)

    def validate_cur(self):
        if len(self.scales) == 0:
            self.curScale = '' # that's okay, the program is going to end next tick anyway
        elif self.curScale not in self.scales:
            self.curScale = rnd.choice(self.scales.keys())

    def update(self, pulse):
        if pulse >= self.nextChange:
            self.set_next_change(pulse)
            if self.curScale:
                next_scale = self.scales[self.curScale].next_scale()
                #print 'Scale Change: %s -> %s; next change at %d'%(self.curScale, next_scale, self.nextChange)
                if next_scale != self.curScale:
                    self.curScale = next_scale
                    self.player.change_scale(self.scales[self.curScale])
        self.state = self.curScale

    def set_next_change(self, pulse):
        self.nextChange = pulse + int(rnd.choice(self.changeTimes) * self.player.ppb)

