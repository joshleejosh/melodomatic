import math, pytweening
import consts
from util import *

EXPANDERS = {}
EXPANDERS_ORDERED = []

def register_expander(name, maker):
    name = name.strip().upper()
    EXPANDERS[name] = maker
    EXPANDERS_ORDERED.append(name)

def autocomplete_expander_name(n):
    n = n.strip().upper()
    for name in EXPANDERS_ORDERED:
        if name.startswith(n):
            return name
    if consts.VERBOSE:
        print 'ERROR: Bad expander name %s'%n
    return 'LIST'

def expand_list(a):
    rv, i = expand_sublist(a, 0)
    return rv

def expand_sublist(a, i):
    cmd = 'LIST'
    if a[i][0] == '%':
        cmd = autocomplete_expander_name(a[i][1:])
        i += 1

    buf = []
    while i < len(a):
        if a[i] == ')':
            i += 1
            break
        elif a[i] == '(':
            b, i = expand_sublist(a, i+1)
            buf.extend(b)
        else:
            buf.append(a[i])
            i += 1

    rv = tuple(str(i) for i in EXPANDERS[cmd](buf))
    return rv, i

# ######################################################## #

def ex_list(data):
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
    a, b, step = _cleanse_range_args(data)
    return range(a, b+sign(step), step)
register_expander('RANGE', ex_range)

def ex_crange(data):
    center = min = max = spread = 0
    step = 1
    try:
        center = int(data[0])
        spread = int(data[1])
        if len(data) > 2:
            step = int(data[2])
        min = center - spread/2
        max = center + spread/2
    except ValueError:
        pass
    if step == 0:
        step = 1
    if min > max:
        t = max
        max = min
        min = t
    rv = [center]
    v = center - step
    while v >= min and v <= max:
        rv.insert(0, v)
        v -= step
    v = center + step
    while v >= min and v <= max:
        rv.append(v)
        v += step
    return rv
register_expander('CRANGE', ex_crange)

def ex_pingpong(data):
    a, b, step = _cleanse_range_args(data)
    rv = range(a, b+sign(step), step)
    if rv:
        rv += range(rv[-1]-step, a, -step)
    return rv
register_expander('PINGPONG', ex_pingpong)
register_expander('PP', ex_pingpong)

def ex_xerox(data):
    n = 1
    try:
        n = int(data[0])
    except ValueError:
        pass
    data = data[1:]
    rv = []
    for i in xrange(n):
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
    s = s.strip().upper()
    if not s:
        return CURVE_FUNCTIONS_ORDERED[0]
    for i in CURVE_FUNCTIONS_ORDERED:
        if i.startswith(s):
            return i
    if consts.VERBOSE:
        print 'ERROR: Bad curve function %s'%s
    return CURVE_FUNCTIONS_ORDERED[0]

def autocomplete_curve_direction(s):
    s = s.strip().upper()
    if s == 'IO' or s == 'INOUT':
        return 2
    elif s[0] == 'I':
        return 0
    elif s[0] == 'O':
        return 1
    if consts.VERBOSE:
        print 'ERROR: Bad curve direction %s'%s
    return 0

def ex_curve(data):
    rv = []
    try:
        ef = autocomplete_curve_function(data[0])
        ed = autocomplete_curve_direction(data[1])
        period = 2
        try:
            period = int(data[2])
            if period < 2:
                period = 2
        except ValueError:
            pass
        data = data[3:]
        if not data:
            if consts.VERBOSE:
                print 'ERROR: No data for curve'
            return []
        f = CURVE_FUNCTIONS[ef][ed]
        maxi = len(data)-1
        for i in xrange(period):
            v = f(float(i) / float(period-1))
            di = int(round(v*float(maxi)))
            rv.append(data[di])

    except Exception as e:
        if consts.VERBOSE:
            print 'ERROR: Curve failed [%s]'%e

    return rv
register_expander('CURVE', ex_curve)


