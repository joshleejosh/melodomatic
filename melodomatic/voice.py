import sys, random
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
        self.rng = random.Random()
        self.set_seed(self.player.rng.random())
        self.channel = 0
        self.status = ''
        self.curNote = None
        self.pulse = 0
        self.nextPulse = 0
        self.generator = None
        self.parameters = {}
        bind_voice_generator(self, 'MELODOMATIC')

    def __eq__(self, o):
        if not o: return False
        if self.id != o.id: return False
        if self.channel != o.channel: return False
        #if self.rngSeed != o.rngSeed: return False
        if self.generator != o.generator: return False
        a, r, m, s = dict_compare(self.parameters, o.parameters)
        if a or r or m: return False
        # don't check player or time, we expect that to be different.
        return True

    def __ne__(self, o):
        return not self.__eq__(o)

    def dump(self):
        print 'VOICE "%s" : generator %s '%(self.id, self.generator.name)
        print '    channel %d'%self.channel
        print '    seed %s'%self.rngSeed
        for n,i in self.parameters.iteritems():
            print '    %s: %s'%(n, i)

    def set_seed(self, sv):
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def set_generator(self, gname):
        bind_voice_generator(self, gname)

    def set_parameter(self, data):
        pname = data[0].strip().upper()
        if self.generator:
            pname = autocomplete_voice_parameter(pname, self)
            if not pname:
                return ''
        data = data[1:]
        g = generators.bind_generator(data, self)
        if g:
            self.parameters[pname] = g
            return pname

    def validate_generator(self):
        if not self.generator:
            if consts.VERBOSE:
                print 'ERROR: Voice [%s] has no generator'%self.id
                return False
        for parm in VOICE_GENERATORS[self.generator.name][1].iterkeys():
            if parm not in self.parameters:
                print 'ERROR: Voice [%s] is missing parameter [%s] for generator [%s]'%(self.id, parm, self.generator)
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
            self.player.play(self.channel, note.pitch, note.velocity)
            self.status = str(self.curNote)
        else:
            self.status = ''

    def end_cur_note(self):
        self.player.play(self.channel, self.curNote.pitch, 0)
        self.curNote = None


# ############################################################################ #

class VoiceGenerator:
    def __init__(self, n, v):
        self.name = n
        self.parameters = VOICE_GENERATORS[self.name][1].keys()
        self.voice = v
        self._f = VOICE_GENERATORS[self.name][0](v)
    def __eq__(self, o):
        if not o: return False
        if self.name != o.name: return False
        if self.parameters != o.parameters: return False
        # don't check the voice, we expect that to be different.
        return True
    def __ne__(self, o):
        return not self.__eq__(o)
    def __str__(self):
        return '$%s'%self.name
    def __iter__(self):
        return self
    def next(self):
        return self._f.next()

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
        print 'ERROR: Bad voice generator name [%s]?'%n
    return n

def autocomplete_voice_parameter(n, v):
    n = n.strip().upper()
    if n[0] == '.':
        n = n[1:]
    gtype = 'MELODOMATIC'
    if v and v.generator:
        gtype = v.generator.name
    for parm in VOICE_GENERATORS[gtype][1].iterkeys():
        if parm.startswith(n):
            return parm
    if consts.VERBOSE:
        #print 'ERROR: Bad generator parameter [%s] for [%s]?'%(n, gtype)
        return ''
    return n

def bind_voice_generator(voice, gtype):
    if not gtype:
        gtype = 'MELODOMATIC'
    elif gtype[0] == '$':
        gtype = gtype[1:]
    gtype = autocomplete_voice_generator_name(gtype)
    if gtype not in VOICE_GENERATORS:
        if consts.VERBOSE:
            print 'ERROR: Bad voice generator [%s]'%gtype
        return (None, '')
    gspec = VOICE_GENERATORS[gtype]
    voice.generator = VoiceGenerator(gtype, voice)
    voice.parameters.clear()
    for key,default in gspec[1].iteritems():
        data = [key,]
        data.extend(default)
        voice.set_parameter(data)
    return voice.generator


# ############################################################################ #

def g_melodomatic(vo):
    pitcher = vo.parameters['PITCH']
    durationer = vo.parameters['DURATION']
    velocitier = vo.parameters['VELOCITY']
    transposer = vo.parameters['TRANSPOSE']
    while True:
        d = vo.player.parse_duration(durationer.next())
        p = 1
        v = 0
        if d < 0:
            d = abs(d)
        else:
            t = int(transposer.next())
            p = vo.player.curScale.degree_to_pitch(pitcher.next())
            p = clamp(p+t, 0, 127)
            v = int(velocitier.next())
            v = clamp(v, 0, 127)
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
    voicer = vo.parameters['VOICE']
    transposer = vo.parameters['TRANSPOSE']
    velocitier = vo.parameters['VELOCITY']
    while True:
        vn = voicer.next()
        if vn not in vo.player.voices:
            # don't know what to do, emit a rest
            yield Note(vo.pulse, 1, 1, 0)
            continue
        vf = vo.player.voices[vn]
        notef = vf.curNote
        if not notef:
            yield Note(vo.pulse, 1, 1, 0)
            continue
        d = notef.duration
        p = notef.pitch + int(transposer.next())
        p = clamp(p, 0, 127)
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

