import consts
from util import *

# Return the input value forever.
def scalar(v):
    while True:
        yield v

# Loop through the given list on repeat forever.
def loop(a):
    i = 0
    while True:
        yield a[i]
        i += 1
        if i >= len(a):
            i = 0

# Traverse forwards and backwards through the list forever.
def pingpong(a):
    i = 0
    dir = 1
    while True:
        yield a[i]
        if i >= len(a)-1:
            i = len(a)-2
            dir = -1
        elif i <= 0:
            i = 1
            dir = 1
        else:
            i += dir

def random(a):
    while True:
        yield rnd.choice(a)

# Shuffle the list, loop over it, and repeat forever.
# Does not modify the list.
def shuffle(a):
    while True:
        ia = range(len(a))
        rnd.shuffle(ia)
        for i in ia:
            yield a[i]

# Randomly walks up and down the given array forever.
# Only steps on random occasion, based on the given chance.
# When not at the edges of the array, step direction is an even coin flip.
def random_walk(chance, a):
    i = rnd.randint(0, len(a)-1)
    while True:
        yield a[i]
        if rnd.random() < chance:
            if i == 0:
                i = 1
            elif i == len(a)-1:
                i = len(a)-2
            else:
                i += coinflip()

# Returns a 3-tuple containing the generator, a description string, and a tuple with converted values.
def make_generator(data, converter=None):
    cmd = ''
    if data[0][0] == '$':
        cmd = data[0][1:].upper()
        data = data[1:]
    elif len(data) == 1:
        cmd = 'SCALAR'
    else:
        cmd = 'RANDOM'
    if cmd == 'SCALAR':
        v = converter(data[0]) if converter else data[0]
        return (scalar(v), '$%s %s'%(cmd, v), (v,))
    elif cmd == 'LOOP':
        a = tuple(converter(d) if converter else d for d in data)
        return (loop(a), '$%s %s'%(cmd, tuple(str(i) for i in a)), a)
    elif cmd == 'PINGPONG':
        a = tuple(converter(d) if converter else d for d in data)
        return (pingpong(a), '$%s %s'%(cmd, tuple(str(i) for i in a)), a)
    elif cmd == 'RANDOM':
        a = tuple(converter(d) if converter else d for d in data)
        return (random(a), '$%s %s'%(cmd, tuple(str(i) for i in a)), a)
    elif cmd == 'SHUFFLE':
        a = tuple(converter(d) if converter else d for d in data)
        return (shuffle(a), '$%s %s'%(cmd, tuple(str(i) for i in a)), a)
    elif cmd == 'RANDOM-WALK':
        c = float(data[0])
        a = tuple(converter(d) if converter else d for d in data[1:])
        return (random_walk(c, a), '$%s %f %s'%(cmd, c, tuple(str(i) for i in a)), a)

    if consts.VERBOSE:
        print 'ERROR: Bad generator funtion [%s]'%cmd
    return (None, '', ())

