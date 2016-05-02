import os, os.path, imp, sys, time, re
import consts
from util import *
import generators, player, voice, scale

BLOCK_LABELS = {
        ':PLAYER': [
            'BEATS_PER_MINUTE', 'BPM',
            'PULSES_PER_BEAT', 'PPB',
            'SCALE_CHANGE_TIMES',
            'RELOAD_INTERVAL',
            'START_SCALE',
            'VISUALIZATION_WINDOW'
            ],
        ':SCALE': [ 'ROOT', 'INTERVALS', 'PITCHES', 'LINKS' ],
        ':VOICE': [ 'CHANNEL', 'PITCH', 'TRANSPOSE', 'DURATION', 'VELOCITY', 'FOLLOW' ],
        }

RE_EVAL = re.compile(r'\{([^}]*)\}')

# I am responsible for parsing script data and configuring a Player instance
# based on what I find.  Along the way, I am responsible for creating Scales
# and Voices and attaching them to the player.
class Parser:
    def __init__(self):
        self.text = ''
        self.data = []
        self.reader = None
        self.player = None

    def make_player(self, lines, reader, oldPlayer):
        self.text = lines
        self.data = []
        self.reader = reader
        self.player = player.Player()
        self.prepreprocess() # not funny
        self.preprocess()
        self.parse()
        self.build_player()
        if oldPlayer:
            self.player.transfer_state(oldPlayer)
        return self.player

    def parse(self):
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

        for linei in xrange(len(self.text)):
            line = self.text[linei].split('#')[0].strip()
            if len(line) == 0:
                continue
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

    # Replace include calls with the lines of the included file.
    def prepreprocess(self):
        toInsert = []
        for linei,line in enumerate(self.text):
            if line.upper().startswith('!INCLUDE'):
                fn = line[len('!INCLUDE'):].split('#')[0].strip()
                fp = open(fn)
                lines = fp.readlines()
                fp.close()
                toInsert.append((linei, lines))
                if consts.VERBOSE:
                    print '!include %s'%fn
        for i in reversed(toInsert):
            line = i[0]
            chunk = i[1]
            # splice the lines in over the include call.
            del self.text[line]
            self.text[line:1] = chunk

    # Handle preprocessing directives other than !include:
    # !import - import python code (totally unsafe!)
    # !define - define macros
    # @       - perform macro substitutions. We only do one pass, so
    #           definitions *must* come before references.
    # { }     - evaluate inline expressions (also unsafe!)
    def preprocess(self):
        macros = []
        todel = []
        for linei,line in enumerate(self.text):
            if line.strip().upper().startswith('!IMPORT'):
                fn = line.strip()[len('!IMPORT'):].split('#')[0].strip()
                mname,ext = os.path.splitext(os.path.split(fn)[-1])
                imp.load_source(mname, fn)
                todel.append(linei)
                if consts.VERBOSE:
                    print '!import %s'%fn
                continue

            if line.strip().upper().startswith('!DEFINE'):
                line = line.strip()[len('!DEFINE'):].split('#')[0]
                a = line.split()
                id = a[0].strip()
                val = ' '.join(a[1:])
                macros.append((id, val))
                todel.append(linei)
                continue

            if '@' in line:
                for macro in macros:
                    self.text[linei] = self.text[linei].replace('@'+macro[0], macro[1])
                    line = self.text[linei]
                if '@' in line:
                    if consts.VERBOSE:
                        print 'ERROR line %d: unresolved macro reference [%s]'%(linei, line[:-1])

            if '{' in line and '}' in line:
                for code in RE_EVAL.findall(line):
                    val = ''
                    if code.strip():
                        val = friendly_eval(code)
                    if is_iterable(val):
                        val = ' '.join(str(v) for v in val)
                    else:
                        val = str(val)
                    self.text[linei] = self.text[linei].replace('{%s}'%code, val, 1)
                    line = self.text[linei]
        # Remove preprocessor lines so they don't much with things later.
        for linei in reversed(todel):
            del self.text[linei]

    def build_player(self):
        scaleIDs = set()

        # Process player info first, no mattter where it was in the file (because so many things depend on ppb being set)...
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == ':PLAYER':
                # Do one pass just to look for ppb and bpm, since so many other things depend on them being set.
                for ca in block[1:]:
                    cmd = self.autocomplete_label(ca[0], btype)
                    if cmd == 'BEATS_PER_MINUTE' or cmd == 'BPM':
                        bpm = int(ca[1])
                        self.player.change_tempo(bpm, self.player.ppb)
                    elif cmd == 'PULSES_PER_BEAT' or cmd == 'PPB':
                        ppb = int(ca[1])
                        self.player.change_tempo(self.player.bpm, ppb)
                # Go through again and get everything else.
                for ca in block[1:]:
                    cmd = self.autocomplete_label(ca[0], btype)
                    if cmd == 'SCALE_CHANGE_TIMES':
                        g,d = generators.bind_generator(ca[1:], self.player)
                        if g:
                            self.player.scaleChangeTimer = g
                            self.player.scaleChangeTimerLabel = d
                    elif cmd == 'RELOAD_INTERVAL':
                        # This isn't a player property at all! It's on the reader.
                        self.reader.reloadInterval = self.player.parse_duration(ca[1])
                    elif cmd == 'START_SCALE':
                        self.player.startScale = ca[1]
                    elif cmd == 'VISUALIZATION_WINDOW':
                        self.player.visualizationWindow = self.player.parse_duration(ca[1])
            # while we're here, build a list of valid scale IDs.
            elif btype == ':SCALE':
                scid = block[0][1].strip()
                scaleIDs.add(scid)

        # ...Then build scales...
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == ':SCALE':
                sc = scale.Scale(block[0][1].strip(), self.player)
                for ca in block[1:]:
                    cmd = self.autocomplete_label(ca[0], btype)
                    if cmd == 'ROOT':
                        if len(ca) > 1 and is_int(ca[1]):
                            n = int(ca[1])
                            if n >= 0 and n <= 127:
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
                    elif cmd == 'LINKS':
                        # try to strip out invalid links before setting
                        sc.set_linker(tuple((id for id in ca[1:] if id in scaleIDs or id[0] == '$')))
                    else:
                        if consts.VERBOSE:
                            print 'ERROR: Bad scale command .%s'%cmd
                self.player.add_scale(sc)

        # ...And finally do voices.
        for block in self.data:
            btype = self.autocomplete_type(block[0][0])
            if btype == ':VOICE':
                vo = voice.Voice(block[0][1].strip(), self.player)
                for ca in block[1:]:
                    cmd = self.autocomplete_label(ca[0], btype)
                    if cmd == 'CHANNEL':
                        if len(ca) > 1 and is_int(ca[1]):
                            vo.channel = int(ca[1])
                    elif cmd == 'TRANSPOSE':
                        if len(ca) > 1 and is_int(ca[1]):
                            vo.transpose = int(ca[1])
                    elif cmd == 'FOLLOW':
                        vo.set_follow(ca[1:])
                    elif cmd == 'PITCH':
                        vo.set_pitcher(ca[1:])
                    elif cmd == 'DURATION':
                        vo.set_durationer(ca[1:])
                    elif cmd == 'VELOCITY':
                        vo.set_velocitier(ca[1:])
                self.player.add_voice(vo)

        if consts.VERBOSE:
            self.player.dump()

    def autocomplete_type(self, d):
        if not d.startswith(':'):
            d = ':' + d
        d = d.upper()
        for directive in BLOCK_LABELS.iterkeys():
            if directive.startswith(d):
                return directive
        return d

    def autocomplete_label(self, c, ctx):
        if c.startswith('.'):
            c = c[1:]
        c = c.upper()
        if ctx not in BLOCK_LABELS:
            return c
        for command in BLOCK_LABELS[ctx]:
            if command.startswith(c):
                return command
        return c

# I am responsible for reading a script file and feeding its contents to a Parser.
# I am also responsible for checking for changes to the file at regular
# intervals and rebuilding the Player when that happens.
class Reader:
    def __init__(self, fn):
        self.filename = fn
        self.filetime = time.time()
        self.reloadInterval = consts.DEFAULT_RELOAD_INTERVAL * consts.DEFAULT_PULSES_PER_BEAT
        self.status = ''

    def load_script(self, ts, oldPlayer=None):
        self.filetime = os.stat(self.filename).st_mtime
        fp = open(self.filename)
        lines = fp.readlines()
        fp.close()
        rv = Parser().make_player(lines, self, oldPlayer)
        if consts.VERBOSE:
            print '(Re)load at %d, hotload interval %d'%(ts, self.reloadInterval)
        return rv

    def update(self, pulse):
        self.status = ''
        if pulse%self.reloadInterval == 0:
            t = os.stat(self.filename).st_mtime
            if t != self.filetime:
                self.status = '*'
                return True
            else:
                self.status = '_'
        return False

