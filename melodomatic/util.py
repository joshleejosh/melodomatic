import random, time
import consts

def coinflip(ctx=None):
    r = ctx.rng.random() if ctx else random.random()
    if r < .5:
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


# http://stackoverflow.com/a/18860653
def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same


def is_iterable(i):
    if i is None:
        return False
    return hasattr(i, '__iter__')

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


# No code execution is ever really "safe," so let's just call it "friendly!"
FRIENDLY_EVAL_FUNCTIONS = {
    'abs'     : abs     , 'all'    : all    , 'any'    : any    , 'bin'      : bin      ,
    'bool'    : bool    , 'chr'    : chr    , 'cmp'    : cmp    , 'divmod'   : divmod   ,
    'filter'  : filter  , 'float'  : float  , 'hex'    : hex    , 'int'      : int      ,
    'len'     : len     , 'list'   : list   , 'long'   : long   , 'map'      : map      ,
    'max'     : max     , 'min'    : min    , 'oct'    : oct    , 'ord'      : ord      ,
    'pow'     : pow     , 'range'  : range  , 'reduce' : reduce , 'reversed' : reversed ,
    'round'   : round   , 'set'    : set    , 'slice'  : slice  , 'sorted'   : sorted   ,
    'str'     : str     , 'sum'    : sum    , 'tuple'  : tuple  , 'unichr'   : unichr   ,
    'unicode' : unicode , 'xrange' : xrange , 'zip'    : zip    ,
    }
def friendly_eval(code):
    return eval(code, {'__builtins__':None}, FRIENDLY_EVAL_FUNCTIONS)


# for stashing global values without getting clobbered (by players rebuilding,
# custom modules getting re-imported, etc). Bad programming practices ahoy!
SECRET = {}

