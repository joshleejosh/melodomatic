"""
Contains default generator functions for producing values.

See doc/05-generator for details.
"""

import math
from melodomatic import consts, expanders
from melodomatic.util import *

# pylint: disable=unused-argument # all generators take a `ctx` arg

# ######################################################## #

class GeneratorBinding:
    """ Wraps a generator function in an iterator w/ additional relevant data/metadata. """
    def __init__(self, n, d, c):
        self.name = n
        self.data = d
        self.context = c
        self._f = GENERATORS[self.name](self.data, self.context)

    def __eq__(self, o):
        if not o:
            return False
        if self.name != o.name:
            return False
        if self.data != o.data:
            return False
        # don't check context, we expect that to be different
        return True

    def __ne__(self, o):
        return not self.__eq__(o)

    def __str__(self):
        return '$%s %s'%(self.name, str(self.data))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._f)

# ----------------------------

# The master dictionary of known generator functions.
GENERATORS = {}

# The same keys as in GENERATORS, but sorted in order of registration.
GENERATORS_ORDERED = []

def register_generator(name, maker):
    """ Register a new generator function in the master dictionary. """
    name = name.strip().upper()
    GENERATORS[name] = maker
    GENERATORS_ORDERED.append(name)

def autocomplete_generator_name(n):
    """ Look up a partial generator name in the main dictionary and return its normalized form. """
    n = n.strip().upper()
    for name in GENERATORS_ORDERED:
        if name.startswith(n):
            return name
    return n

# ----------------------------

def bind_generator(data, ctx):
    """
    Binds a generator function to the given data and context object.

    The first element in the data array should be a $ descriptor of which
    generator to use. If none is given, we'll assume $SCALAR for single values
    and $RANDOM for multiple.

    If a converter function is given, any output from the generator will be run
    through it on its way out.

    The context object should be either a Player, Scale, or Voice. The default
    generators depend on the `rng` property of each of these types for random
    number generation.

    Returns a 2-tuple containing the generator and a text label.
    """
    cmd = ''
    if not data:
        cmd = 'SCALAR'
    elif data[0][0] == '$':
        cmd = data[0][1:].upper()
        data = data[1:]
    elif len(data) == 1:
        cmd = 'SCALAR'
    else:
        cmd = 'RANDOM'

    # guarantee that there's some data for the function.
    if not data:
        data = ('1',) # who even knows? this works in a lot of contexts, I guess

    cmd = autocomplete_generator_name(cmd)
    if cmd in GENERATORS:
        gb = GeneratorBinding(cmd, data, ctx)
        return gb
        #return (GENERATORS[cmd](data, ctx), '$%s %s'%(cmd, str(data)))

    if consts.VERBOSE:
        print('ERROR: Bad generator funtion [%s]'%cmd)
    return GeneratorBinding('SCALAR', data, ctx)


# ######################################################## #


def scalar(data, ctx):
    """ Return the input value forever. """
    while True:
        yield data[0]

def loop(data, ctx):
    """ Loop through the given list on repeat forever. """
    i = 0
    while True:
        yield data[i]
        i = (i+1)%len(data)

def pingpong(data, ctx):
    """ Traverse forwards and backwards through the list forever. """
    a = ('%PINGPONG', '0', str(len(data)-1), '1')
    indices = tuple(int(i) for i in expanders.expand_list(a))
    while True:
        for i in indices:
            yield data[i]

def random(data, ctx):
    """ Pick randomly from the list forever. """
    # pylint: disable=function-redefined
    while True:
        yield ctx.rng.choice(data)

def shuffle(data, ctx):
    """
    Shuffle the list, loop over it, and repeat forever.
    Does not modify the list.
    """
    while True:
        ia = list(range(len(data)))
        ctx.rng.shuffle(ia)
        for i in ia:
            yield data[i]

def _safearg(data, i, castf, default):
    rv = default
    try:
        rv = castf(data[i])
    except:
        if consts.VERBOSE:
            print('ERROR: Can\'t get %s(%s[%d])'%(castf, data, i))
        return default
    return rv

def random_walk(data, ctx):
    """
    Randomly walks up and down the given array forever.
    Only steps on random occasion, based on the given chance.
    When not at the edges of the array, step direction is an even coin flip.
    """
    chance = _safearg(data, 0, float, 1)
    a = ['1',]
    if len(data) > 1:
        a = data[1:]
    i = ctx.rng.randint(0, len(a)-1)
    while True:
        yield a[i]
        if len(a) == 1:
            continue
        if ctx.rng.random() < chance:
            if i == 0:
                i = 1
            elif i == len(a)-1:
                i = len(a)-2
            else:
                i += coinflip(ctx)


def wave(data, ctx):
    """
    Walk up and down the range on a curve.
    """
    curf = expanders.autocomplete_curve_function(data[0]) if len(data) > 0 else 'LINEAR'
    curd = expanders.autocomplete_curve_direction(data[1]) if len(data) > 1 else 2 # inout
    fcurve = expanders.CURVE_FUNCTIONS[curf][curd]
    period = _safearg(data, 2, int, 16)
    vmin = _safearg(data, 3, int, 0)
    vmax = _safearg(data, 4, int, 127)

    while True:
        for i in range(period):
            # Result should cycle from 0 to 1 back to 0 over period
            t = 2.0 * float(i) / float(period)
            if t > 1.0:
                t = 2.0 - t
            t = fcurve(t)
            v = int(round(t*(vmax-vmin) + vmin))
            #print('%0.6f %3d'%(t,v))
            yield str(v)


# Cobbled together from various references
# TODO: surely there's a library for this (1D perlin noise)
def _mod289(x):
    return x - math.floor(x * (1.0 / 289.0)) * 289.0
def _permute(x):
    return _mod289(((x * 34.0) + 1.0) * x)
def _grad(hashval, x):
    return -x if (hashval & 8) else x * ((hashval & 7) + 1)
def _fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
def _lerp(t, a, b):
    return t * (b - a) + a
def _map(t, imin, imax, omin, omax):
    return ((t-imin) / (imax-imin)) * (omax-omin) + omin
def _noise1(x):
    xf = math.floor(x)
    xm = x - xf
    pa = int(_permute(xf))
    pb = int(_permute(xf+1))
    t = _fade(xm)
    return _lerp(t, _grad(pa, xm), _grad(pb, xm - 1)) * 0.4

def noise(data, ctx):
    """ Use a 1D perlin noise function to pick values. """
    minv = maxv = 0
    step = 0.05
    try:
        if len(data) > 0:
            minv = int(data[0])
    except:
        pass
    try:
        if len(data) > 1:
            maxv = int(data[1])
    except:
        pass
    try:
        if len(data) > 2:
            step = float(data[2])
    except:
        pass
    i = 255.0 * ctx.rng.random()
    while True:
        p = _noise1(i)
        v = _map(p, -1.0, 1.0, minv, maxv)
        yield str(int(v))
        i += step



# ######################################################## #

register_generator('SCALAR', scalar)
register_generator('LOOP', loop)
register_generator('PINGPONG', pingpong)
register_generator('PP', pingpong)
register_generator('RANDOM', random)
register_generator('SHUFFLE', shuffle)
register_generator('RANDOM-WALK', random_walk)
register_generator('RW', random_walk)
register_generator('WAVE', wave)
register_generator('NOISE', noise)

