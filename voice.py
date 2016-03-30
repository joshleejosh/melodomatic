import sys
import consts
from util import *

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
        self.velocity = consts.DEFAULT_VELOCITY
        self.queue = []
        self.harmonies = []
        self.nextNote = 0
        self.scale = None
        self.playing = False
        self.state = ''

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.offset, self.durations, self.velocities)

    def validate(self):
        self.validate_harmonies()

    def validate_harmonies(self):
        del self.harmonies[:]
        for v in self.player.voices:
            if isinstance(v, Harmony):
                if v.voice == self.id:
                    self.harmonies.append(v)

    def update(self, pulse):
        if pulse >= self.nextNote:
            self.gen_note(pulse)
            b = self.rnddur()
            self.nextNote = pulse + b

    def play(self, pulse):
        # Collate events for this tick so that we send all note off events
        # before the note-ons, for the case where we're repeating a held note
        # (we don't want the release of an old press to cancel out the new one)
        ons = []
        offs = []
        for i in range(len(self.queue)-1, -1, -1):
            q = self.queue[i]
            if q['when'] <= pulse:
                if q['velocity'] == 0:
                    offs.append(q)
                else:
                    ons.append(q)
                del self.queue[i]

        for q in offs:
            self.state = ''
            self.playing = False
            self.player.play(q['note'], q['velocity'])
        for q in ons:
            self.playing = True
            self.state = '%s@%d'%(note_name(q['note']), q['velocity'])
            self.player.play(q['note'], q['velocity'])

    def gen_note(self, at):
        if not self.scale:
            return
        pitch = self.offset + self.scale.next_pitch()
        dur = self.rnddur()
        vel = self.velocity
        if (rnd.random() < self.player.velocityChangeChance):
            vel = self.change_velocity()

        self.mknote(at, pitch, vel, dur)

        for h in self.harmonies:
            h.harmonize(at, pitch, vel, dur)

    def mknote(self, at, n, v, d):
        # a note-off is just a note-on with velocity 0.
        if n >= 0 and n <= 127:
            self.queue.append({ 'when':at+d, 'note':n, 'velocity':0 })
            self.queue.append({ 'when':at,   'note':n, 'velocity':v })

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
            ni = -2
        else:
            ni = vi + coinflip()
        #print '%s v: %d -> %d'%(self.id, self.velocities[vi], self.velocities[ni])
        self.velocity = self.velocities[ni]
        return self.velocity

    def new_scale(self, sc):
        self.scale = sc

    def rnddur(self):
        if not self.durations:
            return self.player.ppb
        return int(rnd.choice(self.durations) * self.player.ppb)


class Harmony(Voice):
    def __init__(self, i, p):
        Voice.__init__(self, i, p)
        self.voice = ''
        self.pitchOffset = 0
        self.velocityOffset = 0

    def dump(self):
        print '%s: Harmony of %s, %d %d'%(self.id, self.voice, self.pitchOffset, self.velocityOffset)

    def verify(self):
        pass

    def update(self, pulse):
        # skip note generation
        pass

    def harmonize(self, at, n, v, d):
        self.mknote(at, n + self.pitchOffset, v + self.velocityOffset, d)


class Step:
    def __init__(self, p, d, v):
        self.pitch = p
        self.duration = d
        self.velocity = v
    def dump(self):
        print '    Step: %s %0.2f %d'%(('.' if self.pitch==sys.maxint else str(self.pitch)), self.duration, self.velocity)

class Loop(Voice):
    def __init__(self, i, p):
        Voice.__init__(self, i, p)
        self.steps = []
        self.curStep = -1

    # arguments are strings, since some of them might be a dot (representing a
    # rest or carry) or undefined (representing a carry)
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

    def update(self, pulse):
        if pulse >= self.nextNote:
            self.curStep = (self.curStep + 1)%len(self.steps)
            dur = self.gen_note(pulse)
            self.nextNote = pulse + dur

    def gen_note(self, at):
        step = self.steps[self.curStep]
        d = step.duration * self.player.ppb
        if step.pitch == sys.maxint:
            # this is a rest, so don't play a note and just return the time of the next note.
            return d

        p = self.offset + self.scale.root + step.pitch
        self.mknote(at, p, step.velocity, d)

        for h in self.harmonies:
            h.harmonize(at, p, step.velocity, d)

        return d


