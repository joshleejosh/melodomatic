# encoding: utf-8
import sys, curses, curses.panel, collections, time
import consts
from util import *

import locale
locale.setlocale(locale.LC_ALL, '')

STATUSBUFFERLEN = 200
PULSEWIDTH = 6
VOICEWIDTH = 9

# Are there any significant characters in this status that
# should trigger output, even if we're off-meter?
def should_force_print(s):
    return s[PULSEWIDTH:].replace(' ', '').replace('|', '') != ''

def navkey(keyname, buflen, pagelen):
    rv = 0
    if keyname in ('K', 'k', 'KEY_UP'):
        rv = -1
    elif keyname in ('J', 'j', 'KEY_DOWN'):
        rv = +1
    elif keyname in ('^B', 'KEY_PPAGE', ):
        rv = -pagelen
    elif keyname in ('^F', 'KEY_NPAGE', ):
        rv = +pagelen
    elif keyname in ('KEY_HOME', ):
        rv = -buflen
    elif keyname in ('KEY_END', ):
        rv = +buflen
    return rv

class Visualizer:
    def __init__(self):
        self.statusBuffer = collections.deque(tuple(), STATUSBUFFERLEN)

    def startup(self):
        self.statusBuffer.clear()

    def shutdown(self):
        pass

    def update(self, player, reader):
        status = {
                'pulse': 0,
                'reader': '',
                'scale': {},
                'voiceOrder': [],
                'voices': {},
                'controlOrder': [],
                'controls': {}
                }
        status['pulse'] = player.pulse
        status['reader'] = reader.status

        status['scale']['status'] = player.curScale.status
        status['scale']['id'] = player.curScale.id

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
        return 0

    def status_line_all(self, status):
        fmt = '%%%02dd'%PULSEWIDTH
        s = fmt%status['pulse']
        s += '%2s'%status['reader']

        controlStatus = ''
        if any(((status['controls'][c]['status'] != '') for c in status['controlOrder'])):
            controlStatus = '+'
        s += '%2s'%controlStatus

        s += str.center(status['scale']['status'], VOICEWIDTH)

        for vk in status['voiceOrder']:
            v = status['voices'][vk]
            s += str.center(v['status'], VOICEWIDTH)

        return s

    def status_line_voice(self, status, vk):
        fmt = '%%%02dd'%PULSEWIDTH
        vs = fmt%status['pulse']
        if vk in status['voices']:
            vs += str.center(status['voices'][vk]['status'], VOICEWIDTH)
        return vs

    def status_line_controls(self, status):
        fmt = '%%%02dd'%PULSEWIDTH
        s = fmt%status['pulse']
        s += '%2s'%status['reader']
        for ck in status['controlOrder']:
            c = status['controls'][ck]
            s += str.center(c['status'], VOICEWIDTH)
        return s


class TTYVisualizer(Visualizer):
    def __init__(self):
        Visualizer.__init__(self)
    def startup(self):
        Visualizer.startup(self)

    # Update our half-baked visualization string and print it out.
    def update(self, player, reader):
        Visualizer.update(self, player, reader)
        status = self.statusBuffer[-1]
        s = self.status_line_all(status)

        if (player.pulse%player.visualizationWindow == 0) or should_force_print(s):
            print s
        return 0


class CursesVisualizer(Visualizer):
    TOOLBARHEIGHT = 2
    TOOLSEP = '   '
    class Mode:
        MAIN = ('M', 'Main')
        VOICE = ('V', 'Voice')
        SCALES = ('S', 'Scales')
        CONTROLS = ('C', 'Controls')
        READER = ('R', 'Reader')
        order = ( MAIN, VOICE, SCALES, CONTROLS, READER )

    class ModeScreen:
        def __init__(self, p):
            self.parent = p
        def startup(self):
            height = self.parent.screen.getmaxyx()[0] - 1
            width = self.parent.screen.getmaxyx()[1] - 1
            self.win = curses.newwin(height-CursesVisualizer.TOOLBARHEIGHT, width, 0, 0)
        def hide(self):
            self.win.erase()
        def update(self, player, reader):
            self.win.erase()
            self.win.border()
            self.win.noutrefresh()
        def check_key(self, key, player):
            return 0
        def get_toolbar_labels(self):
            return tuple()

    class ModeMain(ModeScreen):
        def update(self, player, reader):
            self.win.erase()
            self.win.border()
            rows = self.win.getmaxyx()[0] - 3
            columns = self.win.getmaxyx()[1]-3
            self.display_headers(player, reader, columns)

            i = len(self.parent.statusBuffer) - 1
            y = rows + 1
            while y >= 2 and i >= 0:
                pulse = self.parent.statusBuffer[i]['pulse']
                line = self.parent.status_line_all(self.parent.statusBuffer[i])
                if (pulse%player.visualizationWindow == 0) or should_force_print(line):
                    s = str.ljust(line[0:columns], columns)
                    self.win.addstr(y, 1, s)
                    y -= 1
                i -= 1

            self.win.noutrefresh()

        def display_headers(self, player, reader, columns):
            s = str.ljust('', PULSEWIDTH+2+2+VOICEWIDTH)
            for vk in player.voiceOrder:
                s += str.center(player.voices[vk].id, VOICEWIDTH)
            s = str.ljust(s[0:columns], columns)
            self.win.addstr(1, 1, s, curses.A_UNDERLINE)

    class ModeVoice(ModeScreen):
        def startup(self):
            height = self.parent.screen.getmaxyx()[0] - 1
            width = self.parent.screen.getmaxyx()[1] - 1
            statwidth = max(int(width*.25), VOICEWIDTH+PULSEWIDTH+4)
            self.winConf = curses.newwin(height-CursesVisualizer.TOOLBARHEIGHT, width-statwidth, 0, 0)
            self.winStat = curses.newwin(height-CursesVisualizer.TOOLBARHEIGHT, statwidth, 0, width-statwidth)

        def hide(self):
            self.winConf.erase()
            self.winStat.erase()

        def update(self, player, reader):
            self.update_conf(player, reader)
            self.update_stat(player, reader)

        def update_conf(self, player, reader):
            self.voice = clamp(self.parent.voice, 0, len(player.voiceOrder)-1)
            self.winConf.erase()
            self.winConf.border()
            rows = self.winConf.getmaxyx()[0] - 3
            columns = self.winConf.getmaxyx()[1] - 3
            voice = player.voices[player.voiceOrder[self.voice]]
            self.winConf.addstr(1, 1, 'VOICE ')
            self.winConf.addstr(voice.id, curses.A_REVERSE)
            if voice.mute:
                self.winConf.addstr(' [MUTE]')
            self.winConf.addstr(2, 5, 'channel %d'%voice.channel)
            self.winConf.addstr(3, 5, 'seed %s'%voice.rngSeed)
            self.winConf.addstr(4, 5, 'generator %s'%voice.generator.name)

            widthPName = max((len(p) for p in voice.parameters.keys())) + 1
            widthGName = max((len(g.name) for g in voice.parameters.values())) + 1
            y = 6
            for p,g in voice.parameters.iteritems():
                if y >= rows - 1:
                    break
                self.winConf.addstr(y, 1, p)
                self.winConf.addstr(y, widthPName+1, '$%s'%g.name)
                dwidth = columns - widthGName - widthPName - 2
                gds = ' '.join(g.data)
                while len(gds) > dwidth:
                    gdt = gds[0:dwidth]
                    gds = gds[dwidth:]
                    self.winConf.addstr(y, widthGName+widthPName+2, gdt)
                    y += 1
                self.winConf.addstr(y, widthGName+widthPName+2, gds)
                y += 1

        def update_stat(self, player, reader):
            self.winStat.erase()
            self.winStat.border()
            height = self.winStat.getmaxyx()[0]-1
            columns = self.winStat.getmaxyx()[1]-3
            y = height - 1
            for i in xrange(len(self.parent.statusBuffer)-1, -1, -1):
                if y < 1:
                    break
                pulse = self.parent.statusBuffer[i]['pulse']
                line = self.parent.status_line_voice(self.parent.statusBuffer[i], player.voiceOrder[self.voice])
                if (pulse%player.visualizationWindow == 0) or should_force_print(line):
                    s = str.ljust(line[0:columns], columns)
                    self.winStat.addstr(y, 1, s)
                    y -= 1

            self.winConf.noutrefresh()
            self.winStat.noutrefresh()

        def check_key(self, key, player):
            if key in (ord(u'v'), curses.KEY_RIGHT):
                self.parent.change_voice(1, player)
            elif key in (ord(u'V'), curses.KEY_LEFT):
                self.parent.change_voice(-1, player)
            return 0

        def get_toolbar_labels(self):
            return (
                    [ u'←/→', u'Prev/Next Voice' ],
                    )

    class ModeControls(ModeScreen):
        def update(self, player, reader):
            self.win.erase()
            self.win.border()
            height = self.win.getmaxyx()[0]-1
            width = self.win.getmaxyx()[1]-1
            columns = width - 2
            self.display_headers(player, reader, columns)

            y = height - 1
            for i in xrange(len(self.parent.statusBuffer)-1, -1, -1):
                if y < 2:
                    break
                pulse = self.parent.statusBuffer[i]['pulse']
                line = self.parent.status_line_controls(self.parent.statusBuffer[i])
                if (pulse%player.visualizationWindow == 0) or should_force_print(line):
                    s = str.ljust(line[0:columns], columns)
                    self.win.addstr(y, 1, s)
                    y -= 1

            self.win.noutrefresh()

        def display_headers(self, player, reader, columns):
            s = str.ljust('', PULSEWIDTH+2)
            for vk in player.controlOrder:
                s += str.center(player.controls[vk].id, VOICEWIDTH)
            s = str.ljust(s[0:columns], columns)
            self.win.addstr(1, 1, s, curses.A_UNDERLINE)

    class ModeScales(ModeScreen):
        def update(self, player, reader):
            self.win.erase()
            self.win.border()
            rows = self.win.getmaxyx()[0] - 3
            cols = self.win.getmaxyx()[1] - 3

            self.win.addstr(1, 1, 'CURRENT SCALE: ')
            self.win.addstr(player.curScale.id, curses.A_BOLD)
            eta = player.curScale.changeTime - player.pulse
            self.win.addstr(2, 1, 'NEXT SCALE: %s'%player.curScale.moveLinker)
            self.win.addstr(3, 1, '        IN: %d.%d'%(int(eta/player.ppb), eta%player.ppb))

            y = 5
            for sk in player.scaleOrder:
                if y >= rows - 1:
                    break
                scale = player.scales[sk]
                self.win.addstr(y, 2, scale.id, curses.A_BOLD)
                self.win.addstr(', seed=%s'%scale.rngSeed)
                self.win.addstr(y+1, 5, '%s [%d + %s]'%(scale.pitches, scale.root, scale.intervals))
                self.win.addstr(y+2, 5, 'move: %s -> %s'%(scale.moveTimer, scale.moveLinker))
                y += 3

            self.win.noutrefresh()

    class ModeReader(ModeScreen):
        def startup(self):
            height = self.parent.screen.getmaxyx()[0] - 1
            width = self.parent.screen.getmaxyx()[1] - 1
            self.winRdr = curses.newwin(5, width, 0, 0)
            self.winLog = curses.newwin(height-7, width, 5, 0)
            self.logLine = -1

        def hide(self):
            self.winRdr.erase()
            self.winLog.erase()

        def update(self, player, reader):
            self.updateRdr(player, reader)
            self.updateLog(player, reader)

        def updateRdr(self, player, reader):
            self.winRdr.erase()
            self.winRdr.border()
            self.winRdr.addstr(1, 1, 'FILE: ')
            self.winRdr.addstr(reader.filename, curses.A_REVERSE)
            self.winRdr.addstr(2, 1, 'LAST MODIFIED AT: %s'%time.ctime(reader.filetime))
            self.winRdr.addstr(3, 1, 'NEXT CHECK IN: %d'%(reader.reloadInterval - player.pulse%reader.reloadInterval))
            self.winRdr.noutrefresh()

        def updateLog(self, player, reader):
            self.winLog.erase()
            self.winLog.border()
            rows = self.winLog.getmaxyx()[0] - 2
            cols = self.winLog.getmaxyx()[1] - 2

            y = rows
            i = len(self.parent.fakeOut.buffer) - 1
            if self.logLine != -1:
                i = self.logLine

            while i>=0 and y>=1:
                line = self.parent.fakeOut.buffer[i]
                self.winLog.addstr(y, 1, line[0:cols]) # TODO: horizontal scroll
                y -= 1
                i -= 1

            self.winLog.noutrefresh()

        def scrollLog(self, n):
            rows = self.winLog.getmaxyx()[0] - 2
            buflen = len(self.parent.fakeOut.buffer)
            if self.logLine == -1:
                self.logLine = buflen - 1 + n
            else:
                self.logLine += n
            self.logLine = clamp(self.logLine, rows-1, buflen-1)
            if self.logLine == buflen - 1:
                self.logLine = -1

        def check_key(self, key, player):
            kn = curses.keyname(key)
            buflen = len(self.parent.fakeOut.buffer)
            rows = self.winLog.getmaxyx()[0] - 2
            if kn in ('F', 'f'):
                self.parent.fakeOut.flush()
            elif navkey(kn, buflen, rows):
                self.scrollLog(navkey(kn, buflen, rows))
            return 0

        def get_toolbar_labels(self):
            return (
                    [ u'F', u'Flush Messages' ],
                    [ u'↑ ↓ PGUP PGDN HOME END', u'Scroll Log' ],
                    )

    def __init__(self, scr):
        Visualizer.__init__(self)
        self.screen = scr
        self.modeOrder = [
                CursesVisualizer.Mode.MAIN,
                CursesVisualizer.Mode.VOICE,
                CursesVisualizer.Mode.SCALES,
                CursesVisualizer.Mode.CONTROLS,
                CursesVisualizer.Mode.READER,
                ]
        self.modeScreens = {
                CursesVisualizer.Mode.MAIN: CursesVisualizer.ModeMain(self),
                CursesVisualizer.Mode.VOICE: CursesVisualizer.ModeVoice(self),
                CursesVisualizer.Mode.SCALES: CursesVisualizer.ModeScales(self),
                CursesVisualizer.Mode.CONTROLS: CursesVisualizer.ModeControls(self),
                CursesVisualizer.Mode.READER: CursesVisualizer.ModeReader(self),
                }
        self.mode = CursesVisualizer.Mode.MAIN
        self.voice = 0
        self.scale = 0

    def startup(self):
        self.mode = CursesVisualizer.Mode.MAIN
        self.voice = 0
        self.scale = 0

        Visualizer.startup(self)
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()
        self.screen.nodelay(True)
        self.screen.keypad(True)
        self.screen.clear()
        self.screen.refresh()

        for m in self.modeScreens.values():
            m.startup()
        height = self.screen.getmaxyx()[0] - 1
        width = self.screen.getmaxyx()[1] - 1
        self.winToolbar = curses.newwin(2, width, height-2, 0)

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.fakeOut = FakeSysOut()
        sys.stdout = self.fakeOut
        sys.stderr = self.fakeOut

        self.display_toolbar()
        curses.doupdate()

    def shutdown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        for line in self.fakeOut.buffer:
            sys.stdout.write(line)
        self.fakeOut = None

    def update(self, player, reader):
        Visualizer.update(self, player, reader)
        self.modeScreens[self.mode].update(player, reader)
        #self.display_toolbar()
        curses.doupdate()
        return self.check_key(player)

    def choose_mode(self, newmode):
        if self.mode != newmode:
            self.modeScreens[self.mode].hide()
            self.mode = newmode
            self.display_toolbar()
    def rotate_mode(self, n):
        mi = self.modeOrder.index(self.mode)
        if mi != -1:
            mi = (mi+n)%len(self.modeOrder)
            self.choose_mode(self.modeOrder[mi])

    def change_voice(self, i, player):
        self.voice = (self.voice + i)%len(player.voices)

    def addtool(self, label):
        if isinstance(label, basestring):
            self.winToolbar.addstr(label.encode('utf-8'))
        elif hasattr(label, '__iter__'):
            self.winToolbar.addstr(label[0].encode('utf-8'), curses.A_REVERSE)
            self.winToolbar.addstr(':')
            self.winToolbar.addstr(label[1].encode('utf-8'))
        self.winToolbar.addstr(CursesVisualizer.TOOLSEP)

    def display_toolbar(self):
        self.winToolbar.erase()
        self.winToolbar.move(0, 1)
        self.winToolbar.addstr(self.mode[1].upper(), curses.A_REVERSE)
        self.winToolbar.addstr(CursesVisualizer.TOOLSEP)
        for label in self.modeScreens[self.mode].get_toolbar_labels():
            self.addtool(label)

        self.winToolbar.move(1, 1)
        for label in self.get_toolbar_labels():
            self.addtool(label)

        title = 'MELODOMATIC'
        c = self.winToolbar.getmaxyx()[1] - 1 - len(title)
        self.winToolbar.addstr(1, c, title, curses.A_BOLD)
        self.winToolbar.noutrefresh()

    def check_key(self, player):
        c = self.screen.getch()
        if c == -1:
            return 0
        rv = self.modeScreens[self.mode].check_key(c, player)
        if rv:
            return rv
        k = curses.keyname(c)
        if k in ('^I', ):
            self.rotate_mode(+1)
        elif k in ('KEY_BTAB', ):
            self.rotate_mode(-1)
        elif k in ('M', 'm'):
            self.choose_mode(CursesVisualizer.Mode.MAIN)
        elif k in ('V', 'v'):
            self.choose_mode(CursesVisualizer.Mode.VOICE)
        elif k in ('S', 's'):
            self.choose_mode(CursesVisualizer.Mode.SCALES)
        elif k in ('C', 'c'):
            self.choose_mode(CursesVisualizer.Mode.CONTROLS)
        elif k in ('R', 'r'):
            self.choose_mode(CursesVisualizer.Mode.READER)
        elif k in ('Q', 'q'):
            return 1
        return 0

    def get_toolbar_labels(self):
        rv = []
        for m in CursesVisualizer.Mode.order:
            if m != self.mode:
                rv.append(m)
        rv.append(CursesVisualizer.TOOLSEP)
        rv.append([ u'Q', u'Quit' ])
        return rv

class FakeSysOut:
    def __init__(self):
        self.buffer = collections.deque(tuple(), STATUSBUFFERLEN)
    def flush(self):
        self.buffer.clear()
    def write(self, data):
        if data != '\n':
            self.buffer.append(data)

