import consts, random, time
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
        self.change_tempo(consts.DEFAULT_BEATS_PER_MINUTE, consts.DEFAULT_PULSES_PER_BEAT)
        self.midi = midi.MelodomaticMidi()
        self.visualizationWindow = self.parse_duration(consts.DEFAULT_VISUALIZATION_WINDOW)
        self.startScale = ''
        self.curScale = None
        self.pulse = 0
        self.nextScaleChange = 0

    def dump(self):
        print 'Player: %d bpm, %d ppb, %f pulse time'%(self.bpm, self.ppb, self.pulseTime)
        print '    seed %s'%self.rngSeed
        for sc in self.scaleOrder:
            self.scales[sc].dump()
        for vo in self.voiceOrder:
            self.voices[vo].dump()

    def set_seed(self, sv):
        self.rngSeed = sv
        self.rng.seed(self.rngSeed)

    def transfer_state(self, old):
        old.shutdown()
        self.startup()
        self.pulse = old.pulse
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

    def add_voice(self, v):
        if v not in self.voices.values():
            v.player = self
            self.voices[v.id] = v
            self.voiceOrder.append(v.id)

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

    def play(self, n, v):
        # note-off is sent as a note-on with velocity 0.
        self.midi.note_on(n, v)

    def startup(self):
        if not self.is_valid():
            return
        self.midi.open()
        self.pulse = 0
        if self.startScale and self.startScale in self.scaleOrder:
            self.change_scale(self.startScale)
        else:
            self.change_scale(self.scaleOrder[0])
        if consts.VERBOSE:
            print 'starting up'

    def shutdown(self):
        if consts.VERBOSE:
            print 'shutting down'
        self.midi.close()

    def tick(self):
        self.pulse += 1

    def update(self):
        if self.curScale:
            self.curScale.update(self.pulse)

        # generate some notes and play them
        for vid in self.voiceOrder:
            self.voices[vid].update(self.pulse)

        return True

    def change_scale(self, ns):
        newScale = self.curScale
        if ns in self.scales:
            newScale = self.scales[ns]
        if newScale != self.curScale:
            self.curScale = newScale
            self.curScale.begin(self.pulse)

    def parse_duration(self, d):
        d = d.strip()
        if d[-1] == 'p' and is_float(d[:-1]):
            return float(d[:-1])
        if is_float(d):
            return float(d) * self.ppb
        return d

