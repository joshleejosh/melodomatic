import sys, random
import consts, generators
from util import *

class Control:
    def __init__(self, id, pl):
        self.id = id
        self.player = pl
        self.rng = random.Random()
        self.set_seed(self.player.rng.random())
        self.channel = 0
        self.pulse = 0
        self.nextPulse = 0
        self.status = ''
        self.parameters = {}
        self.set_parameter('RATE', ('1',))

    def dump(self):
        print 'CONTROL "%s"'%self.id
        print '    channel %d'%self.channel
        print '    seed %s'%self.rngSeed
        for n,i in self.parameters.iteritems():
            print '    %s: %s'%(n, i)

    def set_seed(self, sv):
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def set_parameter(self, pname, data):
        if pname == 'CID':
            pname = 'CONTROL_ID'
        if pname == 'CVAL':
            pname = 'CONTROL_VALUE'
        g = generators.bind_generator(data, self.player)
        if g:
            self.parameters[pname] = g
            return g.name

    def update(self, pulse):
        self.pulse = pulse
        self.status = ''
        if pulse >= self.nextPulse:
            self.nextPulse = self.pulse + self.player.parse_duration(self.parameters['RATE'].next())
            self.set_control()

    def set_control(self):
        if 'CONTROL_ID' in self.parameters and 'CONTROL_VALUE' in self.parameters:
            cid = int(self.parameters['CONTROL_ID'].next())
            cval = int(self.parameters['CONTROL_VALUE'].next())
            self.player.midi.control(self.channel, cid, cval)

        if 'PITCHBEND' in self.parameters:
            p = self.parameters['PITCHBEND']
            bend = int(p.next())
            self.player.midi.pitchbend(self.channel, bend)

        if 'AFTERTOUCH' in self.parameters:
            p = self.parameters['AFTERTOUCH']
            touch = int(p.next())

            if 'VOICE' in self.parameters:
                voice = self.player.voices[self.parameters['VOICE'].next()]
                note = voice.curNote
                if note and note.velocity > 0:
                    self.player.midi.aftertouch_note(self.channel, note.pitch, touch)
            else:
                self.player.midi.aftertouch_channel(self.channel, touch)

