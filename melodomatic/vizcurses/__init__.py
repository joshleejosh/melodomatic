# encoding: utf-8
import sys, curses, curses.panel, collections, time
import melodomatic
from melodomatic.viz import *
from melodomatic.util import *

# pylint: disable-all

class CursesVisualizer(melodomatic.viz.Visualizer):
    TOOLBARHEIGHT = 2
    TOOLSEP = '   '
    class Mode:
        MAIN     = ('1', 'Main')
        VOICE    = ('2', 'Voice')
        SCALES   = ('3', 'Scales')
        CONTROLS = ('4', 'Controls')
        READER   = ('5', 'Reader')
        order    = ( MAIN, VOICE, SCALES, CONTROLS, READER )

    def __init__(self, scr):
        Visualizer.__init__(self)
        self.screen = scr
        self.modeScreens = {
                CursesVisualizer.Mode.MAIN: ModeMain(self),
                CursesVisualizer.Mode.VOICE: ModeVoice(self),
                CursesVisualizer.Mode.SCALES: ModeScales(self),
                CursesVisualizer.Mode.CONTROLS: ModeControls(self),
                CursesVisualizer.Mode.READER: ModeReader(self),
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

        for m in list(self.modeScreens.values()):
            m.startup()
        height = self.screen.getmaxyx()[0] - 1
        width = self.screen.getmaxyx()[1] - 1
        self.winToolbar = curses.newwin(2, width, height-2, 0)

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.fakeOut = FakeSysOut()
        sys.stdout = self.fakeOut
        sys.stderr = self.fakeOut

        self.paint_toolbar()
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
        #self.paint_toolbar()
        curses.doupdate()
        return self.check_key(player)

    def choose_mode(self, newmode):
        if self.mode != newmode:
            self.modeScreens[self.mode].hide()
            self.mode = newmode
            self.paint_toolbar()

    def rotate_mode(self, n):
        mi = CursesVisualizer.Mode.order.index(self.mode)
        if mi != -1:
            mi = (mi+n)%len(CursesVisualizer.Mode.order)
            self.choose_mode(CursesVisualizer.Mode.order[mi])

    def change_voice(self, i, player):
        self.voice = (self.voice + i)%len(player.voices)

    def mute_voice(self, player):
        vk = player.voiceOrder[self.voice]
        voice = player.voices[vk]
        voice.set_mute(not voice.mute)
        player.resolve_solos()

    def solo_voice(self, player):
        vk = player.voiceOrder[self.voice]
        voice = player.voices[vk]
        osolo = voice.solo
        voice.set_solo(not voice.solo)
        if osolo and not voice.solo:
            nosolos = True
            for v in list(player.voices.values()):
                if v.solo:
                    nosolos = False
                    break
            if nosolos:
                for v in list(player.voices.values()):
                    if v.mute:
                        v.set_mute(False)
        player.resolve_solos()

    def panic(self, player):
        player.panic()

    def addtool(self, label):
        if isinstance(label, str):
            self.winToolbar.addstr(label.encode('utf-8'))
        elif hasattr(label, '__iter__'):
            self.winToolbar.addstr(label[0].encode('utf-8'), curses.A_REVERSE)
            self.winToolbar.addstr(':')
            self.winToolbar.addstr(label[1].encode('utf-8'))
        self.winToolbar.addstr(CursesVisualizer.TOOLSEP)

    def paint_toolbar(self):
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
        elif k in ('1', ):
            self.choose_mode(CursesVisualizer.Mode.MAIN)
        elif k in ('2', ):
            self.choose_mode(CursesVisualizer.Mode.VOICE)
        elif k in ('3', ):
            self.choose_mode(CursesVisualizer.Mode.SCALES)
        elif k in ('4', ):
            self.choose_mode(CursesVisualizer.Mode.CONTROLS)
        elif k in ('5', ):
            self.choose_mode(CursesVisualizer.Mode.READER)
        elif k in ('^[', '^D', ):
            return 1
        return 0

    def get_toolbar_labels(self):
        rv = []
        for m in CursesVisualizer.Mode.order:
            if m != self.mode:
                rv.append(m)
        rv.append(CursesVisualizer.TOOLSEP)
        rv.append(( 'ESC', 'Quit' ))
        return rv

# ------------------------------------------------------------------ #

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

# ------------------------------------------------------------------ #

class ModeMain(ModeScreen):
    def update(self, player, reader):
        self.win.erase()
        self.win.border()
        rows = self.win.getmaxyx()[0] - 3
        columns = self.win.getmaxyx()[1]-3
        self.paint_headers(player, reader, columns)

        i = len(self.parent.statusBuffer) - 1
        y = rows + 1
        while y >= 2 and i >= 0:
            pulse = self.parent.statusBuffer[i]['pulse']
            line = self.parent.status_line_main(self.parent.statusBuffer[i])
            if (pulse%player.visualizationWindow == 0) or should_force_print(line):
                s = str.ljust(line[0:columns], columns)
                self.win.addstr(y, 1, s)
                y -= 1
            i -= 1

        self.win.noutrefresh()

    def paint_headers(self, player, reader, columns):
        s = str.ljust('', PULSEWIDTH+2+2+VOICEWIDTH)
        for vk in player.voiceOrder:
            s += str.center(player.voices[vk].id, VOICEWIDTH)
        s = str.ljust(s[0:columns], columns)
        self.win.addstr(1, 1, s, curses.A_UNDERLINE)
        self.win.addstr(1, 1, '%d/%d'%(player.bpm, player.ppb), curses.A_UNDERLINE)

    def check_key(self, key, player):
        if key in (ord('P'), ord('p')):
            self.parent.panic(player)
        return 0

    def get_toolbar_labels(self):
        return ( ( 'P', 'Panic' ), )

# ------------------------------------------------------------------ #

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
        self.winConf.addstr(1, 1, 'VOICE %s'%voice.id, curses.A_UNDERLINE)
        if voice.mute:
            self.winConf.addstr(' [MUTE]')
        if voice.solo:
            self.winConf.addstr(' [SOLO]')
        self.winConf.addstr(2,  2, 'channel: ')
        self.winConf.addstr(2, 11, str(voice.channel+1))
        self.winConf.addstr(3,  2, 'seed: ')
        self.winConf.addstr(3, 11, str(voice.rngSeed))
        self.winConf.addstr(5, 1, 'Generator $%s'%voice.generator.name)

        widthPName = max((len(p) for p in list(voice.parameters.keys()))) + 1
        widthGName = max((len(g.name) for g in list(voice.parameters.values()))) + 1
        y = 6
        for p,g in list(voice.parameters.items()):
            if y >= rows - 1:
                break
            self.winConf.addstr(y, 2, p)
            self.winConf.addstr(y, widthPName+2, '$%s'%g.name)
            dwidth = columns - widthGName - widthPName - 3
            gds = ' '.join(g.data)
            while len(gds) > dwidth:
                gdt = gds[0:dwidth]
                gds = gds[dwidth:]
                self.winConf.addstr(y, widthGName+widthPName+3, gdt)
                y += 1
            self.winConf.addstr(y, widthGName+widthPName+3, gds)
            y += 1

        self.winConf.noutrefresh()

    def update_stat(self, player, reader):
        self.winStat.erase()
        self.winStat.border()
        height = self.winStat.getmaxyx()[0]-1
        columns = self.winStat.getmaxyx()[1]-3
        y = height - 1
        for i in range(len(self.parent.statusBuffer)-1, -1, -1):
            if y < 1:
                break
            pulse = self.parent.statusBuffer[i]['pulse']
            line = self.parent.status_line_voice(self.parent.statusBuffer[i], player.voiceOrder[self.voice])
            if (pulse%player.visualizationWindow == 0) or should_force_print(line):
                s = str.ljust(line[0:columns], columns)
                self.winStat.addstr(y, 1, s)
                y -= 1
        self.winStat.noutrefresh()

    def check_key(self, key, player):
        if key in (ord('M'), ord('m')):
            self.parent.mute_voice(player)
        elif key in (ord('S'), ord('s')):
            self.parent.solo_voice(player)
        elif key in (ord('P'), ord('p')):
            self.parent.panic(player)
        elif key in (ord('v'), curses.KEY_RIGHT, ord('2')):
            self.parent.change_voice(1, player)
        elif key in (ord('V'), curses.KEY_LEFT, ord('@')):
            self.parent.change_voice(-1, player)
        return 0

    def get_toolbar_labels(self):
        return (
                ( 'M', 'Mute' ),
                ( 'S', 'Solo' ),
                ( 'P', 'Panic' ),
                ( '←/→', 'Prev/Next Voice' ),
                )

# ------------------------------------------------------------------ #

class ModeControls(ModeScreen):
    def update(self, player, reader):
        self.win.erase()
        self.win.border()
        height = self.win.getmaxyx()[0]-1
        width = self.win.getmaxyx()[1]-1
        columns = width - 2
        self.paint_headers(player, reader, columns)

        y = height - 1
        for i in range(len(self.parent.statusBuffer)-1, -1, -1):
            if y < 2:
                break
            pulse = self.parent.statusBuffer[i]['pulse']
            line = self.parent.status_line_controls(self.parent.statusBuffer[i])
            if (pulse%player.visualizationWindow == 0) or should_force_print(line):
                s = str.ljust(line[0:columns], columns)
                self.win.addstr(y, 1, s)
                y -= 1

        self.win.noutrefresh()

    def paint_headers(self, player, reader, columns):
        s = str.ljust('', PULSEWIDTH+2)
        for vk in player.controlOrder:
            s += str.center('%s/%d'%(player.controls[vk].id, player.controls[vk].channel+1), VOICEWIDTH)
        s = str.ljust(s[0:columns], columns)
        self.win.addstr(1, 1, s, curses.A_UNDERLINE)

    def check_key(self, key, player):
        if key in (ord('P'), ord('p')):
            self.parent.panic(player)
        return 0

    def get_toolbar_labels(self):
        return ( ( 'P', 'Panic' ), )

# ------------------------------------------------------------------ #

class ModeScales(ModeScreen):
    def update(self, player, reader):
        self.win.erase()
        self.win.border()
        rows = self.win.getmaxyx()[0] - 3
        cols = self.win.getmaxyx()[1] - 3

        self.win.addstr(1, 1, 'CURRENT SCALE: %s'%player.curScale.id, curses.A_UNDERLINE)
        eta = player.curScale.changeTime - player.pulse
        self.win.addstr(2, 1, 'next scale: $%s %s'%(player.curScale.moveLinker.name, ' '.join(player.curScale.moveLinker.data) ))
        self.win.addstr(3, 1, '        in: %d.%d'%(int(eta/player.ppb), eta%player.ppb))

        y = 5
        for sk in player.scaleOrder:
            if y >= rows - 1:
                break
            scale = player.scales[sk]
            self.win.addstr(y, 2, scale.id, curses.A_BOLD)
            self.win.addstr(', seed=%s'%scale.rngSeed)
            self.win.addstr(y+1, 5, '%s [%d + %s]'%(scale.pitches, scale.root, scale.intervals))
            self.win.addstr(y+2, 5, 'move: $%s %s -> $%s %s'%(scale.moveTimer.name, ' '.join(scale.moveTimer.data), scale.moveLinker.name, ' '.join(scale.moveLinker.data)))
            y += 3

        self.win.noutrefresh()

# ------------------------------------------------------------------ #

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
        self.winRdr.addstr(1, 1, 'FILE: %s'%reader.filename, curses.A_UNDERLINE)
        self.winRdr.addstr(2, 1, 'last modified at: %s'%time.ctime(reader.filetime))
        self.winRdr.addstr(3, 4, 'next check in: %d'%(reader.reloadInterval - player.pulse%reader.reloadInterval))
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
            self.winLog.addstr(y, 1, line[0:cols].encode('utf-8')) # TODO: horizontal scroll
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
                ( 'F', 'Flush Messages' ),
                ( '↑ ↓ PGUP PGDN HOME END', 'Scroll Log' ),
                )

# ------------------------------------------------------------------ #

class FakeSysOut:
    def __init__(self):
        self.buffer = collections.deque(tuple(), STATUSBUFFERLEN)
    def flush(self):
        self.buffer.clear()
    def write(self, data):
        if data != '\n':
            self.buffer.append(data)

# ------------------------------------------------------------------ #

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

