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
        return '%dv%d'%(self.pitch, self.velocity)
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
        self.pitcher, self.pitcherLabel, self.pitcherValues = generators.make_generator(('$SCALAR', 1))
        self.durationer, self.durationerLabel, self.durationerValues = generators.make_generator(('$SCALAR', consts.DEFAULT_PULSES_PER_BEAT))
        self.velocitier, self.velocitierLabel, self.velocitierValues = generators.make_generator(('$SCALAR', 64))
        self.status = ''
        self.curNote = None
        self.nextPulse = 0

    def dump(self):
        print 'VOICE "%s": channel %d'%(self.id, self.channel)
        if self.follow:
            print '    following %s'%self.follow.id
        if self.transpose:
            print '    transpose by %d'%self.transpose
        if not self.follow:
            print '    pitch = %s'%self.pitcherLabel
            print '    duration = %s'%self.durationerLabel
        print '    velocity = %s'%self.velocitierLabel

    def set_pitcher(self, data):
        g,d,v = generators.make_generator(data, lambda x: scale.ScaleDegree(x))
        if g:
            self.pitcher = g
            self.pitcherLabel = d
            self.pitcherValues = v

    def set_durationer(self, data):
        g,d,v = generators.make_generator(data, lambda x: self.player.parse_duration(x))
        if g:
            self.durationer = g
            self.durationerLabel = d
            self.durationerValues = v

    def set_velocitier(self, data):
        g,d,v = generators.make_generator(data, lambda x: int(x))
        if g:
            self.velocitier = g
            self.velocitierLabel = d
            self.velocitierValues = v

    def update(self, pulse):
        if self.curNote and not self.curNote.is_rest() and pulse >= self.curNote.until:
            self.end_cur_note()
        if self.follow:
            if self.follow.curNote != self.followNote:
                self.followNote = self.follow.curNote
                note = self.follow_along(pulse)
                if note:
                    self.play(note)
        else:
            if pulse >= self.nextPulse:
                note = self.make_note(pulse)
                if note:
                    self.play(note)

    def make_note(self, at):
        d = self.durationer.next()
        p = 0
        v = 0
        if d < 0:
            d = abs(d)
            # whatever, this is a rest so nothing will play, we just need a valid value
            p = self.transpose + self.pitcherValues[0].get_pitch(self.player.curScale)
        else:
            p = self.transpose + self.pitcher.next().get_pitch(self.player.curScale)
            v = self.velocitier.next()
        rv = Note(at, d, p, v)
        return rv

    def follow_along(self, at):
        d = self.followNote.duration
        p = self.followNote.pitch + self.transpose
        v = self.followNote.velocity + self.velocitier.next()
        v = clamp(v, 0, 127)
        if p >= 0 and p <= 127:
            return Note(at, d, p, v)

    def play(self, note):
        self.curNote = note
        self.nextPulse = note.until
        if not note.is_rest():
            self.player.play(note.pitch, note.velocity)
        if self.curNote:
            if not self.curNote.is_rest():
                self.status = str(self.curNote)
            else:
                self.status = ''

    def end_cur_note(self):
        self.player.play(self.curNote.pitch, 0)
        self.curNote = None
        self.status = ''

