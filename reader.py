import os, time
import consts
from util import *
import player, voice, scale



# I am responsible for reading a script file and modifying a
# Player instance based on what I find. I am also responsible for
# hotloading changes to the file.
class Reader:
    def __init__(self, fn, pl):
        self.filename = fn
        self.filetime = time.time()
        self.player = pl
        self.player.reader = self
        self.reloadInterval = consts.DEFAULT_RELOAD_INTERVAL

    def load_script(self):
        self.filetime = os.stat(self.filename).st_mtime

        # Blow away existing scales and voice instances, but
        # otherwise leave player state intact since we're hotloading
        self.player.scaler.scales.clear()
        del self.player.voices[:]

        fp = open(self.filename)
        scabuf = []
        vocbuf = []
        self.player.shortestDuration = 9999
        reloadIntervalBeats = -1

        def close_brackets():
            if scabuf:
                ns = self.make_scale(scabuf)
                if ns:
                    self.player.scaler.scales[ns.id] = ns
                    if not self.player.scaler.curScale:
                        self.player.scaler.curScale = ns.id
                del scabuf[:]

            if vocbuf:
                nv = self.make_voice(vocbuf)
                if nv:
                    self.player.voices.append(nv)
                    if nv.durations:
                        self.player.shortestDuration = min(self.player.shortestDuration, min(nv.durations))
                del vocbuf[:]

        for line in fp.readlines():
            line = line.split('#')[0].strip()
            if len(line) == 0:
                continue
            elif line[0] == ':':
                close_brackets()
                if line.startswith(':beats_per_minute'):
                    self.player.change_tempo(int(line.split()[1]), self.player.ppb)

                elif line.startswith(':pulses_per_beat'):
                    self.player.change_tempo(self.player.bpm, int(line.split()[1]))

                elif line.startswith(':reload_interval'):
                    reloadIntervalBeats = int(line.split()[1])

                elif line.startswith(':scale_change_times'):
                    self.player.scaler.changeTimes = tuple(int(n) for n in line.split()[1:])

                elif line.startswith(':scale_first'):
                    self.player.scaler.curScale = line.split()[1]

                elif line.startswith(':velocity_change_chance'):
                    self.player.velocityChangeChance = float(line.split()[1])
                    print self.player.velocityChangeChance

                elif line.startswith(':scale'):
                    a = line.split()
                    if len(a) < 2:
                        print 'Error: no id for scale'
                    else:
                        scabuf = [a[1], ]

                elif line.startswith(':voice'):
                    a = line.split()
                    if len(a) < 2:
                        print 'Error: no id for voice'
                    else:
                        vocbuf = [a[1], ]
            else:
                if scabuf:
                    scabuf.append(line)
                if vocbuf:
                    vocbuf.append(line)

        close_brackets()
        fp.close()
        self.player.scaler.reset()
        for v in self.player.voices:
            v.reset()
        self.player.shortestDuration = self.player.shortestDuration * self.player.ppb
        if reloadIntervalBeats >= 0:
            self.reloadInterval = reloadIntervalBeats * self.player.ppb

        if consts.VERBOSE:
            self.player.dump()
            print 'Reloaded at %d, interval %d'%(self.player.pulse, self.reloadInterval)

    def make_scale(self, scabuf):
        sid = scabuf[0].strip()
        rv = scale.Scale(sid)
        if len(scabuf) > 1:
            rv.root = int(scabuf[1].strip())
        if len(scabuf) > 2:
            rv.notes = tuple(int(n) for n in scabuf[2].strip().split())
        if len(scabuf) > 3:
            rv.links = scabuf[3].strip().split()
        if len(scabuf) > 4:
            if consts.VERBOSE:
                print 'Warning: scale [%s] has extra junk'%sid
        return rv

    def make_voice(self, vocbuf):
        vid = vocbuf[0].strip()
        rv = voice.Voice(vid, self.player)
        if len(vocbuf) > 1:
            rv.offset = int(vocbuf[1].strip())
        if len(vocbuf) > 2:
            rv.durations = tuple(float(n) for n in vocbuf[2].strip().split())
        if len(vocbuf) > 3:
            rv.velocities = tuple(int(n) for n in vocbuf[3].strip().split())
        if len(vocbuf) > 4:
            if consts.VERBOSE:
                print 'Warning: voice [%s] has extra junk'%vid
        return rv

    def update(self, pulse):
        if pulse%self.reloadInterval == 0:
            t = os.stat(self.filename).st_mtime
            if t != self.filetime:
                self.load_script()

