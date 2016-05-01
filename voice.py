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
        self.set_pitcher(('$SCALAR', '1'))
        self.set_durationer(('$SCALAR', '4'))
        self.set_velocitier(('$SCALAR', '64'))
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
        d = self.player.parse_duration(self.durationer.next())
        p = 0
        v = 0
        if d < 0:
            d = abs(d)
            # whatever, this is a rest so nothing will play, we just need a valid value
            p = self.transpose + self.player.curScale.get_pitch(0)
        else:
            p = self.transpose + self.player.curScale.parse_degree(self.pitcher.next())
            v = int(self.velocitier.next())
        rv = Note(at, d, p, v)
        return rv

    def follow_along(self, at):
        d = self.followNote.duration
        p = self.followNote.pitch + self.transpose
        v = self.followNote.velocity + int(self.velocitier.next())
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

