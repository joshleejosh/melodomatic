import argparse, time
import consts
from util import *
import reader

class MelodomaticMain:
    def __init__(self, fn):
        self.filename = fn
        self.reader = reader.Reader(self.filename)

    def load(self):
        self.player = self.reader.load_script(0)

    def run(self):
        if not self.player.is_valid():
            if consts.VERBOSE:
                print 'Ending: empty script'
            return
        self.player.startup()
        lastt = t = time.time()

        try:
            while True:
                # update time
                lastt = t
                t = time.time()
                dt = t - lastt

                # check for a file change
                if self.reader.update(self.player.pulse):
                    # if the file has changed, build a new player and swap it in for the old one.
                    self.player = self.reader.load_script(self.player.pulse, self.player)
                    if not self.player.is_valid():
                        if consts.VERBOSE:
                            print 'Ending: empty script'
                        break

                # play some music!
                if not self.player.update():
                    break

                if not consts.QUIET:
                    self.update_status()

                # wait for next pulse
                nextt = t + self.player.pulseTime
                waitt = nextt - time.time()
                if waitt > 0:
                    time.sleep(waitt)
                self.player.tick()

        except KeyboardInterrupt:
            if consts.VERBOSE:
                print 'Ending: hit ^C'
            pass
        except:
            self.player.shutdown()
            raise
        self.player.shutdown()

    # Update our half-baked visualization string and print it out.
    def update_status(self):
        statuses = [ ]
        if self.player.curScale:
            statuses.append(self.player.curScale.status)
        else:
            statuses.append('')

        #statuses.extend((self.player.voices[v].status for v in self.player.voiceOrder))
        # Unison voices don't get their own status, they just decorate their parent voice's.
        vstatus = {}
        for vk in self.player.voiceOrder:
            v = self.player.voices[vk]
            if v.generator.name == 'UNISON':
                uv = self.player.voices[v.parameters['VOICE'].next()]
                vstatus[uv.id] += ('\'' if uv.status not in ('', '|') else '')
            else:
                vstatus[v.id] = v.status
        statuses.extend((vstatus[v] for v in self.player.voiceOrder if vstatus.has_key(v)))

        #statuses.extend((self.player.controls[v].status for v in self.player.controlOrder))
        controlStatus = ''
        if any(((self.player.controls[c].status != '') for c in self.player.controlOrder)):
            controlStatus = '+'

        doit = False
        s = '%06d'%self.player.pulse
        s += '%2s'%self.reader.status
        s += '%2s'%controlStatus
        for i in xrange(len(statuses)):
            if statuses[i].strip() not in ('', '|'):
                doit = True
            s += str.center(statuses[i], 9)

        if doit or self.player.pulse%self.player.visualizationWindow == 0:
            print s


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='file containing player script')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true', help='don\'t print out visualization junk')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='print extra debug spam')
    args = parser.parse_args()
    if args.verbose:
        consts.set_verbose(True)
    if args.quiet:
        consts.set_quiet(True)

    main = MelodomaticMain(args.filename)
    main.load()
    main.run()

