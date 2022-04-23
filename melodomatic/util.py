"""
Utility functions.
"""

import random
import math


def coinflip(ctx=None):
    """
    Return -1 or 1.

    If a context is provided, use its RNG.
    """
    r = ctx.rng.random() if ctx else random.random()
    if r < .5:
        return -1
    return +1

def sign(n):
    """
    Returns -1, 0, or 1.
    """
    if n < 0:
        return -1
    if n > 0:
        return +1
    return 0

def clamp(v, low, high):
    """
    Limit the value to the range [low, high].
    """
    return min(high, max(low, v))

def dict_compare(d1, d2):
    """
    Compare two dicts by their key/value pairs.

    cf. http://stackoverflow.com/a/18860653
    """
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same

def is_int(i):
    """
    Returns True/False based on whether the given value is an int.
    """
    try:
        int(i)
        return True
    except ValueError:
        return False

def is_float(i):
    """
    Returns True/False based on whether the given value is a float.
    """
    try:
        float(i)
        return True
    except ValueError:
        return False

def split_ints(a):
    """
    Convert and copy a list of arbitrary values to a tuple of ints.

    Only copy values that can be cast to int; throw away invalid values.
    """
    return tuple(int(i) for i in a if is_int(i))

def split_floats(a):
    """
    TODO: I am only called in tests, deleteme
    """
    return tuple(float(i) for i in a if is_float(i))

NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
def note_name(v):
    """
    Convert a numeric value (e.g., 61) to a readable note+octave string (e.g., "C#5")
    """
    octave = math.floor(v/12)
    note = NOTE_NAMES[v%12]
    return '%s%d'%(note, octave)

# for stashing global values without getting clobbered (by players rebuilding,
# custom modules getting re-imported, etc). Bad programming practices ahoy!
SECRET = {}

