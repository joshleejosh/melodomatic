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
        self.nextPulse = 0
        self.scale = None
        self.playing = False
        self.state = ''

    def validate(self):
        pass

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.offset, self.durations, self.velocities)

    def update(self, pulse):
        if pulse >= self.nextPulse:
            self.gen_note(pulse)
            b = self.rnddur()
            self.nextPulse = pulse + b

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

    def gen_note(self, at, n=-1, d=-1):
        if not self.scale:
            return
        note = 0
        if n >= 0:
            note = self.offset + self.scale.get_pitch(n)
        else:
            note = self.offset + self.scale.next_pitch()
        dur = 0
        if d >= 0:
            dur = d * self.player.ppb
        else:
            dur = self.rnddur()

        if (rnd.random() < self.player.velocityChangeChance):
            self.change_velocity()

        # a note-off is just a note-on with velocity 0.
        self.queue.append({ 'when':at+dur, 'note':note, 'velocity':0 })
        self.queue.append({ 'when':at,     'note':note, 'velocity':self.velocity })

    def change_velocity(self):
        if len(self.velocities) == 0:
            self.velocity = consts.DEFAULT_VELOCITY
            return
        if self.velocity not in self.velocities:
            self.velocity = rnd.choice(self.velocities)
            return

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

    def new_scale(self, sc):
        self.scale = sc

    def rnddur(self):
        if not self.durations:
            return self.player.ppb
        return int(rnd.choice(self.durations) * self.player.ppb)

