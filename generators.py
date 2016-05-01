import consts
from util import *

# Return the input value forever.
def scalar(data, player):
    while True:
        yield data[0]

# Loop through the given list on repeat forever.
def loop(data, player):
    i = 0
    while True:
        yield data[i]
        i = (i+1)%len(data)

# Traverse forwards and backwards through the list forever.
def pingpong(data, player):
    i = 0
    dir = 1
    while True:
        yield data[i]
        if i >= len(data)-1:
            i = len(data)-2
            dir = -1
        elif i <= 0:
            i = 1
            dir = 1
        else:
            i += dir

# Pick randomly from the list forever.
def random(data, player):
    while True:
        yield rnd.choice(data)

# Shuffle the list, loop over it, and repeat forever.
# Does not modify the list.
def shuffle(data, player):
    while True:
        ia = range(len(data))
        rnd.shuffle(ia)
        for i in ia:
            yield data[i]

# Randomly walks up and down the given array forever.
# Only steps on random occasion, based on the given chance.
# When not at the edges of the array, step direction is an even coin flip.
def random_walk(data, player):
    chance = float(data[0])
    a = data[1:]
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

# ######################################################## #

GENERATORS = { }
GENERATORS_ORDERED = []

def register_generator(name, maker):
    name = name.strip().upper()
    GENERATORS[name] = maker
    GENERATORS_ORDERED.append(name)

def autocomplete_generator_name(n):
    n = n.strip().upper()
    for name in GENERATORS_ORDERED:
        if name.startswith(n):
            return name
    return n

# Binds a generator function to the given data and player.
#
# The first element in the data array should be a $ descriptor of which generator to use.
# If none is given, we'll assume $SCALAR for single values and $RANDOM for multiple.
#
# If a converter function is given, any output from the generator will be run
# through it on its way out.
#
# Returns a 2-tuple containing the generator and a text label.
def bind_generator(data, player):
    cmd = ''
    if data[0][0] == '$':
        cmd = data[0][1:].upper()
        data = data[1:]
    elif len(data) == 1:
        cmd = 'SCALAR'
    else:
        cmd = 'RANDOM'

    cmd = autocomplete_generator_name(cmd)
    if cmd in GENERATORS:
        return (GENERATORS[cmd](data, player), '$%s %s'%(cmd, str(data)))

    if consts.VERBOSE:
        print 'ERROR: Bad generator funtion [%s]'%cmd
    return (None, '')

register_generator('SCALAR', scalar)
register_generator('LOOP', loop)
register_generator('PINGPONG', pingpong)
register_generator('PP', pingpong)
register_generator('RANDOM', random)
register_generator('SHUFFLE', shuffle)
register_generator('RANDOM-WALK', random_walk)
register_generator('RW', random_walk)

