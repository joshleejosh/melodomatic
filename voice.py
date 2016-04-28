import sys
import consts
from util import *

class Note:
    def __init__(self, a, d, p, v):
        self.pitch = p
        self.velocity = v
        self.duration = d
        self.at = a
        self.until = self.at + self.duration
    def __str__(self):
        return '%dv%d'%(self.pitch, self.velocity)
        #return '%dv%dd%d(%d-%d)'%(self.pitch, self.velocity, self.duration, self.at, self.until)
    def is_rest(self):
        return (self.velocity == 0)

# I am responsible for taking pitches from a Scale and turning them into
# playable notes. This mostly involves deciding when and how long to play each
# note. I also decide how hard to play a note (its velocity).
class Voice:
    def __init__(self, i, p):
        self.id = i;
        self.player = p
        self.offset = 0
        self.durations = ()
        self.velocities = ()
        self.harmonies = []
        self.state = ''
        self.playing = False
        self.velocity = consts.DEFAULT_VELOCITY
        self.nextPulse = 0
        self.lastNote = None
        self.scale = None
        self.pitchSet = ''

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.offset, self.durations, self.velocities)

    def validate(self):
        self.validate_harmonies()
        self.velocity = -1
        self.change_velocity()
        if not self.pitchSet:
            self.pitchSet = self.player.pitchSets.values()[0].id

    def validate_harmonies(self):
        del self.harmonies[:]
        for v in self.player.voices.itervalues():
            if isinstance(v, Harmony):
                if v.voice == self.id:
                    self.harmonies.append(v)

    def update(self, pulse):
        if self.lastNote and not self.lastNote.is_rest() and pulse >= self.lastNote.until:
            self.end_last_note()

        if pulse >= self.nextPulse:
            if (rnd.random() < self.player.velocityChangeChance):
                vel = self.change_velocity()
            note = self.gen_note(pulse)
            if note:
                self.play(note)

    def play(self, note):
        if not note.is_rest():
            self.player.play(note.pitch, note.velocity)
        self.lastNote = note
        self.nextPulse = note.until
        if self.lastNote:
            if not self.lastNote.is_rest():
                self.state = str(self.lastNote)

    def end_last_note(self):
        self.player.play(self.lastNote.pitch, 0)
        self.lastNote = None
        self.state = ''

    def gen_note(self, at):
        if not self.scale:
            return None
        v = p = 0
        d = self.make_duration()
        if d < 0:
            d = abs(d)
        else:
            p = self.offset + self.make_pitch()
            v = self.velocity
        rv = Note(at, d, p, v)
        for h in self.harmonies:
            h.harmonize(rv)
        return rv

    def make_pitch(self):
        return self.player.pitchSets[self.pitchSet].random_pitch(self.scale)

    def make_duration(self):
        return self.rnddur()

    # randomly walk up or down one step in my list of velocities.
    def change_velocity(self):
        if len(self.velocities) == 0:
            self.velocity = consts.DEFAULT_VELOCITY
            return self.velocity
        if self.velocity not in self.velocities:
            self.velocity = rnd.choice(self.velocities)
            return self.velocity

        vi = self.velocities.index(self.velocity)
        if len(self.velocities) == 1:
            ni = 0
        elif vi == 0:
            ni = 1
        elif vi == len(self.velocities) - 1:
            ni = len(self.velocities) - 2
        else:
            ni = vi + coinflip()
        #print '%s v: %d -> %d'%(self.id, self.velocities[vi], self.velocities[ni])
        self.velocity = self.velocities[ni]
        return self.velocity

    def rnddur(self):
        if not self.durations:
            return self.player.ppb
        return rnd.choice(self.durations)


# I am a special kind of Voice that plays along with another Voice in unison,
# but with my pitches and velocities offset by a certain amount.
class Harmony(Voice):
    def __init__(self, i, p):
        Voice.__init__(self, i, p)
        self.voice = ''
        self.pitchOffset = 0
        self.stepOffset = 0
        self.velocityOffset = 0

    def dump(self):
        print '%s: Harmony of %s, %d %d'%(self.id, self.voice, self.pitchOffset, self.velocityOffset)

    # I should never generate a note on my own
    def validate(self):
        self.nextPulse = sys.maxint
    def gen_note(self):
        return None

    def harmonize(self, note):
        if self.lastNote and not self.lastNote.is_rest():
            self.end_last_note()
        if note.is_rest():
            self.play(note)
            return

        # walk up/down the scale's intervals according to stepOffset, wrapping
        # around and octaving when neccessary.
        so = 0
        pii = self.scale.pitch_to_interval(note.pitch)
        if pii >= 0:
            op = self.scale.intervals[pii]
            pii += self.stepOffset
            if self.stepOffset < 0:
                if pii < 0:
                    so -= 12
                so += self.scale.intervals[pii] - op
            elif self.stepOffset > 0:
                if pii >= len(self.scale.intervals):
                    so += 12
                    pii = pii%len(self.scale.intervals)
                so += self.scale.intervals[pii] - op

        hnote = Note(note.at, note.duration, note.pitch + self.pitchOffset + so, note.velocity + self.velocityOffset)
        self.play(hnote)


# I am a special type of Voice that plays a static sequence of notes in a loop,
# instead of generating them algorithmically.
class Loop(Voice):
    def __init__(self, i, p):
        Voice.__init__(self, i, p)
        self.steps = []
        self.curStep = -1

    # arguments are strings, since some of them might be a dot (representing a
    # rest or carryover of the previous value) or empty (representing a carryover)
    def add_step(self, p, d, v):
        if p == '.':
            p = sys.maxint
        if not d or d == '.':
            d = self.steps[-1].duration
        if not v or v == '.':
            v = self.steps[-1].velocity
        self.steps.append(Step(int(p), float(d), int(v)))
        self.durations = tuple(s.duration for s in self.steps) # for reporting

    def dump(self):
        print '%s: Loop: %d steps, %d beats'%(self.id, len(self.steps), sum(self.durations))
        #for step in self.steps:
        #    step.dump()

    def validate(self):
        self.curStep = -1
        self.validate_harmonies()

    def gen_note(self, at):
        rv = None
        self.curStep = (self.curStep + 1)%len(self.steps)
        step = self.steps[self.curStep]

        d = step.duration
        p = step.pitch
        v = step.velocity
        if p == sys.maxint:
            p = v = 0
        else:
            p += self.offset + self.scale.root
        rv = Note(at, d, p, v)

        for h in self.harmonies:
            h.harmonize(rv)
        return rv


# I am used by Loop, and represent a step in its sequence.
class Step:
    def __init__(self, p, d, v):
        self.pitch = p
        self.duration = d
        self.velocity = v
    def dump(self):
        print '    Step: %s %0.2f %d'%(('.' if self.pitch==sys.maxint else str(self.pitch)), self.duration, self.velocity)


