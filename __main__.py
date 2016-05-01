import argparse, time
import consts
from util import *
import reader

class MelodomaticMain:
    def __init__(self, fn):
        self.filename = fn
        self.reader = reader.Reader(self.filename)
        self.statuses = []

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
                if self.reader:
                    if self.reader.update(self.player.pulse):
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

    # Update the status string and print it out.
    def update_status(self):
        newstats = [ self.player.status, ]
        for v in self.player.voiceOrder:
            newstats.append(self.player.voices[v].status)

        doit = False
        s = '%06d'%self.player.pulse
        s += '%2s'%self.reader.status
        for i in xrange(len(newstats)):
            # Try not to repeat status messages.
            if i < len(self.statuses) and self.statuses[i] == newstats[i]:
                if i==0 or not newstats[i]:
                    s += str.center('', 9)
                else:
                    s += str.center('|', 9)
            else:
                doit = True
                s += str.center(newstats[i], 9)

        if doit or self.player.pulse%self.player.visualizationWindow==0:
            print s
        self.statuses = newstats


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='File containing player data.')
    parser.add_argument('-s', '--seed', dest='seed', action='store', help='Seed value for random numbers.')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true', help='Don\'t print out visualization junk.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print extra debug spam.')
    parser.add_argument('-i', '--import', dest='ifile', action='store', help='Custom code to be imported. Totally unsafe!')
    args = parser.parse_args()
    if args.verbose:
        consts.set_verbose(True)
    if args.quiet:
        consts.set_quiet(True)

    if args.ifile:
        fp = open(args.ifile)
        code = fp.read()
        fp.close()
        exec(code) # oh my god

    seed_random(args.seed)

    main = MelodomaticMain(args.filename)
    main.load()
    main.run()

