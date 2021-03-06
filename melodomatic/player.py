import math, random, time
import consts
from util import *
import generators, voice, scale, midi

# I am the top-level updater, and I also own the MIDI connection.
# I am configured by a Reader.
class Player:
    def __init__(self):
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
        print 'Player: %d bpm, %d ppb, %f pulse time'%(self.bpm, self.ppb, self.pulseTime)
        print '    port %s'%self.midiPortName
        print '    seed %s'%self.rngSeed
        for sc in self.scaleOrder:
            self.scales[sc].dump()
        for vo in self.voiceOrder:
            self.voices[vo].dump()
        for co in self.controlOrder:
            self.controls[co].dump()

    def set_seed(self, sv):
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def transfer_state(self, old):
        copiedMidi = False
        if (old.midi.is_open()):
            self.midi = old.midi
            copiedMidi = True
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
            print 'Transferred state from old player: pulse=%d, next change=%d'%(self.pulse, self.nextScaleChange)

    def add_scale(self, s):
        if s not in self.scales.values():
            s.player = self
            self.scales[s.id] = s
            self.scaleOrder.append(s.id)
            if not self.curScale:
                self.curScale = s

    def add_voice(self, v):
        if v not in self.voices.values():
            v.player = self
            self.voices[v.id] = v
            self.voiceOrder.append(v.id)

    def add_control(self, c):
        if c not in self.controls.values():
            c.player = self
            self.controls[c.id] = c
            self.controlOrder.append(c.id)

    def is_valid(self):
        rv = True
        if not self.voices:
            rv = False
        if not self.scales:
            rv = False
        return rv

    def change_tempo(self, bpm, ppb):
        self.bpm = bpm
        self.ppb = ppb
        self.pulseTime = 60.0 / self.bpm / self.ppb

    def play(self, ch, n, v):
        # note-off is sent as a note-on with velocity 0.
        self.midi.note_on(ch, n, v)

    def startup(self):
        if not self.is_valid():
            return
        self.resolve_solos()
        self.midi.open(self.midiPortName)
        self.pulse = 0
        if self.startScale and self.startScale in self.scaleOrder:
            self.change_scale(self.startScale)
        else:
            self.change_scale(self.scaleOrder[0])
        for v in self.voices.itervalues():
            if not v.mute:
                v.begin(self.pulse)
        if consts.VERBOSE:
            print 'starting up'

    def shutdown(self):
        if consts.VERBOSE:
            print 'shutting down'
        for v in self.voices.itervalues():
            if v.curNote:
                v.release_cur_note();
        self.midi.close()

    def tick(self):
        self.pulse += 1

    def update(self):
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
        newScale = self.curScale
        if ns in self.scales:
            newScale = self.scales[ns]
        if newScale != self.curScale:
            self.curScale = newScale
        self.curScale.begin(self.pulse)

    def change_voice(self, ovid, nvid):
        if ovid == nvid:
            return
        self.voices[ovid].mute = True
        if self.voices[nvid].mute:
            self.voices[nvid].begin(self.pulse)

    # If one voice is flagged with .solo, mute all other voices.
    def resolve_solos(self):
        dosolo = False
        for voice in self.voices.itervalues():
            if voice.solo:
                dosolo = True
        if dosolo:
            for voice in self.voices.itervalues():
                if not voice.solo:
                    voice.set_mute(True)

    def panic(self):
        for voice in self.voices.itervalues():
            voice.panic()
        for control in self.controls.itervalues():
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

    # returns a 2-tuple containing a duration and an optional hold time.
    # if hold is not specified, it will match duration.
    def parse_duration(self, code):
        a = code.strip().split(',')
        d = a[0] if len(a) > 0 else '0'
        d = self._parse_duration_code(d)
        h = a[1] if len(a) > 1 else str(d)+'p'
        h = self._parse_duration_code(h)
        h = min(h, d)
        if d > 0 and h < 0:
            h = d
        return d, h

