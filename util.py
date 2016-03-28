import random, time
import consts

rnd = random.Random()

def seed_random(s):
    if not s:
        s = time.time()
    if consts.VERBOSE:
        print 'Seed = %d'%float(s)
    rnd.seed(s)

def coinflip():
    if rnd.random() < .5:
        return -1
    else:
        return +1

NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
def note_name(v):
    octave = int(v/12)
    note = NOTE_NAMES[v%12]
    return '%s%d'%(note, octave)

