
QUIET = False
VERBOSE = 0

def set_quiet(q):
    global QUIET
    QUIET = q

def set_verbose(v):
    global VERBOSE
    VERBOSE = v
    if VERBOSE > 0:
        print 'Verbose level %d'%VERBOSE

DEFAULT_BEATS_PER_MINUTE = 120
DEFAULT_PULSES_PER_BEAT = 12
DEFAULT_RELOAD_INTERVAL = 64 # this is pulses, but in the script, you should count this in beats.
DEFAULT_SCALE_ROOT = 60
DEFAULT_SCALE_INTERVALS = (0,)
DEFAULT_VELOCITY = 64
DEFAULT_SCALE_CHANGE_TIMES = (16,)
DEFAULT_VELOCITY_CHANGE_CHANCE = 1.0/6.0

