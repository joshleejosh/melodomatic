import sys
import consts, generators, scale
from util import *

# I represent a playable midi note.
class Note:
    def __init__(self, a, d, p, v):
        self.pitch = p
        self.velocity = v
        self.duration = d # This is always in pulses, NOT beats
        self.at = a
        self.until = self.at + self.duration
    def __str__(self):
        return '%s.%d'%(note_name(self.pitch), self.velocity)
        #return '%dv%d'%(self.pitch, self.velocity)
        #return '%dv%dd%d(%d-%d)'%(self.pitch, self.velocity, self.duration, self.at, self.until)
    def is_rest(self):
        return (self.velocity == 0)



# I am responsible for generating actual notes to play.
class Voice:
    def __init__(self, id, pl):
        self.id = id
        self.player = pl
        self.channel = 1
        self.follow = None
        self.followNote = None
        self.transpose = 0
        self.set_pitcher(('$SCALAR', '1'))
        self.set_durationer(('$SCALAR', '4'))
        self.set_velocitier(('$SCALAR', '64'))
        self.status = ''
        self.curNote = None
        self.pulse = 0
        self.nextPulse = 0
        self.noter = mknote(self)

    def dump(self):
        print 'VOICE "%s": channel %d'%(self.id, self.channel)
        if self.follow:
            print '    following %s'%self.follow
        if self.transpose:
            print '    transpose by %d'%self.transpose
        if not self.follow:
            print '    pitch = %s'%self.pitcherLabel
            print '    duration = %s'%self.durationerLabel
        print '    velocity = %s'%self.velocitierLabel

    def set_pitcher(self, data):
        g,d = generators.bind_generator(data, self.player)
        if g:
            self.pitcher = g
            self.pitcherLabel = d

    def set_durationer(self, data):
        g,d = generators.bind_generator(data, self.player)
        if g:
            self.durationer = g
            self.durationerLabel = d

    def set_velocitier(self, data):
        g,d = generators.bind_generator(data, self.player)
        if g:
            self.velocitier = g
            self.velocitierLabel = d

    def set_follow(self, data):
        self.follow = data[0]
        self.noter = mkfollow(self)

    def update(self, pulse):
        self.pulse = pulse
        self.status = ''
        if self.curNote and not self.curNote.is_rest():
            if pulse >= self.curNote.until:
                self.end_cur_note()
            else:
                self.status = '|' # holding a note
        if pulse >= self.nextPulse:
            note = self.noter.next()
            if note:
                self.play(note)

    def play(self, note):
        self.curNote = note
        if not note:
            self.nextPulse = self.player.pulse
            return
        self.nextPulse = note.until
        if not note.is_rest():
            self.player.play(note.pitch, note.velocity)
            self.status = str(self.curNote)
        else:
            self.status = ''

    def end_cur_note(self):
        self.player.play(self.curNote.pitch, 0)
        self.curNote = None

def mknote(voice):
    while True:
        d = voice.player.parse_duration(voice.durationer.next())
        p = 0
        v = 0
        if d < 0:
            d = abs(d)
            # whatever, this is a rest so nothing will play, we don't even really need a valid value
            p = voice.transpose + voice.player.curScale.get_pitch(0)
        else:
            p = voice.transpose + voice.player.curScale.degree_to_pitch(voice.pitcher.next())
            v = int(voice.velocitier.next())
        yield Note(voice.pulse, d, p, v)

# Play whatever the voice I'm following is currently playing.
# As long as nothing throws off the timing, this should stay in unison with the other voice.
def mkfollow(voice):
    while True:
        vf = voice.player.voices[voice.follow]
        notef = vf.curNote
        d = notef.duration
        p = notef.pitch + voice.transpose
        v = notef.velocity + int(voice.velocitier.next())
        v = clamp(v, 0, 127)
        if p >= 0 and p <= 127:
            yield Note(voice.pulse, d, p, v)

