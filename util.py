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

def sign(n):
    if n < 0:
        return -1
    elif n > 0:
        return +1
    else:
        return 0

def clamp(v, low, high):
    return min(high, max(low, v))

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

def to_num(i):
    if is_int(i):
        return int(i)
    elif is_float(i):
        return float(i)
    else:
        raise ValueError('Can\'t parse number out of [%s]'%str(i))

def split_ints(a):
    return tuple(int(i) for i in a if is_int(i))

def split_floats(a):
    return tuple(float(i) for i in a if is_float(i))


NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
def note_name(v):
    octave = int(v/12)
    note = NOTE_NAMES[v%12]
    return '%s%d'%(note, octave)

