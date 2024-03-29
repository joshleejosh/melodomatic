"""
The Player is the top-level controller for the engine.
"""

import random
import time
from melodomatic import consts
from melodomatic.util import *
from melodomatic import midi

class Player:
    """
    I am the top-level updater, and I also own the MIDI connection.
    I am configured by a Reader.
    """

    def __init__(self):
        """ Initialize members. Creates but does not open a MIDI connection. """
        self.rng = random.Random()
        self.player = self # Generators frequently want a ref to their context's player, so make sure we match the interface.
        self.set_seed(time.time())
        self.scales = {}
        self.scaleOrder = []
        self.voices = {}
        self.voiceOrder = []
        self.controls = {}
        self.controlOrder = []
        self.change_tempo(consts.DEFAULT_BEATS_PER_MINUTE, consts.DEFAULT_PULSES_PER_BEAT)
        self.midi = midi.MelodomaticMidi()
        self.midiPortName = ''
        self.visualizationWindow = self.parse_duration(consts.DEFAULT_VISUALIZATION_WINDOW)[0]
        self.startScale = ''
        self.curScale = None
        self.pulse = 0
        self.nextScaleChange = 0

    def dump(self):
        """ Debug output. """
        print('Player: %d bpm, %d ppb, %f pulse time'%(self.bpm, self.ppb, self.pulseTime))
        print('    port %s'%self.midiPortName)
        print('    seed %s'%self.rngSeed)
        for sc in self.scaleOrder:
            self.scales[sc].dump()
        for vo in self.voiceOrder:
            self.voices[vo].dump()
        for co in self.controlOrder:
            self.controls[co].dump()

    def set_seed(self, sv):
        """ Initialize my RNG. """
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def transfer_state(self, old):
        """ Copy unchanged state from another player. """
        if old.midi.is_open():
            self.midi = old.midi
        else:
            old.shutdown()
            self.startup()
        self.pulse = old.pulse

        # Look for unchanged scales, voices, and controls
        for sid in self.scaleOrder:
            if sid in old.scales and self.scales[sid] == old.scales[sid]:
                self.scales[sid] = old.scales[sid]
                self.scales[sid].player = self
        for vid in self.voiceOrder:
            if vid in old.voices:
                if self.voices[vid] == old.voices[vid]:
                    self.voices[vid] = old.voices[vid]
                    self.voices[vid].player = self
                elif old.voices[vid].curNote:
                    old.voices[vid].release_cur_note()

        for cid in self.controlOrder:
            if cid in old.controls and self.controls[cid] == old.controls[cid]:
                self.controls[cid] = old.controls[cid]
                self.controls[cid].player = self

        # Preserve the current scale and change time, but only if it makes sense to.
        if old.curScale and old.curScale.id in self.scaleOrder and self.ppb == old.ppb:
            self.curScale = self.scales[old.curScale.id]
            self.nextScaleChange = old.nextScaleChange
        else:
            # use whatever scale and change time startup() decided on.
            pass
        if consts.VERBOSE:
            print('Transferred state from old player: pulse=%d, next change=%d'%(self.pulse, self.nextScaleChange))

    def add_scale(self, s):
        """ Add a Scale. """
        if s not in list(self.scales.values()):
            s.player = self
            self.scales[s.id] = s
            self.scaleOrder.append(s.id)
            if not self.curScale:
                self.curScale = s

    def add_voice(self, v):
        """ Add a Voice. """
        if v not in list(self.voices.values()):
            v.player = self
            self.voices[v.id] = v
            self.voiceOrder.append(v.id)

    def add_control(self, c):
        """ Add a Control. """
        if c not in list(self.controls.values()):
            c.player = self
            self.controls[c.id] = c
            self.controlOrder.append(c.id)

    def is_valid(self):
        """ True if I have at least one Voice and one Scale, the minimum state needed to produce notes. """
        rv = True
        if not self.voices:
            rv = False
        if not self.scales:
            rv = False
        return rv

    def change_tempo(self, bpm, ppb):
        """ Adjust the time of a pulse. """
        self.bpm = bpm
        self.ppb = ppb
        self.pulseTime = 60.0 / self.bpm / self.ppb

    def play(self, ch, n, v):
        """
        Send a note to the MIDI device.
        """
        # note-off is sent as a note-on with velocity 0.
        self.midi.note_on(ch, n, v)

    def startup(self):
        """
        Prime myself to start playing: open the MIDI channel, assign my opening scale, and prime voices.
        """
        if not self.is_valid():
            return
        self.resolve_solos()
        self.midi.open(self.midiPortName)
        self.pulse = 0
        if self.startScale and self.startScale in self.scaleOrder:
            self.change_scale(self.startScale)
        else:
            self.change_scale(self.scaleOrder[0])
        for v in list(self.voices.values()):
            if not v.mute:
                v.begin(self.pulse)
        if consts.VERBOSE:
            print('starting up')

    def shutdown(self):
        """
        Tear down resources and close MIDI.
        """
        if consts.VERBOSE:
            print('shutting down')
        for v in list(self.voices.values()):
            if v.curNote:
                v.release_cur_note()
        self.midi.close()

    def tick(self):
        """ Advance the pulse counter. Everything important happens in update(). """
        self.pulse += 1

    def update(self):
        """ Update the current Scale and Voice, or change them. """
        if self.curScale:
            nextid = self.curScale.update(self.pulse)
            if nextid:
                self.change_scale(nextid)

        # generate some notes and play them
        for vid in self.voiceOrder:
            nextid = self.voices[vid].update(self.pulse)
            if nextid and nextid != vid:
                # mute this voice and unmute the other.
                wasMute = self.voices[nextid].mute
                self.change_voice(vid, nextid)
                # if the new voice was already checked (and skipped because it
                # was muted), then we need to go back and update it asap.
                oseq = self.voiceOrder.index(vid)
                nseq = self.voiceOrder.index(nextid)
                if nseq < oseq and wasMute:
                    self.voices[nextid].update(self.pulse)

        for cid in self.controlOrder:
            self.controls[cid].update(self.pulse)

        return True

    def change_scale(self, ns):
        """ Attach and prime a new Scale. Argument is an ID. """
        newScale = self.curScale
        if ns in self.scales:
            newScale = self.scales[ns]
        if newScale != self.curScale:
            self.curScale = newScale
        self.curScale.begin(self.pulse)

    def change_voice(self, ovid, nvid):
        """ Attach and prime a new Voice. Arguments are IDs. """
        if ovid == nvid:
            return
        self.voices[ovid].mute = True
        if self.voices[nvid].mute:
            self.voices[nvid].begin(self.pulse)

    def resolve_solos(self):
        """ If any voices are flagged with .solo, mute all other voices. """
        dosolo = False
        for v in list(self.voices.values()):
            if v.solo:
                dosolo = True
        if dosolo:
            for v in list(self.voices.values()):
                if not v.solo:
                    v.set_mute(True)

    def panic(self):
        """ omg! Cut off Voices and Controls and force a new signal on the next pulse. """
        for voice in list(self.voices.values()):
            voice.panic()
        for control in list(self.controls.values()):
            control.panic()

    # Assumes the code has been split and scrubbed.
    def _parse_duration_code(self, d):
        if not d:
            return 0
        # 'b' is for 'beat', which is redundant (but is sometimes useful for clairty)
        if d[-1] == 'b':
            d = d[:-1]
        # 'p' is for 'pulse'
        if d[-1] == 'p':
            d = d[:-1]
            return int(d) if is_int(d) else 0
        if is_float(d):
            return int(float(d) * self.ppb)
        return 0

    def parse_duration(self, code):
        """
        Returns a 2-tuple containing a duration and an optional hold time.
        If hold is not specified, it will match duration.
        """
        a = code.strip().split(',')
        d = a[0] if len(a) > 0 else '0'
        d = self._parse_duration_code(d)
        h = a[1] if len(a) > 1 else str(d)+'p'
        h = self._parse_duration_code(h)
        h = min(h, d)
        # pylint: disable=chained-comparison # whaaaat
        if d > 0 and h < 0:
            h = d
        return d, h

