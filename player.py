import time
import mido
import consts
from util import *
import voice, scale, reader

# I am the top level controller for the ScaleChanger, all Scales, and all Voices. 
# I am configured by a Reader.
class Player:
    def __init__(self):
        self.reader = None
        self.scaler = scale.ScaleChanger(self)
        self.voices = []
        self.change_tempo(consts.DEFAULT_BEATS_PER_MINUTE, consts.DEFAULT_PULSES_PER_BEAT)
        self.velocityChangeChance = consts.DEFAULT_VELOCITY_CHANGE_CHANCE
        self.statuses = []
        self.midi = None
        self.pulse = 0

    def dump(self):
        print 'Tempo: %d bpm, %d ppb, %f pulse time'%(self.bpm, self.ppb, self.pulseTime)
        self.scaler.dump()
        for vo in self.voices:
            vo.dump()

    def validate(self):
        self.scaler.validate()
        for v in self.voices:
            v.validate()
        # make sure pulseTime got reset
        self.change_tempo(self.bpm, self.ppb)
        # make sure voices have scales
        self.change_scale(self.scaler.scales[self.scaler.curScale])

    def is_valid(self):
        rv = True
        if not self.voices:
            rv = False
        if not self.scaler.scales:
            rv = False
        return rv

    def change_tempo(self, bpm, ppb):
        self.bpm = bpm
        self.ppb = ppb
        self.pulseTime = 60.0 / self.bpm / self.ppb

    def change_scale(self, newScale):
        for v in self.voices:
            # create separate instances of the scale, in case the note sequence involves keeping state.
            v.new_scale(newScale.clone())

    def play(self, n, v):
        # note-off is sent as a note-on with velocity 0.
        self.midi.send(mido.Message('note_on', note=n, velocity=v))

    def run(self):
        self.midi = mido.open_output()
        queue = []
        lastt = t = time.time()
        self.pulse = -1

        try:
            while True:
                # update time
                lastt = t
                t = time.time()
                dt = t - lastt
                self.pulse += 1

                # check for a file change
                if self.reader:
                    self.reader.update(self.pulse)
                    if not self.is_valid(): # game over
                        if consts.VERBOSE:
                            print 'End via empty script'
                        break

                # check for a scale change
                self.scaler.update(self.pulse)

                # generate some notes...
                for voice in self.voices:
                    voice.update(self.pulse)
                # ... and play them!
                for voice in self.voices:
                    voice.play(self.pulse)

                if not consts.QUIET:
                    self.update_status()

                # wait for next pulse
                nextt = t + self.pulseTime
                waitt = nextt - time.time()
                time.sleep(waitt)

        except KeyboardInterrupt:
            if consts.VERBOSE:
                print 'End via ^C'
            pass
        except:
            self.shutdown()
            raise

        self.shutdown()

    def shutdown(self):
        if self.midi:
            self.midi.reset()
            time.sleep(1.0)
            self.midi.close()
        self.midi = None

    # Update the status string and print it out.
    def update_status(self):
        newstats = [ self.scaler.state, ]
        for v in self.voices:
            newstats.append(v.state)

        doit = False
        s = '%06d'%self.pulse
        for i in xrange(len(newstats)):
            # Try not to repeat status messages.
            if i < len(self.statuses) and self.statuses[i] == newstats[i]:
                if i==0 or not newstats[i]:
                    s += str.center('', 12)
                else:
                    s += str.center('|', 12)
            else:
                doit = True
                s += str.center(newstats[i], 12)

        if doit or self.pulse%self.shortestDuration==0:
            print s
        self.statuses = newstats

