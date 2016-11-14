import sys, random
import consts, generators, scale
from util import *

# I represent a playable midi note.
class Note:
    def __init__(self, a, d, p, v, h):
        self.at = a
        self.pitch = p
        self.velocity = v
        self.hold = h
        self.release = self.at + self.hold
        self.duration = d # This is always in pulses, NOT beats
        self.until = self.at + self.duration
        self.playing = False
    def __str__(self):
        #return '%s.%d'%(note_name(self.pitch), self.velocity)
        return '%d_%d'%(self.pitch, self.velocity)
        #return '%dv%dd%d(%d-%d)'%(self.pitch, self.velocity, self.duration, self.at, self.until)
    def is_rest(self):
        return (self.velocity == 0)

class Rest(Note):
    def __init__(self, a, d):
        Note.__init__(self, a, d, 1, 0, d)


# I am responsible for generating actual notes to play.
class Voice:
    def __init__(self, id, pl):
        self.id = id
        self.player = pl
        self.rng = random.Random()
        self.set_seed(self.player.rng.random())
        self.channel = 0
        self.mute = False
        self.solo = False
        self.set_move_timer([])
        self.set_move_linker([])
        self.status = ''
        self.curNote = None
        self.pulse = 0
        self.nextPulse = 0
        self.changeTime = 0
        self.generator = None
        self.parameters = {}
        bind_voice_generator(self, 'MELODOMATIC')

    def __eq__(self, o):
        if not o: return False
        if self.id != o.id: return False
        if self.channel != o.channel: return False
        #if self.rngSeed != o.rngSeed: return False
        if self.mute != o.mute: return False
        if self.moveTimer != o.moveTimer: return False
        if self.moveLinker != o.moveLinker: return False
        if self.generator != o.generator: return False
        a, r, m, s = dict_compare(self.parameters, o.parameters)
        if a or r or m: return False
        # don't check player or time, we expect them to be different.
        return True

    def __ne__(self, o):
        return not self.__eq__(o)

    def dump(self):
        print 'VOICE "%s" : generator %s '%(self.id, self.generator.name)
        print '    channel %d'%self.channel
        print '    seed %s'%self.rngSeed
        if self.mute:
            print '    muted!'
        for n,i in self.parameters.iteritems():
            print '    %s: %s'%(n, i)
        if self.moveTimer:
            print '    move time = %s'%self.moveTimer
        if self.moveLinker:
            print '    move link = %s'%self.moveLinker

    def set_seed(self, sv):
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def set_mute(self, m):
        self.mute = m

    def set_solo(self, s):
        self.solo = s

    def set_move_timer(self, data):
        if not data:
            data = (consts.DEFAULT_MOVE_TIME,)
        g = generators.bind_generator(data, self)
        if g:
            self.moveTimer = g

    def set_move_linker(self, data):
        if not data:
            data = (self.id,)
        g = generators.bind_generator(data, self)
        if g:
            self.moveLinker = g

    def set_generator(self, gname):
        bind_voice_generator(self, gname)

    def set_parameter(self, data):
        pname = data[0].strip().upper()
        if self.generator:
            pname = autocomplete_voice_parameter(pname, self)
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

    def begin(self, pulse):
        self.mute = False
        self.pulse = pulse
        self.changeTime = self.pulse + self.player.parse_duration(self.moveTimer.next())[0]
        self.status = self.id
        #if consts.VERBOSE:
        #    print 'Begin voice %s at %d, change at %d'%(self.id, self.pulse, self.changeTime)

    def update(self, pulse):
        self.pulse = pulse
        self.status = ''
        if self.curNote and not self.curNote.is_rest():
            if pulse >= self.curNote.release:
                self.release_cur_note()
            if pulse >= self.curNote.until:
                self.end_cur_note()
            if self.curNote and self.curNote.playing:
                self.status = '|' # holding a note

        if self.mute:
            return ''

        if self.pulse >= self.changeTime:
            self.changeTime = self.pulse + self.player.parse_duration(self.moveTimer.next())[0]
            nid = self.moveLinker.next()
            if nid != self.id:
                return nid

        if pulse >= self.nextPulse:
            note = self.generator.next()
            if note:
                self.play(note)
        return ''

    def play(self, note):
        self.curNote = note
        if not note:
            self.nextPulse = self.player.pulse
            return
        self.nextPulse = note.until
        if not note.is_rest():
            self.player.play(self.channel, note.pitch, note.velocity)
            note.playing = True
            self.status = str(self.curNote)
        else:
            self.status = ''

    def release_cur_note(self):
        self.player.play(self.channel, self.curNote.pitch, 0)
        self.curNote.playing = False

    def end_cur_note(self):
        if self.curNote.playing:
            self.release_cur_note()
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
    #if consts.VERBOSE:
    #    print 'ERROR: Bad generator parameter [%s] for [%s]?'%(n, gtype)
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
        d,h = vo.player.parse_duration(durationer.next())
        p = 1
        v = 0
        if d < 0 or h == 0:
            yield Rest(vo.pulse, abs(d))
        else:
            t = int(transposer.next())
            p = vo.player.curScale.degree_to_pitch(pitcher.next())
            p = clamp(p+t, 0, 127)
            v = int(velocitier.next())
            v = clamp(v, 0, 127)
            yield Note(vo.pulse, d, p, v, h)

register_voice_generator('MELODOMATIC', g_melodomatic,
        {
            'TRANSPOSE': ('0',),
            'PITCH': ('1',),
            'DURATION': ('1',),
            'VELOCITY': ('64',),
        })


# Works like Melodomatic, but instead of picking notes out of a scale, it works
# off a direct list of MIDI note values, ignoring all scale logic and changes.
# Useful for drum patches or drones.
def g_unscaled(vo):
    noter = vo.parameters['NOTE']
    durationer = vo.parameters['DURATION']
    velocitier = vo.parameters['VELOCITY']
    while True:
        d,h = vo.player.parse_duration(durationer.next())
        n = consts.DEFAULT_SCALE_ROOT
        v = 0
        if d < 0 or h == 0:
            yield Rest(vo.pulse, abs(d))
        else:
            n = int(noter.next())
            n = clamp(n, 0, 127)
            v = int(velocitier.next())
            v = clamp(v, 0, 127)
            yield Note(vo.pulse, d, n, v, h)

register_voice_generator('UNSCALED', g_unscaled,
        {
            'NOTE': (str(consts.DEFAULT_SCALE_ROOT),),
            'DURATION': ('1',),
            'VELOCITY': (str(consts.DEFAULT_VELOCITY),),
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
            # invalid voice, emit a rest
            yield Rest(vo.pulse, 1)
            continue
        vf = vo.player.voices[vn]
        notef = vf.curNote
        if not notef or vf.mute:
            # no note to mirror, emit a rest
            yield Rest(vo.pulse, 1)
            continue
        d = notef.duration
        h = notef.hold
        v = notef.velocity + int(velocitier.next())
        v = clamp(v, 0, 127)
        p = notef.pitch + int(transposer.next())
        if p >= 0 and p <= 127:
            yield Note(notef.at, d, p, v, h)
        else:
            yield Rest(notef.at, h)

register_voice_generator('UNISON', g_unison,
        {
            'VOICE': ('X',),
            'TRANSPOSE': ('0',),
            'VELOCITY': ('0',),
        })

