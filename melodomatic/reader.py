"""
This module handles reading and parsing of scripts.
"""

import os
import os.path
import time
from melodomatic import consts
from melodomatic.util import *
from melodomatic import expanders, player, voice, scale, control

# Dictionary of valid blocks (:) and parameters (.) in script. Does not include directives (!).
BLOCK_LABELS = {
        'PLAYER': [
            'BEATS_PER_MINUTE', 'BPM',
            'PULSES_PER_BEAT', 'PPB',
            'RELOAD_INTERVAL',
            'START_SCALE',
            'VISUALIZATION_WINDOW',
            'MIDI_PORT',
            'SEED',
            ],
        'SCALE': [
            'SEED',
            'MOVE_TIME', 'MT',
            'MOVE_LINK', 'ML',
            'ROOT',
            'INTERVALS',
            'PITCHES',
            ],
        'VOICE': [
            'CHANNEL',
            'SEED',
            'MUTE',
            'SOLO',
            'MOVE_TIME', 'MT',
            'MOVE_LINK', 'ML',
            # All other parameters are driven by the voice generator.
            ],
        'CONTROL': [
            'CHANNEL',
            'SEED',
            'RATE',
            'VOICE',
            'CONTROL_ID',
            'CID',
            'CONTROL_VALUE',
            'CVAL',
            'PITCHBEND',
            'AFTERTOUCH',
            ],
        }

class Parser:
    """
    I am responsible for parsing script data and configuring a Player instance
    based on what I find.  Along the way, I am responsible for creating Scales
    and Voices and attaching them to the player.
    """

    def __init__(self):
        """ Initialize members. No parsing happens here. """
        self.text = ''
        self.data = []
        self.reader = None
        self.player = None
        self.scriptdir = ''
        self.buf = []

    def make_player(self, lines, reader, oldPlayer, scriptdir=''):
        """
        Parse the script in the given Reader instance and return a new Player instance.

        If oldPlayer is given, pass it to the Player to transfer its most recent state.
        """
        self.scriptdir = scriptdir
        self.text = lines
        self.data = []
        self.reader = reader
        self.player = player.Player()
        self._prepreprocess() # you're not funny
        self._preprocess()
        self._parse()
        self._build_player()
        if oldPlayer:
            self.player.transfer_state(oldPlayer)
        if consts.VERBOSE:
            self.player.dump()
        return self.player

    def _parse(self):
        self.data = []
        self.buf = []

        def clear_buf():
            if self.buf:
                # Slice the buffer into a definition block.
                block = []
                bbuf = []
                for i in self.buf:
                    # Each parameter starts with '.'
                    # But make sure we don't catch decimal numbers!
                    if len(i) > 1 and i[0] == '.' and not is_int(i[1]):
                        if bbuf:
                            block.append(bbuf)
                        bbuf = [i,]
                    else:
                        bbuf.append(i)
                if bbuf:
                    block.append(bbuf)
                self.data.append(block)
            self.buf = []

        for _, line in enumerate(self.text):
            line = line.split('#')[0].strip()
            if len(line) == 0:
                continue
            line = line.replace('(',' ( ').replace(')', ' ) ')
            a = line.strip().split()
            if line[0] == ':':
                # clean up the previous block and start a new one.
                clear_buf()
                self.buf = a
            else:
                # The current data block spans multiple lines, so just append to it.
                if self.buf:
                    self.buf.extend(a)
        clear_buf()

    def _prepreprocess(self):
        """
        Replace !INCLUDE calls with the lines of the included file.
        Relative paths are relative to the script.
        """

        toInsert = []
        for linei,line in enumerate(self.text):
            if line.upper().startswith('!INCLUDE'):
                fn = line[len('!INCLUDE'):].split('#')[0].strip()
                if not os.path.isabs(fn):
                    fn = os.path.join(self.scriptdir, fn)
                with open(fn) as fp:
                    lines = fp.readlines()
                toInsert.append((linei, lines))
                if consts.VERBOSE:
                    print('!include %s'%fn)
        for linei,chunk in reversed(toInsert):
            # splice the lines in over the include call.
            self.text[linei+1:1] = chunk
            del self.text[linei]

    def _preprocess(self):
        """
        Handle preprocessing directives other than !include:
        !define - define macros
        @       - perform macro substitutions. We only do one pass,
                  so definitions *must* come before references.
        """
        macros = []
        todel = []
        defining = []
        for linei,line in enumerate(self.text):
            if len(defining) == 2:
                todel.append(linei)
                a = line.split()
                val = ' '.join(a)
                if len(val) > 0 and val[-1] == '\\':
                    defining[1] = '%s %s'%(defining[1], val[:-1])
                else:
                    defining[1] = '%s %s'%(defining[1], val)
                    macros.append((defining[0], defining[1]))
                    defining = []

            elif line.strip().upper().startswith('!DEFINE'):
                todel.append(linei)
                line = line.strip()[len('!DEFINE'):].split('#')[0]
                a = line.split()
                mid = a[0].strip()
                val = ' '.join(a[1:])
                if len(val) > 0 and val[-1] == '\\':
                    defining = [mid, val[:-1]]
                else:
                    macros.append((mid, val))
                continue

            if '@' in line:
                for macro in macros:
                    self.text[linei] = self.text[linei].replace('@'+macro[0], macro[1])
                    line = self.text[linei]
                if '@' in line:
                    if consts.VERBOSE:
                        print('ERROR line %d: unresolved macro reference [%s]'%(linei, line[:-1]))

        # Remove preprocessor lines so they don't much with things later.
        for linei in reversed(todel):
            del self.text[linei]

    def _build_player(self):
        scaleIDs = set()
        voiceIDs = set()

        # Process player info first, no mattter where it was in the file (because so many things depend on ppb being set)...
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == 'PLAYER':

                # Do one pass just to look for ppb and bpm, since so many other things depend on them being set.
                for ca in block[1:]:
                    cmd = self.autocomplete_label(ca[0], btype)
                    if cmd in ('BEATS_PER_MINUTE', 'BPM'):
                        bpm = int(ca[1])
                        self.player.change_tempo(bpm, self.player.ppb)
                    elif cmd in ('PULSES_PER_BEAT', 'PPB'):
                        ppb = int(ca[1])
                        self.player.change_tempo(self.player.bpm, ppb)

                # Go through again and get everything else.
                for ca in block[1:]:
                    cmd = self.autocomplete_label(ca[0], btype)
                    if cmd in ('BEATS_PER_MINUTE', 'BPM', 'PULSES_PER_BEAT', 'PPB'):
                        continue
                    if cmd == 'RELOAD_INTERVAL':
                        # This isn't a player property at all! It's on the reader.
                        if self.reader:
                            self.reader.reloadInterval = self.player.parse_duration(ca[1])[0]
                    elif cmd == 'START_SCALE':
                        self.player.startScale = ca[1]
                    elif cmd == 'VISUALIZATION_WINDOW':
                        self.player.visualizationWindow = self.player.parse_duration(ca[1])[0]
                    elif cmd == 'MIDI_PORT':
                        self.player.midiPortName = ' '.join(ca[1:])
                    elif cmd == 'SEED':
                        self.player.set_seed(ca[1])
                    elif consts.VERBOSE:
                        print('ERROR: Bad player command .%s'%cmd)

            # while we're here, build lists of valid scale and voice IDs.
            elif btype == 'SCALE':
                scid = 'DUMMY'
                if len(block[0]) > 1:
                    scid = block[0][1].strip()
                scaleIDs.add(scid)
            elif btype == 'VOICE':
                vid = 'DUMMY'
                if len(block[0]) > 1:
                    vid = block[0][1].strip()
                voiceIDs.add(vid)

        # ...Then build scales...
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == 'SCALE':
                self._build_scale(block, scaleIDs)

        # ...Then build voices...
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == 'VOICE':
                self._build_voice(block, voiceIDs)

        # ...Then build controls.
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == 'CONTROL':
                self._build_control(block)

    def _build_scale(self, block, scaleIDs):
        if len(block[0]) < 2:
            if consts.VERBOSE:
                print('ERROR: Scale block has no ID')
            block[0].append('DUMMY')
        sc = scale.Scale(block[0][1].strip(), self.player)
        for ca in (expanders.expand_list(b) for b in block[1:]):
            cmd = self.autocomplete_label(ca[0], ':SCALE')
            if cmd == 'ROOT':
                if len(ca) > 1 and is_int(ca[1]):
                    n = int(ca[1])
                    if 0 <= n <= 127:
                        sc.set_root(int(ca[1]))
            elif cmd == 'INTERVALS':
                if len(ca) > 1:
                    a = split_ints(ca[1:])
                    if len(a) > 0:
                        sc.set_intervals(a)
            elif cmd == 'PITCHES':
                if len(ca) > 1:
                    a = split_ints(ca[1:])
                    if len(a) > 0:
                        sc.set_pitches(a)
            elif cmd in ('MOVE_TIME', 'MT'):
                sc.set_move_timer(ca[1:])
            elif cmd in ('MOVE_LINK', 'ML'):
                # try to strip out invalid links before setting
                sc.set_move_linker(tuple((id for id in ca[1:] if id in scaleIDs or id[0] == '$')))
            elif cmd == 'SEED':
                sc.set_seed(ca[1])
            elif consts.VERBOSE:
                print('ERROR: Bad scale command .%s'%cmd)
        self.player.add_scale(sc)

    def _build_voice(self, block, voiceIDs):
        if len(block[0]) < 2:
            if consts.VERBOSE:
                print('ERROR: Voice block has no ID')
            block[0].append('DUMMY')
        vid = block[0][1].strip()
        vo = voice.Voice(vid, self.player)

        # set special parameters before generator-specific ones
        skipit = []
        for ca in (expanders.expand_list(b) for b in block[1:]):
            cmd = self.autocomplete_label(ca[0], ':VOICE')
            if cmd == 'CHANNEL':
                # Channel comes in on range [1-16], but should be stored
                # and sent on range [0-15]!
                if len(ca) > 1 and is_int(ca[1]):
                    vo.channel = clamp(int(ca[1])-1, 0, 127)
                skipit.append(ca[0])
            elif cmd == 'SEED':
                if len(ca) > 1:
                    vo.set_seed(ca[1])
                skipit.append(ca[0])
            elif cmd == 'MUTE':
                vo.set_mute(True)
                skipit.append(ca[0])
            elif cmd == 'SOLO':
                vo.set_solo(True)
                skipit.append(ca[0])
            elif cmd in ('MOVE_TIME', 'MT'):
                vo.set_move_timer(ca[1:])
                skipit.append(ca[0])
            elif cmd in ('MOVE_LINK', 'ML'):
                # try to strip out invalid links before setting
                vo.set_move_linker(tuple((vid for vid in ca[1:] if vid in voiceIDs or vid[0] == '$')))
                skipit.append(ca[0])

        gn = ''
        if len(block[0]) > 2:
            gn = block[0][2]
        vo.set_generator(gn)

        for ca in (expanders.expand_list(b) for b in block[1:]):
            if ca[0] in skipit:
                continue
            if not vo.set_parameter(ca) and consts.VERBOSE:
                print('ERROR: Bad voice command .%s'%cmd)

        vo.validate_generator()
        self.player.add_voice(vo)

    def _build_control(self, block):
        if len(block[0]) < 2:
            if consts.VERBOSE:
                print('ERROR: Control block has no ID')
            block[0].append('DUMMY')
        cid = block[0][1].strip()
        co = control.Control(cid, self.player)

        for ca in (expanders.expand_list(b) for b in block[1:]):
            cmd = self.autocomplete_label(ca[0], ':CONTROL')
            if cmd == 'CHANNEL':
                # Channel comes in on range [1-16], but should be stored
                # and sent on range [0-15]!
                if len(ca) > 1 and is_int(ca[1]):
                    co.channel = clamp(int(ca[1])-1, 0, 127)
            elif cmd == 'SEED':
                if len(ca) > 1:
                    co.set_seed(ca[1])
            else:
                if len(ca) > 1:
                    co.set_parameter(cmd, ca[1:])

        self.player.add_control(co)

    def autocomplete_type(self, d):
        """ Expand a shortened block label to its proper form. """
        if d.startswith(':'):
            d = d[1:]
        d = d.upper()
        for directive in BLOCK_LABELS:
            if directive.startswith(d):
                return directive
        return d

    def autocomplete_label(self, c, ctx):
        """ Expand a shortened parameter label to its proper form. Requires a valid block label as context. """
        if c.startswith('.'):
            c = c[1:]
        c = c.upper()
        if ctx.startswith(':'):
            ctx = ctx[1:]
        if ctx not in BLOCK_LABELS:
            return c
        for command in BLOCK_LABELS[ctx]:
            if command.startswith(c):
                return command
        return c


class Reader:
    """
    I am responsible for reading a script file and feeding its contents to a
    Parser.

    I am also responsible for checking for changes to the file at regular
    intervals and rebuilding the Player when that happens.
    """

    def __init__(self, fn):
        """ Initialize values. Don't open the file yet. """
        self.filename = fn
        self.filetime = time.time()
        self.reloadInterval = consts.DEFAULT_RELOAD_INTERVAL
        self.status = ''

    def load_script(self, ts, oldPlayer=None):
        """ Load the file and send the script through a Parser. Returns a new Player instance. """
        fp = None
        try:
            self.filetime = os.stat(self.filename).st_mtime
            lines = []
            with open(self.filename) as fp:
                lines = fp.readlines()
            rv = Parser().make_player(lines, self, oldPlayer, os.path.dirname(self.filename))
            if consts.VERBOSE:
                print('(Re)load at %d, hotload interval %d'%(ts, self.reloadInterval))
            return rv
        except Exception as e:
            print(e)
            if fp:
                fp.close()
            return oldPlayer

    def update(self, pulse):
        """ Check whether the file has been touched and needs to be reparsed. Return True if so. """
        self.status = ''
        if pulse%self.reloadInterval == 0:
            self.status = '_'
            try:
                t = os.stat(self.filename).st_mtime
                if t != self.filetime:
                    self.status = '*'
                    return True
            except Exception as e:
                print(e)
        return False

