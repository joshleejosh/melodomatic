import os, time, re
import consts
from util import *
import player, voice, scale

def is_int(i):
    try:
        int(i)
        return True
    except ValueError:
        return False

def is_float(i):
    try:
        float(i)
        return True
    except ValueError:
        return False

def split_ints(a):
    return tuple(int(i) for i in a if is_int(i))

def split_floats(a):
    return tuple(float(i) for i in a if is_float(i))


RE_MACRO = re.compile('@(\S+)')

# I am responsible for reading a script file and configuring the
# Player instance based on what I find. Along the way, I am responsible for
# creating Scales and Voices.
#
# I am also responsible for checking for changes to the file at regular
# intervals and reconfiguring the Player when that happens.
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
        macros = {}
        self.player.shortestDuration = 9999
        newReloadInterval = -1

        def close_blocks():
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

            # handle macro definitions.
            if line[0] == '@':
                if scabuf or vocbuf:
                    pass
                else:
                    a = line.split()
                    car = a[0][1:]
                    cdr = ' '.join(a[1:])
                    macros[car] = cdr
                    continue

            # do macro substitutions before processing the line.
            if '@' in line:
                for g in RE_MACRO.findall(line):
                    if g in macros:
                        line = line.replace('@'+g, macros[g])
                    else:
                        line = line.replace('@'+g, '')

            # handle directives.
            if line[0] == ':':
                close_blocks()
                if line.startswith(':beats_per_minute'):
                    i = line.split()[1]
                    if is_int(i):
                        self.player.change_tempo(int(i), self.player.ppb)

                elif line.startswith(':pulses_per_beat'):
                    i = line.split()[1]
                    if is_int(i):
                        self.player.change_tempo(self.player.bpm, int(i))

                elif line.startswith(':reload_interval'):
                    i = line.split()[1]
                    if is_int(i):
                        newReloadInterval = int(i)

                elif line.startswith(':scale_change_times'):
                    t = split_ints(line.split()[1:])
                    if t:
                        self.player.scaler.changeTimes = t

                elif line.startswith(':scale_first'):
                    a = line.split()
                    if len(a) > 1:
                        self.player.scaler.curScale = line.split()[1]
                        # we can't check the validity of this value until we have finished loading.

                elif line.startswith(':velocity_change_chance'):
                    self.player.velocityChangeChance = float(line.split()[1])

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
                        vocbuf = ['voice', a[1], ]

                elif line.startswith(':harmony'):
                    a = line.split()
                    if len(a) < 2:
                        print 'Error: no id for harmony'
                    else:
                        vocbuf = ['harmony', a[1], ]

                elif line.startswith(':loop'):
                    a = line.split()
                    if len(a) < 2:
                        print 'Error: no id for loop'
                    else:
                        vocbuf = ['loop', a[1], ]

                else:
                    print 'Warning: Ignoring unrecognized directive %s'%line


            # add data to blocks.
            else:
                if scabuf:
                    scabuf.append(line)
                if vocbuf:
                    vocbuf.append(line)

        close_blocks()
        fp.close()

        self.player.validate()
        self.player.shortestDuration = self.player.shortestDuration * self.player.ppb
        if newReloadInterval >= 0:
            self.reloadInterval = newReloadInterval * self.player.ppb

        if consts.VERBOSE:
            self.player.dump()
            print 'Reloaded at %d, hotload interval %d'%(self.player.pulse, self.reloadInterval)

    def make_scale(self, scabuf):
        sid = scabuf[0].strip()
        rv = scale.Scale(sid)
        if len(scabuf) > 1:
            rv.root = int(scabuf[1].strip())
        if len(scabuf) > 2:
            rv.intervals = split_ints(scabuf[2].strip().split())
        if len(scabuf) > 3:
            # we can't verify the validity of the links until after we're
            # finished loading, so just accept them all for now.
            rv.links = scabuf[3].strip().split()
        return rv

    def make_voice(self, vocbuf):
        which = vocbuf[0].strip()
        vid = vocbuf[1].strip()
        if which == 'voice':
            rv = voice.Voice(vid, self.player)
            if len(vocbuf) > 2:
                i = vocbuf[2].strip()
                if is_int(i):
                    rv.offset = int(i)
            if len(vocbuf) > 3:
                rv.durations = split_floats(vocbuf[3].strip().split())
            if len(vocbuf) > 4:
                rv.velocities = split_ints(vocbuf[4].strip().split())
            return rv

        elif which == 'harmony':
            rv = voice.Harmony(vid, self.player)
            if len(vocbuf) > 2:
                rv.voice = vocbuf[2].strip()
            if len(vocbuf) > 3:
                i = vocbuf[3].strip()
                if is_int(i):
                    rv.pitchOffset = int(i)
            if len(vocbuf) > 4:
                i = vocbuf[4].strip()
                if is_int(i):
                    rv.stepOffset = int(i)
            if len(vocbuf) > 5:
                i = vocbuf[5].strip()
                if is_int(i):
                    rv.velocityOffset = int(i)
            return rv

        elif which == 'loop':
            rv = voice.Loop(vid, self.player)
            if len(vocbuf) > 2:
                i = vocbuf[2].strip()
                if is_int(i):
                    rv.offset = int(i)
            for step in vocbuf[3:]:
                a = step.split()
                p = d = v = ''
                p = a[0]
                if len(a) > 1:
                    d = a[1]
                if len(a) > 2:
                    v = a[2]
                rv.add_step(p, d, v)

            return rv




    def update(self, pulse):
        if pulse%self.reloadInterval == 0:
            t = os.stat(self.filename).st_mtime
            if t != self.filetime:
                self.load_script()


