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
        self.parameters['CONTROL_ID'] = []
        self.parameters['CONTROL_VALUE'] = []
        self.set_parameter('RATE', ('1',))

    def __eq__(self, o):
        if not o: return False
        if self.id != o.id: return False
        #if self.rngSeed != o.rngSeed: return False
        if self.channel != o.channel: return False
        a, r, m, s = dict_compare(self.parameters, o.parameters)
        if a or r or m: return False
        # Don't check player or current time; we expect those to be different.
        return True

    def __ne__(self, o):
        return not self.__eq__(o)

    def dump(self):
        print 'CONTROL "%s"'%self.id
        print '    channel %d'%self.channel
        print '    seed %s'%self.rngSeed
        for n,i in self.parameters.iteritems():
            if n in ('CONTROL_ID','CONTROL_VALUE'):
                print '    %s: %s'%(n, list(str(j) for j in i))
            else:
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
            if pname in ('CONTROL_ID','CONTROL_VALUE'):
                self.parameters[pname].append(g)
            else:
                self.parameters[pname] = g
            return g.name

    def update(self, pulse):
        self.pulse = pulse
        self.status = ''
        if pulse >= self.nextPulse:
            rate = self.parameters['RATE'].next()
            self.nextPulse = self.pulse + self.player.parse_duration(rate)[0]
            self.set_control()

    def set_control(self):
        statii = []
        if ('CONTROL_ID' in self.parameters 
                and 'CONTROL_VALUE' in self.parameters):
            n = min(len(self.parameters['CONTROL_ID']),
                    len(self.parameters['CONTROL_VALUE']))
            for i in range(n):
                cid = int(self.parameters['CONTROL_ID'][i].next())
                cval = int(self.parameters['CONTROL_VALUE'][i].next())
                cval = clamp(cval, 0, 127)
                self.player.midi.control(self.channel, cid, cval)
                statii.append('c%d=%d'%(cid, cval))

        if 'PITCHBEND' in self.parameters:
            p = self.parameters['PITCHBEND']
            bend = int(p.next())
            self.player.midi.pitchbend(self.channel, bend)
            statii.append('pb=%d'%bend)

        if 'AFTERTOUCH' in self.parameters:
            p = self.parameters['AFTERTOUCH']
            touch = int(p.next())

            if 'VOICE' in self.parameters:
                voice = self.player.voices[self.parameters['VOICE'].next()]
                note = voice.curNote
                if note and note.velocity > 0:
                    self.player.midi.aftertouch_note(self.channel,
                            note.pitch, touch)
                    statii.append('a=%d'%touch)
            else:
                self.player.midi.aftertouch_channel(self.channel, touch)
                statii.append('a=%d'%touch)
        self.status = ','.join(statii)

    def panic(self):
        self.nextPulse = self.pulse

