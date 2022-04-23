"""
A Voice is responsible for picking out notes to play.

The Voice is driven by generator functions, which are bound through a VoiceGenerator object.

See doc/03-voice for details.
"""

import random
from melodomatic import consts, generators
from melodomatic.util import *

# pylint: disable=stop-iteration-return # lots of false positives in generators

class Note:
    """ I represent a playable MIDI note. """

    def __init__(self, a, d, p, v, h):
        """ Initialize me. """
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
        """ Return True if this is a rest, i.e., the velocity is 0. """
        return self.velocity == 0

class Rest(Note):
    """ I am a Note that is actually a rest. """
    def __init__(self, a, d):
        """ Initialize this as a Note with velocity 0. """
        Note.__init__(self, a, d, 1, 0, d)


class Voice:
    """ I am responsible for generating actual notes to play. """
    def __init__(self, vid, pl):
        self.id = vid
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
        if not o:
            return False
        if self.id != o.id:
            return False
        if self.channel != o.channel:
            return False
        #if self.rngSeed != o.rngSeed:
        #    return False
        if self.mute != o.mute:
            return False
        if self.moveTimer != o.moveTimer:
            return False
        if self.moveLinker != o.moveLinker:
            return False
        if self.generator != o.generator:
            return False
        a, r, m, _ = dict_compare(self.parameters, o.parameters)
        if a or r or m:
            return False
        # don't check player or time, we expect them to be different.
        return True

    def __ne__(self, o):
        return not self.__eq__(o)

    def dump(self):
        """ Print debug info to stdout. """
        print('VOICE "%s" : generator %s '%(self.id, self.generator.name))
        print('    channel %d'%self.channel)
        print('    seed %s'%self.rngSeed)
        if self.mute:
            print('    muted!')
        for n,i in list(self.parameters.items()):
            print('    %s: %s'%(n, i))
        if self.moveTimer:
            print('    move time = %s'%self.moveTimer)
        if self.moveLinker:
            print('    move link = %s'%self.moveLinker)

    def set_seed(self, sv):
        """ Initialize my RNG. """
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def set_mute(self, m):
        """ Set my mute flag. If I am muting, unset my solo flag. """
        if m and self.solo:
            self.set_solo(False)
        self.mute = m

    def set_solo(self, s):
        """ Set my solo flag. If I am soloing, unset my mute flag. """
        if s and self.mute:
            self.set_mute(False)
        self.solo = s

    def set_move_timer(self, data):
        """
        Bind a generator function that will tell me when it's time to shift to a new voice.

        If data is not provided, set up a scalar generator that just returns DEFAULT_MOVE_TIME.
        """
        if not data:
            data = (consts.DEFAULT_MOVE_TIME,)
        g = generators.bind_generator(data, self)
        if g:
            self.moveTimer = g

    def set_move_linker(self, data):
        """
        Bind a generator function that will tell me what voice to move to when it's time.
        """
        if not data:
            data = (self.id,)
        g = generators.bind_generator(data, self)
        if g:
            self.moveLinker = g

    def set_generator(self, gname):
        """
        Bind a generator function that will tell me what notes to play.
        """
        bind_voice_generator(self, gname)

    def set_parameter(self, data):
        """
        Bind a generator function that will generate parameter values for my voice generator.
        """
        pname = data[0].strip().upper()
        if self.generator:
            pname = autocomplete_voice_parameter(pname, self)
        data = data[1:]
        g = generators.bind_generator(data, self)
        if g:
            self.parameters[pname] = g
        return pname

    def validate_generator(self):
        """
        Make sure that I have a voice generator, as well as generators for each parameter in my voice generator's spec.
        """
        if not self.generator:
            if consts.VERBOSE:
                print('ERROR: Voice [%s] has no generator'%self.id)
            return False
        for parm in list(VOICE_GENERATORS[self.generator.name][1].keys()):
            if parm not in self.parameters:
                print('ERROR: Voice [%s] is missing parameter [%s] for generator [%s]'%(self.id, parm, self.generator))
                return False
        return True

    def begin(self, pulse):
        """ Prime myself for running. """
        self.mute = False
        self.pulse = pulse
        self.changeTime = self.pulse + self.player.parse_duration(next(self.moveTimer))[0]
        self.status = self.id
        #if consts.VERBOSE:
        #    print('Begin voice %s at %d, change at %d'%(self.id, self.pulse, self.changeTime))

    def update(self, pulse):
        """
        On each pulse, play notes as needed.
        """
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
            self.changeTime = self.pulse + self.player.parse_duration(next(self.moveTimer))[0]
            nid = next(self.moveLinker)
            if nid != self.id:
                return nid

        if pulse >= self.nextPulse:
            note = next(self.generator)
            if note:
                self.play(note)
        return ''

    def play(self, note):
        """
        Notify my parent Player of a note to play.
        """
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
        """
        Tell my parent Player to release a note, i.e., stop playing it.
        """
        self.player.play(self.channel, self.curNote.pitch, 0)
        self.curNote.playing = False

    def end_cur_note(self):
        """
        Clear my current note. Also release it if needed.
        """
        if self.curNote and self.curNote.playing:
            self.release_cur_note()
        self.curNote = None

    def panic(self):
        """ Force the current note to end and force a new one on the next pulse. """
        self.end_cur_note()
        self.nextPulse = self.pulse


# ############################################################################ #

class VoiceGenerator:
    """
    I wrap a generator function and know about what parameters it needs,
    as well as what Voice it is currently bound to.
    """

    def __init__(self, n, v):
        """ Look up a generator by name and bind it to a voice. """
        self.name = n
        self.parameters = list(VOICE_GENERATORS[self.name][1].keys())
        self.voice = v
        self._f = VOICE_GENERATORS[self.name][0](v)
    def __eq__(self, o):
        if not o:
            return False
        if self.name != o.name:
            return False
        if self.parameters != o.parameters:
            return False
        # don't check the voice, we expect that to be different.
        return True
    def __ne__(self, o):
        return not self.__eq__(o)
    def __str__(self):
        return '$%s'%self.name
    def __iter__(self):
        return self
    def __next__(self):
        return next(self._f)

# The master dictionary of known voice generator functions.
VOICE_GENERATORS = { }

# The same keys as in VOICE_GENERATORS, but sorted in order of registration.
VOICE_GENERATORS_ORDERED = []

def register_voice_generator(name, fun, parms):
    """ Register a new generator function in the master dictionary. """
    name = name.strip().upper()
    VOICE_GENERATORS[name] = (fun, parms)
    VOICE_GENERATORS_ORDERED.append(name)

def autocomplete_voice_generator_name(n):
    """ Look up a partial generator name in the main dictionary and return its normalized form. """
    n = n.strip().upper()
    for name in VOICE_GENERATORS_ORDERED:
        if name.startswith(n):
            return name
    if consts.VERBOSE:
        print('ERROR: Bad voice generator name [%s]?'%n)
    return n

def autocomplete_voice_parameter(n, v):
    """ Look up a partial voice parameter name for the voice's current generator, and return its normalized form. """
    n = n.strip().upper()
    if n[0] == '.':
        n = n[1:]
    gtype = 'MELODOMATIC'
    if v and v.generator:
        gtype = v.generator.name
    for parm in list(VOICE_GENERATORS[gtype][1].keys()):
        if parm.startswith(n):
            return parm
    #if consts.VERBOSE:
    #    print('ERROR: Bad generator parameter [%s] for [%s]?'%(n, gtype))
    return n

def bind_voice_generator(voice, gtype):
    """
    Look up a voice generator function, wrap it in a VoiceGenerator instance, and attach it to the voice.

    Mutates the voice's generator and parameters.
    """
    if not gtype:
        gtype = 'MELODOMATIC'
    elif gtype[0] == '$':
        gtype = gtype[1:]
    gtype = autocomplete_voice_generator_name(gtype)
    if gtype not in VOICE_GENERATORS:
        if consts.VERBOSE:
            print('ERROR: Bad voice generator [%s]'%gtype)
        return (None, '')
    gspec = VOICE_GENERATORS[gtype]
    voice.generator = VoiceGenerator(gtype, voice)
    voice.parameters.clear()
    for key,default in list(gspec[1].items()):
        data = [key,]
        data.extend(default)
        voice.set_parameter(data)
    return voice.generator


# ############################################################################ #

def g_melodomatic(vo):
    """ Let parameter generators for pitch, duration, velocity, and transpotion do all the work. """
    pitcher = vo.parameters['PITCH']
    durationer = vo.parameters['DURATION']
    velocitier = vo.parameters['VELOCITY']
    transposer = vo.parameters['TRANSPOSE']
    while True:
        d,h = vo.player.parse_duration(next(durationer))
        p = 1
        v = 0
        if d < 0 or h == 0:
            yield Rest(vo.pulse, abs(d))
        else:
            t = int(next(transposer))
            p = vo.player.curScale.degree_to_pitch(next(pitcher))
            p = clamp(p+t, 0, 127)
            v = int(next(velocitier))
            v = clamp(v, 0, 127)
            yield Note(vo.pulse, d, p, v, h)

register_voice_generator('MELODOMATIC', g_melodomatic,
        {
            'TRANSPOSE': ('0',),
            'PITCH': ('1',),
            'DURATION': ('1',),
            'VELOCITY': ('64',),
        })


def g_unscaled(vo):
    """
    Works like Melodomatic, but instead of picking notes out of a scale, it
    works off a direct list of MIDI note values, ignoring all scale logic and
    changes. Useful for drum patches or drones.
    """
    noter = vo.parameters['NOTE']
    durationer = vo.parameters['DURATION']
    velocitier = vo.parameters['VELOCITY']
    while True:
        d,h = vo.player.parse_duration(next(durationer))
        n = consts.DEFAULT_SCALE_ROOT
        v = 0
        if d < 0 or h == 0:
            yield Rest(vo.pulse, abs(d))
        else:
            n = int(next(noter))
            n = clamp(n, 0, 127)
            v = int(next(velocitier))
            v = clamp(v, 0, 127)
            yield Note(vo.pulse, d, n, v, h)

register_voice_generator('UNSCALED', g_unscaled,
        {
            'NOTE': (str(consts.DEFAULT_SCALE_ROOT),),
            'DURATION': ('1',),
            'VELOCITY': (str(consts.DEFAULT_VELOCITY),),
        })


def g_unison(vo):
    """
    Play whatever the voice I'm following is currently playing.
    The following voice must come *after* the voice it wants to follow in script.
    As long as nothing throws off their timing, this should stay in unison with the other voice.
    """
    voicer = vo.parameters['VOICE']
    transposer = vo.parameters['TRANSPOSE']
    velocitier = vo.parameters['VELOCITY']
    while True:
        vn = next(voicer)
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
        v = notef.velocity + int(next(velocitier))
        v = clamp(v, 0, 127)
        p = notef.pitch + int(next(transposer))
        if 0 <= p <= 127:
            yield Note(notef.at, d, p, v, h)
        else:
            yield Rest(notef.at, h)

register_voice_generator('UNISON', g_unison,
        {
            'VOICE': ('X',),
            'TRANSPOSE': ('0',),
            'VELOCITY': ('0',),
        })

