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
        #return '%s.%d'%(note_name(self.pitch), self.velocity)
        return '%d_%d'%(self.pitch, self.velocity)
        #return '%dv%dd%d(%d-%d)'%(self.pitch, self.velocity, self.duration, self.at, self.until)
    def is_rest(self):
        return (self.velocity == 0)



# I am responsible for generating actual notes to play.
class Voice:
    def __init__(self, id, pl):
        self.id = id
        self.player = pl
        self.channel = 1
        self.status = ''
        self.curNote = None
        self.pulse = 0
        self.nextPulse = 0
        self.generator = None
        self.generatorName = ''
        self.parameters = {}
        bind_voice_generator(self, 'MELODOMATIC')

    def dump(self):
        print 'VOICE "%s" : channel %d : generator %s '%(self.id, self.channel, self.generatorName)
        for n,i in self.parameters.iteritems():
            print '    %s: %s'%(n, i[1])

    def set_generator(self, gname):
        bind_voice_generator(self, gname)

    def set_parameter(self, data):
        pname = data[0].strip().upper()
        if self.generatorName:
            pname = autocomplete_voice_parameter(pname, self)
        data = data[1:]
        g,d = generators.bind_generator(data, self.player)
        if g:
            self.parameters[pname] = (g, d)

    def validate_generator(self):
        if not self.generator or not self.generatorName:
            if consts.VERBOSE:
                print 'ERROR: Voice [%s] has no generator'%self.id
                return False
        for parm in VOICE_GENERATORS[self.generatorName][1].iterkeys():
            if parm not in self.parameters:
                print 'ERROR: Voice [%s] is missing parameter [%s] for generator [%s]'%(self.id, parm, self.generatorName)
                return False
        return True

    def update(self, pulse):
        self.pulse = pulse
        self.status = ''
        if self.curNote and not self.curNote.is_rest():
            if pulse >= self.curNote.until:
                self.end_cur_note()
            else:
                self.status = '|' # holding a note
        if pulse >= self.nextPulse:
            note = self.generator.next()
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


# ############################################################################ #

VOICE_GENERATORS = { }
VOICE_GENERATORS_ORDERED = []

def register_voice_generator(name, fun, parms):
    name = name.strip().upper()
    VOICE_GENERATORS[name] = (fun, parms)
    VOICE_GENERATORS_ORDERED.append(name)

def autocomplete_voice_generator_name(n):
    n = n.strip().upper()
    rv = n
    for name in VOICE_GENERATORS_ORDERED:
        if name.startswith(n):
            return name
    if consts.VERBOSE:
        print 'ERROR: Bad generator name [%s]?'%n
    return n

def autocomplete_voice_parameter(n, v):
    n = n.strip().upper()
    if n[0] == '.':
        n = n[1:]
    gtype = 'MELODOMATIC'
    if v and v.generatorName:
        gtype = autocomplete_voice_generator_name(v.generatorName)
    for parm in VOICE_GENERATORS[gtype][1].iterkeys():
        if parm.startswith(n):
            return parm
    if consts.VERBOSE:
        print 'ERROR: Bad generator parameter [%s] for [%s]?'%(n, gtype)
    return n

def bind_voice_generator(voice, gtype):
    if not gtype:
        gtype = 'MELODOMATIC'
    elif gtype[0] == '$':
        gtype = gtype[1:]
    gtype = autocomplete_voice_generator_name(gtype)
    if gtype in VOICE_GENERATORS:
        gspec = VOICE_GENERATORS[gtype]
        voice.generatorName = gtype
        voice.generator = gspec[0](voice)
        voice.parameters.clear()
        for key,default in gspec[1].iteritems():
            data = [key,]
            data.extend(default)
            voice.set_parameter(data)
        return (voice.generator, voice.generatorName)
    if consts.VERBOSE:
        print 'ERROR: Bad voice generator [%s]'%gtype
    return (None, '')


# ############################################################################ #

def g_melodomatic(vo):
    pitcher = vo.parameters['PITCH'][0]
    durationer = vo.parameters['DURATION'][0]
    velocitier = vo.parameters['VELOCITY'][0]
    transposer = vo.parameters['TRANSPOSE'][0]
    while True:
        d = vo.player.parse_duration(durationer.next())
        p = 0
        v = 0
        if d < 0:
            d = abs(d)
            # whatever, this is a rest so nothing will play, we don't even really need a valid value
            p = int(transposer.next()) + vo.player.curScale.get_pitch(0)
        else:
            p = int(transposer.next()) + vo.player.curScale.degree_to_pitch(pitcher.next())
            v = int(velocitier.next())
        yield Note(vo.pulse, d, p, v)

register_voice_generator('MELODOMATIC', g_melodomatic,
        {
            'TRANSPOSE': ('0',),
            'PITCH': ('1',),
            'DURATION': ('1',),
            'VELOCITY': ('64',),
        })


# Play whatever the voice I'm following is currently playing.
# The following voice must come *after* the voice it wants to follow in script.
# As long as nothing throws off their timing, this should stay in unison with the other voice.
def g_unison(vo):
    voicer = vo.parameters['VOICE'][0]
    transposer = vo.parameters['TRANSPOSE'][0]
    velocitier = vo.parameters['VELOCITY'][0]
    while True:
        vn = voicer.next()
        if vn not in vo.player.voices:
            # don't know what to do, emit a rest
            yield vo.Note(vo.pulse, self.player.parse_duration('1'), 1, 0)
        vf = vo.player.voices[vn]
        notef = vf.curNote
        d = notef.duration
        p = notef.pitch + int(transposer.next())
        v = notef.velocity + int(velocitier.next())
        v = clamp(v, 0, 127)
        if p >= 0 and p <= 127:
            yield Note(vo.pulse, d, p, v)

register_voice_generator('UNISON', g_unison,
        {
            'VOICE': ('X',),
            'TRANSPOSE': ('0',),
            'VELOCITY': ('0',),
        })

