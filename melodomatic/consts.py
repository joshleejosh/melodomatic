
# pylint: disable=global-statement

QUIET = False
VERBOSE = 0

def set_quiet(q):
    global QUIET
    QUIET = q

def set_verbose(v):
    global VERBOSE
    VERBOSE = v
    if VERBOSE > 0:
        print('Verbose level %d'%VERBOSE)

DEFAULT_BEATS_PER_MINUTE = 120
DEFAULT_PULSES_PER_BEAT = 12
DEFAULT_RELOAD_INTERVAL = 96
DEFAULT_SCALE_ROOT = 60
DEFAULT_SCALE_INTERVALS = (0, 2, 4, 5, 7, 9, 11)
DEFAULT_VELOCITY = 64
DEFAULT_MOVE_TIME = '8b'
DEFAULT_VISUALIZATION_WINDOW = '.5'

