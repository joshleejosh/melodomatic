import curses, collections
import consts
from util import *


class Visualizer:
    def __init__(self):
        self.statusBuffer = collections.deque(tuple(), 10)

    def startup(self):
        self.statusBuffer.clear()

    def update(self, player, reader):
        status = {
                'pulse': 0,
                'reader': '',
                'scale': '',
                'voiceOrder': [],
                'voices': {},
                'controlOrder': [],
                'controls': {}
                }
        status['pulse'] = player.pulse
        status['reader'] = reader.status
        status['scale'] = player.curScale.status

        for vk in player.voiceOrder:
            status['voiceOrder'].append(vk)
            v = player.voices[vk]
            status['voices'][vk] = {
                    'status': v.status,
                    'note': v.curNote,
                    }

        for ck in player.controlOrder:
            status['controlOrder'].append(ck)
            c = player.controls[ck]
            status['controls'][ck] = {
                    'status': c.status,
                    }

        self.statusBuffer.append(status)


class TTYVisualizer(Visualizer):
    def __init__(self):
        Visualizer.__init__(self)
    def startup(self):
        Visualizer.startup(self)

    # Update our half-baked visualization string and print it out.
    def update(self, player, reader):
        Visualizer.update(self, player, reader)
        status = self.statusBuffer[-1]
        forcePrint = False

        s = '%06d'%status['pulse']
        if status['reader']:
            forcePrint = True
        s += '%2s'%status['reader']

        controlStatus = ''
        if any(((status['controls'][c]['status'] != '') for c in status['controlOrder'])):
            controlStatus = '+'
            forcePrint = True
        s += '%2s'%controlStatus

        if status['scale'].strip() not in ('', '|'):
            forcePrint = True
        s += str.center(status['scale'], 7)

        for vk in status['voiceOrder']:
            v = status['voices'][vk]
            if v['status'].strip() not in ('', '|'):
                forcePrint = True
            s += str.center(v['status'], 7)

        #for ck in status['controlOrder']:
        #    c = status['controls'][ck]
        #    if c['status'].strip() not in ('', '|'):
        #        forcePrint = True
        #    s += str.center(c['status'], 9)

        if player.pulse%player.visualizationWindow == 0 or forcePrint:
            print s


class CursesVisualizer(Visualizer):
    def __init__(self, scr):
        Visualizer.__init__(self)
        self.screen = scr

    def startup(self):
        Visualizer.startup(self)
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()
        #for i in xrange(curses.COLORS):
        #    curses.init_pair(i+1, i, -1)
        self.screen.keypad(True)

    def update(self, player, reader):
        Visualizer.update(self, player, reader)
        self.screen.clear()
        self.screen.border()
        self.screen.refresh()

