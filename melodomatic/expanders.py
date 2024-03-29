"""
Contains functions for creating a list of values that can be used to feed a generator.

See doc/11-expander for details.
"""
import pytweening
from melodomatic import consts
from melodomatic.util import *

# The master dictionary of known expander functions.
EXPANDERS = {}

# The same keys as in EXPANDERS, but sorted in order of registration.
EXPANDERS_ORDERED = []

def register_expander(name, maker):
    """ Register a new expander function in the master dictionary. """
    name = name.strip().upper()
    EXPANDERS[name] = maker
    EXPANDERS_ORDERED.append(name)

def autocomplete_expander_name(n):
    """ Look up a partial expander name in the main dictionary and return its normalized form. """
    n = n.strip().upper()
    for name in EXPANDERS_ORDERED:
        if name.startswith(n):
            return name
    if consts.VERBOSE:
        print('ERROR: Bad expander name %s'%n)
    return 'LIST'

def expand_list(a):
    """ Perform the expansion. Takes a tokenized list of values, including names, parentheses, etc. """
    rv, _ = _expand_sublist(a, 0)
    return rv

def _expand_sublist(a, i):
    cmd = 'LIST'
    if a[i][0] == '%':
        cmd = autocomplete_expander_name(a[i][1:])
        i += 1

    buf = []
    while i < len(a):
        # close an open (we hope!) sublist and pop up
        if a[i] == ')':
            i += 1
            break

        # open a new sublist by recursing down
        if a[i] == '(':
            b, i = _expand_sublist(a, i+1)
            buf.extend(b)

        # a token of form x*y gets expanded as if it was (%xerox x y)
        elif '*' in a[i]:
            sa = a[i].split('*')
            if not sa[0]: # skip this if there's no left hand side
                i += 1
                continue
            right = 1
            try:
                right = int(sa[1])
            except ValueError:
                pass
            b = [sa[0],] * right
            buf.extend(b)
            i += 1

        else:
            buf.append(a[i])
            i += 1

    rv = tuple(str(i) for i in EXPANDERS[cmd](buf))
    return rv, i

# ######################################################## #

def ex_list(data):
    """ Just returns the input list of values. """
    return tuple(data)
register_expander('LIST', ex_list)

def _cleanse_range_args(data):
    a = b = 0
    step = 1
    try:
        a = int(data[0])
        b = int(data[1])
        if len(data) > 2:
            step = int(data[2])
    except ValueError:
        pass
    if step == 0:
        step = 1
    if step < 0:
        if a < b:
            a,b = b,a
    elif a > b:
        a,b = b,a
    return a, b, step

def ex_range(data):
    """ Creates a linear series of values. """
    a, b, step = _cleanse_range_args(data)
    return list(range(a, b+sign(step), step))
register_expander('RANGE', ex_range)

def ex_crange(data):
    """ Creates a linear series of values going out from a center value. """
    center = minv = maxv = spread = 0
    step = 1
    try:
        center = int(data[0])
        spread = int(data[1])
        if len(data) > 2:
            step = int(data[2])
        minv = center - spread/2
        maxv = center + spread/2
    except ValueError:
        pass
    if step == 0:
        step = 1
    if minv > maxv:
        minv, maxv = maxv, minv
    rv = [center]
    v = center - step
    while minv <= v <= maxv:
        rv.insert(0, v)
        v -= step
    v = center + step
    while minv <= v <= maxv:
        rv.append(v)
        v += step
    return rv
register_expander('CRANGE', ex_crange)

def ex_pingpong(data):
    """ Works like `%RANGE`, but adds on a back half that walks back down the range. """
    a, b, step = _cleanse_range_args(data)
    rv = list(range(a, b+sign(step), step))
    if rv:
        rv += list(range(rv[-1]-step, a, -step))
    return rv
register_expander('PINGPONG', ex_pingpong)
register_expander('PP', ex_pingpong)

def ex_xerox(data):
    """ Duplicate a single value multiple times. """
    n = 1
    try:
        n = int(data[0])
    except ValueError:
        pass
    data = data[1:]
    rv = []
    for _ in range(n):
        rv += data
    return rv
register_expander('XEROX', ex_xerox)

# ---------------------------

# Easing functions take values in range [0.0-1.0] and return values in the same range.
CURVE_FUNCTIONS = {
        'LINEAR'     : [ pytweening.linear        , pytweening.linear         , pytweening.linear           ],
        'SINE'       : [ pytweening.easeInSine    , pytweening.easeOutSine    , pytweening.easeInOutSine    ],
        'QUADRATIC'  : [ pytweening.easeInQuad    , pytweening.easeOutQuad    , pytweening.easeInOutQuad    ],
        'CUBIC'      : [ pytweening.easeInCubic   , pytweening.easeOutCubic   , pytweening.easeInOutCubic   ],
        'QUARTIC'    : [ pytweening.easeInQuart   , pytweening.easeOutQuart   , pytweening.easeInOutQuart   ],
        'QUINTIC'    : [ pytweening.easeInQuint   , pytweening.easeOutQuint   , pytweening.easeInOutQuint   ],
        'EXPONENTIAL': [ pytweening.easeInExpo    , pytweening.easeOutExpo    , pytweening.easeInOutExpo    ],
        'CIRCULAR'   : [ pytweening.easeInCirc    , pytweening.easeOutCirc    , pytweening.easeInOutCirc    ],
        'BOUNCE'     : [ pytweening.easeInBounce  , pytweening.easeOutBounce  , pytweening.easeInOutBounce  ],
        # These try to stretch out of their bounds, so they don't work too well.
        #'ELASTIC'    : [ pytweening.easeInElastic , pytweening.easeOutElastic , pytweening.easeInOutElastic ],
        #'BACK'       : [ pytweening.easeInBack    , pytweening.easeOutBack    , pytweening.easeInOutBack    ],
        }
CURVE_FUNCTIONS_ORDERED = [ 'LINEAR', 'SINE', 'QUADRATIC', 'CUBIC', 'QUARTIC', 'QUINTIC', 'EXPONENTIAL', 'CIRCULAR', 'BOUNCE', 'BACK' ]

def autocomplete_curve_function(s):
    """ Look up a partial curve name and return its normalized form. """
    s = s.strip().upper()
    if not s:
        return CURVE_FUNCTIONS_ORDERED[0]
    for i in CURVE_FUNCTIONS_ORDERED:
        if i.startswith(s):
            return i
    if consts.VERBOSE:
        print('ERROR: Bad curve function %s'%s)
    return CURVE_FUNCTIONS_ORDERED[0]

def autocomplete_curve_direction(s):
    """
    Turn a string into an enumerated direction code.

    IN = 0
    OUT = 1
    INOUT or IO = 2

    """
    s = s.strip().upper()
    if s in ('IO', 'INOUT'):
        return 2
    if s[0] == 'I':
        return 0
    if s[0] == 'O':
        return 1
    if consts.VERBOSE:
        print('ERROR: Bad curve direction %s'%s)
    return 0

def ex_curve(data):
    """ Redistributes the values in a list on a curve. """
    rv = []
    try:
        ef = autocomplete_curve_function(data[0])
        ed = autocomplete_curve_direction(data[1])
        period = 2
        try:
            period = max(int(data[2]), 2)
        except ValueError:
            pass
        data = data[3:]
        if not data:
            if consts.VERBOSE:
                print('ERROR: No data for curve')
            return []
        f = CURVE_FUNCTIONS[ef][ed]
        maxi = len(data)-1
        for i in range(period):
            v = f(float(i) / float(period-1))
            di = int(round(v*float(maxi)))
            rv.append(data[di])

    except Exception as e:
        if consts.VERBOSE:
            print('ERROR: Curve failed [%s]'%e)

    return rv
register_expander('CURVE', ex_curve)


