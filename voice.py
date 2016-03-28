import mido
import consts
from util import *

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

    def reset(self):
        self.playing = False
        self.scale = self.player.scaler.get_scale()
        self.change_velocity()

    def dump(self):
        print '%s: %d %s %s'%(self.id, self.offset, self.durations, self.velocities)

    def update(self, pulse, midi):
        if pulse >= self.nextPulse:
            self.gen_note(pulse)
            b = self.rnddur()
            self.nextPulse = pulse + b

        didon = False
        for i in range(len(self.queue)-1, -1, -1):
            q = self.queue[i]
            if q['when'] <= pulse:
                if q['event'] == 'note_on':
                    self.playing = True
                    self.state = '%s@%d'%(note_name(q['note']), q['velocity'])
                    didon = True
                if q['event'] == 'note_off':
                    if not didon:
                        self.state = ''
                        self.playing = False
                midi.send(mido.Message(q['event'], note=q['note'], velocity=q['velocity']))
                del self.queue[i]

    def gen_note(self, at, n=-1, d=-1):
        if not self.scale:
            return
        note = 0
        if n >= 0:
            note = self.offset + self.scale.get_note(n)
        else:
            note = self.offset + self.scale.next_note()
        dur = 0
        if d >= 0:
            dur = d * self.player.ppb
        else:
            dur = self.rnddur()

        if (rnd.random() < self.player.velocityChangeChance):
            self.change_velocity()

        self.queue.append({ 'when':at+dur, 'event':'note_off',  'note':note, 'velocity':self.velocity })
        self.queue.append({ 'when':at,     'event':'note_on',   'note':note, 'velocity':self.velocity })

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

